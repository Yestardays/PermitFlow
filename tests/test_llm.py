from types import SimpleNamespace

from permitflow.llm import EmbeddingClient, IntentExtractor


class FakeCompletions:
    def __init__(self):
        self.kwargs = None

    async def create(self, **kwargs):
        self.kwargs = kwargs
        message = SimpleNamespace(
            content='{"permission_query":"github写权限","system":"GitHub",'
            '"project":null,"role":"写入","reason":null,"validity":null,"fields":{}}'
        )
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeEmbeddings:
    def __init__(self):
        self.kwargs = None

    async def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(data=[SimpleNamespace(embedding=[0.1] * 1536)])


async def test_deepseek_extractor_uses_chat_json_mode():
    completions = FakeCompletions()
    client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    slots = await IntentExtractor(client, "deepseek-v4-pro").extract("申请 github 写权限")
    assert slots.permission_query == "github写权限"
    assert completions.kwargs["response_format"] == {"type": "json_object"}


async def test_embedding_client_requests_pgvector_dimensions():
    embeddings = FakeEmbeddings()
    client = SimpleNamespace(embeddings=embeddings)
    vector = await EmbeddingClient(client, "text-embedding-v4", 1536).embed("监控权限")
    assert len(vector) == 1536
    assert embeddings.kwargs["dimensions"] == 1536
