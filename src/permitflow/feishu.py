import json

import httpx

from permitflow.models import UserProfile


def _data(response: httpx.Response) -> dict:
    response.raise_for_status()
    payload = response.json()
    if payload.get("code", 0) != 0:
        raise RuntimeError(
            f"Feishu API failed: code={payload.get('code')} msg={payload.get('msg', 'unknown')}"
        )
    return payload


class FeishuClient:
    def __init__(self, app_id: str, app_secret: str, client: httpx.AsyncClient | None = None):
        self.app_id = app_id
        self.app_secret = app_secret
        self.client = client or httpx.AsyncClient(timeout=10)
        self._tenant_token: str | None = None

    async def _token(self) -> str:
        if self._tenant_token:
            return self._tenant_token
        response = await self.client.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": self.app_id, "app_secret": self.app_secret},
        )
        self._tenant_token = _data(response)["tenant_access_token"]
        return self._tenant_token

    async def get_user_profile(self, open_id: str) -> UserProfile:
        token = await self._token()
        response = await self.client.get(
            f"https://open.feishu.cn/open-apis/contact/v3/users/{open_id}",
            params={"user_id_type": "open_id"},
            headers={"Authorization": f"Bearer {token}"},
        )
        user = _data(response)["data"]["user"]
        departments = user.get("department_ids") or []
        return UserProfile(
            open_id=open_id,
            name=user["name"],
            email=user["email"],
            department=departments[0] if departments else "",
            manager_open_id=user.get("leader_user_id"),
        )

    async def send_card(self, open_id: str, card: dict) -> None:
        token = await self._token()
        response = await self.client.post(
            "https://open.feishu.cn/open-apis/im/v1/messages",
            params={"receive_id_type": "open_id"},
            headers={"Authorization": f"Bearer {token}"},
            json={
                "receive_id": open_id,
                "msg_type": "interactive",
                "content": json.dumps(card, ensure_ascii=False),
            },
        )
        _data(response)

    async def send_text(self, open_id: str, message: str) -> None:
        token = await self._token()
        response = await self.client.post(
            "https://open.feishu.cn/open-apis/im/v1/messages",
            params={"receive_id_type": "open_id"},
            headers={"Authorization": f"Bearer {token}"},
            json={
                "receive_id": open_id,
                "msg_type": "text",
                "content": json.dumps({"text": message[:500]}, ensure_ascii=False),
            },
        )
        _data(response)
