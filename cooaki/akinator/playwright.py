import base64
import json
import re
from typing import TYPE_CHECKING, Any, Optional, TypedDict
from typing_extensions import override

from ..const import DEFAULT_TIMEOUT, DEFAULT_URL_TEMPLATE, Theme
from .base import BaseAkinator

if TYPE_CHECKING:
    from playwright.async_api import Page

FORM_OP_JS_TEMPLATE = """
(el) => {
    el.querySelector("#cm").value = "{cm}"
    el.querySelector("#sid").value = "{sid}"
    el.submit()
}
"""
REQUEST_JS_TEMPLATE = """
async () => {
    const form = new FormData()
    for (const [k, v] of Object.entries({data})) {
        form.append(k, v)
    }
    const method = '{method}'
    const resp = await fetch('{url}', {
        method,
        body: ['GET', 'HEAD'].includes(method) ? undefined : form,
        headers: {headers},
    })
    const buf = new Uint8Array(await resp.arrayBuffer())
    const data = btoa(String.fromCharCode(...buf))
    return { status: resp.status, status_text: resp.statusText, data }
}
"""


class RequestReturn(TypedDict):
    status: int
    status_text: str
    data: str


def format_template(template: str, **kwargs) -> str:
    for k, v in kwargs.items():
        template = template.replace(f"{{{k}}}", str(v))  # noqa: UP032
    return template


class PlaywrightAkinator(BaseAkinator):
    def __init__(
        self,
        page: "Page",
        lang: str = "cn",
        theme: Optional[Theme] = None,
        child_mode: bool = False,
        base_url_template: str = DEFAULT_URL_TEMPLATE,
        allow_not_supported_lang: bool = False,
        allow_not_supported_theme: bool = False,
        timeout: float = DEFAULT_TIMEOUT,
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
        self.page = page

    @override
    async def do_request(
        self,
        method: str,
        url: str,
        data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> bytes:
        js = format_template(
            REQUEST_JS_TEMPLATE,
            method=method,
            url=url,
            data=json.dumps(data or {}),
            headers=json.dumps(headers or {}),
        )
        resp: RequestReturn = await self.page.evaluate(js)
        if resp["status"] != 200:
            raise RuntimeError(
                f"Request failed: [{resp['status']}] {resp['status_text']}",
            )
        return base64.b64decode(resp["data"])

    @override
    async def goto_start_page(self) -> str:
        await self.page.goto(
            self.base_url,
            timeout=self.timeout * 1000,
            wait_until="load",
        )
        game_form_el = await self.page.wait_for_selector(
            "#formTheme",
            timeout=self.timeout * 1000,
            state="attached",
        )
        assert game_form_el
        js = format_template(
            FORM_OP_JS_TEMPLATE,
            cm=str(self.child_mode).lower(),
            sid=self.theme.value,
        )
        await game_form_el.evaluate(js)
        await self.page.wait_for_url(re.compile("game"), wait_until="load")
        return await self.page.content()
