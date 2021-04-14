from .__types__ import *
from .address import Address
T = TypeVar("T")

def with_log_info(p: Fn[[T], Address], t: T, log : Fn[[Tuple[str,str]], None]):
    """
    s = "234 S Bar  Fooville MA"
    p = Parser()
    address = with_log_info(p, s, print)
    print(address)
    """
    from .__zipper__ import Apply as ZApply
    from .__zipper__ import Zipper
    from .parsing import ParseResult, Parser
    PZ = Zipper[str,ParseResult]
    def logged(fn: Fn[[Any], Fn[[PZ], PZ]])->Fn[[PZ], PZ]:
        def _(*args: Any, **kwargs: Any)->Fn[[PZ], PZ]:
            z_z  = fn(*args, **kwargs)
            def __(z: PZ)->PZ:
                z = z_z(z)
                results = list(z.results)
                for r in results:
                    log(r)
                return Zipper(leftover=z.leftover, results=iter(results))
            return __
        return _

    class LoggedApply:
        takewhile = logged(ZApply.takewhile)
        chomp_n = logged(ZApply.chomp_n)
        consume_with = logged(ZApply.consume_with)
        reduce = ZApply.reduce

    Parser.__Apply__ = LoggedApply
    ret = p(t)
    Parser.__Apply__ = ZApply
    return ret
