import asyncio
from collections.abc import Mapping

import httpx

from permitflow.models import ApplicationDraft, JiraResult
from permitflow.security import plain_text


class JiraClient:
    def __init__(
        self,
        base_url: str,
        email: str,
        token: str,
        service_desk_url: str,
        client: httpx.AsyncClient | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.service_desk_url = service_desk_url
        self.client = client or httpx.AsyncClient(auth=(email, token), timeout=10)

    async def submit(self, draft: ApplicationDraft) -> JiraResult:
        payload = self._payload(draft)
        for attempt in range(3):
            try:
                response = await self.client.post(f"{self.base_url}/rest/api/3/issue", json=payload)
                response.raise_for_status()
                key = response.json()["key"]
                return JiraResult(
                    success=True, ticket_key=key, ticket_url=f"{self.base_url}/browse/{key}"
                )
            except (httpx.HTTPError, KeyError, ValueError):
                if attempt < 2:
                    await asyncio.sleep(0.05 * (2**attempt))
        return JiraResult(
            success=False, fallback_text=self._fallback(draft), fallback_url=self.service_desk_url
        )

    @staticmethod
    def _payload(draft: ApplicationDraft) -> dict:
        values: Mapping[str, str] = draft.values
        lines = [
            f"申请人：{plain_text(draft.applicant.name)} <{plain_text(draft.applicant.email)}>",
            f"部门：{plain_text(draft.applicant.department)}",
            f"权限：{plain_text(draft.permission.name)}",
            f"有效期：{plain_text(draft.validity or '')}",
            *[f"{plain_text(key)}：{plain_text(value)}" for key, value in values.items()],
        ]
        return {
            "fields": {
                "project": {"key": draft.permission.jira_project_key},
                "issuetype": {"name": draft.permission.issue_type},
                "summary": (
                    f"[权限申请] {plain_text(draft.permission.name, 100)} - "
                    f"{plain_text(draft.applicant.name, 50)}"
                ),
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": "\n".join(lines)}],
                        }
                    ],
                },
                "labels": ["permitflow", plain_text(draft.permission.category, 50)],
            }
        }

    @staticmethod
    def _fallback(draft: ApplicationDraft) -> str:
        fields = "\n".join(f"- {plain_text(k)}：{plain_text(v)}" for k, v in draft.values.items())
        return (
            f"权限：{plain_text(draft.permission.name)}\n申请人：{plain_text(draft.applicant.name)}"
            f"\n有效期：{plain_text(draft.validity or '')}\n{fields}"
        )[:2000]
