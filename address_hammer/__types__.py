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


class Fns_Of:
    """
    This is a base class used to avoid setting methods in an __init__

    For example, we want to avoid this:
    class Example:
        def __init__(self):
            #some conditional logic and define foo
            self.foo = lambda x: foo(x)

    we define a Fn_of_* class to hold all of the dynamically created instace methods.
    Then they are accessed via properties of the user-facing class

    class Example:
        __fns__: Fns_Of

        def __init__(self):
            class Fns_Of_Example(Fns_Of):
                @staticmethod
                def foo(x):
                    #some conditional logic and return something
            self.__fns__ = Fns_Of_Example()

        @property
        def foo(self):
            return self.__fns__.foo

    """

    pass


(
    Opt[None],
    Fn,
    Seq,
    List,
    Tuple,
    Dict,
    NamedTuple,
    Set,
    TypeVar,
    Union,
    Any,
    Type,
    Fns_Of,
)
