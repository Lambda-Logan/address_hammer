from __future__ import annotations
import unittest
from .__types__ import *
from .address import (
    Address,
    SOFT_COMPONENTS,
    HARD_COMPONENTS,
    example_addresses,
    merge_duplicates,
    HashableFactory,
)
from .parsing import Parser, __difficult_addresses__, ParseError
from .__zipper__ import EndOfInputError, Zipper, GenericInput
from .fuzzy_string import FixTypos
from .hammer import Hammer
from .__logging__ import log_parse_with


def parse_benchmak():
    from .parsing import Parser
    from .address import example_addresses as exs

    # print(len(exs))
    n = 5000
    p = Parser()
    print(n * len(exs))
    for _ in range(n):
        for a in exs:
            p(a.orig, checked=True)


class TestAddress(unittest.TestCase):
    class UniqTest(NamedTuple):
        """
        this is a helper class to facilitate testing removal of duplicate addresses
        xs should be mapped to ys, otherwise it fails
        """

        p: Parser
        xs: Seq[Address]
        ys: Seq[Address]

        @staticmethod
        def new(p: Parser) -> TestAddress.UniqTest:
            return TestAddress.UniqTest(p=p, xs=(), ys=())

        def run(self, test: TestAddress):
            # we can't use set equality because RawAddress doesn't support hashing
            ys = merge_duplicates(self.xs)
            for y in ys:
                test.assertIn(y, ys)
                # if y not in ys:
                #    raise Exception(f"{y.pretty()} not in self.ys")
            test.assertEqual(len(ys), len(self.ys))

        def run_with(self, d: Dict[str, List[str]]):
            f = HashableFactory.from_all_addresses(self.xs)
            for add, add_strs in d.items():
                adds = f(self.p(add))
                adds_2 = list(map(self.p, add_strs))

                for a in adds:
                    if a not in adds_2:
                        raise Exception(f"{a.pretty()} not in output")

                for a in adds_2:
                    if a not in adds:
                        print(add)
                        raise Exception(
                            f"{a.pretty()} not in output: {list(map(Address.Get.pretty, adds))}"
                        )

        def with_x(self, x: Address) -> TestAddress.UniqTest:
            return self._replace(xs=(x, *self.xs))

        def with_y(self, y: Address) -> TestAddress.UniqTest:
            return self._replace(ys=(y, *self.ys))

        def without_x(self, x: Address) -> TestAddress.UniqTest:
            return self._replace(xs=(a for a in self.xs if a != x))

        def without_y(self, y: Address) -> TestAddress.UniqTest:
            return self._replace(ys=(a for a in self.ys if a != y))

    def test_json(self):
        def json_reparse(a: Address) -> Address:
            from json import loads, dumps

            return Address.from_dict(loads(dumps(a.to_dict())))

        self.assertEqual(
            example_addresses, [json_reparse(a) for a in example_addresses]
        )

    def test_lt_gt(self):
        from random import shuffle

        s = sorted(example_addresses)
        ss = example_addresses.copy()
        for _ in range(10):
            shuffle(ss)
            self.assertEqual(sorted(ss), s)

    def test(self):
        p = Parser(known_cities=["City"])
        ambigs_1 = [
            "001 Street City MI",
            "001 Street St City MI",
            "001 E Street City MI",
            "001 Street Apt 0 City MI",
            "001 Street Apt 1 City MI",
        ]
        ambigs_2 = ["0 Main St Smallville AZ", "0 Main Rd Smallville AZ"]

        self.UniqTest(
            xs=tuple(map(p, ambigs_1)),
            ys=[p("001 E Street Apt 1 City MI"), p("001 E Street Apt 0 City MI")],
            p=p,
        ).run(self)

        self.assertEqual(
            2, len(HashableFactory.from_all_addresses(map(p, ambigs_2)).fix_by_hand[0])
        )

        self.UniqTest(p=p, xs=tuple(map(p, ambigs_1)), ys=()).with_x(
            p("001 W Street City MI")
        ).run(self)

        self.UniqTest(p=p, xs=tuple(map(p, ambigs_1)), ys=())  # .run(self)
        # TODO pass the following test
        # a.run_with({"001 e street  st city mi":["001 E Street St Apt 1 City MI", "001 E Street St Apt 0 City MI"]})

    def test__eq__(self):
        for a in example_addresses:
            self.assertEqual(a, a)
            soft_sames: List[Tuple[Opt[str], Opt[str]]] = [(None, "X"), ("X", None)]
            sames: List[Tuple[Opt[str], Opt[str]]] = [(None, None), ("X", "X")]

            for x, y in soft_sames + sames:
                for soft in SOFT_COMPONENTS:
                    self.assertEqual(a.replace(**{soft: x}), a.replace(**{soft: y}))
                    self.assertNotEqual(
                        a.replace(**{soft: "X"}), a.replace(**{soft: "Y"})
                    )

            for hard in HARD_COMPONENTS:
                for x, y in soft_sames:
                    self.assertNotEqual(a.replace(**{hard: x}), a.replace(**{hard: y}))
                for x, y in sames:
                    self.assertEqual(a.replace(**{hard: x}), a.replace(**{hard: y}))

                self.assertNotEqual(a.replace(**{hard: "X"}), a.replace(**{hard: "Y"}))


class TestZipper(unittest.TestCase):
    def test(self):
        def fan_odd(n: int) -> List[int]:
            if n % 2 == 0:
                return []
            else:
                return [n + 0, n + 1, n + 2]

        def fan_even(n: int) -> List[int]:
            if n % 2 == 1:
                return []
            else:
                return [n + 0, n + 1, n + 2]

        def _id(x: T) -> T:
            return x

        import itertools

        odds = [1, 3, 7]
        f_odds = list(itertools.chain.from_iterable(map(fan_odd, odds)))

        evens = [2, 4, 8]
        f_evens = list(itertools.chain.from_iterable(map(fan_even, evens)))

        input = GenericInput

        with self.assertRaises(EndOfInputError):
            i: GenericInput[int] = input([])
            Zipper(i).chomp_n(2, _id)

        with self.assertRaises(EndOfInputError):
            Zipper(input([0])).chomp_n(2, _id)

        Zipper(input([2, 3, 4])).chomp_n(2, _id).test("chomp 0", [2, 3])
        Zipper(input([5, 6])).chomp_n(2, _id).test("chomp 1", [5, 6])
        # should_throw("chomp 2", EndOfInputError, lambda : )
        # should_throw("chomp 3", EndOfInputError, lambda : )

        Zipper(input(odds)).takewhile(fan_odd).test("takewhile 0", f_odds)
        i: GenericInput[int] = input([])
        Zipper(i).takewhile(fan_odd).test("takewhile 1", [])
        Zipper(input(evens + odds)).takewhile(fan_even).test("takewhile 2", f_evens)
        Zipper(input(odds + evens)).takewhile(fan_even).test("takewhile 3", [])

        Zipper(input(odds + evens + odds)).takewhile(fan_odd).takewhile(
            fan_even
        ).takewhile(fan_odd).test("takewhile 4", f_odds + f_evens + f_odds)

        Zipper(input(odds + [2])).takewhile(fan_odd).takewhile(fan_odd).takewhile(
            fan_even
        ).test("takewhile 5", f_odds + fan_even(2))

        with self.assertRaises(EndOfInputError):
            Zipper(input(odds + [2])).takewhile(fan_odd).chomp_n(2, _id)

        Zipper(input(odds + [2])).takewhile(fan_odd).test_leftover("leftover 0", [2])

        Zipper(input(odds)).takewhile(
            fan_odd
        )  # .test_leftover("leftover 1", []) #TODO fix this

        Zipper(input([1, 2])).or_([fan_even, fan_odd]).test("or 0", [1, 2, 3])

        Zipper(input([2, 1])).or_([fan_even, fan_odd]).test("or 1", [2, 3, 4])

        Zipper(input([2, 1])).or_([]).test("or 2", [])


class TestFuzzyString(unittest.TestCase):
    def test(self):
        fix_typos = FixTypos(
            "michigan scalifornia ohio ontario numeric12".upper().split()
        )

        # these are close enough they should be repaired with a level 5 out of 10
        a = "mmichyigan ohiao kscaliofornita nmeric12".upper().split()
        for w in a:
            self.assertNotEqual(a, fix_typos(w))

        # these should be recognized as distinct with a level 5 out of 10
        b = "muichzigaan ohsiao kscaliofyornita numeric21".upper().split()
        for w in b:
            self.assertEqual(w, fix_typos(w))


class TestParser(unittest.TestCase):
    @staticmethod
    def addresses_to_rows(seed: int, adds: Iter[Address]) -> List[List[str]]:
        """
        This is used for testing Parser.parse_row.
        It takes a list of addresses and returns a list of rows that should represent each address
        """
        import random

        random.seed(seed)
        STOP_SEP = "dkjf4oit"

        def make_row(a: Address) -> Iter[str]:
            def _(a: Address) -> Iter[str]:
                flip = lambda: random.choice([True, False])
                for idx, word in enumerate(a[:8]):
                    if word == None:
                        word = ""
                    if flip() or idx == 4:
                        yield STOP_SEP
                    yield word

            return " ".join(_(a)).split(STOP_SEP)

        return [list(make_row(a)) for a in adds]

    def test_parse_row(self):
        import random

        z = 2 ^ 10 - 1
        random.seed(z)
        p = Parser()
        seeds = [random.randrange(0 - z, z) for _ in range(16)]
        for seed in seeds:
            from .address import example_addresses as exs

            rows = self.addresses_to_rows(seed, exs)
            for row, a in zip(rows, exs):
                r = Address(*p.parse_row(row))
                r.reparse_test(lambda s: a)
                if not (a == r):
                    for i, (_a, _r) in enumerate(zip(a, r)):
                        if _a != _r:
                            print(i, _a, "!=", _r)
                    self.assertEqual(a, r)

    def test(self):
        p = Parser(known_cities=["city"])
        adds = [
            "0 Street apt 5 St City MI",
            "0 Street NE City MI",
            "0 Street Apt 3 City MI",
            "0 Street Apt 0 City MI",
            "1 Street City MI",
        ]
        (adds)
        # print([[a.pretty() for a in a_s] for a_s in d.values()])
        # print([a.pretty() for a in RawAddress.merge_duplicates(map(p, adds))])
        p = Parser(known_cities=["Zamalakoo", "Grand Rapids"])
        for a in __difficult_addresses__:
            p(a)

        from .address import example_addresses

        for a in example_addresses:
            a.reparse_test(p)
        zipless = Parser()
        zipless("123 Qwerty St Asdf NY")
        p = Parser()
        should_fail = [
            (
                Parser(known_cities=["Qwerty", "Yuiop", "Asdf", "Hjkl"]),
                "123 Qwerty Hjkl NY 00000",
            )
        ]
        for p, s in should_fail:
            with self.assertRaises((ParseError, EndOfInputError)):
                p(s)


class TestLogging(unittest.TestCase):
    def test_logging(self):
        with log_parse_with(lambda pair: None):
            tp = TestParser()
            tp.test()
            tp.test_parse_row()

        def throw(_: Any) -> None:
            raise Exception("log_parse_with.__exit__ failed")

        with log_parse_with(throw):
            pass

        p = Parser()
        p("000 Fail Rd Failureville NY")


class TestHammer(unittest.TestCase):
    def test_checksum(self):
        exs = example_addresses
        from random import shuffle

        exs = list(map(Address.Set.ignore_checksum, exs))
        h = Hammer(exs)
        self.assertEqual(h.batch_checksum, Hammer(h.__addresses__).batch_checksum)
        switch = [(0, -1), (2, 3), (1, 5)]
        for a, b in switch:
            exs[a], exs[b] = exs[b], exs[a]
            self.assertEqual(h.batch_checksum, Hammer(exs).batch_checksum)
            exs[a], exs[b] = exs[b], exs[a]
        self.assertEqual(h.batch_checksum, Hammer(exs).batch_checksum)

        _0_7 = r"c0c04f4b20d2a1c9d48be55598f0662b"
        _2_6 = r"656e3a4954a688062d89708f0eb53436"
        p = Parser()
        row_exs = [p.parse_row(row) for row in TestParser.addresses_to_rows(0, exs)]
        for adds in [exs, row_exs]:
            self.assertEqual(Hammer(adds[:7]).batch_checksum, _0_7)
            self.assertEqual(Hammer(adds[2:6]).batch_checksum, _2_6)

        def modify(a: str, b: Opt[str]) -> Fn[[Address], Address]:
            return lambda address: address.replace(**{a: b})

        funcs: List[Fn[[Address], Address]] = [
            modify("st_name", ""),
            modify("house_number", "z"),
            modify("unit", "Lot 4594653657555949"),
            modify("us_state", "ZZ"),
            modify("st_suffix", "ZZ"),
        ]

        idxs = [0, 2, 4, 6]
        for idx in idxs:
            a = exs[idx]
            for f in funcs:
                exs[idx] = f(a)
                self.assertNotEqual(h.batch_checksum, Hammer(exs).batch_checksum)
            exs[idx] = a
        self.assertEqual(h.batch_checksum, Hammer(exs).batch_checksum)

        xs = exs + exs
        for soft in SOFT_COMPONENTS:
            f = modify(soft, None)
            for idx in idxs:
                # print(f(exs[idx]))
                xs.append(f(exs[idx]))

        shuffle(xs)
        h.batch_checksum == Hammer(xs).batch_checksum

    def test(self):
        ambigs_1 = [
            "001 Street City MI",
            "001 E Streeet City MI",
            # "001 W Street City MI",
            "001 Street St City MI",
            "001 Street Apt 0 City MI",
            "001 Street Apt 1 Ccity MI",
        ]
        ambigs_2 = ambigs_1 + ["001 W Street City MI"]
        hammer = Hammer(ambigs_1)
        (ambigs_2, hammer)
        self.assertEqual(
            sorted(map(Address.Get.pretty, set(iter(hammer)))),
            sorted(["001 E Street St Apt 1 City MI", "001 E Street St Apt 0 City MI"]),
        )
        # print(list(map(print, map( Address.Get.pretty, join(hammer.ambigous_address_groups)))))
        # print(hammer["001 W Street Ave #4 City MI"].pretty())

    # test()
