from permitflow.models import ApplicationDraft, JiraResult, PermissionItem


def candidate_card(items: list[PermissionItem]) -> dict:
    return {
        "config": {"wide_screen_mode": True},
        "header": {"title": {"tag": "plain_text", "content": "请选择权限类型"}},
        "elements": [
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": item.name},
                        "value": {"action": "select_permission", "permission_name": item.name},
                    }
                    for item in items
                ],
            }
        ],
    }


def confirmation_card(draft: ApplicationDraft) -> dict:
    inputs = []
    for field in draft.permission.required_fields:
        inputs.append(
            {
                "tag": "input",
                "name": field,
                "label": {"tag": "plain_text", "content": field},
                "default_value": draft.values.get(field, ""),
                "placeholder": {"tag": "plain_text", "content": f"请输入{field}"},
            }
        )
    inputs.append(
        {
            "tag": "select_static",
            "name": "validity",
            "placeholder": {"tag": "plain_text", "content": "选择有效期"},
            "initial_option": draft.validity.value if draft.validity else None,
            "options": [
                {"text": {"tag": "plain_text", "content": option.value}, "value": option.value}
                for option in draft.permission.validity_options
            ],
        }
    )
    return {
        "config": {"wide_screen_mode": True, "enable_forward": False},
        "header": {"title": {"tag": "plain_text", "content": "确认权限申请"}},
        "elements": [
            {
                "tag": "markdown",
                "content": f"**权限**：{draft.permission.name}\n**申请人**：{draft.applicant.name}",
            },
            {
                "tag": "form",
                "name": "application",
                "elements": [
                    *inputs,
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "type": "primary",
                                "text": {"tag": "plain_text", "content": "确认提交"},
                                "name": "submit",
                                "value": {"action": "confirm_submit"},
                            },
                            {
                                "tag": "button",
                                "text": {"tag": "plain_text", "content": "取消"},
                                "name": "cancel",
                                "value": {"action": "cancel"},
                            },
                        ],
                    },
                ],
            },
        ],
    }


def result_card(result: JiraResult) -> dict:
    if result.success:
        content = f"申请已提交：[{result.ticket_key}]({result.ticket_url})"
    else:
        content = (
            f"Jira 暂时不可用，请打开[服务台]({result.fallback_url})并粘贴以下内容："
            f"\n```\n{result.fallback_text}\n```"
        )
    return {"elements": [{"tag": "markdown", "content": content}]}
