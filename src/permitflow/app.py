import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from openai import AsyncOpenAI
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from psycopg_pool import AsyncConnectionPool

from permitflow.config import get_settings
from permitflow.feishu import FeishuClient
from permitflow.jira import JiraClient
from permitflow.knowledge import PostgresKnowledgeRepository
from permitflow.llm import EmbeddingClient, IntentExtractor
from permitflow.observability import REQUESTS, configure_logging
from permitflow.persistence import postgres_checkpointer
from permitflow.session import PostgresSessionStore
from permitflow.workflow import PermitFlowService, build_graph

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    pool = AsyncConnectionPool(settings.database_url, open=False)
    await pool.open()
    openai_client = AsyncOpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
    llm = IntentExtractor(openai_client, settings.llm_model)
    embedding = EmbeddingClient(openai_client)
    jira = JiraClient(
        settings.jira_base_url,
        settings.jira_email,
        settings.jira_api_token,
        settings.it_service_desk_url,
    )
    feishu = FeishuClient(settings.feishu_app_id, settings.feishu_app_secret)
    app.state.feishu = feishu
    app.state.service = PermitFlowService(
        PostgresKnowledgeRepository(pool, embedding.embed),
        llm.extract,
        jira.submit,
        PostgresSessionStore(pool, settings.session_ttl_minutes),
    )
    async with postgres_checkpointer(settings.database_url) as checkpointer:
        app.state.graph = build_graph(checkpointer)
        yield
    await pool.close()


app = FastAPI(title="PermitFlow", version="0.1.0", lifespan=lifespan)


def _verify(payload: dict) -> None:
    expected = get_settings().feishu_verification_token
    token = payload.get("token") or payload.get("header", {}).get("token")
    if expected and token != expected:
        raise HTTPException(status_code=403, detail="invalid verification token")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/webhooks/feishu/events")
async def feishu_events(request: Request):
    payload = await request.json()
    _verify(payload)
    if payload.get("type") == "url_verification":
        return {"challenge": payload["challenge"]}
    event = payload.get("event", {})
    if event.get("type") != "message" or event.get("message", {}).get("message_type") != "text":
        return {"ok": True}
    open_id = event["sender"]["sender_id"]["open_id"]
    message = event["message"]
    text = json.loads(message["content"]).get("text", "")[:500]
    profile = await request.app.state.feishu.get_user_profile(open_id)
    result = await request.app.state.service.start(open_id, profile, text)
    if card := result.get("card"):
        await request.app.state.feishu.send_card(open_id, card)
    else:
        await request.app.state.feishu.send_text(open_id, result.get("message", "请求已处理"))
    REQUESTS.labels("message", result["type"]).inc()
    return {"ok": True}


@app.post("/webhooks/feishu/card-actions")
async def card_actions(request: Request):
    payload = await request.json()
    _verify(payload)
    action = payload.get("action", {})
    value = action.get("value", {})
    open_id = payload.get("open_id") or payload.get("operator", {}).get("open_id")
    thread_id = open_id
    kind = value.get("action")
    if kind == "select_permission":
        result = await request.app.state.service.select(thread_id, value["permission_name"])
    elif kind == "confirm_submit":
        result = await request.app.state.service.confirm(thread_id, action.get("form_value", {}))
    elif kind == "cancel":
        result = await request.app.state.service.cancel(thread_id)
    else:
        raise HTTPException(status_code=400, detail="unknown action")
    REQUESTS.labels("card_action", result["type"]).inc()
    return JSONResponse(
        {
            "toast": {"type": "success", "content": result.get("message", "已处理")},
            "card": result.get("card"),
        }
    )


@app.post("/webhooks/jira/status")
async def jira_status(request: Request):
    payload = await request.json()
    open_id = payload.get("open_id")
    ticket = payload.get("issue", {}).get("key")
    status = payload.get("issue", {}).get("fields", {}).get("status", {}).get("name")
    if not open_id or not ticket or not status:
        raise HTTPException(status_code=400, detail="missing notification fields")
    await request.app.state.feishu.send_text(open_id, f"权限工单 {ticket} 状态更新为：{status}")
    return {"ok": True}
