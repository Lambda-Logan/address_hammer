from __future__ import annotations
import typing as t
import re

#from re import split
from address import Address
import __regex__ as regex
from __zipper__ import Zipper, GenericInput, EndOfInputError


Fn = t.Callable
#TODO correctly handle all usps secondary unit identifiers and 1/2

class ParseError(Exception):
    orig: str
    reason: str
    def __init__(self, address_string: str, reason: str):
        super(ParseError, self).__init__("@ " + reason + ": " + address_string)
        self.orig = address_string
        self.reason = reason

class EndOfAddress(ParseError):
    def __init__(self, address: str, label: str):
        super(ParseError, self).__init__(label + ": end of input of " + address)

class ParseResult(t.NamedTuple):
    label: str
    value: str

Input = GenericInput[str]



def __make_stops_on__(stop_patterns: t.Iterable[t.Pattern[str]])-> Fn[[str], bool]:
    def stops_on(s:str)->bool:
        for pat in stop_patterns:
            if regex.match(s,pat):
                return True
        return False
    return stops_on

ArrowParse = t.Callable[[str], t.Sequence[ParseResult]]

class AddressComponent(t.NamedTuple):
    compiled_pattern: t.Pattern[str]
    label: str
    cont: t.Optional[AddressComponent] = None
    optional: bool = False
    stops_on: Fn[[str], bool] = lambda s: False

    def arrow_parse(self)->ArrowParse:
        def ap(s:str)-> t.Sequence[ParseResult]:
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

st_suffices: t.List[str] = ["ALY", "ANX", "ARC", "AVE", "BYU", "BCH", "BND", "BLF", "BLFS", "BTM", "BLVD", "BR", "BRG", "BRK", "BRKS", "BG", "BGS", "BYP", "CP", "CYN", "CPE", "CSWY", "CTR", "CTRS", "CIR", "CIRS", "CLF", "CLFS", "CLB", "CMN", "CMNS", "COR", "CORS", "CRSE", "CT", "CTS", "CV", "CVS", "CRK", "CRES", "CRST", "XING", "XRD", "XRDS", "CURV", "DL", "DM", "DV", "DR", "DRS", "EST", "ESTS", "EXPY", "EXT", "EXTS", "FALL", "FLS", "FRY", "FLD", "FLDS", "FLT", "FLTS", "FRD", "FRDS", "FRST", "FRG", "FRGS", "FRK", "FRKS", "FT", "FWY", "GDN", "GDNS", "GTWY", "GLN", "GLNS", "GRN", "GRNS", "GRV", "GRVS", "HBR", "HBRS", "HVN", "HTS", "HWY", "HL", "HLS", "HOLW", "INLT", "IS", "ISS", "ISLE", "JCT", "JCTS", "KY", "KYS", "KNL ", "KNLS", "LK", "LKS", "LAND", "LNDG", "LN", "LGT", "LGTS", "LF", "LCK", "LCKS", "LDG", "LOOP", "MALL", "MNR", "MNRS", "MDW", "MDWS", "MEWS", "ML", "MLS", "MSN", "MTWY", "MT", "MTN", "MTNS", "NCK", "ORCH", "OVAL", "OPAS", "PARK", "PARK", "PKWY", "PKWY", "PASS", "PSGE", "PATH", "PIKE", "PNE ", "PNES", "PL", "PLN", "PLNS", "PLZ", "PT", "PTS", "PRT", "PRTS", "PR", "RADL", "RAMP", "RNCH", "RPD", "RPDS", "RST", "RDG", "RDGS", "RIV", "RD", "RDS", "RTE", "ROW", "RUE", "RUN", "SHL", "SHLS", "SHR", "SHRS", "SKWY", "SPG", "SPGS", "SPUR", "SPUR", "SQ", "SQS", "STA", "STRA", "STRM", "ST", "STS", "SMT", "TER", "TRWY", "TRCE", "TRAK", "TRFY", "TRL", "TRLR", "TUNL", "TPKE", "UPAS", "UN", "UNS", "VLY", "VLYS", "VIA", "VW", "VWS", "VLG", "VLGS", "VL", "VIS", "WALK", "WALK", "WALL", "WAY", "WAYS", "WL", "WLS"]
st_suffix_R = re.compile(regex.or_(st_suffices))

st_NESWs: t.List[str] = ["NE", "NW", "SE", "SW", "N", "S", "E", "W"]
st_NESW_R = re.compile(regex.or_(st_NESWs))

us_states: t.List[str] = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "PR", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]
us_state_R = re.compile(regex.or_(us_states))

unit_types: t.List[str] = ["#", "APT", "BLDG", "STE", "UNIT", "RM", "DEPT", "TRLR", "LOT", "FL"] 
unit_R = re.compile(regex.or_(unit_types))
unit_identifier_R = re.compile(r"\#?\s*(\d+[A-Z]?|[A-Z]\d*)")


_HOUSE_NUMBER = AddressComponent(
                 label="house_number", #123 1/3 Pine St
                 compiled_pattern=re.compile(r"[\d/]+")).arrow_parse()

def __make_st_name__(known_cities:t.List[t.Pattern[str]]=[])->Fn[[str], t.Sequence[ParseResult]]:
    return AddressComponent(
            label="st_name",
            compiled_pattern=re.compile(r"\w+"),
            stops_on=__make_stops_on__([st_suffix_R,st_NESW_R,unit_R]+known_cities)).arrow_parse()

#_ST_NAME = __make_st_name__()

def __chomp_unit__(words: t.Sequence[str])->t.Sequence[ParseResult]:
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
                compiled_pattern=re.compile(r"\d{5}")).arrow_parse()

address_midpoint_R = re.compile(regex.or_(st_suffices + st_NESWs + unit_types))

def city_repl(s:t.Match[str])->str:
    return " "+s.group(0).strip().replace(" ", "_")+" "
Zip = Zipper[str, str]
class Parser:
    blank_parse: t.Optional[Parser]
    city: Fn[[str], t.Sequence[ParseResult]]
    st_name: Fn[[str], t.Sequence[ParseResult]]
    required : t.Set[str] = set(["house_number", "st_name", "st_NESW", "st_suffix", "city", "us_state", "zip_code"])
    known_cities : t.List[str] = []
    known_cities_R : t.Optional[t.Pattern[str]] = None
    def __init__(self, optionals:t.List[str] = [], known_cities:t.List[str] = []):
        if known_cities:
            self.blank_parse = Parser(optionals=optionals,known_cities = [] )
        else:
            self.blank_parse = None
        for opt in optionals:
            if opt not in Parser.required:
                raise KeyError("{0} is not a vaild optional arg, they are \"st_NESW\", \"st_suffix\", \"city\", \"us_state\", \"zip_code\"".format(opt))
        self.required = set([field for field in Parser.required if field not in optionals])
        normalized_cities = [self.__tokenize__(city) for city in known_cities]
        normalized_cities_B = [w.replace(" ", r"[\s_]") for w in normalized_cities]
        self.known_cities_R = re.compile(regex.or_(normalized_cities_B))
        self.known_cities = known_cities
        city_A = AddressComponent(
                        label="city",
                        compiled_pattern=re.compile(regex.or_(normalized_cities_B + [r"\w+"])),
                        stops_on=__make_stops_on__([us_state_R, re.compile(r"\d+")])).arrow_parse()
        def city_B(s:str)->t.Sequence[ParseResult]:
            #print("city??", s)
            #print("\t", city_A(s))
            return [ParseResult(value=pr.value.replace("_", " "), label=pr.label) for pr in city_A(s)]
        self.city = city_B
        if self.known_cities_R:
            self.st_name = __make_st_name__([self.known_cities_R])
        else:
            self.st_name = __make_st_name__()

    @staticmethod
    def __tokenize__(s:str)->str:
        s = s.replace(",", " ")
        #s = re.sub(p,s," ")
        s = regex.normalize_whitespace(regex.remove_punc(s).upper())
        s = s.replace("#", "APT ")
        s = s.replace("APT APT", "APT")
        return s
    @staticmethod
    def __city_orig__(s:str)->str:
        s =  " ".join([regex.titleize(word) for word in s.split("_")] )
        #print(s)
        return s
    def __call__(self, _s: str, checked:bool=True)->Address:
        if self.blank_parse != None:
            try:
                return self.blank_parse(_s, checked=checked)
            except:
                pass
        s = self.__tokenize__(_s)
        if self.known_cities_R:
            s = re.sub(self.known_cities_R, city_repl, s) 
            #print(s)
            pass
        p = {"ex_types":tuple([ParseError])} #TODO make Zipper.takewhile ignore exceptions after 1 consumed???
        try:
            z:Zip=Zipper(GenericInput(data=s.split()))\
                    .takewhile(_HOUSE_NUMBER, **p)\
                    .consume_with(_ST_NESW, **p)\
                    .takewhile(self.st_name)\
                    .takewhile(_ST_SUFFIX, **p)\
                    .consume_with(_ST_NESW, **p)
            if regex.match(s, unit_R): #the only difference is .chomp_n(2, __chomp_unit__)... #TODO

                    z:Zip = z.chomp_n(2, __chomp_unit__)
            
            z:Zip = z.takewhile(self.city, **p)\
                .consume_with(_US_STATE)

            if "zip_code" in self.required:
                z = z.consume_with(_ZIP_CODE)

        except EndOfInputError as e:
            raise EndOfInputError( orig = _s)
        except ParseError as e:
            raise ParseError(_s, e.reason)

        d : t.Dict[str, t.List[str]] = {
                "house_number" : [],
                "st_name" : [],
                "st_suffix" : [],
                "st_NESW" : [],
                "unit" : [],
                "city" : [],
                "us_state" : [],
                "zip_code" : [] }

        for p_r in z.results:
            d[p_r.label] += [p_r.value]

        #TODO perform S NW AVE bvld sanity checks right here
        if checked:
            for req in self.required:
                if not d[req]:
                    msg_b = """\nIf you want to allow this, try passing creating the Parser with the optional kwarg, i.e \n p =  Parser(optional=[..., "{req}"])
                    """.format(req=req)
                    raise ParseError(_s, "Could not identify "+req+msg_b)

        d["unit"] = [n.replace("#", "") for n in d["unit"]]
        return Address(orig=_s, **{field : " ".join(values) for field, values in d.items()})


def smart_batch(p: Parser,
               adds:t.Iterable[str],
               report_error: Fn[[Exception, str], None] = lambda e,s: None) -> t.Iterable[Address]:
    errs: t.List[str] = []
    cities : t.Set[str] = set([])
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
    p = Parser(optionals=[x for x in Parser.required if x not in p.required],
               known_cities=p.known_cities + list(cities))
    fixed = 0
    for add in errs:
        try:
            a = p(add)
            fixed += 1
            yield a
        except Exception as e:
            report_error(e, add)
    #print("fixed:", fixed)
    
__incorrrectly_parsed_addresses__ = ["2222  Plymouth Rd Trlr 113  Ford MI 48000", 
                                     "22222 Joy Rd Trlr 105  Red MI 48000",
                                     "22222  Stoepel St # 0  Detroit MI 48000",
                                     "32222 W Boston Blvd # 7  Detroit MI 48000"]

def test():
    p = Parser(known_cities = ["Zamalakoo", "Grand Rapids"], 
               optionals=["st_NESW", "st_suffix", ])
    from address import example_addresses
    for a in example_addresses:
        a.reparse_test(p)
    zipless = Parser(optionals=["zip_code", "st_NESW"])
    zipless("123 Qwerty St Asdf NY")
    p = Parser()
    should_fail = [(Parser(known_cities=["Qwerty", "Yuiop", "Asdf", "Hjkl"],
                            optionals = ["st_NESW"]), "123 Qwerty Hjkl NY 00000"),
                    (p, "123 Qwerty ST Hjkl NY 00000"),
                    (p, "123 Qwerty NW  Hjkl NY 00000")]
    for p, s in should_fail:
        try:
            p(s)
            raise Exception("Failed test " + s)
        except (ParseError, EndOfInputError):
            pass
    try:
        Parser(optionals=["st_nesw"])
        raise Exception("Test failed: allowed an illegal optional argument")
    except KeyError:
        pass






