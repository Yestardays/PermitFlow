# 飞书开发应用配置

1. 在飞书开放平台创建企业自建应用，开发与生产分别创建，不共用凭证。
2. 启用机器人能力，配置事件订阅地址：`https://<host>/webhooks/feishu/events`。
3. 订阅“接收消息”事件，并配置卡片回调：`https://<host>/webhooks/feishu/card-actions`。
4. 开通以下应用身份权限，并将通讯录数据范围限制为应用可用范围：
   - `im:message`
   - `im:message.p2p_msg:readonly`
   - `im:message.group_at_msg:readonly`
   - `contact:contact.base:readonly`
   - `contact:user.base:readonly`
   - `contact:user.email:readonly`
5. 将 Verification Token、App ID、App Secret 写入对应环境变量。
6. 发布应用并只向测试成员开放；验证后再发布生产应用。

事件订阅使用 `im.message.receive_v1`。卡片回调使用新版 `card.action.trigger`，确认表单采用
Card JSON 2.0。事件入口会先返回成功响应，再在后台调用 LLM、向量服务和飞书发卡，避免超过
飞书事件响应时限后产生重复投递。

当前服务接受飞书 verification token 校验。生产环境若启用 Encrypt Key，应在网关完成解密，
或扩展 webhook 接入层完成飞书 AES 解密后再交给业务服务。
