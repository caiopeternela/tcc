import re
from typing import NamedTuple


class Rule(NamedTuple):
    name: str
    pattern: re.Pattern
    replacement: str


RULES: list[Rule] = [
    Rule("ph_to_f", re.compile(r"ph"), "f"),
    Rule("th_to_t", re.compile(r"th"), "t"),
    Rule("ct_to_t", re.compile(r"ct"), "t"),
    Rule("pt_to_t", re.compile(r"pt"), "t"),
    Rule("ff_to_f", re.compile(r"ff"), "f"),
    Rule("ll_to_l", re.compile(r"ll"), "l"),
    Rule("nn_to_n", re.compile(r"nn"), "n"),
    Rule("tt_to_t", re.compile(r"tt"), "t"),
    Rule("cc_to_c", re.compile(r"cc(?=[^ei])"), "c"),
    Rule("mm_to_m", re.compile(r"mm"), "m"),
    Rule(
        "y_to_i",
        re.compile(
            r"(?<=[bcdfghjklmnpqrstvwxz])y(?:\b|(?=[bcdfghjklmnpqrstvwxz]))"
            r"|(?<=[aeiou])y(?=[aeiou])"
        ),
        "i",
    ),
]


def modernize(name: str) -> tuple[str, list[str]]:
    result = name
    applied: list[str] = []

    for rule in RULES:
        new_value = rule.pattern.sub(rule.replacement, result)
        if new_value != result:
            applied.append(rule.name)
            result = new_value

    return result, applied
