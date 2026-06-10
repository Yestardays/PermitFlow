from collections.abc import Awaitable, Callable
from typing import Any, Protocol, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from permitflow.cards import candidate_card, confirmation_card, result_card
from permitflow.llm import fallback_extract
from permitflow.models import ApplicationDraft, IntentSlots, PermissionItem, UserProfile, Validity
from permitflow.security import assert_direct_manager, assert_self_application


class Knowledge(Protocol):
    async def search(self, query: str, limit: int = 5) -> list[PermissionItem]: ...


class WorkflowState(TypedDict, total=False):
    user_input: str
    slots: dict[str, Any]
    candidates: list[dict[str, Any]]
    selected: dict[str, Any]
    values: dict[str, str]
    validity: str
    confirmed: bool
    response: dict[str, Any]


def build_graph(checkpointer=None):
    async def collect(state: WorkflowState) -> WorkflowState:
        if state.get("selected") and state.get("values") and state.get("validity"):
            return state
        supplied = interrupt({"type": "missing_fields", "state": state})
        return {**state, **supplied}

    async def confirm(state: WorkflowState) -> WorkflowState:
        decision = interrupt({"type": "confirmation", "state": state})
        return {**state, "confirmed": bool(decision.get("confirmed"))}

    graph = StateGraph(WorkflowState)
    graph.add_node("collect_missing", collect)
    graph.add_node("wait_confirm", confirm)
    graph.add_edge(START, "collect_missing")
    graph.add_edge("collect_missing", "wait_confirm")
    graph.add_edge("wait_confirm", END)
    return graph.compile(checkpointer=checkpointer)


class PermitFlowService:
    def __init__(
        self,
        knowledge: Knowledge,
        extractor: Callable[[str], Awaitable[IntentSlots]],
        jira_submit: Callable[[ApplicationDraft], Awaitable[Any]],
        session_store,
    ):
        self.knowledge = knowledge
        self.extractor = extractor
        self.jira_submit = jira_submit
        self.sessions = session_store

    async def start(self, thread_id: str, user: UserProfile, user_input: str) -> dict:
        try:
            slots = await self.extractor(user_input[:500])
        except RuntimeError:
            slots = fallback_extract(user_input)
        assert_self_application(user.email, slots.fields.get("applicant_email"))
        query = (
            slots.permission_query
            or " ".join(filter(None, [slots.system, slots.role]))
            or user_input
        )
        candidates = await self.knowledge.search(query)
        if not candidates:
            log_unmatched = getattr(self.knowledge, "log_unmatched", None)
            if log_unmatched:
                await log_unmatched(user.open_id, user_input, slots.model_dump(mode="json"))
            return {
                "type": "unmatched",
                "message": "暂未找到确定的权限项，已记录请求，请联系 IT 服务台。",
            }
        state = {
            "user": user.model_dump(),
            "slots": slots.model_dump(mode="json"),
            "candidates": [item.model_dump(mode="json") for item in candidates],
        }
        if len(candidates) > 1:
            await self.sessions.set(thread_id, state)
            return {"type": "candidates", "card": candidate_card(candidates)}
        return await self._prepare(thread_id, state, candidates[0])

    async def start_for_direct_report(
        self, thread_id: str, requester: UserProfile, applicant: UserProfile, user_input: str
    ) -> dict:
        assert_direct_manager(requester, applicant)
        return await self.start(thread_id, applicant, user_input)

    async def select(self, thread_id: str, permission_name: str) -> dict:
        state = await self.sessions.get(thread_id)
        if not state:
            return {"type": "expired", "message": "会话已过期，请重新发起申请。"}
        selected = next(
            (
                PermissionItem.model_validate(item)
                for item in state["candidates"]
                if item["name"] == permission_name
            ),
            None,
        )
        if not selected:
            raise ValueError("候选权限不存在")
        return await self._prepare(thread_id, state, selected)

    async def _prepare(self, thread_id: str, state: dict, selected: PermissionItem) -> dict:
        slots = IntentSlots.model_validate(state["slots"])
        values = dict(slots.fields)
        for key, value in (
            ("project", slots.project),
            ("role", slots.role),
            ("reason", slots.reason),
        ):
            if value:
                values.setdefault(key, value)
        draft = ApplicationDraft(
            permission=selected,
            applicant=UserProfile.model_validate(state["user"]),
            values=values,
            validity=slots.validity,
        )
        state["draft"] = draft.model_dump(mode="json")
        await self.sessions.set(thread_id, state)
        return {
            "type": "confirm" if not draft.missing_fields else "missing_fields",
            "missing_fields": draft.missing_fields,
            "card": confirmation_card(draft),
        }

    async def confirm(self, thread_id: str, form_values: dict[str, str]) -> dict:
        state = await self.sessions.get(thread_id)
        if not state or "draft" not in state:
            return {"type": "expired", "message": "会话已过期，请重新发起申请。"}
        raw = state["draft"]
        raw["values"].update({k: v for k, v in form_values.items() if k != "validity"})
        if form_values.get("validity"):
            raw["validity"] = Validity(form_values["validity"])
        draft = ApplicationDraft.model_validate(raw)
        if draft.missing_fields:
            return {
                "type": "missing_fields",
                "missing_fields": draft.missing_fields,
                "card": confirmation_card(draft),
            }
        result = await self.jira_submit(draft)
        await self.sessions.delete(thread_id)
        return {"type": "submitted" if result.success else "fallback", "card": result_card(result)}

    async def cancel(self, thread_id: str) -> dict:
        await self.sessions.delete(thread_id)
        return {"type": "cancelled", "message": "已取消本次权限申请。"}
