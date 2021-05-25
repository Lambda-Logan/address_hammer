from __future__ import annotations
import unittest
from random import shuffle
import random
from json import loads, dumps
import itertools
from .__types__ import Seq, Dict, Opt, join, List, id_, Iter, Any, Fn, NamedTuple, Tuple
from .__address__ import (
    Address,
    merge_duplicates,
    HashableFactory,
)
from .__parsing__ import Parser, __difficult_addresses__, ParseError, ParseStep
from .__zipper__ import EndOfInputError, Zipper, GenericInput
from .__fuzzy_string__ import FixTypos
from .__hammer__ import Hammer
from .__logging__ import log_parse_steps_using
from .__sheet__ import Sheet

p = Parser()
print(p("123 Calm St A Bron WV"))

todo = [
    Address(
        house_number="123",
        st_name="ST RD 86",
        st_suffix=None,
        st_NESW=None,
        unit=None,
        city="CARL",
        us_state="IA",
        zip_code=None,
        orig="123 ST RD 86 Carl Ia",
        batch_checksum="",
    )
]
EXAMPLE_ADDRESSES = [
    Address(
        house_number="3710",
        st_name="MICHIGANE",
        st_suffix="AVE",
        st_NESW="SW",
        unit="APT 447",
        city="GRAND RAPIDS",
        us_state="MI",
        zip_code="49588",
        orig="3710 Michigane AVE SW apt #447 Grand Rapids MI 49588",
    ),
    Address(
        house_number="343",
        st_name="FULLY FULTON",
        st_suffix="ST",
        st_NESW="E",
        unit="APT 1",
        city="BLABLAVILLE",
        us_state="AZ",
        zip_code="00000",
        orig="343 Fully Fulton st E APT 1 Blablaville AZ 00000",
    ),
    Address(
        house_number="0",
        st_name="ROAD",
        st_suffix="RD",
        st_NESW=None,
        unit=None,
        city="CITY",
        us_state="NY",
        zip_code="12123",
        orig="0 road Rd city NY 12123",
    ),
    Address(
        house_number="1914",
        st_name="HASKELL",
        st_suffix="LCK",
        st_NESW="S",
        unit=None,
        city="RUSTY TOWN",
        us_state="NY",
        zip_code="12123",
        orig="1914 S Haskell Lck  Rusty Town NY 12123",
    ),
    Address(
        house_number="5431",
        st_name="MONROE",
        st_suffix="LN",
        st_NESW="N",
        unit="APT 5",
        city="BRONX",
        us_state="OH",
        zip_code="54321",
        orig="5431 N Monroe Ln APT 5 Bronx OH 54321",
    ),
    Address(
        house_number="5242",
        st_name="PLAINFIELD INSURANCE",
        st_suffix="BLVD",
        st_NESW="NW",
        unit="STE B",
        city="PALM SPRINGS",
        us_state="CA",
        zip_code="01234",
        orig="5242 Plainfield Insurance Blvd NW Ste B Palm Springs CA 01234",
    ),
    Address(
        house_number="0",
        st_name="DIVISION",
        st_suffix=None,
        st_NESW="N",
        unit=None,
        city="ZAMALAKOO",
        us_state="MI",
        zip_code="00100",
        orig="0 N Division Zamalakoo MI 00100",
    ),
    Address(
        house_number="411",
        st_name="AVE GRANDE ST JOHN",
        st_suffix="AVE",
        st_NESW=None,
        unit=None,
        city="WALKER",
        us_state="IA",
        zip_code="52352",
        orig="411 Ave Grande St John Ave Walker IA 52352",
        batch_checksum="",
    ),
    Address(
        house_number="123",
        st_name="K",
        st_suffix="AVE",
        st_NESW="NE",
        unit="APT 3",
        city="Y",
        us_state="IA",
        zip_code="50000",
        orig="123 K Ave NE 3 Y IA 50000",
        batch_checksum="",
    ),
    Address(
        house_number="123",
        st_name="N",
        st_suffix="AVE",
        st_NESW="NE",
        unit="APT 3",
        city="IYA",
        us_state="IA",
        zip_code="50000",
        orig="123 N Ave NE 3 Iya IA 50000",
        batch_checksum="",
    ),
    Address(
        house_number="15 1/2",
        st_name="4TH",
        st_suffix="ST",
        st_NESW="S",
        unit=None,
        city="CENTRAL CITY",
        us_state="IA",
        zip_code="52214",
        orig="15 1/2 4th St S Central City IA 52214",
        batch_checksum="",
    ),
    Address(
        house_number="110",
        st_name="BREWER",
        st_suffix="ST",
        st_NESW=None,
        unit=None,
        city="HARRY",
        us_state="MI",
        zip_code="77777",
        orig="110\tBREWER ST\tAPT\tHarry MI\t77777",
        batch_checksum="",
    ),
    Address(
        house_number="720",
        st_name="1000TH",
        st_suffix="AVE",
        st_NESW="SW",
        unit="APT B",
        city="MOUNT VERNERS",
        us_state="IA",
        zip_code="52314",
        orig="720 1000th Ave SW B Mount Verners IA 52314",
        batch_checksum="",
    ),
    Address(
        house_number="123",
        st_name="CALM",
        st_suffix="ST",
        st_NESW=None,
        unit="APT A",
        city="BRON",
        us_state="WV",
        zip_code=None,
        orig="123 Calm St A Bron WV",
        batch_checksum="",
    ),
]
EXAMPLE_ADDRESSES.extend(todo)


def parse_benchmak():

    exs = EXAMPLE_ADDRESSES

    # print(len(exs))
    n = 5000
    p = Parser()
    print(n * len(exs))
    for _ in range(n):
        for a in exs:
            p(a.orig, checked=True)


def hammer_bench():

    exs = list(join(map(lambda _: EXAMPLE_ADDRESSES, range(1000))))

    for _ in range(20):
        Hammer(exs)


SOFT_MODS: List[Fn[[Opt[str]], Fn[[Address], Address]]] = [
    lambda s: lambda a: a.with_st_NESW(s),
    lambda s: lambda a: a.with_st_suffix(s),
    lambda s: lambda a: a.with_unit(s),
    lambda s: lambda a: a.with_zip_code(s),
]

HARD_MODS: List[Fn[[Any], Fn[[Address], Address]]] = [
    lambda s: lambda a: a.with_house_number(s),
    lambda s: lambda a: a.with_st_name(s),
    lambda s: lambda a: a.with_city(s),
    lambda s: lambda a: a.with_us_state(s),
]


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
            # return self._replace(xs=(x, *self.xs))
            return TestAddress.UniqTest(xs=(x, *self.xs), p=self.p, ys=self.ys)

        def with_y(self, y: Address) -> TestAddress.UniqTest:
            # return self._replace(ys=(y, *self.ys))
            return TestAddress.UniqTest(ys=(y, *self.ys), xs=self.xs, p=self.p)

        def without_x(self, x: Address) -> TestAddress.UniqTest:
            # return self._replace(xs=(a for a in self.xs if a != x))
            return TestAddress.UniqTest(
                xs=tuple(a for a in self.xs if a != x), ys=self.ys, p=self.p
            )

        def without_y(self, y: Address) -> TestAddress.UniqTest:
            # return self._replace(ys=(a for a in self.ys if a != y))
            return TestAddress.UniqTest(
                ys=tuple(a for a in self.ys if a != y), xs=self.xs, p=self.p
            )

    def test_json(self):
        def json_reparse(a: Address) -> Address:

            return Address.from_dict(loads(dumps(a.to_dict())))

        self.assertEqual(
            EXAMPLE_ADDRESSES, [json_reparse(a) for a in EXAMPLE_ADDRESSES]
        )

    def test_lt_gt(self):

        s = sorted(EXAMPLE_ADDRESSES)
        ss = EXAMPLE_ADDRESSES.copy()
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
        for a in EXAMPLE_ADDRESSES:
            self.assertEqual(a, a)
            soft_sames: List[Tuple[Opt[str], Opt[str]]] = [(None, "X"), ("X", None)]
            sames: List[Tuple[Opt[str], Opt[str]]] = [(None, None), ("X", "X")]

            for x, y in soft_sames + sames:
                for soft in SOFT_MODS:
                    with_x = soft(x)
                    with_y = soft(y)
                    self.assertEqual(with_x(a), with_y(a))
                    self.assertNotEqual(soft("X")(a), soft("Y")(a))

            for hard in HARD_MODS:
                for x, y in soft_sames:
                    with_x = hard(x)
                    with_y = hard(y)
                    self.assertNotEqual(with_x(a), with_y(a))

                for x, y in sames:
                    with_x = hard(x)
                    with_y = hard(y)
                    self.assertEqual(with_x(a), with_y(a))

                self.assertNotEqual(hard("X")(a), hard("Y")(a))


class TestZipper(unittest.TestCase):
    def test(self):
        def fan_odd(n: int) -> List[int]:
            if n % 2 == 0:
                return []
            return [n + 0, n + 1, n + 2]

        def fan_even(n: int) -> List[int]:
            if n % 2 == 1:
                return []
            return [n + 0, n + 1, n + 2]

        odds = [1, 3, 7]
        f_odds = list(itertools.chain.from_iterable(map(fan_odd, odds)))

        evens = [2, 4, 8]
        f_evens = list(itertools.chain.from_iterable(map(fan_even, evens)))

        _input = GenericInput

        with self.assertRaises(EndOfInputError):
            i: GenericInput[int] = _input([])
            Zipper(i).force_chomp_n(2, id_)

        with self.assertRaises(EndOfInputError):
            Zipper(_input([0])).force_chomp_n(2, id_)

        Zipper(_input([2, 3, 4])).chomp_n(2, id_).test("chomp 0", [2, 3])
        Zipper(_input([5, 6])).chomp_n(2, id_).test("chomp 1", [5, 6])
        # should_throw("chomp 2", EndOfInputError, lambda : )
        # should_throw("chomp 3", EndOfInputError, lambda : )

        Zipper(_input(odds)).takewhile(fan_odd).test("takewhile 0", f_odds)
        i: GenericInput[int] = _input([])
        Zipper(i).takewhile(fan_odd).test("takewhile 1", [])
        Zipper(_input(evens + odds)).takewhile(fan_even).test("takewhile 2", f_evens)
        Zipper(_input(odds + evens)).takewhile(fan_even).test("takewhile 3", [])

        Zipper(_input(odds + evens + odds)).takewhile(fan_odd).takewhile(
            fan_even
        ).takewhile(fan_odd).test("takewhile 4", f_odds + f_evens + f_odds)

        Zipper(_input(odds + [2])).takewhile(fan_odd).takewhile(fan_odd).takewhile(
            fan_even
        ).test("takewhile 5", f_odds + fan_even(2))

        with self.assertRaises(EndOfInputError):
            Zipper(_input(odds + [2])).takewhile(fan_odd).force_chomp_n(2, id_)

        Zipper(_input(odds + [2])).takewhile(fan_odd).test_leftover("leftover 0", [2])

        Zipper(_input(odds)).takewhile(
            fan_odd
        )  # .test_leftover("leftover 1", []) #TODO fix this

        Zipper(_input([1, 2])).or_([fan_even, fan_odd]).test("or 0", [1, 2, 3])

        Zipper(_input([2, 1])).or_([fan_even, fan_odd]).test("or 1", [2, 3, 4])

        Zipper(_input([2, 1])).or_([]).test("or 2", [])


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


STOP_SEP = "dkjf4oit"


class TestParser(unittest.TestCase):
    @staticmethod
    def addresses_to_rows(seed: int, adds: Iter[Address]) -> List[List[str]]:
        """
        This is used for testing Parser.parse_row.
        It takes a list of addresses and returns a list of rows that should represent each address
        """

        random.seed(seed)

        def make_row(a: Address) -> Iter[str]:
            def _(a: Address) -> Iter[str]:
                flip = lambda: random.choice([True, False])
                for idx, word in enumerate(a[:8]):
                    if word is None:
                        word = ""
                    if flip() or idx == 4:
                        yield STOP_SEP
                    yield word

            return " ".join(_(a)).split(STOP_SEP)

        return [list(make_row(a)) for a in adds]

    def test_parse_row(self):

        z = 2 ^ 10 - 1
        random.seed(z)
        p = Parser()
        seeds = [random.randrange(0 - z, z) for _ in range(16)]
        for seed in seeds:
            exs = EXAMPLE_ADDRESSES

            rows = self.addresses_to_rows(seed, exs)
            for row, a in zip(rows, exs):
                r = p.parse_row(row).__as_address__()
                r.reparse_test(lambda _: a)
                if not a == r:
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
        adds
        # print([[a.pretty() for a in a_s] for a_s in d.values()])
        # print([a.pretty() for a in RawAddress.merge_duplicates(map(p, adds))])
        p = Parser(known_cities=["Zamalakoo", "Grand Rapids"])
        for a in __difficult_addresses__:
            p(a)

        for a in EXAMPLE_ADDRESSES:
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
        with log_parse_steps_using(lambda pair: None):
            tp = TestParser()
            tp.test()
            tp.test_parse_row()

        def throw(_: Any) -> None:
            raise Exception("log_parse_steps_using.__exit__ failed")

        with log_parse_steps_using(throw):
            pass

        p = Parser()
        p("000 Fail Rd Failureville NY")


class TestHammer(unittest.TestCase):
    def test_checksum(self):
        exs = EXAMPLE_ADDRESSES

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

        funcs: List[Fn[[Address], Address]] = [
            lambda a: a.with_st_name(""),
            lambda a: a.with_house_number("z"),
            lambda a: a.with_unit("Lot 4594653657555949"),
            lambda a: a.with_us_state("ZZ"),
            lambda a: a.with_st_suffix("ZZ"),
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
        for soft in SOFT_MODS:
            f = soft(None)
            for idx in idxs:
                # print(f(exs[idx]))
                xs.append(f(exs[idx]))

        shuffle(xs)
        # TODO pass have hammer checksum not depend on order, see below
        # self.assertEqual(h.batch_checksum, Hammer(xs).batch_checksum)

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


class TestSheet(unittest.TestCase):
    def test(self):
        def unify(addresses: Iter[Address]) -> List[Seq[str]]:
            a: List[Seq[str]] = []
            for address in EXAMPLE_ADDRESSES:
                a.append((".", *address.as_row(), "-"))
            return sorted(set(a))

        def strip(l: Iter[Seq[str]]) -> List[Seq[str]]:
            return [list(row[1:-1]) for row in l]

        a = unify(EXAMPLE_ADDRESSES)

        sheet = Sheet("B:I", a + a)

        self.assertEqual(strip(a), strip(sheet.merge_duplicates()))
