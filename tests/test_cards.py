from permitflow.cards import confirmation_card
from permitflow.models import ApplicationDraft, PermissionItem, UserProfile, Validity


def test_confirmation_card_uses_v2_form_submit():
    permission = PermissionItem(
        name="GitHub 仓库写权限",
        category="GitHub",
        jira_project_key="ACCESS",
        approver_group="owners",
        required_fields=["repository", "reason"],
        validity_options=[Validity.THREE_MONTHS],
        aliases=["github写权限"],
    )
    draft = ApplicationDraft(
        permission=permission,
        applicant=UserProfile(open_id="ou_1", name="张三", email=""),
        values={"repository": "team/api", "reason": "开发联调"},
        validity=Validity.THREE_MONTHS,
    )

    card = confirmation_card(draft)
    form = card["body"]["elements"][1]
    submit = form["elements"][-2]

    assert card["schema"] == "2.0"
    assert form["tag"] == "form"
    assert submit["action_type"] == "form_submit"
