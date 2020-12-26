import re
import string
import typing as t

def titleize(s:str)->str:
    return " ".join([word.capitalize() for word in s.lower().split()])

def or_(l: t.Iterable[str])->str:
    ll = [x for x in l if x]
    #ll : t.List[str] = sorted(l, key = len, reverse=True)
    return r"\s*\b(" + "|".join(ll) + r")\b\s*"

def and_(l: t.Iterable[str])->str:
    #multiple patterns separated by whitespace
    return r"\b\s*\b".join(l)

def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def remove(pat: t.Pattern[str], s: str)-> str:
    return normalize_whitespace(re.sub(pat, " ", s))

__punc__ = str.maketrans("", "", string.punctuation.replace("#", ""))
def remove_punc(s:str, punc : t.Dict[int, t.Union[int, None]] = __punc__)->str:
    return s.translate(punc)
def opt(s:str)->str:
    return "(" + s + ")?"

def titleize(s:str)->str:
    return " ".join([word.capitalize() for word in s.lower().split()])

def match(s:str, pat:t.Pattern[str])->t.Optional[str]:
    m = re.search(pat, s)
    if m:
        return m.group(0)
    else:
        return None

__used__ = (or_, and_) 