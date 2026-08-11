from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from bot.embed_parser import extract_robux_from_embeds, make_payment_label
from bot.pricing import format_rub, parse_robux_amount, rubles_from_robux
from bot.yoomoney_client import YooMoneyClient


def test_parse_robux_from_code_style():
    assert parse_robux_amount("`2000`") == 2000
    assert parse_robux_amount("2000") == 2000


def test_rubles_from_robux_example():
    rub = rubles_from_robux(2000, 2)
    assert format_rub(rub) == "1000"
    assert f"{rub:.2f}" == "1000.00"


def test_extract_from_second_embed_fields():
    embeds = [
        {"fields": [{"name": "Другое", "value": "x"}]},
        {"fields": [{"name": "Сумма робуксов для покупки:", "value": "`2000`"}]},
    ]
    assert extract_robux_from_embeds(embeds) == 2000


def test_extract_skips_bad_field_value():
    embeds = [
        {"fields": [{"name": "Сумма робуксов для покупки:", "value": "не число"}]},
        {"fields": [{"name": "Сумма робуксов для покупки:", "value": "1500"}]},
    ]
    assert extract_robux_from_embeds(embeds) == 1500


def test_payment_label_length():
    label = make_payment_label(123456789012345678, 2000)
    assert len(label) <= 64
    assert "2000" in label


@pytest.mark.asyncio
async def test_has_successful_payment_matches_label():
    client = YooMoneyClient(wallet="41001", access_token="token")
    client._session = object()  # type: ignore[assignment]
    client._operation_history = AsyncMock(  # type: ignore[method-assign]
        return_value=[
            {"label": "other", "status": "success"},
            {"label": "t1-r2000", "status": "success"},
        ]
    )
    assert await client.has_successful_payment("t1-r2000") is True
    assert await client.has_successful_payment("missing") is False


def test_build_payment_url_has_sum_and_label():
    client = YooMoneyClient(wallet="410011234", access_token="token")
    url = client.build_payment_url(amount=Decimal("1000.00"), label="t1-r2000")
    assert "receiver=410011234" in url
    assert "sum=1000.00" in url
    assert "label=t1-r2000" in url
