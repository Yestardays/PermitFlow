# PermitFlow

企业内部权限申请助手 —— 飞书Bot，帮员工用自然语言描述权限需求，自动匹配、补全信息、确认后提交 Jira 工单。

**只做申请，不碰审批和权限开通。**

## 快速开始

### 前置要求

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)（Python 依赖管理）
- Docker（运行 PostgreSQL + pgvector）

### 1. 克隆项目

```bash
git clone git@github.com:Yestardays/PermitFlow.git
cd PermitFlow
```

### 2. 启动数据库

```bash
docker compose up -d
```

PostgreSQL 16 + pgvector 会自动启动，migrations 目录下的建表脚本和种子数据（20条高频权限）也会自动执行。

### 3. 安装依赖

```bash
uv sync --all-groups
```

### 4. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入以下必填项：

```bash
# LLM（OpenAI 兼容接口，用于意图提取）
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=sk-xxx
LLM_MODEL=deepseek-v4-pro

# Embedding（OpenAI 兼容接口，用于向量检索）
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_API_KEY=sk-xxx
EMBEDDING_MODEL=text-embedding-v4
EMBEDDING_DIMENSIONS=1536

# 飞书（自建应用凭据）
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
FEISHU_VERIFICATION_TOKEN=xxx

# Jira（工单提交）
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=bot@your-company.com
JIRA_API_TOKEN=xxx
IT_SERVICE_DESK_URL=https://your-domain.atlassian.net/servicedesk
```

| 变量 | 说明 |
|---|---|
| `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` | OpenAI 兼容 Chat Completions 接口 |
| `EMBEDDING_BASE_URL` / `EMBEDDING_API_KEY` | OpenAI 兼容 Embeddings 接口 |
| `EMBEDDING_MODEL` / `EMBEDDING_DIMENSIONS` | 向量模型及维度，默认 1536 |
| `FEISHU_APP_ID` / `FEISHU_APP_SECRET` | 飞书自建应用凭据 |
| `FEISHU_VERIFICATION_TOKEN` | 飞书事件订阅校验 Token |
| `JIRA_BASE_URL` / `JIRA_EMAIL` / `JIRA_API_TOKEN` | Jira Cloud 连接凭据 |
| `IT_SERVICE_DESK_URL` | Jira 提交失败时的降级入口 |
| `SESSION_TTL_MINUTES` | 会话过期时间，默认 30 分钟 |
| `ADMIN_TOKEN` | 管理接口鉴权 Token（可选） |

飞书应用配置细节见 [docs/feishu-setup.md](docs/feishu-setup.md)。

### 5. 生成向量索引

首次运行或更新种子数据后，需要为权限条目生成 embedding：

```bash
uv run python scripts/index_embeddings.py
```

### 6. 启动服务

```bash
uv run uvicorn permitflow.app:app --reload
```

服务默认监听 `http://localhost:8000`，健康检查：`/health`。

### 7. 配置飞书回调

在飞书开放平台将应用的**消息事件**和**卡片回调** Webhook URL 分别指向：

- 消息事件：`https://<你的域名>/webhooks/feishu/events`
- 卡片回调：`https://<你的域名>/webhooks/feishu/card-actions`

本地开发需使用反向代理（如 ngrok）暴露公网地址。

## 使用方式

在飞书中给 Bot 发消息，用自然语言描述权限需求：

> "我要 GitHub 上 ant-design 仓库的写权限"

Bot 会：
1. 提取意图（系统、项目、角色）
2. 搜索权限知识库
3. 缺信息时追问，有多个候选时列出供选择
4. 展示飞书确认卡片，可直接编辑表单字段
5. 确认后自动创建 Jira 工单，返回工单链接

## 运行测试

```bash
uv run ruff check .
uv run pytest
```

Jira HTTP 集成测试（需 WireMock 容器）：

```bash
docker compose -f docker-compose.test.yml up -d jira-mock
JIRA_INTEGRATION_URL=http://localhost:18080 uv run pytest tests/test_jira_integration.py
docker compose -f docker-compose.test.yml down
```

## 技术栈

| 层 | 选型 |
|---|---|
| 编排 | LangGraph（Agent + Tool 模式，interrupt 人机确认） |
| 框架 | FastAPI |
| 数据库 | PostgreSQL 16 + pgvector |
| LLM | OpenAI 兼容接口（DeepSeek / 通义千问 / 任意兼容服务） |
| 检索 | ILIKE 精确匹配优先 → pgvector 向量语义兜底 |
| 交互 | 飞书 v2 交互式卡片 |
| 工单 | Jira REST API |
| 依赖 | uv |
| 中间件 | Docker Compose（PG + pgvector） |

### 核心代码

```
src/permitflow/
├── app.py           # FastAPI 路由、生命周期
├── workflow.py      # LangGraph 状态图 + PermintFlowService
├── knowledge.py     # 知识库检索（ILIKE → pgvector）
├── llm.py           # LLM 意图提取 + 嵌入
├── cards.py         # 飞书 v2 卡片构建
├── feishu.py        # 飞书 API 客户端
├── jira.py          # Jira API 客户端（重试 + 降级）
├── session.py       # 会话存储（30min TTL）
├── persistence.py   # LangGraph PostgresSaver
├── security.py      # 输入安全与身份校验
├── models.py        # Pydantic 数据模型
├── config.py        # 配置管理
└── observability.py # 日志与 Prometheus 指标
```

## License

MIT
