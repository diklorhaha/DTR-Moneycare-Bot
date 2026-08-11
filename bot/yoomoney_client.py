from __future__ import annotations

import json
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode

import aiohttp


class YooMoneyError(RuntimeError):
    pass


class YooMoneyClient:
    HISTORY_URL = "https://yoomoney.ru/api/operation-history"
    QUICKPAY_URL = "https://yoomoney.ru/quickpay/confirm.xml"

    def __init__(
        self,
        *,
        wallet: str,
        access_token: str,
        payment_type: str = "AC",
        quickpay_form: str = "shop",
        targets: str = "Оплата Robux",
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self.wallet = wallet
        self.access_token = access_token
        self.payment_type = payment_type
        self.quickpay_form = quickpay_form
        self.targets = targets
        self._session = session
        self._owns_session = session is None

    async def __aenter__(self) -> YooMoneyClient:
        if self._session is None:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._owns_session and self._session is not None:
            await self._session.close()
            self._session = None

    def build_payment_url(self, *, amount: Decimal, label: str) -> str:
        params = {
            "receiver": self.wallet,
            "quickpay-form": self.quickpay_form,
            "targets": self.targets,
            "paymentType": self.payment_type,
            "sum": f"{amount:.2f}",
            "label": label,
        }
        return f"{self.QUICKPAY_URL}?{urlencode(params)}"

    async def _operation_history(
        self,
        *,
        records: int = 40,
        label: str | None = None,
    ) -> list[dict[str, Any]]:
        if self._session is None:
            raise YooMoneyError("HTTP session is not started")

        data: dict[str, str] = {
            "records": str(records),
            "type": "deposition",
        }
        if label:
            data["label"] = label

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        async with self._session.post(self.HISTORY_URL, data=data, headers=headers) as resp:
            text = await resp.text()
            if resp.status >= 400:
                raise YooMoneyError(f"operation-history HTTP {resp.status}: {text}")
            try:
                payload = json.loads(text) if text else {}
            except json.JSONDecodeError as exc:
                raise YooMoneyError(f"operation-history invalid JSON: {text[:200]}") from exc

        if isinstance(payload, dict) and "error" in payload:
            raise YooMoneyError(f"operation-history error: {payload['error']}")
        if not isinstance(payload, dict):
            raise YooMoneyError(f"operation-history unexpected payload: {payload!r}")
        return list(payload.get("operations") or [])

    @staticmethod
    def _label_paid(operations: list[dict[str, Any]], label: str) -> bool:
        for op in operations:
            if str(op.get("label") or "") != label:
                continue
            if str(op.get("status", "")).lower() == "success":
                return True
        return False

    async def has_successful_payment(self, label: str) -> bool:
        # Один запрос свежих поступлений + матч label на клиенте (надёжнее фильтра API).
        recent = await self._operation_history(records=50)
        return self._label_paid(recent, label)
