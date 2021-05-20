import re
import string
from typing import Pattern

from .__types__ import Iter, Dict, Union, Opt


def or_(l: Iter[str]) -> str:
    ll = [x for x in l if x]
    # ll : t.List[str] = sorted(l, key = len, reverse=True)
    return r"\s*\b(" + "|".join(ll) + r")\b\s*"


def and_(l: Iter[str]) -> str:
    # multiple patterns separated by whitespace
    return r"\b\s*\b".join(l)


def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def remove(pat: Pattern[str], s: str) -> str:
    return normalize_whitespace(re.sub(pat, " ", s))


__punc__ = str.maketrans("", "", string.punctuation.replace("#", "").replace("/", ""))


def remove_punc(s: str, punc: Dict[int, Union[int, None]] = __punc__) -> str:
    r = s.translate(punc)
    return r


def opt(s: str) -> str:
    return "(" + s + ")?"


def titleize(s: str) -> str:
    return " ".join([word.capitalize() for word in s.lower().split()])


def match(s: str, pat: Pattern[str]) -> Opt[str]:
    m = re.search(pat, s)
    if m:
        return m.group(0)
    return None


(or_, and_)
