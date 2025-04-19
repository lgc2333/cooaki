from enum import Enum


class Theme(int, Enum):
    CHARACTERS = 1
    OBJECTS = 2
    ANIMALS = 14


class Answer(int, Enum):
    YES = 0
    NO = 1
    I_DONT_KNOW = 2
    PROBABLY = 3
    PROBABLY_NOT = 4


THEMES = {
    "en": [Theme.CHARACTERS, Theme.OBJECTS, Theme.ANIMALS],
    "ar": [Theme.CHARACTERS],
    "cn": [Theme.CHARACTERS],
    "de": [Theme.CHARACTERS, Theme.ANIMALS],
    "es": [Theme.CHARACTERS, Theme.ANIMALS],
    "fr": [Theme.CHARACTERS, Theme.OBJECTS, Theme.ANIMALS],
    "il": [Theme.CHARACTERS],
    "it": [Theme.CHARACTERS, Theme.ANIMALS],
    "jp": [Theme.CHARACTERS, Theme.ANIMALS],
    "kr": [Theme.CHARACTERS],
    "nl": [Theme.CHARACTERS],
    "pl": [Theme.CHARACTERS],
    "pt": [Theme.CHARACTERS],
    "ru": [Theme.CHARACTERS],
    "tr": [Theme.CHARACTERS],
    "id": [Theme.CHARACTERS],
}

DEFAULT_URL_TEMPLATE = "https://{}.akinator.com"
DEFAULT_TIMEOUT = 15
