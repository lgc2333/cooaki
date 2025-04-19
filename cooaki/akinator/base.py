import re
from abc import abstractmethod
from contextlib import suppress
from dataclasses import dataclass
from typing import Any, Optional

from cookit.pyd import type_validate_json
from pydantic import BaseModel, ValidationError

from ..const import DEFAULT_TIMEOUT, DEFAULT_URL_TEMPLATE, THEMES, Answer, Theme
from ..errors import CanNotGoBackError, GameEndedError

GAME_REFERRER_PATH = "game"


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


class BaseAkinator:
    def __init__(
        self,
        lang: str = "cn",
        theme: Optional[Theme] = None,
        child_mode: bool = False,
        base_url_template: str = DEFAULT_URL_TEMPLATE,
        allow_not_supported_lang: bool = False,
        allow_not_supported_theme: bool = False,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        if (not allow_not_supported_lang) and (lang not in THEMES):
            raise ValueError(f"Unsupported language: {lang}")

        if not theme:
            theme = Theme.CHARACTERS
        if (not allow_not_supported_theme) and (
            (lang not in THEMES) or (theme not in THEMES[lang])
        ):
            raise ValueError(f"Unsupported theme: {theme}")

        self.lang: str = lang
        self.theme: Theme = theme
        self.child_mode: bool = child_mode
        self.base_url_template: str = base_url_template.rstrip("/")
        self.timeout: float = timeout

        self._state: Optional[GameState] = None

    @property
    def state(self) -> GameState:
        if not self._state:
            raise ValueError("Game not started")
        return self._state

    @property
    def base_url(self) -> str:
        return self.base_url_template.format(self.lang)

    @staticmethod
    def get_akitude_path(akitude: str) -> str:
        return f"assets/img/akitudes_670x1096/{akitude}"

    def get_akitude_url(self, akitude: str) -> str:
        return f"{self.base_url}/{self.get_akitude_path(akitude)}"

    async def get_akitude_image(self, akitude: str) -> bytes:
        return await self.do_request("GET", self.get_akitude_url(akitude))

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

    def find_form_input_value(self, name: str, resp_text: str) -> str:
        input_reg = r'name="{0}"\s+id="{0}"\s+value="(?P<value>.+?)"'
        if not (m := re.search(input_reg.format(name), resp_text)):
            raise ValueError(f"Failed to find {name}")
        return m["value"]

    def find_question(self, resp_text: str) -> str:
        question_match = re.search(
            r'<div class="bubble-body"><p class="question-text" id="question-label">'
            r"(?P<question>.+?)"
            r"</p></div>",
            resp_text,
        )
        if not question_match:
            raise ValueError("Failed to find question")
        return question_match["question"]

    def make_referrer_headers(self, referrer_path: str = "") -> dict[str, str]:
        return {
            "origin": self.base_url,
            "referer": f"{self.base_url}/{referrer_path}",
        }

    @abstractmethod
    async def do_request(
        self,
        method: str,
        url: str,
        data: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> bytes: ...

    async def request(
        self,
        method: str,
        path: str,
        data: Optional[dict[str, Any]] = None,
        referrer_path: Optional[str] = "",
    ) -> bytes:
        headers = {}
        if referrer_path:
            headers.update(self.make_referrer_headers(referrer_path))
        return await self.do_request(
            method,
            f"{self.base_url}/{path}",
            data=data,
            headers=headers,
        )

    @abstractmethod
    async def goto_start_page(self) -> str: ...

    async def start(self):
        resp_text = await self.goto_start_page()
        self._state = GameState(
            self.find_form_input_value("session", resp_text),
            self.find_form_input_value("signature", resp_text),
            self.find_question(resp_text),
        )
        return self._state

    async def answer(self, answer: Answer):
        state = self.state
        self.ensure_not_win()

        data = {
            **self.make_answer_req_data(),
            "answer": answer.value,
            "step_last_proposition": (x if (x := state.step_last_proposition) else ""),
        }
        resp_text = await self.request(
            "POST",
            "answer",
            data=data,
            referrer_path="game",
        )

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

        data = self.make_answer_req_data()
        resp_text = await self.request(
            "POST",
            "exclude",
            data=data,
            referrer_path="game",
        )
        self.handle_answer_resp(resp := type_validate_json(AnswerResp, resp_text))
        return resp

    async def back(self):
        self.ensure_can_back()

        data = self.make_answer_req_data()
        resp_text = await self.request(
            "POST",
            "cancel_answer",
            data=data,
            referrer_path="game",
        )
        self.handle_answer_resp(resp := type_validate_json(AnswerResp, resp_text))
        return resp
