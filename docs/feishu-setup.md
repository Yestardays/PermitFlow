# 飞书开发应用配置

1. 在飞书开放平台创建企业自建应用，开发与生产分别创建，不共用凭证。
2. 启用机器人能力，配置事件订阅地址：`https://<host>/webhooks/feishu/events`。
3. 订阅“接收消息”事件，并配置卡片回调：`https://<host>/webhooks/feishu/card-actions`。
4. 申请通讯录用户基本信息、邮箱、部门，以及机器人收发消息权限。
5. 将 Verification Token、App ID、App Secret 写入对应环境变量。
6. 发布应用并只向测试成员开放；验证后再发布生产应用。

当前服务接受飞书 verification token 校验。生产环境若启用 Encrypt Key，应在网关完成解密，
或扩展 webhook 接入层完成飞书 AES 解密后再交给业务服务。

