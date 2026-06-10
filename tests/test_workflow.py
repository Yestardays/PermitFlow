from permitflow.models import IntentSlots, JiraResult, PermissionItem, UserProfile, Validity
from permitflow.session import MemorySessionStore
from permitflow.workflow import PermitFlowService


def permission(sensitive=False):
    options = [Validity.ONE_MONTH, Validity.THREE_MONTHS]
    if not sensitive:
        options.append(Validity.PERMANENT)
    return PermissionItem(
        name="GitHub 仓库写权限",
        category="GitHub",
        jira_project_key="ACCESS",
        approver_group="owners",
        required_fields=["repository", "reason"],
        validity_options=options,
        aliases=["github写权限"],
        sensitive=sensitive,
    )


class Repo:
    def __init__(self, items):
        self.items = items

    async def search(self, query, limit=5):
        return self.items


async def test_happy_path_collects_missing_fields_then_submits():
    submitted = []

    async def extract(_):
        return IntentSlots(permission_query="github写权限", fields={"repository": "team/api"})

    async def submit(draft):
        submitted.append(draft)
        return JiraResult(success=True, ticket_key="ACCESS-1", ticket_url="https://jira/ACCESS-1")

    service = PermitFlowService(Repo([permission()]), extract, submit, MemorySessionStore())
    user = UserProfile(open_id="ou_1", name="张三", department="研发", email="z@example.com")

    response = await service.start("thread", user, "申请 github 写权限")
    assert response["type"] == "missing_fields"
    assert response["missing_fields"] == ["reason", "validity"]

    response = await service.confirm("thread", {"reason": "参与开发", "validity": "3个月"})
    assert response["type"] == "submitted"
    assert submitted[0].applicant.email == "z@example.com"


async def test_generic_project_slot_maps_to_selected_resource_field():
    async def extract(_):
        return IntentSlots(
            permission_query="github写权限",
            project="team/api",
            reason="参与开发",
            validity=Validity.THREE_MONTHS,
        )

    async def submit(_):
        raise AssertionError("must not submit before confirmation")

    service = PermitFlowService(Repo([permission()]), extract, submit, MemorySessionStore())
    user = UserProfile(open_id="ou_1", name="张三", department="研发", email="z@example.com")

    response = await service.start("thread", user, "申请 github 写权限")

    assert response["type"] == "confirm"


async def test_multiple_matches_are_presented_as_candidates():
    async def extract(_):
        return IntentSlots(permission_query="github")

    async def submit(_):
        raise AssertionError("must not submit before confirmation")

    service = PermitFlowService(
        Repo([permission(), permission().model_copy(update={"name": "GitHub 只读"})]),
        extract,
        submit,
        MemorySessionStore(),
    )
    user = UserProfile(open_id="ou_1", name="张三", email="z@example.com")
    response = await service.start("thread", user, "github")
    assert response["type"] == "candidates"
    assert len(response["card"]["elements"][0]["actions"]) == 2


async def test_proxy_application_is_rejected():
    async def extract(_):
        return IntentSlots(
            permission_query="github", fields={"applicant_email": "other@example.com"}
        )

    service = PermitFlowService(Repo([permission()]), extract, lambda _: None, MemorySessionStore())
    user = UserProfile(open_id="ou_1", name="张三", email="z@example.com")
    try:
        await service.start("thread", user, "帮别人申请")
    except ValueError as exc:
        assert "仅允许为自己申请" in str(exc)
    else:
        raise AssertionError("proxy application should fail")


async def test_sensitive_permission_rejects_permanent_validity():
    async def extract(_):
        return IntentSlots(permission_query="github", fields={"repository": "a", "reason": "b"})

    service = PermitFlowService(
        Repo([permission(sensitive=True)]), extract, lambda _: None, MemorySessionStore()
    )
    user = UserProfile(open_id="ou_1", name="张三", email="z@example.com")
    await service.start("thread", user, "github")
    try:
        await service.confirm("thread", {"validity": "永久"})
    except ValueError as exc:
        assert "不支持" in str(exc) or "不能" in str(exc)
    else:
        raise AssertionError("permanent validity should fail")


async def test_only_direct_manager_can_start_proxy_application():
    async def extract(_):
        return IntentSlots(permission_query="github")

    service = PermitFlowService(Repo([permission()]), extract, lambda _: None, MemorySessionStore())
    manager = UserProfile(open_id="manager", name="经理", email="m@example.com")
    report = UserProfile(
        open_id="report",
        name="员工",
        email="r@example.com",
        manager_open_id="another-manager",
    )
    try:
        await service.start_for_direct_report("thread", manager, report, "申请 github")
    except ValueError as exc:
        assert "直属上级" in str(exc)
    else:
        raise AssertionError("non-manager proxy application should fail")
