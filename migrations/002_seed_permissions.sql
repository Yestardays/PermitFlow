INSERT INTO permission_items
(name, category, jira_project_key, issue_type, approver_group, required_fields,
 prerequisites, validity_options, aliases, sensitive, description)
VALUES
('GitHub 仓库只读权限','GitHub','ACCESS','Service Request','github-owners','["repository","reason"]','[]','["1个月","3个月","6个月","12个月","永久"]','["github只读","仓库查看","repo read"]',false,'查看指定代码仓库'),
('GitHub 仓库写权限','GitHub','ACCESS','Service Request','github-owners','["repository","reason"]','[]','["1个月","3个月","6个月","12个月"]','["github写权限","仓库写入","repo write"]',true,'向指定代码仓库推送代码'),
('GitHub 仓库管理员','GitHub','ACCESS','Service Request','github-admins','["repository","reason"]','["GitHub 仓库写权限"]','["1个月","3个月","6个月"]','["github admin","仓库管理员"]',true,'管理仓库配置及成员'),
('Jira 项目浏览权限','Jira','ACCESS','Service Request','jira-owners','["project","reason"]','[]','["1个月","3个月","6个月","12个月","永久"]','["jira查看","jira browse"]',false,'浏览指定 Jira 项目'),
('Jira 项目成员权限','Jira','ACCESS','Service Request','jira-owners','["project","reason"]','[]','["1个月","3个月","6个月","12个月"]','["jira成员","jira编辑"]',false,'创建和编辑 Jira 事项'),
('Jira 项目管理员','Jira','ACCESS','Service Request','jira-admins','["project","reason"]','["Jira 项目成员权限"]','["1个月","3个月","6个月"]','["jira admin","jira管理员"]',true,'管理 Jira 项目配置'),
('CI/CD 流水线查看权限','CI/CD','ACCESS','Service Request','cicd-owners','["pipeline","reason"]','[]','["1个月","3个月","6个月","12个月","永久"]','["流水线查看","pipeline read"]',false,'查看流水线及构建日志'),
('CI/CD 流水线执行权限','CI/CD','ACCESS','Service Request','cicd-owners','["pipeline","environment","reason"]','[]','["1个月","3个月","6个月","12个月"]','["执行流水线","pipeline run","部署权限"]',true,'执行指定环境流水线'),
('CI/CD 流水线管理权限','CI/CD','ACCESS','Service Request','cicd-admins','["pipeline","reason"]','["CI/CD 流水线执行权限"]','["1个月","3个月","6个月"]','["pipeline admin","流水线管理员"]',true,'修改流水线配置'),
('Grafana 面板查看权限','监控','ACCESS','Service Request','observability-owners','["dashboard","reason"]','[]','["1个月","3个月","6个月","12个月","永久"]','["grafana查看","监控面板","dashboard read"]',false,'查看 Grafana 面板'),
('Grafana 面板编辑权限','监控','ACCESS','Service Request','observability-owners','["dashboard","reason"]','[]','["1个月","3个月","6个月","12个月"]','["grafana编辑","dashboard edit"]',false,'编辑 Grafana 面板'),
('Prometheus 查询权限','监控','ACCESS','Service Request','observability-owners','["environment","reason"]','[]','["1个月","3个月","6个月","12个月"]','["prometheus","promql"]',false,'查询 Prometheus 指标'),
('生产日志查看权限','监控','ACCESS','Service Request','sre-approvers','["service","environment","reason"]','[]','["1个月","3个月","6个月"]','["生产日志","prod logs","日志平台"]',true,'查看生产环境应用日志'),
('AWS 开发账号只读权限','云账号','CLOUD','Service Request','cloud-approvers','["account","reason"]','[]','["1个月","3个月","6个月","12个月"]','["aws只读","aws read"]',false,'只读访问 AWS 开发账号'),
('AWS 开发账号开发者权限','云账号','CLOUD','Service Request','cloud-approvers','["account","reason"]','[]','["1个月","3个月","6个月","12个月"]','["aws开发者","aws developer"]',true,'操作 AWS 开发资源'),
('AWS 生产账号只读权限','云账号','CLOUD','Service Request','cloud-prod-approvers','["account","reason"]','[]','["1个月","3个月","6个月"]','["aws生产只读","aws prod read"]',true,'只读访问 AWS 生产账号'),
('阿里云开发账号只读权限','云账号','CLOUD','Service Request','cloud-approvers','["account","reason"]','[]','["1个月","3个月","6个月","12个月"]','["阿里云只读","aliyun read"]',false,'只读访问阿里云开发账号'),
('阿里云开发账号开发者权限','云账号','CLOUD','Service Request','cloud-approvers','["account","reason"]','[]','["1个月","3个月","6个月","12个月"]','["阿里云开发者","aliyun developer"]',true,'操作阿里云开发资源'),
('Kubernetes 开发集群只读权限','云账号','CLOUD','Service Request','platform-approvers','["cluster","namespace","reason"]','[]','["1个月","3个月","6个月","12个月"]','["k8s只读","集群查看","kubectl read"]',false,'查看开发集群资源'),
('Kubernetes 开发集群操作权限','云账号','CLOUD','Service Request','platform-approvers','["cluster","namespace","reason"]','["Kubernetes 开发集群只读权限"]','["1个月","3个月","6个月"]','["k8s操作","集群部署","kubectl write"]',true,'变更开发集群资源')
ON CONFLICT (name) DO NOTHING;

