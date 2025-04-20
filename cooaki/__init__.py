from .akinator import (
    AnswerResp as AnswerResp,
    BaseAkinator as BaseAkinator,
    GameState as GameState,
    HTTPXAkinator as HTTPXAkinator,
    PlaywrightAkinator as PlaywrightAkinator,
    WinResp as WinResp,
)
from .const import THEMES as THEMES, Answer as Answer, Theme as Theme
from .errors import (
    CanNotGoBackError as CanNotGoBackError,
    GameEndedError as GameEndedError,
)

Akinator = HTTPXAkinator

__version__ = "0.3.0.post2"
