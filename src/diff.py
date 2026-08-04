"""差异引擎：与界面无关的纯数据与算法部分，便于单独测试。"""

import difflib
from dataclasses import dataclass


@dataclass
class Change:
    """一处差异。start/end 是差异在预览文本中的字符区间（接受/拒绝前）。"""
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
    """返回 (off_orig, off_mod)：strip 后文本相对输入框的前导空白偏移。"""
    return len(raw1) - len(raw1.lstrip()), len(raw2) - len(raw2.lstrip())


def opcodes(text1, text2):
    """对两个文本跑 SequenceMatcher，返回差异操作码列表。"""
    return difflib.SequenceMatcher(None, text1, text2,
                                   autojunk=False).get_opcodes()
