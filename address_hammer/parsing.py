from __future__ import annotations

from .__types__ import *

from typing import Pattern, Match

import re

from .address import Address, RawAddress
from . import address
from . import __regex__ as regex
from .__zipper__ import Zipper, GenericInput, EndOfInputError


#TODO correctly handle all usps secondary unit identifiers and 1/2

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
        super(ParseError, self).__init__(reason + ": end of input of " + orig)

class ParserConfigError(Exception):
    msg: str
    def __init__(self, msg: str):
        super(ParserConfigError, self).__init__(msg)
        self.msg = msg


class ParseResult(NamedTuple):
    label: str
    value: str

Input = GenericInput[str]



def __make_stops_on__(stop_patterns: Iter[Pattern[str]])-> Fn[[str], bool]:
    def stops_on(s:str)->bool:
        for pat in stop_patterns:
            if regex.match(s,pat):
                return True
        return False
    return stops_on



ArrowParse = Fn[[str], Seq[ParseResult]]

class AddressComponent(NamedTuple):
    compiled_pattern: Pattern[str]
    label: str
    cont: Opt[AddressComponent] = None
    optional: bool = False
    stops_on: Fn[[str], bool] = lambda s: False

    def arrow_parse(self)->ArrowParse:
        def ap(s:str)-> Seq[ParseResult]:
            #print(s)
            if self.stops_on(s):
                #print("stopped")
                return []

            m = regex.match(s, self.compiled_pattern)

            if m == None:
                if self.optional:
                    return []
                raise ParseError(s, self.label)
            p_r = ParseResult(value=m,label=self.label)
            #print(p_r)
            return [p_r]
        return ap

    def then(self, cont: AddressComponent)->AddressComponent:
        return self._replace(cont=cont)

st_suffices: List[str] = ["ALY", "ANX", "ARC", "AVE", "BYU", "BCH", "BND", "BLF", "BLFS", "BTM", "BLVD", "BR", "BRG", "BRK", "BRKS", "BG", "BGS", "BYP", "CP", "CYN", "CPE", "CSWY", "CTR", "CTRS", "CIR", "CIRS", "CLF", "CLFS", "CLB", "CMN", "CMNS", "COR", "CORS", "CRSE", "CT", "CTS", "CV", "CVS", "CRK", "CRES", "CRST", "XING", "XRD", "XRDS", "CURV", "DL", "DM", "DV", "DR", "DRS", "EST", "ESTS", "EXPY", "EXT", "EXTS", "FALL", "FLS", "FRY", "FLD", "FLDS", "FLT", "FLTS", "FRD", "FRDS", "FRST", "FRG", "FRGS", "FRK", "FRKS", "FT", "FWY", "GDN", "GDNS", "GTWY", "GLN", "GLNS", "GRN", "GRNS", "GRV", "GRVS", "HBR", "HBRS", "HVN", "HTS", "HWY", "HL", "HLS", "HOLW", "INLT", "IS", "ISS", "ISLE", "JCT", "JCTS", "KY", "KYS", "KNL ", "KNLS", "LK", "LKS", "LAND", "LNDG", "LN", "LGT", "LGTS", "LF", "LCK", "LCKS", "LDG", "LOOP", "MALL", "MNR", "MNRS", "MDW", "MDWS", "MEWS", "ML", "MLS", "MSN", "MTWY", "MT", "MTN", "MTNS", "NCK", "ORCH", "OVAL", "OPAS", "PARK", "PARK", "PKWY", "PKWY", "PASS", "PSGE", "PATH", "PIKE", "PNE ", "PNES", "PL", "PLN", "PLNS", "PLZ", "PT", "PTS", "PRT", "PRTS", "PR", "RADL", "RAMP", "RNCH", "RPD", "RPDS", "RST", "RDG", "RDGS", "RIV", "RD", "RDS", "RTE", "ROW", "RUE", "RUN", "SHL", "SHLS", "SHR", "SHRS", "SKWY", "SPG", "SPGS", "SPUR", "SPUR", "SQ", "SQS", "STA", "STRA", "STRM", "ST", "STS", "SMT", "TER", "TRWY", "TRCE", "TRAK", "TRFY", "TRL", "TUNL", "TPKE", "UPAS", "UN", "UNS", "VLY", "VLYS", "VIA", "VW", "VWS", "VLG", "VLGS", "VL", "VIS", "WALK", "WALK", "WALL", "WAY", "WAYS", "WL", "WLS"]
st_suffix_R = re.compile(regex.or_(st_suffices))

st_NESWs: List[str] = ["NE", "NW", "SE", "SW", "N", "S", "E", "W"]
st_NESW_R = re.compile(regex.or_(st_NESWs))

us_states: List[str] = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "PR", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
us_state_R = re.compile(regex.or_(us_states))

unit_types: List[str] = ["#", "APT", "BLDG", "STE", "UNIT", "RM", "DEPT", "TRLR", "LOT", "FL"] 
unit_R = re.compile(regex.or_(unit_types))
unit_identifier_R = re.compile(r"\#?\s*(\d+[A-Z]?|[A-Z]\d*)")

zip_code_R = re.compile(r"\d{5}")

_HOUSE_NUMBER = AddressComponent(
                 label="house_number", #123 1/3 Pine St
                 compiled_pattern=re.compile(r"[\d/]+")).arrow_parse()

def __make_st_name__(known_cities:List[Pattern[str]]=[])->Fn[[str], Seq[ParseResult]]:
    return AddressComponent(
            label="st_name",
            compiled_pattern=re.compile(r"\w+"),
            stops_on=__make_stops_on__([st_suffix_R,st_NESW_R,unit_R]+known_cities)).arrow_parse()

#_ST_NAME = __make_st_name__()

def __chomp_unit__(words: Seq[str])->Seq[ParseResult]:
    assert len(words)==2
    if words[0] == "#":
        unit = "APT"
    else:
        unit = regex.match(words[0], unit_R)
    identifier = regex.match(words[1], unit_identifier_R)
    #print("uunit", unit, identifier)
    if (unit == None) or (identifier == None):
        #print("unit failed")
        return []
    result = ParseResult(value="{0} {1}".format(unit, identifier),
                        label = "unit")
    return [result]

_ST_NESW = AddressComponent(
            label="st_NESW",
            compiled_pattern=st_NESW_R).arrow_parse()

_ST_SUFFIX = AddressComponent(
                label="st_suffix",
                compiled_pattern= st_suffix_R).arrow_parse()

_US_STATE = AddressComponent(
                label = "us_state",
                compiled_pattern=us_state_R).arrow_parse()

_ZIP_CODE = AddressComponent(
                label="zip_code",
                compiled_pattern=zip_code_R).arrow_parse()

address_midpoint_R = re.compile(regex.or_(st_suffices + st_NESWs + unit_types))
def str_to_opt(s:Opt[str])->Opt[str]:
    if s == None:
        return None
    if not s.split():
        return None
    return s
def city_repl(s:Match[str])->str:
    return " "+s.group(0).strip().replace(" ", "_")+" "
Zip = Zipper[str, str]




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
    __ex_types__ = {"ex_types":tuple([ParseError])}
    blank_parse: Opt[Parser]
    city: Fn[[str], Seq[ParseResult]]
    st_name: Fn[[str], Seq[ParseResult]]
    required : Set[str] = set(address.HARD_COMPONENTS)
    optional: Set[str] = set(address.SOFT_COMPONENTS)
    known_cities : List[str] = []
    known_cities_R : Opt[Pattern[str]] = None
    def __init__(self,  known_cities:List[str]= []):
        
        known_cities = list(filter(None, known_cities))
        if known_cities:
            self.blank_parse = Parser(known_cities = [])
        else:
            self.blank_parse = None
        normalized_cities = [self.__tokenize__(city) for city in known_cities]
        normalized_cities_B = [w.replace(" ", r"[\s_]") for w in normalized_cities]
        self.known_cities_R = re.compile(regex.or_(normalized_cities_B))
        self.known_cities = known_cities
        city_A = AddressComponent(
                        label="city",
                        compiled_pattern=re.compile(regex.or_(normalized_cities_B + [r"\w+"])),
                        stops_on=__make_stops_on__([us_state_R, re.compile(r"\d+")])).arrow_parse()
        def city_B(s:str)->Seq[ParseResult]:
            #print("city??", s)
            #print("\t", city_A(s))
            return [ParseResult(value=pr.value.replace("_", " "), label=pr.label) for pr in city_A(s)]
        self.city = city_B
        if self.known_cities_R:
            self.st_name = __make_st_name__([self.known_cities_R])
        else:
            self.st_name = __make_st_name__()


    def __tokenize__(self,s:str)->str:
        s = s.replace(",", " ")
        #s = re.sub(p,s," ")
        s = regex.normalize_whitespace(regex.remove_punc(s).upper())
        s = s.replace("#", "APT ")
        s = s.replace("APT APT", "APT")
        if self.known_cities_R:
            s = re.sub(self.known_cities_R, city_repl, s) 
        return s
    @staticmethod
    def __city_orig__(s:str)->str:
        s =  " ".join([regex.titleize(word) for word in s.split("_")] )
        #print(s)
        return s

    def __hn_nesw__(self)->List[Fn[[Zipper[str, ParseResult]], Zipper[str, ParseResult]]]:
        from .__zipper__ import Apply
        p = Parser.__ex_types__
        return [
                    Apply.consume_with(_HOUSE_NUMBER, **p),
                    Apply.consume_with(_ST_NESW, **p ),
                    Apply.takewhile(self.st_name, **p ),
                    Apply.takewhile(_ST_SUFFIX, **p ),
                    Apply.consume_with(_ST_NESW, **p)
            ]
    def __collect_results__(self, _s:str, results: Iter[ParseResult], checked:bool)->RawAddress:
        d : Dict[str, List[str]] = {
                "house_number" : [],
                "st_name" : [],
                "st_suffix" : [],
                "st_NESW" : [],
                "unit" : [],
                "city" : [],
                "us_state" : [],
                "zip_code" : [] }

        for p_r in results:
            if p_r.label != "junk":
                d[p_r.label] += [p_r.value]

        #TODO perform S NW AVE bvld sanity checks right here
        if checked:
            for req in self.required:
                if not d[req]:
                    #msg_b = """\nIf you want to allow this, try passing creating the Parser with the optional kwarg, i.e \n p =  Parser(optional=[..., "{req}"])
                    #""".format(req=req)
                    raise ParseError(_s, "Could not identify "+req)

        d["unit"] = [n.replace("#", "") for n in d["unit"]]
        str_d: Dict[str, Opt[str]] = {field : " ".join(values) for field, values in d.items()}
        for opt in Parser.optional:
            str_d[opt] = str_to_opt(str_d[opt])
        return RawAddress(orig=_s, **str_d)

    def __call__(self, _s: str, checked:bool=True)->RawAddress:
        from .__zipper__ import Apply

        #print(_s)
        if self.blank_parse != None:
            try:
                return self.blank_parse(_s, checked=checked)
            except:
                pass
        s = self.__tokenize__(_s)
        p = Parser.__ex_types__
        unit: Fn[[Zipper[str,ParseResult]], Zipper[str,ParseResult]] = lambda z: z
        zip_code: Fn[[Zipper[str,ParseResult]], Zipper[str,ParseResult]] = lambda z: z
        if regex.match(s, unit_R):
            unit = Apply.chomp_n(2, __chomp_unit__, **p)
        data = s.split()
        if data and regex.match(data[-1], zip_code_R):
            zip_code = Apply.consume_with(_ZIP_CODE, **p)
         #TODO make Zipper.takewhile ignore exceptions after 1 consumed???
        funcs = [*self.__hn_nesw__(), 
                 unit,
                 Apply.takewhile(self.city),
                 Apply.consume_with(_US_STATE),
                 zip_code]
        try:

            
            f: Fn[[Zipper[str, ParseResult]], Zipper[str, ParseResult]] = Apply.reduce(funcs)
            z:Zipper[str, ParseResult]=f(Zipper(GenericInput(data=data)))

        except EndOfInputError as e:
            raise EndOfAddressError(_s, "unknown")

        except ParseError as e:
            raise ParseError(_s, e.reason)

        return self.__collect_results__(_s, z.results, checked)
    
    def parse_row(self, row: Iter[str])->RawAddress:
        from .__zipper__ import x, Zipper, Apply
        from .__zipper__ import GenericInput as Input
        unit: Fn[[Zipper[str,ParseResult]], Zipper[str,ParseResult]] = lambda z: z
        zip_code: Fn[[Zipper[str,ParseResult]], Zipper[str,ParseResult]] = lambda z: z
        row = [self.__tokenize__(s) for s in row]
        for cell in row:
            if regex.match(cell, unit_R):
                unit = Apply.chomp_n(2, __chomp_unit__)
                break
        leftovers = [cell.split() for cell in row]
        z: Zipper[List[str], ParseResult] = Zipper(leftover=Input(leftovers), results=[])
        
        funcs = [*self.__hn_nesw__(), 
                 unit,
                 Apply.takewhile(self.city),
                 Apply.consume_with(_US_STATE),
                 Apply.consume_with(_ZIP_CODE)]
        
        z = x(z, funcs)

        results = list(z.results)

        #print(results)
        
        return self.__collect_results__("\t".join(row),
                 results,
                 False)
def smart_batch(p: Parser,
               adds:Iter[str],
               report_error: Fn[[ParseError, str], None] = lambda e,s: None) -> Iter[RawAddress]:
    """
    This function takes an iter of address strings and tries to repair dirty addresses by using the city information from clean ones.
    For example: "123 Main, Springfield OH 12123" will be correctly parsed iff 'SPRINGFIELD' is a city of another address.
    The 'report_error' callback is called on all address strings that cannot be repaired
    (other than 'report_error', all ParseErrors are ignored)
    """
    errs: List[str] = []
    cities : Set[str] = set([])
    pre = 0
    for add in adds:
        try:
            a = p(add)
            cities.add(a.city)
            pre+=1
            if pre%1000 == 0:
                print(str(pre//1000)+"k good so far!")
                pass
            yield a
        except EndOfInputError:
            errs.append(add)
        except ParseError:
            errs.append(add)

    #print("good:", pre)
    #print(cities)
    p = Parser(known_cities=p.known_cities + list(cities))
    fixed = 0
    for add in errs:
        try:
            a = p(add)
            fixed += 1
            yield a
        except ParseError as e:
            report_error(e, add)
    #print("fixed:", fixed)
    
__difficult_addresses__ = ["000  Plymouth Rd Trlr 113  Ford MI 48000", 
                                     "0 Joy Rd Trlr 105  Red MI 48000",
                                     "0  Stoepel St #0  Detroit MI 48000",
                                     "0 W Boston Blvd # 7  Detroit MI 48000"]


def addresses_to_rows(seed: int, adds: Iter[Address])->List[List[str]]:
    """
    This is used for testing Parser.parse_row.
    It takes a list of addresses and returns a list of rows that should represent each address
    """
    import random
    random.seed(seed)
    STOP_SEP = "dkjf4oit"
    def make_row(a:Address)->Iter[str]:
        def _(a:Address)->Iter[str]:
            flip = lambda : random.choice([True, False])
            for idx, word in enumerate(a[:8]):
                if word == None:
                    word = ""
                if flip() or idx == 4:
                    yield STOP_SEP
                yield word
        return " ".join(_(a)).split(STOP_SEP)
    return [list(make_row(a)) for a in adds]

def test_parse_row():
    import random
    z = 2^10 - 1
    random.seed(z)
    p = Parser() 
    seeds = [random.randrange(0-z,z) for _ in range(16)]
    for seed in seeds:
        print(seed)
        from .address import example_addresses as exs
        rows = addresses_to_rows(seed, exs)
        for row, a in zip(rows,exs):
            r = Address(*p.parse_row(row))
            r.reparse_test(lambda s: a)
            if not (a == r):
                for i, (_a, _r) in enumerate(zip(a,r)):
                    if _a != _r:
                        print(i, _a, "!=", _r)
                raise Exception()

def test():
    test_parse_row()
    p = Parser(known_cities= ["city"])
    adds = ["0 Street apt 5 St City MI", 
            "0 Street NE City MI",
            "0 Street Apt 3 City MI",
            "0 Street Apt 0 City MI",
            "1 Street City MI"]
    (adds)
    #print([[a.pretty() for a in a_s] for a_s in d.values()])
    #print([a.pretty() for a in RawAddress.merge_duplicates(map(p, adds))])
    p = Parser(known_cities = ["Zamalakoo", "Grand Rapids"])
    for a in __difficult_addresses__:
        p(a)

    from .address import example_addresses
    for a in example_addresses:
        a.reparse_test(p)
    zipless = Parser()
    zipless("123 Qwerty St Asdf NY")
    p = Parser()
    should_fail = [(Parser(known_cities=["Qwerty", "Yuiop", "Asdf", "Hjkl"]), "123 Qwerty Hjkl NY 00000")]
    for p, s in should_fail:
        try:
            p(s)
            raise Exception("Should have failed test " + s)
        except (ParseError, EndOfInputError):
            pass




