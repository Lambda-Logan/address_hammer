from __future__ import annotations
from address_hammer.__zipper__ import GenericInput
from .__zipper__ import Apply as ZApply
from .__zipper__ import Zipper
from .parsing import ParseStep, Parser
from .__types__ import *
from contextlib import AbstractContextManager


class log_parse_with(AbstractContextManager):
    def __init__(self, log: Fn[[Tuple[str, str]], None]):
        def logged(
            fn: Fn[[Any], Fn[[Zipper[str, ParseStep]], Zipper[str, ParseStep]]]
        ) -> Fn[[Zipper[str, ParseStep]], Zipper[str, ParseStep]]:
            def _(
                *args: Any, **kwargs: Any
            ) -> Fn[[Zipper[str, ParseStep]], Zipper[str, ParseStep]]:
                z_z = fn(*args, **kwargs)

                def __(z: Zipper[str, ParseStep]) -> Zipper[str, ParseStep]:
                    z = z_z(z)
                    results = list(z.results)
                    for r in results:
                        log(r)
                    leftover: GenericInput[str] = z.leftover
                    rz: Zipper[str, ParseStep] = Zipper(
                        leftover=leftover, results=iter(results)
                    )
                    return rz

                return __

            return _

        class LoggedApply(ZApply):
            takewhile = logged(ZApply.takewhile)
            chomp_n = logged(ZApply.chomp_n)
            consume_with = logged(ZApply.consume_with)
            reduce = ZApply.reduce

        self.LoggedApply = LoggedApply
        self.ZApply = ZApply

    def __enter__(self) -> log_parse_with:
        Parser.__Apply__ = self.LoggedApply
        return self

    def __exit__(self, *_):
        Parser.__Apply__ = self.ZApply
        return False