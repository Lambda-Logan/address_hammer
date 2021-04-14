from __future__ import annotations
from .__types__ import *
from typing import Generic

class EndOfInputError(Exception):
    orig: str
    def __init__(self, orig: str = ""):
        self.orig = orig
        super(EndOfInputError, self).__init__("'" + orig + "'... reached end of input. Maybe a parsing stage consumed all input? Street name? City?")


class GenericInput(Generic[T]):
    state: int
    data: Seq[T]
    def __init__(self, data: Seq[T], state: int = 0):
        self.data = list(data)
        self.state = state
    
    def __iter__(self)->InputIter[T]:
        return InputIter(self)

    def item(self)->T:
        #print(self.as_str())
        if self.state + 1 > len(self.data):
            raise EndOfInputError() #(self.as_str(), "getting item")
        return self.data[self.state]

    def orig_str(self)->str:
        return(" ".join(map(str,self.data)))

    def as_str(self)->str:
        idx = len(self.data)-self.state
        return " ".join(map(str, self.data[-idx:]))
    
    def advance(self, step: int)-> GenericInput[T]:
        new_state = self.state + step

        if new_state > len(self.data):
            raise EndOfInputError()

        return GenericInput(state=new_state,
                            data = self.data)

    def rest_as_str(self)->str:
        idx = len(self.data)-self.state-1
        return " ".join(map(str,self.data[-idx:]))

    def rest(self)->GenericInput[T]:
        return GenericInput(self.data, self.state+1)

    def view(self)->Tuple[T, GenericInput[T]]:
        return (self.item(), self.rest())
    
    @staticmethod
    def from_str(s:str)->GenericInput[T]:
        return GenericInput(s.upper().split())

    def empty(self)->bool:
        return self.state + 1 > len(self.data)

class InputIter(Generic[T]):
    i: GenericInput[T]
    def __init__(self, i: GenericInput[T]):
        self.i = i
    def __next__(self)->T:
        try:
            item = self.i.item()
        except EndOfInputError:
            raise StopIteration
        self.i = self.i.rest()
        return item


class Uncatchable(Exception):
    pass

I = TypeVar("I")
O = TypeVar("O")

def n_args(func: Fn[[Any], Any])-> int:
    from inspect import signature
    return len(signature(func).parameters)

#Arrow = Fn[[I], Seq[O]]

class Zipper(Generic[I,O]):
    """
    A stateless, streaming transformation from multiple 'I's to multiple 'O's.

    By being stateless and automatically tracking how much input is consumed,
      -we get ergonomic backtracking for free.

    This is a monadic interface in a candy coating.
    - instead of a bunch of (i -> Zipper[i,o]) functions, the interface only exposes (i -> Sequence[o]) 
    - - (and that's ok, because avoiding explicit handling of position is what this class is trying to avoid)

    To consume a single input, use zipper = zipper.consume_with(func), where func is (i->Sequence[o]).

    To consume until failure,  use zipper = zipper.takewhile(func), where func is (i->Sequence[o]).

    To fail, have 'func' return []

    To ignore an exception your 'func' might raise, pass the 'ex_types' optional argument.
    """

    leftover: GenericInput[I]
    results: Iter[O]

    def __init__(self, leftover: GenericInput[I], results: Iter[O] = []):
        self.leftover = leftover
        self.results = results

    def merge(self, other: Zipper[I,O])-> Zipper[I,O]:
        """Returns a new zipper that has:
             - the final leftover state of the second arg
             - the the concat of both results as the final result"""
        #print()
        #print(self.leftover.as_str())
        #print(other.leftover.as_str())
        def r()->Iter[O]:
            yield from self.results
            yield from other.results
        return Zipper(leftover=other.leftover, results=r())

    def realize(self)->Zipper[I,O]:
        return Zipper(leftover=self.leftover, results=list(self.results))
    

    def chomp_n(self, 
                  n: int,
                  list_func: Fn[[Seq[I]],Seq[O]], #Idk how to typecheck [*args: I]
                  ex_types: Seq[Type[Exception]] = [Uncatchable])->Zipper[I,O]:
        """
        'list_func' is a function taking an 'n' length list of type 'I' and returning a Sequence[O]
        If non-empty, the output sequence of 'list_func(items)' is added to the results.
        To ignore an exception your 'list_func' might raise, pass the 'ex_types' optional argument.
        """
        try:
            state = self.leftover.state
            args = self.leftover.data[state:state+n]
            #print("chomp", args)

            results = list_func(list(args))
            leftover = self.leftover.advance(n)
            #print(self.leftover.as_str())
            return self.merge(Zipper(leftover=leftover,
                                    results=results)) 
        except tuple(ex_types):
            pass
        return self

    def successful(self)->bool:
        "Did the zipper produce any results?"
        return len(list(self.realize().results)) > 0

    def or_(self, funcs: Seq[Fn[[I], Seq[O]]],
                  ex_types: Seq[Type[Exception]] = [Uncatchable])->Zipper[I,O]:
        """
        Takes a sequence of (i -> Sequence[O]),
        returns for first one to succeed on the next item of input.
        If none are successful, returns self and consumes no input.
        To ignore an exception one of your 'funcs' might raise, pass the 'ex_types' optional argument.
        TIP: To enforce failure, make the last (i -> Sequence[O]) raise an error.
        """
        for func in funcs:
            try:
                item = self.leftover.item()
                results = func(item)
                if len(results) > 0:
                    return self.merge(Zipper(leftover=self.leftover.advance(1),
                                            results=results))
            except tuple(ex_types):
                pass
        
        return self

    
    def consume_with(self,
                  func: Fn[[I], Seq[O]],
                  ex_types: Seq[Type[Exception]] = [Uncatchable])  ->  Zipper[I,O]:
        """
        If 'func(i)' returns a non-empty list, 'consume_with' will consume one item of input and the results are accumulated.
        If 'func(i)' returns [], no input is consumed and no results are accumulated.
        To consume input while not accumulating a result, 'func(i)' should return [None]... use a Zipper[I, Optional[O]].
        To ignore an exception your 'func' might raise, pass the 'ex_types' optional argument.
        """
        return self.takewhile(func, ex_types=ex_types, single=True)

    def takewhile(self, 
                  pred_arrow: Fn[[I], Seq[O]],
                  single: bool = False,
                  ex_types: Seq[Type[Exception]] = [Uncatchable])  ->  Zipper[I,O]:    
        """
        'pred_arrow' is (i -> Sequence[o]), the same as 'consume_with'
        While 'pred_arrow(i)' is non-empty, the the results are accumulated.
        Consumes no input if 'pred_arrow(i)' is [].
        """    
        n : int = 0
        results : List[O] = []

        if single:
            try:
                leftover = [self.leftover.item()]
            except tuple(ex_types):
                leftover: List [I] = []
        else:
            leftover = self.leftover

        for i in leftover:
            #print(GenericInput(self.leftover.data, state=self.leftover.state+1))
            try:
                new_results = list(pred_arrow(i))
                #print("d",i,new_results)
                if len(new_results) == 0:
                    break
                results = results + new_results
                n += 1
            except tuple(ex_types):
                break
        #print("n", n)

        new_input = self.leftover.advance(n)

        #print('K', self.leftover.as_str())
        #print('K', new_input.as_str())

        return self.merge(Zipper(leftover=new_input,
                          results=results))

    def test(self, name: str, result: Seq[int]):
        _r = list(self.realize().results)
        passed = list(result) == _r
        if not passed:
            raise Exception(" ".join(["zipper", "'"+name+"'", "failed at", str(result), "\n", str(_r)]))

    def test_leftover(self, name: str, leftover: Seq[I]):
        _l = self.realize().leftover.as_str()
        passed = " ".join(map(str,leftover))== _l
        if not passed:
            raise Exception(" ".join(["zipper", "'"+name+"'", "failed LEFTOVER", str(leftover), "\n", str(_l)]))

def x(_z: Zipper[Seq[I],O],
    _funcs: Iter[Fn[[Zipper[I, O]], Zipper[I, O]]])->Zipper[I,O]:
    leftover: GenericInput[Seq[I]] = _z.leftover
    z: Zipper[I,O] = Zipper(leftover=GenericInput([]), results=_z.results)
    funcs: Iter[Fn[[Zipper[I, O]], Zipper[I, O]]] = iter(_funcs)
    for seq in leftover:
        l = GenericInput(seq)
        while not l.empty():
            try:
                f = next(funcs)
            except StopIteration:
                return z
            y: Zipper[I,O] = Zipper(leftover=l, results=z.results)
            z: Zipper[I,O] = f(y)
            l = z.leftover
    return z

    


class Apply:
    @staticmethod
    def consume_with(func: Fn[[I], Seq[O]],
                    ex_types: Seq[Type[Exception]] = [Uncatchable])  ->  Fn[[Zipper[I,O]], Zipper[I,O]]:
        return lambda z: z.takewhile(func, ex_types=ex_types, single=True)
    
    @staticmethod
    def takewhile(pred_arrow: Fn[[I], Seq[O]],
                  single: bool = False,
                  ex_types: Seq[Type[Exception]] = [Uncatchable])  ->  Fn[[Zipper[I,O]], Zipper[I,O]]:    
        return lambda z: z.takewhile(pred_arrow, ex_types=ex_types, single=single)

    @staticmethod
    def reduce(funcs: Iter[Fn[[Zipper[I,O]], Zipper[I,O]]])->Fn[[Zipper[I,O]], Zipper[I,O]]:
        def _(z: Zipper[I,O])->Zipper[I,O]:
            for f in funcs:
                if z.leftover.empty():
                    break
                z = f(z)
            return z
        return _

    @staticmethod
    def chomp_n(n: int,
                  list_func: Fn[[Seq[I]],Seq[O]], #Idk how to typecheck [*args: I]
                  ex_types: Seq[Type[Exception]] = [Uncatchable])->Fn[[Zipper[I,O]], Zipper[I,O]]:
        return lambda z: z.chomp_n(n, list_func=list_func, ex_types=ex_types)

