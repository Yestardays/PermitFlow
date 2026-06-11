from permitflow.app import _card_action, _card_callback_response, _message_event


def test_v2_message_event_is_parsed():
    payload = {
        "header": {"event_type": "im.message.receive_v1"},
        "event": {
            "sender": {"sender_id": {"open_id": "ou_123"}},
            "message": {"message_type": "text", "content": '{"text":"申请 GitHub 权限"}'},
        },
    }

    assert _message_event(payload) == ("ou_123", "申请 GitHub 权限")


def test_legacy_message_event_remains_supported():
    payload = {
        "event": {
            "type": "message",
            "sender": {"sender_id": {"open_id": "ou_old"}},
            "message": {"message_type": "text", "content": '{"text":"hello"}'},
        }
    }

    assert _message_event(payload) == ("ou_old", "hello")


def test_v2_card_action_is_normalized():
    payload = {
        "event": {
            "operator": {"operator_id": {"open_id": "ou_123"}},
            "action": {
                "value": {"action": "confirm_submit"},
                "form_value": {"reason": "开发需要", "validity": "3个月"},
            },
        }
    }

    assert _card_action(payload) == (
        "ou_123",
        {"action": "confirm_submit"},
        {"reason": "开发需要", "validity": "3个月"},
    )


def test_legacy_card_action_is_normalized():
    payload = {
        "open_id": "ou_old",
        "action": {
            "value": {"action": "cancel"},
            "form_value": {},
        },
    }

    assert _card_action(payload) == ("ou_old", {"action": "cancel"}, {})


def test_v2_callback_returns_success_toast():
    card = {"schema": "2.0", "body": {"elements": []}}

    response = _card_callback_response({"type": "submitted", "card": card})

    assert response == {"toast": {"type": "success", "content": "已处理"}}
