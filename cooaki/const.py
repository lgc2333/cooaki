from enum import Enum

HEADERS = {
    "Accept": (
        "text/html,"
        "application/xhtml+xml,"
        "application/xml;q=0.9,"
        "image/avif,"
        "image/webp,"
        "image/apng,"
        "*/*;q=0.8,"
        "application/signed-exchange;v=b3;q=0.7"
    ),
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 "
        "Safari/537.36"
    ),
    "x-requested-with": "XMLHttpRequest",
}


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
