from __future__ import annotations
from typing import Pattern, Match
import re
from .__types__ import *
from .__address__ import Address, RawAddress
from . import __address__ as address
from . import __regex__ as regex
from .__zipper__ import Zipper, GenericInput, EndOfInputError, Apply
from .__zipper__ import x as zipper_x

# TODO correctly handle all usps secondary unit identifiers and 1/2


class ParseError(Exception):
    "The base class for all parsing errors"
    orig: str
    reason: str

    def __init__(self, address_string: str, reason: str):
        super(ParseError, self).__init__("@ " + reason + ": " + address_string)
        self.orig = address_string
        self.reason = reason


class EndOfAddressError(ParseError):
    """
    The address parser unexpectedly reached the end of the given string.
    This is usually cause by either the 'st_name' or the 'city' consumed the entire string.
    If you get this error, you are probably missing either (a) both the st_suffix and the st_NESW or (b) a us_state.
    """

    def __init__(self, orig: str, reason: str):
        super().__init__(orig, reason + ": end of input")


class ParserConfigError(Exception):
    msg: str

    def __init__(self, msg: str):
        super(ParserConfigError, self).__init__(msg)
        self.msg = msg


class ParseStep(NamedTuple):
    label: str
    value: str


Input = GenericInput[str]


def __make_stops_on__(stop_patterns: Iter[Pattern[str]]) -> Fn[[str], bool]:
    def stops_on(s: str) -> bool:
        for pat in stop_patterns:
            if regex.match(s, pat):
                return True
        return False

    return stops_on


ArrowParse = Fn[[str], Seq[ParseStep]]


class AddressComponent(NamedTuple):
    compiled_pattern: Pattern[str]
    label: str
    cont: Opt[AddressComponent] = None
    optional: bool = False
    stops_on: Fn[[str], bool] = lambda s: False

    def arrow_parse(self) -> ArrowParse:
        def ap(s: str) -> Seq[ParseStep]:
            # print(s)
            if self.stops_on(s):
                # print("stopped")
                return []

            m = regex.match(s, self.compiled_pattern)

            if m is None:
                if self.optional:
                    return []
                raise ParseError(s, self.label)
            p_r = ParseStep(value=m, label=self.label)
            # print(p_r)
            return [p_r]

        return ap

    def then(self, cont: AddressComponent) -> AddressComponent:
        return self._replace(cont=cont)


# fmt: off
st_suffices: List[str] = ["ALY", "ANX", "ARC", "AVE", "BYU", "BCH", "BND", "BLF", "BLFS", "BTM", "BLVD", "BR", "BRG", "BRK", "BRKS", "BG", "BGS", "BYP", "CP", "CYN", "CPE", "CSWY", "CTR", "CTRS", "CIR", "CIRS", "CLF", "CLFS", "CLB", "CMN", "CMNS", "COR", "CORS", "CRSE", "CT", "CTS", "CV", "CVS", "CRK", "CRES", "CRST", "XING", "XRD", "XRDS", "CURV", "DL", "DM", "DV", "DR", "DRS", "EST", "ESTS", "EXPY", "EXT", "EXTS", "FALL", "FLS", "FRY", "FLD", "FLDS", "FLT", "FLTS", "FRD", "FRDS", "FRST", "FRG", "FRGS", "FRK", "FRKS", "FT", "FWY", "GDN", "GDNS", "GTWY", "GLN", "GLNS", "GRN", "GRNS", "GRV", "GRVS", "HBR", "HBRS", "HVN", "HTS", "HWY", "HL", "HLS", "HOLW", "INLT", "IS", "ISS", "ISLE", "JCT", "JCTS", "KY", "KYS", "KNL ", "KNLS", "LK", "LKS", "LAND", "LNDG", "LN", "LGT", "LGTS", "LF", "LCK", "LCKS", "LDG", "LOOP", "MALL", "MNR", "MNRS", "MDW", "MDWS", "MEWS", "ML", "MLS", "MSN", "MTWY", "MT", "MTN", "MTNS", "NCK", "ORCH", "OVAL", "OPAS", "PARK", "PARK", "PKWY", "PKWY", "PASS", "PSGE", "PATH", "PIKE", "PNE ", "PNES", "PL", "PLN", "PLNS", "PLZ", "PT", "PTS", "PRT", "PRTS", "PR", "RADL", "RAMP", "RNCH", "RPD", "RPDS", "RST", "RDG", "RDGS", "RIV", "RD", "RDS", "RTE", "ROW", "RUE", "RUN", "SHL", "SHLS", "SHR", "SHRS", "SKWY", "SPG", "SPGS", "SPUR", "SPUR", "SQ", "SQS", "STA", "STRA", "STRM", "ST", "STS", "SMT", "TER", "TRWY", "TRCE", "TRAK", "TRFY", "TRL", "TUNL", "TPKE", "UPAS", "UN", "UNS", "VLY", "VLYS", "VIA", "VW", "VWS", "VLG", "VLGS", "VL", "VIS", "WALK", "WALK", "WALL", "WAY", "WAYS", "WL", "WLS"]
us_states: List[str] = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "PR", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
unit_types: List[str] = ["#", "APT", "BLDG", "STE", "UNIT", "RM", "DEPT", "TRLR", "LOT", "FL"] 
# fmt: on

# KY is a valid street suffix!!!!!!!
# TODO
state_set = set(us_states)
st_suffices = [s for s in st_suffices if s not in state_set]


unit_types_set = set(unit_types)

st_suffix_R = re.compile(regex.or_(st_suffices))

st_NESWs: List[str] = ["NE", "NW", "SE", "SW", "N", "S", "E", "W"]
st_NESW_R = re.compile(regex.or_(st_NESWs))


us_state_R = re.compile(regex.or_(us_states))

unit_R = re.compile(regex.or_(unit_types))
unit_identifier_R = re.compile(r"\#?\s*(\d+[A-Z]?|[A-Z]\d*)")

zip_code_R = re.compile(r"\d{5}")

_HOUSE_NUMBER_R = re.compile(regex.or_([r"[\d/]+", r"\d+FRAC\d+"]))

_HOUSE_NUMBER = AddressComponent(
    label="house_number", compiled_pattern=_HOUSE_NUMBER_R  # 123 1/3 Pine St
).arrow_parse()


def __make_st_name__(
    known_cities: Seq[Pattern[str]] = (),
) -> Fn[[str], Seq[ParseStep]]:
    return AddressComponent(
        label="st_name",
        compiled_pattern=re.compile(r"\w+"),
        stops_on=__make_stops_on__(
            [st_suffix_R, st_NESW_R, unit_R] + list(known_cities)
        ),
    ).arrow_parse()


# _ST_NAME = __make_st_name__()


def __chomp_rd_number__(words: Seq[str]) -> Seq[ParseStep]:
    # TODO normalize "Road 12" to "Rd 12", highway, etc
    if len(words) == 1:
        return []  # [ParseStep("house_number", "")]
        # print("\n\n", words, "\n\n")
    # assert len(words) == 2
    rd = regex.match(words[0], st_suffix_R)
    if rd in ["RD", "HWY", "RTE"]:
        nm = regex.match(words[1], re.compile(r"\d+"))
        if nm:
            return [ParseStep("st_name", rd), ParseStep("st_name", nm)]
    return []


pre_unit_id_R = re.compile(r"[A-Z]?\d+[A-Z]*")

no_N = re.compile(
    r"\b(\d+|[A-D]|[F-M]|[O-R]|[T-V]|[X-Z])(\d+|[A-D]|[F-M]|[O-R]|[T-V]|[X-Z])?\b"
)


def __chomp_unit__(words: Seq[str]) -> Seq[ParseStep]:
    # assert len(words) == 2
    if len(words) == 1:
        return [ParseStep("city", "")]
    unit: Opt[str] = None
    if words[0] not in unit_types_set:
        if regex.match(words[0], no_N):
            return [ParseStep("unit", "APT " + words[0])]
        else:
            return []
    if words[0] == "#":
        unit = "APT"
    else:
        unit = regex.match(words[0], unit_R)

    if not re.match(no_N, words[1]):
        return [ParseStep("junk", "")]

    identifier = regex.match(words[1], unit_identifier_R)
    # print("uunit", unit, identifier)
    if (unit is None) or (identifier is None):
        # print("unit failed")
        return []
    # result = ParseStep(value="{0} {1}".format(unit, identifier), label="unit")
    return [ParseStep("unit", unit), ParseStep("unit", identifier)]


_ST_NESW = AddressComponent(label="st_NESW", compiled_pattern=st_NESW_R).arrow_parse()

_ST_SUFFIX = AddressComponent(
    label="st_suffix", compiled_pattern=st_suffix_R
).arrow_parse()

_US_STATE = AddressComponent(
    label="us_state", compiled_pattern=us_state_R
).arrow_parse()

_ZIP_CODE = AddressComponent(
    label="zip_code", compiled_pattern=zip_code_R
).arrow_parse()

address_midpoint_R = re.compile(regex.or_(st_suffices + st_NESWs + unit_types))

st_NESW_suffix_R = re.compile(regex.or_(st_NESWs) + r" " + regex.or_(st_suffices))


def str_to_opt(s: Opt[str]) -> Opt[str]:
    if s is None:
        return None
    if not s.split():
        return None
    return s


def city_repl(s: Match[str]) -> str:
    return " " + s.group(0).strip().replace(" ", "_") + " "


Zip = Zipper[str, str]


class Fns_Of_Parser(Fns_Of):
    @staticmethod
    def city(s: str) -> Seq[ParseStep]:
        raise NotImplementedError

    @staticmethod
    def st_name(s: str) -> Seq[ParseStep]:
        raise NotImplementedError


pre_tok: Dict[
    str,
    Tuple[Fn[[str], str], Fn[[Fn[[Dict[str, str]], None]], Fn[[Dict[str, str]], None]]],
] = {}


class Parser:

    """
    A callable address parser.
    In general, prefer using the Hammer class instead of calling the parser directly.
    Parser does not correct typos or auto-infer street suffices or dirrectionals.
    Parser also has the limitation that if the address's city is not in known_cities,
    it will need some kind of identifier to separate the street name and the city name (such as st_suffix, st_NESW or a unit.)

        p = Parser(known_cities="Houston Dallas".split())

    'p' WILL parse the following addresses:

        "123 Straight Houston TX"        # no identifier bewteen street and city (BUT a known city)

        "123 8th Ave NE Ste A Dallas TX" # nothing to see here, normal address

        "123 Dallas Rd Houston TX"       # the street would be recognized as a city (BUT fortunately there is an identifier bewteen the street and city)



    ... but will NOT parse these:

        "123 Straight Houuston TX" #typo

        "123 Straight Austin TX"   #(1) unknown city and (2) no identifier bewteen street and city

        "123 Dallas Houston TX"    # # the street is recognized as a city (and unfortunately there is not an identifier bewteen the street and city)
    """

    __Apply__ = Apply
    __ex_types__ = {"ex_types": tuple([ParseError])}
    __fns__: Fns_Of_Parser
    blank_parse: Opt[Parser]
    required: Set[str] = set(address.HARD_COMPONENTS)
    optional: Set[str] = set(address.SOFT_COMPONENTS)
    known_cities: List[str] = []
    known_cities_R: Opt[Pattern[str]] = None

    def __init__(self, known_cities: Seq[str] = ()):

        known_cities = list(filter(None, known_cities))
        if known_cities:
            self.blank_parse = Parser(known_cities=[])
        else:
            self.blank_parse = None
        normalized_cities = [self.__tokenize__(city) for city in known_cities]
        normalized_cities_B = [w.replace(" ", r"[\s_]") for w in normalized_cities]
        self.known_cities_R = re.compile(regex.or_(normalized_cities_B))
        self.known_cities = known_cities
        city_A = AddressComponent(
            label="city",
            compiled_pattern=re.compile(regex.or_(normalized_cities_B + [r"\w+"])),
            stops_on=__make_stops_on__([us_state_R, re.compile(r"\d+")]),
        ).arrow_parse()

        if self.known_cities_R:
            st_name = __make_st_name__([self.known_cities_R])
        else:
            st_name = __make_st_name__()

        class __Fns_Of_Parser__(Fns_Of_Parser):
            @staticmethod
            def city(s: str) -> Seq[ParseStep]:
                return [
                    ParseStep(value=pr.value.replace("_", " "), label=pr.label)
                    for pr in city_A(s)
                ]

            @staticmethod
            def st_name(s: str) -> Seq[ParseStep]:
                return st_name(s)

        self.__fns__ = __Fns_Of_Parser__()

    @property
    def city(self) -> Fn[[str], Seq[ParseStep]]:
        return self.__fns__.city

    @property
    def st_name(self) -> Fn[[str], Seq[ParseStep]]:
        return self.__fns__.st_name

    def __tokenize__(self, s: str) -> str:
        # s = s.replace(",", " ")
        # s = re.sub(p,s," ")
        s = regex.normalize_whitespace(regex.remove_punc(s).upper())
        s = s.replace("#", "APT ")
        s = s.replace("APT APT", "APT")
        s = s.replace("/", "FRAC")
        if self.known_cities_R:
            s = re.sub(self.known_cities_R, city_repl, s)
        return s

    def __handle_many_suffix__(
        self, s: str
    ) -> Opt[Fn[[Zipper[str, ParseStep]], Zipper[str, ParseStep]]]:

        """
        This is to allow st suffices as part of a st name.
        For example, "123 Park St".
        It only keeps the last valid st_suffix and all the rest will be part of the st_name.

        However, this means " 123 Main St Isle Royal" will not be correctly parsed.
        (you would need to use 'known_cities')
        """
        st_name: Opt[Fn[[Zipper[str, ParseStep]], Zipper[str, ParseStep]]] = None
        all_suffices: List[str] = re.findall(st_suffix_R, s)
        all_suffices.reverse()
        if len(all_suffices) > 1 and all_suffices[0] != "ST":

            def st_name_arrow(s: str) -> Seq[ParseStep]:
                if len(all_suffices) > 1 and s == all_suffices[-1]:
                    all_suffices.pop()
                    return [ParseStep("st_name", s)]
                else:
                    return self.st_name(s)

            st_name = Apply.takewhile(st_name_arrow, False, **Parser.__ex_types__)
        return st_name

    @staticmethod
    def __city_orig__(s: str) -> str:
        s = " ".join([regex.titleize(word) for word in s.split("_")])
        # print(s)
        return s

    def __outline__(
        self,
        st_name: Opt[Fn[[Zipper[str, ParseStep]], Zipper[str, ParseStep]]] = None,
    ) -> List[Fn[[Zipper[str, ParseStep]], Zipper[str, ParseStep]]]:
        Apply = Parser.__Apply__
        p = Parser.__ex_types__
        if st_name is None:
            st_name = Apply.takewhile(self.st_name, False, **p)

        def __pre_nesw_maybe_suffix__(words: Seq[str]) -> Seq[ParseStep]:
            "to parse street names that could also be a NESW, like 123 N Ave ..."
            # TODO
            return []

        return [
            Apply.takewhile(_HOUSE_NUMBER, False, **p),
            Apply.consume_with(_ST_NESW, **p),
            st_name,
            Apply.chomp_n(2, __chomp_rd_number__, **p),
            Apply.takewhile(_ST_SUFFIX, False, **p),
            Apply.consume_with(_ST_NESW, **p),
            Apply.chomp_n(2, __chomp_unit__, **p),
            Apply.takewhile(self.city),
            Apply.consume_with(_US_STATE),
            Apply.consume_with(_ZIP_CODE, **p),
        ]

    def __collect_results__(
        self, _s: str, results: Iter[ParseStep], checked: bool
    ) -> RawAddress:
        d: Dict[str, List[str]] = {
            "house_number": [],
            "st_name": [],
            "st_suffix": [],
            "st_NESW": [],
            "unit": [],
            "city": [],
            "us_state": [],
            "zip_code": [],
        }

        for p_r in results:
            if p_r.label != "junk":
                d[p_r.label] += [p_r.value]
        if not d["st_name"]:
            if d["st_NESW"]:
                m = regex.match(_s.upper(), st_NESW_suffix_R)
                if m:
                    nesw = m.split()[0]
                    d_nesw = d["st_NESW"]
                    try:
                        d["st_name"] = [d_nesw.pop(d_nesw.index(nesw))]
                    except ValueError:
                        pass

        # TODO perform S NW AVE bvld sanity checks right here
        if checked:
            for req in self.required:
                if not d[req]:
                    # msg_b = """\nIf you want to allow this, try passing creating the Parser with the optional kwarg, i.e \n p =  Parser(optional=[..., "{req}"])
                    # """.format(req=req)
                    raise ParseError(_s, "Could not identify " + req)

        d["unit"] = [n.replace("#", "") for n in d["unit"]]
        str_d: Dict[str, Opt[str]] = {
            field: " ".join(values) for field, values in d.items()
        }
        for opt in Parser.optional:
            str_d[opt] = str_to_opt(str_d[opt])
        str_d["is_raw"] = "true"
        str_d["orig"] = _s
        hn = str_d["house_number"]
        if hn:
            str_d["house_number"] = hn.replace("FRAC", "/")
        a = Address.from_dict(str_d)
        assert isinstance(a, RawAddress)
        return a

    def __call__(self, _s: str, checked: bool = True) -> RawAddress:
        Apply = Parser.__Apply__
        if self.blank_parse is not None:
            try:
                return self.blank_parse(_s, checked=checked)
            except:
                pass
        s = self.__tokenize__(_s)
        st_name = self.__handle_many_suffix__(s)
        data = s.split()
        funcs: List[
            Fn[[Zipper[str, ParseStep]], Zipper[str, ParseStep]]
        ] = self.__outline__(st_name=st_name)
        try:

            f: Fn[[Zipper[str, ParseStep]], Zipper[str, ParseStep]] = Apply.reduce(
                funcs
            )
            l: GenericInput[str] = GenericInput(data=data)
            z: Zipper[str, ParseStep] = f(Zipper(l))

        except EndOfInputError as e:
            raise EndOfAddressError(_s, "unknown")

        except ParseError as e:
            raise ParseError(_s, e.reason)

        return self.__collect_results__(_s, z.results, checked)

    def parse_row(self, row: Iter[str]) -> RawAddress:

        unit: Fn[[Zipper[str, ParseStep]], Zipper[str, ParseStep]] = lambda z: z

        # zip_code: Fn[[Zipper[str,ParseStep]], Zipper[str,ParseStep]] = lambda z: z
        p = self.__ex_types__
        row = [self.__tokenize__(s) for s in row]
        st_name = self.__handle_many_suffix__(" ".join(row))
        for cell in row:
            if regex.match(cell, unit_R):
                unit = Apply.chomp_n(2, __chomp_unit__)
                break
        leftovers = [cell.split() for cell in row]
        _z: Zipper[Seq[str], ParseStep] = Zipper(
            leftover=GenericInput(leftovers), results=[]
        )
        if st_name is None:
            st_name = Apply.takewhile(self.st_name, False, **p)

        funcs: List[Fn[[Zipper[str, ParseStep]], Zipper[str, ParseStep]]] = [
            Apply.takewhile(_HOUSE_NUMBER, False, **p),
            Apply.consume_with(_ST_NESW, **p),
            st_name,
            Apply.chomp_n(2, __chomp_rd_number__, **p),
            Apply.takewhile(_ST_SUFFIX, False, **p),
            Apply.consume_with(_ST_NESW, **p),
            unit,
            Apply.takewhile(self.city),
            Apply.consume_with(_US_STATE),
            Apply.consume_with(_ZIP_CODE),
        ]

        z = zipper_x(_z, funcs)

        results = list(z.results)

        # print(results)

        return self.__collect_results__("\t".join(row), results, False)


def smart_batch(
    p: Parser,
    adds: Iter[str],
    report_error: Fn[[ParseError, str], None] = lambda e, s: None,
) -> Iter[RawAddress]:
    """
    This function takes an iter of address strings and tries to repair dirty addresses by using the city information from clean ones.
    For example: "123 Main, Springfield OH 12123" will be correctly parsed iff 'SPRINGFIELD' is a city of another address.
    The 'report_error' callback is called on all address strings that cannot be repaired
    (other than 'report_error', all ParseErrors are ignored)
    """
    errs: List[str] = []
    cities: Set[str] = set([])
    pre = 0
    for add in adds:
        try:
            a = p(add)
            cities.add(a.city)
            pre += 1
            # if pre % 1000 == 0:
            # print(str(pre // 1000) + "k good so far!")
            yield a
        except EndOfInputError:
            errs.append(add)
        except ParseError:
            errs.append(add)

    # print("good:", pre)
    # print(cities)
    p = Parser(known_cities=p.known_cities + list(cities))
    fixed = 0
    for add in errs:
        try:
            a = p(add)
            fixed += 1
            yield a
        except ParseError as e:
            report_error(e, add)
    # print("fixed:", fixed)


__difficult_addresses__ = [
    "000  Plymouth Rd Trlr 113  Ford MI 48000",
    "0 Joy Rd Trlr 105  Red MI 48000",
    "0  Stoepel St #0  Detroit MI 48000",
    "0 W Boston Blvd # 7  Detroit MI 48000",
]
