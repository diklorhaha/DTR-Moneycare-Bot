from __future__ import annotations

import argparse
import sys
from urllib.parse import parse_qs, urlencode, urlparse

import aiohttp

AUTHORIZE_URL = "https://yoomoney.ru/oauth/authorize"
TOKEN_URL = "https://yoomoney.ru/oauth/token"
DEFAULT_SCOPE = "account-info operation-history"


async def exchange_code(
    *,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code: str,
) -> dict:
    data = {
        "code": code,
        "client_id": client_id,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    }
    if client_secret:
        data["client_secret"] = client_secret

    async with aiohttp.ClientSession() as session:
        async with session.post(TOKEN_URL, data=data) as resp:
            payload = await resp.json(content_type=None)
            if resp.status >= 400 or "access_token" not in payload:
                raise RuntimeError(f"Token exchange failed: {payload}")
            return payload


def extract_code(redirected_url: str) -> str:
    parsed = urlparse(redirected_url.strip())
    qs = parse_qs(parsed.query)
    if "code" in qs and qs["code"]:
        return qs["code"][0]
    if "error" in qs:
        raise RuntimeError(f"OAuth error: {qs}")
    raise RuntimeError("No code= in redirect URL")


def main() -> int:
    parser = argparse.ArgumentParser(description="Получить YOOMONEY_ACCESS_TOKEN")
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--client-secret", default="")
    parser.add_argument("--redirect-uri", default="https://localhost")
    parser.add_argument("--scope", default=DEFAULT_SCOPE)
    args = parser.parse_args()

    query = urlencode(
        {
            "client_id": args.client_id,
            "response_type": "code",
            "redirect_uri": args.redirect_uri,
            "scope": args.scope,
        }
    )
    print("1) Открой в браузере и подтверди доступ:")
    print(f"{AUTHORIZE_URL}?{query}")
    print()
    print("2) После редиректа скопируй полный URL из адресной строки и вставь сюда:")
    redirected = input("> ").strip()
    code = extract_code(redirected)

    import asyncio

    payload = asyncio.run(
        exchange_code(
            client_id=args.client_id,
            client_secret=args.client_secret,
            redirect_uri=args.redirect_uri,
            code=code,
        )
    )
    print()
    print("Готово. Вставь в .env:")
    print(f"YOOMONEY_ACCESS_TOKEN={payload['access_token']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 — CLI surface
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
