from bot.webhook import build_notification_sign, verify_notification


def test_notification_sign_roundtrip():
    params = {
        "notification_type": "p2p-incoming",
        "operation_id": "123",
        "amount": "1000.00",
        "currency": "643",
        "datetime": "2024-01-01T00:00:00Z",
        "sender": "41001",
        "codepro": "false",
        "label": "t1-r2000",
        "sha1_hash": "unused",
    }
    secret = "test-secret"
    sign = build_notification_sign(params, secret)
    params_with_sign = {**params, "sign": sign}
    assert verify_notification(params_with_sign, secret)
    assert not verify_notification({**params, "sign": "deadbeef"}, secret)
