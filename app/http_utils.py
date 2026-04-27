# Ported from appevidence/evidence-capture-app at commit 090a5facd92737445cabaf48812b9d6f953e852d
from __future__ import annotations

import httpx

_DEFAULT_USER_AGENT = "webfix-solo/1.0 (https://github.com/appevidence/webfix-solo)"


def build_default_headers(user_agent: str | None = None) -> dict[str, str]:
    return {
        "User-Agent": user_agent or _DEFAULT_USER_AGENT,
        "Accept": "*/*",
    }


async def fetch_bytes(
    url: str,
    timeout: float = 30.0,
    headers: dict | None = None,
) -> bytes:
    merged = {**build_default_headers(), **(headers or {})}
    async with httpx.AsyncClient(timeout=timeout, headers=merged, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content


async def fetch_json(url: str, timeout: float = 30.0) -> dict:
    async with httpx.AsyncClient(
        timeout=timeout,
        headers=build_default_headers(),
        follow_redirects=True,
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
