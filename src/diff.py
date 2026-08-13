import difflib
from dataclasses import dataclass


@dataclass
class Change:
    id: int
    start: int
    end: int
    orig_start: int
    orig_end: int
    mod_start: int
    mod_end: int
    orig_text: str
    mod_text: str
    resolved: bool = False


def leading_offsets(raw1, raw2):
    return len(raw1) - len(raw1.lstrip()), len(raw2) - len(raw2.lstrip())


def opcodes(text1, text2):
    return difflib.SequenceMatcher(None, text1, text2, autojunk=False).get_opcodes()
