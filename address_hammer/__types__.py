from typing import List, Tuple, Dict, NamedTuple, Set, TypeVar, Union, Any, Type

from typing import Optional as Opt
from typing import Callable as Fn
from typing import Sequence as Seq
from typing import Iterable as Iter

T = TypeVar("T")


def join(tss: Iter[Iter[T]]) -> Iter[T]:
    for ts in tss:
        yield from ts


def id_(t: T) -> T:
    return t


(Opt[None], Fn, Seq, List, Tuple, Dict, NamedTuple, Set, TypeVar, Union, Any, Type)