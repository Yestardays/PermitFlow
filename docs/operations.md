# 运维说明

- `/health` 用于存活检查，`/metrics` 暴露 Prometheus 指标。
- 日志为 JSON，建议采集 `levelname`、`name`、`message` 和请求关联 ID。
- PostgreSQL 保存权限知识、未命中请求、事件和 LangGraph checkpoint。
- Jira webhook 可调用 `/webhooks/jira/status` 向申请人发送状态变化；它不执行审批或开通。
- 申请草稿和 LangGraph checkpoint 均保存在 PostgreSQL，会话 TTL 默认为 30 分钟。
