import asyncio
import sys
from contextlib import suppress

from . import (
    THEMES,
    Akinator,
    Answer,
    CanNotGoBackError,
    GameEndedError,
    Theme,
    WinResp,
    __version__,
)


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

    aki = Akinator(lang, theme, child_mode)
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

        if msg.isdigit():
            try:
                answer = Answer(int(msg) - 1)
            except Exception:
                print("Invalid answer")
                continue

            try:
                resp = await aki.answer(answer)
            except GameEndedError:
                print("You beat me!")
                break

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
                    break
                print()
                await aki.continue_answer()
                continue

        elif msg == "b":
            try:
                await aki.back()
            except CanNotGoBackError:
                print("Cant go back any further!")
                print()

        else:
            print("Invalid answer")
            print()

    return 0


with suppress(KeyboardInterrupt):
    sys.exit(asyncio.run(main()))
