from __future__ import annotations
from typing import Generic
from .__types__ import Iter, Seq, T, List, Tuple


class EndOfInputError(Exception):
    orig: str

    def __init__(self, orig: str = ""):
        self.orig = orig
        super(EndOfInputError, self).__init__(
            f"'{orig}' ... reached end of input. Maybe a parsing stage consumed all input? Street name? City?"
        )


class GenericInput(Generic[T]):
    __slots__ = ["state", "data"]
    state: int
    data: Seq[T]

    def __init__(self, data: Seq[T], state: int = 0):
        self.data = list(data)
        self.state = state

    def copy(self) -> GenericInput[T]:
        return GenericInput(self.data, self.state)

    def __iter__(self) -> InputIter[T]:
        return InputIter(self)

    def as_iter(self) -> InputIter[T]:
        return InputIter(self)

    def as_list(self) -> List[T]:
        return [x for x in self.as_iter()]

    def item(self) -> T:
        # print(self.as_str())
        if self.state + 1 > len(self.data):
            raise EndOfInputError()  # (self.as_str(), "getting item")
        return self.data[self.state]

    def orig_str(self) -> str:
        return " ".join(map(str, self.data))

    def as_str(self) -> str:
        idx = len(self.data) - self.state
        return " ".join(map(str, self.data[-idx:]))

    def advance(self, step: int) -> GenericInput[T]:
        new_state = self.state + step

        if new_state > len(self.data):
            raise EndOfInputError()

        g: GenericInput[T] = GenericInput(state=new_state, data=self.data)
        return g

    def rest_as_str(self) -> str:
        idx = len(self.data) - self.state - 1
        return " ".join(map(str, self.data[-idx:]))

    def rest(self) -> GenericInput[T]:
        return GenericInput(self.data, self.state + 1)

    def view(self) -> Tuple[T, GenericInput[T]]:
        return (self.item(), self.rest())

    @staticmethod
    def from_str(s: str) -> GenericInput[str]:
        return GenericInput(s.upper().split())

    def empty(self) -> bool:
        return self.state + 1 > len(self.data)

    def __len__(self) -> int:
        return len(self.data) - self.state + 1

    def as_steps(self) -> Iter[Tuple[T, GenericInput[T]]]:
        s = self
        while not s.empty():
            item, s = s.view()
            yield item, s


class InputIter(Generic[T]):
    __slots__ = ["i"]
    i: GenericInput[T]

    def __init__(self, i: GenericInput[T]):
        self.i = i

    def __iter__(self) -> InputIter[T]:
        return InputIter(self.i)

    def __next__(self) -> T:
        try:
            item = self.i.item()
        except EndOfInputError:
            raise StopIteration
        self.i = self.i.rest()
        return item