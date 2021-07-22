from __future__ import annotations
import unittest
from random import shuffle
import random
from json import loads, dumps
import itertools
import time
from .__types__ import Seq, Dict, Opt, join, List, Iter, Any, Fn, NamedTuple, Tuple
from .__address__ import (
    Address,
    merge_duplicates,
    HashableFactory,
)
from .__parsing__ import (
    Parser,
    __difficult_addresses__,
    ParseError,
    test_state_m,
    get_unit,
    to_input_lst,
    get_nesw,
    get_full_hwy,
)
from .__zipper__ import EndOfInputError, GenericInput
from .__fuzzy_string__ import FixTypos
from .__hammer__ import Hammer
from .__sheet__ import Sheet


# print(p("123 Park St Bla Av St John FL"))
# SUPPORT THESE ADDRESSES

"""
123 COVE RD WEIRTON WV
106     DAVIS   City    TX !!!!!!!!!!
3267    NORTHPARK BLVD  STE E   ALCOA   TN      37701 !!!!!!!!!!!  st_name='NORTHPARK BLVD STE'
1003 1/2    Spring S    Harrison    AR
116     PINE REAR       WEIRTON WV
312    PINE   N    Harrison    AR    72601
691     Valley Tr       City    WI
1333    Rapids Tr       City    WI
314     Dale Ct City    WI
912     COURT DR        PALESTINE       TX      75803
503     AVE  D  PALESTINE       TX      75803
2089    SPUR  324       TENNESSEE COLONY        TX      75861
2648    SEVIERVILLE RD  RM E11  MARYVILLE       TN      37804
704     TUPELO WAY      APT E   ALCOA   TN      37777
41029   BOTTOM RD       City    SD
410     LINCOLN City    SD
121     W DAKOTA        City    SD
1410    ELM     City    SD
473     WEST RD AIKEN   SC      29801
569     RIVER RD        SALLEY  SC      29137
310     1/2  CENTER     Lexington       OK
1968    TRI COUNTY RD   A       WINCHESTER      OH      45697
1500    DORSEY RD       E1      WINCHESTER      OH      45697
628     LN A    City    NE
707     CIRCLE M        City    NE
817     CIRCLE N        City    NE
2474    MORAN ST        SUITE E BURLINGTON      NC      27215
811     NORTH AV        BURLINGTON      NC      27217
1241    S FIFTH ST      E4      MEBANE  NC      27302
3341    N NC 62 HWY     A       BURLINGTON      NC      27217
2116    TRAIL TWO       UNIT 9E BURLINGTON      NC      27215
2116    TRAIL TWO       UNIT 9N BURLINGTON      NC      27215
111     TRAIL ONE       SUITE   BURLINGTON      NC      27215
716     SHAWNEE DR      UNIT E  BURLINGTON      NC      27215
64545 MN-65 Jacobson, MN 55752
64545   65      JACOBSON        MN      55752

"""
# 3809    STH 13  City    WI ???
todo = [
    Address(
        house_number="123",
        st_name="SR 86",  # TODO "STATE ROAD 86"
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
        unit="UNIT 3",
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
        unit="UNIT 3",
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
        st_name="1000",  # note used to be 1000th, but 'get_house_number' accidentally normalizes :-D
        st_suffix="AVE",
        st_NESW="SW",
        unit="UNIT B",
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
        unit="UNIT A",
        city="BRON",
        us_state="WV",
        zip_code=None,
        orig="123 Calm St A Bron WV",
        batch_checksum="",
    ),
    Address(
        house_number="3323",
        st_name="GOLDENROD",
        st_suffix="DR",
        st_NESW=None,
        unit=None,
        city="ERLANGER",
        us_state="KY",
        zip_code="41018",
        orig="  3323  \t  GOLDENROD    DR  \t  ERLANGER  \t  KY  \t  41018  ",
        batch_checksum="",
    ),
    Address(
        house_number="123",
        st_name="PARK",
        st_suffix="ST",
        st_NESW=None,
        unit=None,
        city="ST JOHN",
        us_state="FL",
        zip_code=None,
        orig="123 Park St St John FL",
        batch_checksum="",
    ),
    Address(
        house_number="34",
        st_name="FIELDS",
        st_suffix=None,
        st_NESW="E",
        unit=None,
        city="CITY",
        us_state="IL",
        zip_code="61822",
        orig="34    Fields East    City    IL    61822",
        batch_checksum="",
    ),
    Address(
        house_number="123",
        st_name="COSINE",
        st_suffix="TRL",
        st_NESW=None,
        unit="UNIT B",
        city="CITY",
        us_state="IN",
        zip_code="46804",
        orig="123\tCOSINE tr\tB STE\tCity\tIN\t46804",
        batch_checksum="",
    ),
    Address(
        house_number="12345",
        st_name="OLD KNOXVILLE HIGHWAY A",
        st_suffix=None,
        st_NESW=None,
        unit=None,
        city="ROCKFORD",
        us_state="TN",
        zip_code="37000",
        orig="12345 OLD KNOXVILLE HWY   A   ROCKFORD    TN  37000",
        batch_checksum="",
    ),
    Address(
        house_number="123",
        st_name="STRAIGHT",
        st_suffix="ST",
        st_NESW=None,
        unit="UNIT 1B-2A",
        city="SACRAMENTO",
        us_state="CA",
        zip_code=None,
        orig="123 Straight St  1B-2A Sacramento CA",
        batch_checksum="",
    ),
    Address(
        house_number="12345",
        st_name="W 1000",
        st_suffix=None,
        st_NESW="N",
        unit=None,
        city="DECATUR",
        us_state="IN",
        zip_code="46733-0000",
        orig="12345\tW 1000 N\tDECATUR\tIN\t46733-0000",
        batch_checksum="",
    ),
]
EXAMPLE_ADDRESSES.extend(todo)

test_parser = Parser(known_cities=[a.city for a in EXAMPLE_ADDRESSES])
# print(list(test_parser.tag("343 Fully Fulton st E APT 1 Blablaville AZ 00000")))


def parse_benchmak():

    exs = [a.orig for a in EXAMPLE_ADDRESSES]
    n = 5000
    adds = itertools.cycle(exs)
    p = test_parser
    start = time.time_ns()
    for _ in range(n):
        p(next(adds))

    stop = time.time_ns()
    print("EACH: ", int(((stop - start) / n) / 1000))


parse_benchmak()


def parse_row_benchmak():

    exs = [a.as_row() for a in EXAMPLE_ADDRESSES]
    n = 5000
    adds = itertools.cycle(exs)
    p = test_parser
    start = time.time_ns()
    for _ in range(n):
        p.parse_row(next(adds))

    stop = time.time_ns()
    print("EACH ROW: ", int(((stop - start) / n) / 1000))


parse_row_benchmak()


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


class TestStateMParts(unittest.TestCase):
    def test_unit_hwy(self):
        def get_unit_or_hwy(
            inpt: GenericInput[str], save: Fn[[GenericInput[str]], None]
        ) -> Opt[Tuple[str, str]]:
            a = get_unit(inpt, save)
            if a:
                return a
            return get_full_hwy(inpt, save)

        out_in = [
            (("unit", "REAR"), "123 kay rear"),
            (("unit", "REAR 6"), "123 kay rear 6"),
            (("st_name", "COUNTY ROAD A3"), "123 Kay Co rd a3"),
            (("st_name", "COUNTY ROAD"), "123 kay co rd"),
            (("unit", "APT 3"), "123 Kay Apt 3"),
        ]

        for _out, _in in out_in:
            f = to_input_lst(_in)
            self.assertEqual(_out, test_state_m(get_unit_or_hwy, f))
            self.assertEqual(["KAY", "123"], list(f[0]))

    def test_full_hwy(self):
        out_in = [
            (("st_name", "COUNTY ROAD A3"), "123 Kay Co rd a3"),
            (("st_name", "COUNTY ROAD"), "123 kay co rd"),
        ]

        for _out, _in in out_in:
            f = to_input_lst(_in)
            self.assertEqual(_out, test_state_m(get_full_hwy, f))
            self.assertEqual(["KAY", "123"], list(f[0]))

    def test_get_nesw(self):
        out_in = [
            (("st_NESW", "E"), "123 kay east"),
            (("st_NESW", "SW"), "123 kay south w"),
            (("st_NESW", "NE"), "123 kay northeast"),
            (("st_NESW", "N"), "123 Kay n"),
        ]
        for _out, _in in out_in:
            f = to_input_lst(_in)
            self.assertEqual(_out, test_state_m(get_nesw, f))
            self.assertEqual(["KAY", "123"], list(f[0]))


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

    def _______test(self):  # TODO
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
        # TODO accept zip/state/city in same cell of row

        return [a.as_row() for a in adds]

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
        p = test_parser
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
        p = Parser(known_cities=["Zamalakoo", "Grand Rapids", "Ford", "Red", "Detroit"])
        for a in __difficult_addresses__:
            p(a)

        for a in EXAMPLE_ADDRESSES:
            a.reparse_test(test_parser)
        zipless = Parser(known_cities=["Asdf"])
        zipless("123 Qwerty St Asdf NY")
        p = test_parser  # Parser()
        should_fail = [
            (
                Parser(known_cities=["Qwerty", "Yuiop", "Asdf"]),
                "123 Qwerty Hjkl NY 00000",
            )
        ]
        for p, s in should_fail:
            with self.assertRaises((ParseError, EndOfInputError)):
                p(s)


class TestHammer(unittest.TestCase):
    def test_checksum(self):  # passes, but slow
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
        p = test_parser
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

    def ___test(self):  # TODO
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
            sorted(map(Address.Get.pretty, set(hammer.as_list()))),
            sorted(["001 E Street St Apt 1 City MI", "001 E Street St Apt 0 City MI"]),
        )


class TestSheet(unittest.TestCase):
    def test(self):
        def unify(addresses: Iter[Address]) -> List[Seq[str]]:
            a: List[Seq[str]] = []
            for address in EXAMPLE_ADDRESSES:
                a.append((".", *address.as_row(), "-"))
            a = [aa for aa in set(a)]
            a = sorted(a)
            return a

        def strip(l: Iter[Seq[str]]) -> List[Seq[str]]:
            return [list(row[1:-1]) for row in l]

        a = unify(EXAMPLE_ADDRESSES)

        sheet = Sheet("B:I", a + a)

        self.assertEqual(strip(a), strip(sheet.merge_duplicates()))
