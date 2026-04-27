# Ported from appevidence/evidence-capture-app at commit b9e1e82c8fdff2fd2aaa735323e116a5e539b51a
from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
    pass

_DEFAULT_UA_CHROMIUM = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 webfix-solo/1.0"
)


class PageMetadata(TypedDict):
    title: str
    url: str
    final_url: str
    status_code: int | None
    content_type: str | None
    content_length: int | None
    headers: dict[str, str]
    timing: dict[str, float]


def build_user_agent(browser_type: str = "chromium") -> str:
    """Return a standard user agent string for the given browser type."""
    return _DEFAULT_UA_CHROMIUM


async def collect_page_metadata(page: Any) -> dict[str, Any]:
    """Collect metadata from a Playwright page after navigation."""
    title = await page.title()
    url = page.url

    # Attempt to get response info from the page
    status_code: int | None = None
    content_type: str | None = None
    content_length: int | None = None
    headers: dict[str, str] = {}

    try:
        response = await page.evaluate(
            """() => ({
                status: window._webfix_response_status,
                contentType: document.contentType,
            })"""
        )
        status_code = response.get("status")
        content_type = response.get("contentType")
    except Exception:  # noqa: S110
        pass

    # Collect navigation timing
    timing: dict[str, float] = {}
    try:
        timing = await page.evaluate(
            """() => {
                const t = performance.timing;
                return {
                    navigationStart: t.navigationStart,
                    domContentLoaded: t.domContentLoadedEventEnd - t.navigationStart,
                    loadComplete: t.loadEventEnd - t.navigationStart,
                };
            }"""
        )
    except Exception:  # noqa: S110
        pass

    return PageMetadata(
        title=title or "",
        url=url,
        final_url=url,
        status_code=status_code,
        content_type=content_type,
        content_length=content_length,
        headers=headers,
        timing=timing,
    )
