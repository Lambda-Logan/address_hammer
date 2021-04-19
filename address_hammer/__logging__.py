from __future__ import annotations
from contextlib import AbstractContextManager
from .__zipper__ import Apply as ZApply
from .__zipper__ import Zipper, GenericInput, Uncatchable, I, O
from .parsing import Parser
from .__types__ import Fn, Tuple, Any, Seq, Type


class LogParseUsing(AbstractContextManager):
    def __init__(self, log: Fn[[Any], None]):
        def logged_fn(
            fn: Fn[[Zipper[I, O]], Zipper[I, O]]
        ) -> Fn[[Zipper[I, O]], Zipper[I, O]]:
            def _(z: Zipper[I, O]) -> Zipper[I, O]:
                z = fn(z)
                results = list(z.results)
                for r in results:
                    log(r)
                leftover: GenericInput[I] = z.leftover
                rz: Zipper[I, O] = Zipper(leftover=leftover, results=iter(results))
                return rz

            return _

        class LoggedApply(ZApply):
            reduce = ZApply.reduce

            @staticmethod
            def consume_with(
                func: Fn[[I], Seq[O]], ex_types: Seq[Type[Exception]] = (Uncatchable,)
            ) -> Fn[[Zipper[I, O]], Zipper[I, O]]:
                return logged_fn(ZApply.takewhile(func, ex_types=ex_types, single=True))

            @staticmethod
            def takewhile(
                pred_arrow: Fn[[I], Seq[O]],
                single: bool = False,
                ex_types: Seq[Type[Exception]] = (Uncatchable,),
            ) -> Fn[[Zipper[I, O]], Zipper[I, O]]:
                return logged_fn(
                    ZApply.takewhile(pred_arrow, ex_types=ex_types, single=single)
                )

            @staticmethod
            def chomp_n(
                n: int,
                list_func: Fn[[Seq[I]], Seq[O]],  # Idk how to typecheck [*args: I]
                ex_types: Seq[Type[Exception]] = (Uncatchable,),
            ) -> Fn[[Zipper[I, O]], Zipper[I, O]]:
                return logged_fn(
                    ZApply.chomp_n(n, list_func=list_func, ex_types=ex_types)
                )

        self.logged_apply = LoggedApply
        self.z_apply = ZApply

    def __enter__(self) -> LogParseUsing:
        Parser.__Apply__ = self.logged_apply
        return self

    def __exit__(self, *_):
        Parser.__Apply__ = self.z_apply
        return False


def log_parse_steps_using(log: Fn[[Tuple[str, str]], None]) -> LogParseUsing:
    return LogParseUsing(log)