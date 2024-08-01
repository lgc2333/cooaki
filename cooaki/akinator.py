import re
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast

from cookit.pyd import type_validate_json
from httpx import AsyncClient, Cookies
from pydantic import BaseModel, ValidationError

from .const import HEADERS, THEMES, Answer, Theme
from .errors import CanNotGoBackError, GameEndedError


@dataclass
class GameState:
    session: str
    signature: str

    question: str
    akitude: str = "defi.png"
    progression: float = 0.0
    step: int = 0
    win: bool = False
    step_last_proposition: Optional[int] = None
    ended: bool = False


class AnswerResp(BaseModel):
    akitude: str
    step: int
    progression: float
    question_id: int
    question: str
    completion: Optional[str] = None

    @property
    def akitude_url(self) -> str:
        return Akinator.get_akitude_url(self.akitude)


class WinResp(BaseModel):
    completion: str
    id_proposition: int
    id_base_proposition: int
    valide_contrainte: int
    name_proposition: str
    description_proposition: str
    flag_photo: int
    photo: str
    pseudo: str
    nb_elements: int


class Akinator:
    def __init__(
        self,
        lang: str = "cn",
        theme: Optional[Theme] = None,
        child_mode: bool = False,
        **cli_kwargs,
    ) -> None:
        if lang not in THEMES:
            raise ValueError(f"Unsupported language: {lang}")

        if not theme:
            theme = THEMES[lang][0]
        elif theme not in THEMES[lang]:
            raise ValueError(f"Unsupported theme: {theme}")

        self.lang: str = lang
        self.theme: Theme = theme
        self.child_mode: bool = child_mode

        self._state: Optional[GameState] = None

        self.cli_kwargs: Dict[str, Any] = cli_kwargs
        self.cookies: Optional[Cookies] = None

    @property
    def state(self) -> GameState:
        if not self._state:
            raise ValueError("Game not started")
        return self._state

    @property
    def base_url(self) -> str:
        return f"https://{self.lang}.akinator.com"

    @asynccontextmanager
    async def create_client(self):
        async with AsyncClient(  # noqa: S113
            base_url=self.base_url,
            headers=HEADERS,
            follow_redirects=True,
            cookies=self.cookies,
            **self.cli_kwargs,
        ) as cli:
            try:
                yield cli
            finally:
                self.cookies = cli.cookies

    @staticmethod
    def get_akitude_url(akitude: str) -> str:
        return f"https://cn.akinator.com/assets/img/akitudes_670x1096/{akitude}"

    async def get_akitude_image(self, akitude: str) -> bytes:
        async with self.create_client() as cli:
            return (
                (await cli.get(self.get_akitude_url(akitude)))
                .raise_for_status()
                .content
            )

    def make_answer_req_data(self):
        state = self.state
        return {
            "step": state.step,
            "progression": state.progression,
            "sid": self.theme.value,
            "cm": self.child_mode,
            "session": state.session,
            "signature": state.signature,
        }

    def handle_answer_resp(self, resp: AnswerResp):
        state = self.state
        if state.win:
            state.win = False
        state.step = resp.step
        state.progression = resp.progression
        state.question = resp.question
        state.akitude = resp.akitude

    def handle_win_resp(self, _: WinResp):
        state = self.state
        state.win = True
        state.step_last_proposition = state.step

    def ensure_not_end(self):
        state = self.state
        if state.ended:
            raise GameEndedError

    def ensure_not_win(self):
        state = self.state
        self.ensure_not_end()
        if state.win:
            raise RuntimeError(
                "Game already win, "
                "if you want to continue, please call `continue_answer`.",
            )

    def ensure_win(self):
        state = self.state
        self.ensure_not_end()
        if not state.win:
            raise RuntimeError("Game not win")

    def ensure_can_back(self):
        state = self.state
        self.ensure_not_win()
        if state.step <= 0:
            raise CanNotGoBackError

    async def start(self):
        url = "/game"
        data = {"sid": self.theme.value, "cm": self.child_mode}
        async with self.create_client() as cli:
            resp_text = (await cli.post(url, data=data)).raise_for_status().text

        session, signature = cast(
            List[str],
            re.findall(r"[a-zA-Z0-9+/]+==", resp_text),
        )[-2:]

        question_match = re.search(
            (
                r'<div class="bubble-body"><p class="question-text" id="question-label">'
                r"(?P<question>.+?)"
                r"</p></div>"
            ),
            resp_text,
        )
        if not question_match:
            raise ValueError("Failed to find question")
        question: str = question_match["question"]

        self._state = GameState(session, signature, question)
        return self._state

    async def answer(self, answer: Answer):
        state = self.state
        self.ensure_not_win()

        url = "/answer"
        data = {
            **self.make_answer_req_data(),
            "answer": answer.value,
            "step_last_proposition": (x if (x := state.step_last_proposition) else ""),
        }
        async with self.create_client() as cli:
            resp_text = ((await cli.post(url, data=data)).raise_for_status()).text

        with suppress(ValidationError):
            self.handle_answer_resp(resp := type_validate_json(AnswerResp, resp_text))
            return resp

        with suppress(ValidationError):
            self.handle_win_resp(resp := type_validate_json(WinResp, resp_text))
            return resp

        state.ended = True
        state.akitude = "deception.png"
        raise GameEndedError

    async def continue_answer(self):
        self.ensure_win()

        url = "/exclude"
        data = self.make_answer_req_data()
        async with self.create_client() as cli:
            resp_text = ((await cli.post(url, data=data)).raise_for_status()).text

        self.handle_answer_resp(resp := type_validate_json(AnswerResp, resp_text))
        return resp

    async def back(self):
        self.ensure_can_back()

        url = "/cancel_answer"
        data = self.make_answer_req_data()
        async with self.create_client() as cli:
            resp_text = ((await cli.post(url, data=data)).raise_for_status()).text

        self.handle_answer_resp(resp := type_validate_json(AnswerResp, resp_text))
        return resp
