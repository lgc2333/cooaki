import asyncio
import sys
from contextlib import asynccontextmanager, suppress
from importlib.util import find_spec
from typing import TYPE_CHECKING, cast

from . import (
    THEMES,
    Answer,
    BaseAkinator,
    CanNotGoBackError,
    GameEndedError,
    HTTPXAkinator,
    PlaywrightAkinator,
    Theme,
    WinResp,
    __version__,
)

if TYPE_CHECKING:
    from playwright.async_api import Browser, Page, Playwright


@asynccontextmanager
async def use_akinator(**kwargs):
    if (pr := find_spec("patchright")) or find_spec("playwright"):
        if pr:
            from patchright.async_api import async_playwright
        else:
            from playwright.async_api import async_playwright

        playwright = None
        browser = None
        page = None
        try:
            playwright = cast("Playwright", await async_playwright().start())
            # must disable headless mode for bypassing
            browser = cast("Browser", await playwright.chromium.launch(headless=False))
            page = cast("Page", await browser.new_page())
            yield PlaywrightAkinator(page, **kwargs)
        finally:
            if page:
                await page.close()
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()

    else:
        yield HTTPXAkinator(**kwargs)


async def handle_input(aki: BaseAkinator, msg: str):
    if msg.isdigit():
        try:
            answer = Answer(int(msg) - 1)
        except Exception:
            print("Invalid answer")
            return False

        try:
            resp = await aki.answer(answer)
        except GameEndedError:
            print("You beat me!")
            return True

        if isinstance(resp, WinResp):
            should_continue = (
                input(
                    f"I guess: {resp.name_proposition} - {resp.description_proposition}\n"
                    f"Photo URL: {resp.photo} (From: {resp.pseudo})\n"
                    f"Continue? (y/N) ",
                ).lower()
                or "n"
            ) == "y"
            if not should_continue:
                return True

            print()
            await aki.continue_answer()
            return False

    elif msg == "b":
        try:
            await aki.back()
        except CanNotGoBackError:
            print("Cant go back any further!")
            print()

    else:
        print("Invalid answer")
        print()

    return False


async def main() -> int:
    print(f"CooAki v{__version__} | Console Demo")
    print()

    lang = (
        input(
            f"Available languages: {', '.join(THEMES)}\n"
            f'Input language (Defaults to "cn"): ',
        ).lower()
        or "cn"
    )
    if lang not in THEMES:
        print("Invalid language")
        return 1

    themes = THEMES[lang]
    if len(themes) == 1:
        theme = themes[0]
    else:
        default_theme = themes[0]
        theme = (
            input(
                f"Available themes: "
                f"{', '.join(f'{x} ({x.name.capitalize()})' for x in themes)}\n"
                f"Input theme (Defaults to {default_theme}): ",
            ).lower()
            or default_theme
        )
        try:
            theme = Theme(int(theme))
            assert theme in themes
        except Exception:
            print("Invalid theme")
            return 1

    child_mode = (input("Enable child mode? (y/N) ").lower() or "n") == "y"

    print()
    print(f"Using language: {lang}")
    print(f"Using theme: {theme.name.capitalize()}")
    print(f"Child mode {'enabled' if child_mode else 'disabled'}")
    print()

    async with use_akinator(
        lang=lang,
        theme=theme,
        child_mode=child_mode,
        timeout=15,
    ) as aki:
        await aki.start()

        while not aki.state.ended:
            answer_tip = ", ".join(
                f"{x + 1} ({x.name.capitalize().replace('_', ' ')})" for x in Answer
            )

            msg = input(
                f"{aki.state.step + 1}: {aki.state.question}\n"
                f"Answer: {answer_tip}, B (Back), Ctrl-C (Quit)\n"
                f"Input answer: ",
            ).lower()
            print()

            if await handle_input(aki, msg):
                break

    return 0


with suppress(KeyboardInterrupt):
    sys.exit(asyncio.run(main()))
