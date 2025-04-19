from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Optional
from typing_extensions import override

from httpx import AsyncClient

from ..const import DEFAULT_TIMEOUT, DEFAULT_URL_TEMPLATE, Theme
from .base import BaseAkinator

if TYPE_CHECKING:
    from httpx import Cookies


HEADERS = {
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        " AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/135.0.0.0 Safari/537.36"
    ),
}
PAGE_EXTRA_HEADERS = {
    "accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9"
        ",image/avif,image/webp,image/apng"
        ",*/*;q=0.8"
        ",application/signed-exchange;v=b3;q=0.7"
    ),
    "priority": "u=0, i",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
}
XHR_EXTRA_HEADERS = {
    "accept": "*/*",
    "priority": "u=1, i",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-requested-with": "XMLHttpRequest",
}


class HTTPXAkinator(BaseAkinator):
    def __init__(
        self,
        lang: str = "cn",
        theme: Optional[Theme] = None,
        child_mode: bool = False,
        base_url_template: str = DEFAULT_URL_TEMPLATE,
        allow_not_supported_lang: bool = False,
        allow_not_supported_theme: bool = False,
        timeout: float = DEFAULT_TIMEOUT,
        **kwargs,
    ) -> None:
        super().__init__(
            lang=lang,
            theme=theme,
            child_mode=child_mode,
            base_url_template=base_url_template,
            allow_not_supported_lang=allow_not_supported_lang,
            allow_not_supported_theme=allow_not_supported_theme,
            timeout=timeout,
        )
        self.cookies: Optional[Cookies] = None
        self.cli_kwargs: dict[str, Any] = kwargs

    @asynccontextmanager
    async def create_client(self, *extra_headers: Optional[dict[str, str]]):
        headers = {**HEADERS}
        for extra in extra_headers:
            if extra:
                headers.update(extra)
        async with AsyncClient(
            headers=headers,
            follow_redirects=True,
            cookies=self.cookies,
            timeout=self.timeout,
            **self.cli_kwargs,
        ) as cli:
            try:
                yield cli
            finally:
                self.cookies = cli.cookies

    @override
    async def do_request(
        self,
        method: str,
        url: str,
        data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> bytes:
        async with self.create_client(XHR_EXTRA_HEADERS, headers) as cli:
            resp = await cli.request(method, url, data=data)
            resp.raise_for_status()
            return resp.content

    @override
    async def goto_start_page(self) -> str:
        data = {"sid": self.theme.value, "cm": self.child_mode}
        async with self.create_client(PAGE_EXTRA_HEADERS) as cli:
            resp = await cli.post(f"{self.base_url}/game", data=data)
            resp.raise_for_status()
            return resp.text
