from __future__ import annotations
from typing import Pattern, NamedTuple, Type, Mapping
from .__types__ import *
from .__zipper__ import GenericInput as In
from .__zipper__ import EndOfInputError
from .__regex__ import or_ as regex_or
from .__regex__ import normalize_whitespace
from .__data__ import state_city_pairs, default_cities
from .__address__ import RawAddress
import re


class ParseError(Exception):
    "The base class for all parsing errors"
    orig: str
    reason: str

    def __init__(self, address_string: str, reason: str):
        super(ParseError, self).__init__("@ " + reason + ": " + address_string)
        self.orig = address_string
        self.reason = reason


# fmt: off
st_suffices: List[str] = ["ALY", "ANX", "ARC", "AVE", "BYU", "BCH", "BND", "BLF", "BLFS", "BTM", "BLVD", "BR", "BRG", "BRK", "BRKS", "BG", "BGS", "BYP", "CP", "CYN", "CPE", "CSWY", "CTR", "CTRS", "CIR", "CIRS", "CLF", "CLFS", "CLB", "CMN", "CMNS", "COR", "CORS", "CRSE", "CT", "CTS", "CV", "CVS", "CRK", "CRES", "CRST", "XING", "XRD", "XRDS", "CURV", "DL", "DM", "DV", "DR", "DRS", "EST", "ESTS", "EXPY", "EXT", "EXTS", "FALL", "FLS", "FRY", "FLD", "FLDS", "FLT", "FLTS", "FRD", "FRDS", "FRST", "FRG", "FRGS", "FRK", "FRKS", "FT", "FWY", "GDN", "GDNS", "GTWY", "GLN", "GLNS", "GRN", "GRNS", "GRV", "GRVS", "HBR", "HBRS", "HVN", "HTS", "HWY", "HL", "HLS", "HOLW", "INLT", "IS", "ISS", "ISLE", "JCT", "JCTS", "KY", "KYS", "KNL ", "KNLS", "LK", "LKS", "LAND", "LNDG", "LN", "LGT", "LGTS", "LF", "LCK", "LCKS", "LDG", "LOOP", "MALL", "MNR", "MNRS", "MDW", "MDWS", "MEWS", "ML", "MLS", "MSN", "MTWY", "MT", "MTN", "MTNS", "NCK", "ORCH", "OVAL", "OPAS", "PARK", "PARK", "PKWY", "PKWY", "PASS", "PSGE", "PATH", "PIKE", "PNE ", "PNES", "PL", "PLN", "PLNS", "PLZ", "PT", "PTS", "PRT", "PRTS", "PR", "RADL", "RAMP", "RNCH", "RPD", "RPDS", "RST", "RDG", "RDGS", "RIV", "RD", "RDS", "RTE", "ROW", "RUE", "RUN", "SHL", "SHLS", "SHR", "SHRS", "SKWY", "SPG", "SPGS", "SPUR", "SPUR", "SQ", "SQS", "STA", "STRA", "STRM", "ST", "STS", "SMT", "TER", "TRWY", "TRCE", "TRAK", "TRFY", "TRL", "TUNL", "TPKE", "UPAS", "UN", "UNS", "VLY", "VLYS", "VIA", "VW", "VWS", "VLG", "VLGS", "VL", "VIS", "WALK", "WALK", "WALL", "WAY", "WAYS", "WL", "WLS"]
us_states: List[str] = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "PR", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

MDict = Dict[str, List[Union[str, List[str]]]]
__suffix_syns__ =  {"ALY  ": ["ALLEY", "ALLEE", "ALLEY", "ALLY", "ALY"],     "ANX  ": ["ANEX", "ANEX", "ANNEX", "ANNX", "ANX"],     "ARC  ": ["ARCADE", "ARC ", "ARCADE "],     "AVE  ": ["AVENUE", "AV", "AVE", "AVEN", "AVENU", "AVENUE", "AVN", "AVNUE"],     "BYU  ": ["BAYOU", "BAYOO", "BAYOU"],     "BCH  ": ["BEACH", "BCH", "BEACH"],     "BND  ": ["BEND", "BEND", "BND"],     "BLF  ": ["BLUFF", "BLF", "BLUF", "BLUFF"],     "BLFS  ": ["BLUFFS", "BLUFFS "],     "BTM  ": ["BOTTOM", " ", "BOT", "BTM", "BOTTM", "BOTTOM"],     "BLVD  ": ["BOULEVARD", "BLVD", "BOUL", "BOULEVARD ", "BOULV"],     "BR  ": ["BRANCH", "BR", "BRNCH", "BRANCH"],     "BRG  ": ["BRIDGE", "BRDGE", "BRG", "BRIDGE"],     "BRK  ": ["BROOK", "BRK", "BROOK"],     "BRKS  ": ["BROOKS", "BROOKS "],     "BG  ": ["BURG", "BURG"],     "BGS  ": ["BURGS", "BURGS"],     "BYP  ": ["BYPASS", "BYP", "BYPA", "BYPAS", "BYPASS", "BYPS"],     "CP  ": ["CAMP", "CAMP", "CP", "CMP"],     "CYN  ": ["CANYON", " ", "CANYN", "CANYON", "CNYN"],     "CPE  ": ["CAPE", " ", "CAPE", "CPE"],     "CSWY  ": ["CAUSEWAY", " ", "CAUSEWAY", "CAUSWA", "CSWY"],     "CTR  ": ["CENTER",      "CEN",      "CENT",      "CENTER",      "CENTR",      "CENTRE",      "CNTER",      "CNTR",      "CTR"],     "CTRS  ": ["CENTERS", "CENTERS "],     "CIR  ": ["CIRCLE", "CIR", "CIRC", "CIRCL", "CIRCLE", "CRCL", "CRCLE"],     "CIRS  ": ["CIRCLES", "CIRCLES"],     "CLF  ": ["CLIFF", "CLF", "CLIFF"],     "CLFS  ": ["CLIFFS", "CLFS", "CLIFFS"],     "CLB  ": ["CLUB", "CLB", "CLUB"],     "CMN  ": ["COMMON", "COMMON"],     "CMNS  ": ["COMMONS", "COMMONS"],     "COR  ": ["CORNER", "COR", "CORNER"],     "CORS  ": ["CORNERS", "CORNERS", "CORS"],     "CRSE  ": ["COURSE", "COURSE", "CRSE"],     "CT  ": ["COURT", "COURT", "CT"],     "CTS  ": ["COURTS", "COURTS", "CTS"],     "CV  ": ["COVE", "COVE", "CV"],     "CVS  ": ["COVES", "COVES"],     "CRK  ": ["CREEK", "CREEK", "CRK"],     "CRES  ": ["CRESCENT", "CRESCENT", "CRES", "CRSENT", "CRSNT"],     "CRST  ": ["CREST", "CREST"],     "XING  ": ["CROSSING", " ", "CROSSING ", "CRSSNG ", "XING "],     "XRD  ": ["CROSSROAD", "CROSSROAD"],     "XRDS  ": ["CROSSROADS", "CROSSROADS"],     "CURV  ": ["CURVE ", "CURVE "],     "DL  ": ["DALE", "DALE ", "DL "],     "DM  ": ["DAM", "DAM ", "DM "],     "DV  ": ["DIVIDE", "DIV", "DIVIDE", "DV", "DVD"],     "DR  ": ["DRIVE", "DR", "DRIV", "DRIVE", "DRV"],     "DRS  ": ["DRIVES ", "DRIVES"],     "EST  ": ["ESTATE", "EST", "ESTATE"],     "ESTS  ": ["ESTATES", "ESTATES", "ESTS"],     "EXPY  ": ["EXPRESSWAY",      "EXP",      "EXPR",      "EXPRESS",      "EXPRESSWAY",      "EXPW",      "EXPY"],     "EXT  ": ["EXTENSION", "EXT", "EXTENSION", "EXTN", "EXTNSN"],     "EXTS  ": ["EXTENSIONS", "EXTS"],     "FALL  ": ["FALL", "FALL"],     "FLS  ": ["FALLS", "FALLS", "FLS"],     "FRY  ": ["FERRY", "FERRY", "FRRY", "FRY"],     "FLD  ": ["FIELD", "FIELD", "FLD"],     "FLDS  ": ["FIELDS", "FIELDS", "FLDS"],     "FLT  ": ["FLAT", "FLAT", "FLT"],     "FLTS  ": ["FLATS", "FLATS", "FLTS"],     "FRD  ": ["FORD", "FORD", "FRD"],     "FRDS  ": ["FORDS", "FORDS"],     "FRST  ": ["FOREST", "FOREST", "FORESTS", "FRST"],     "FRG  ": ["FORGE", "FORG", "FORGE", "FRG"],     "FRGS  ": ["FORGES", "FORGES"],     "FRK  ": ["FORK", "FORK", "FRK"],     "FRKS  ": ["FORKS", "FORKS", "FRKS"],     "FT  ": ["FORT", "FORT", "FRT", "FT"],     "FWY  ": ["FREEWAY", "FREEWAY", "FREEWY", "FRWAY", "FRWY", "FWY"],     "GDN  ": ["GARDEN", "GARDEN", "GARDN", "GRDEN", "GRDN"],     "GDNS  ": ["GARDENS", "GARDENS", "GDNS", "GRDNS"],     "GTWY  ": ["GATEWAY", "GATEWAY", "GATEWY", "GATWAY", "GTWAY", "GTWY"],     "GLN  ": ["GLEN", "GLEN", "GLN"],     "GLNS  ": ["GLENS", "GLENS"],     "GRN  ": ["GREEN", "GREEN", "GRN"],     "GRNS  ": ["GREENS", "GREENS"],     "GRV  ": ["GROVE", "GROV", "GROVE", "GRV"],     "GRVS  ": ["GROVES", "GROVES"],     "HBR  ": ["HARBOR", "HARB", "HARBOR", "HARBR", "HBR", "HRBOR"],     "HBRS  ": ["HARBORS", "HARBORS"],     "HVN  ": ["HAVEN", "HAVEN", "HVN"],     "HTS  ": ["HEIGHTS", "HT", "HTS"],     "HWY  ": ["HIGHWAY", "HIGHWAY", "HIGHWY", "HIWAY", "HIWY", "HWAY", "HWY"],     "HL  ": ["HILL", "HILL", "HL"],     "HLS  ": ["HILLS", "HILLS", "HLS"],     "HOLW  ": ["HOLLOW", "HLLW", "HOLLOW", "HOLLOWS", "HOLW", "HOLWS"],     "INLT  ": ["INLET", "INLT"],     "IS  ": ["ISLAND", "IS", "ISLAND", "ISLND"],     "ISS  ": ["ISLANDS", "ISLANDS", "ISLNDS", "ISS"],     "ISLE  ": ["ISLE", "ISLE", "ISLES"],     "JCT  ": ["JUNCTION",      "JCT",      "JCTION",      "JCTN",      "JUNCTION",      "JUNCTN",      "JUNCTON"],     "JCTS  ": ["JUNCTIONS", "JCTNS", "JCTS", "JUNCTIONS"],     "KY  ": ["KEY", "KEY", "KY"],     "KYS  ": ["KEYS", "KEYS", "KYS"],     "KNL   ": ["KNOLL", "KNL", "KNOL", "KNOLL"],     "KNLS  ": ["KNOLLS", "KNLS", "KNOLLS"],     "LK  ": ["LAKE", "LK", "LAKE"],     "LKS  ": ["LAKES", "LKS", "LAKES"],     "LAND  ": ["LAND", "LAND"],     "LNDG  ": ["LANDING", "LANDING", "LNDG", "LNDNG"],     "LN  ": ["LANE", "LANE", "LN"],     "LGT  ": ["LIGHT", "LGT", "LIGHT"],     "LGTS  ": ["LIGHTS", "LIGHTS"],     "LF  ": ["LOAF", "LF", "LOAF"],     "LCK  ": ["LOCK", "LCK", "LOCK"],     "LCKS  ": ["LOCKS", "LCKS", "LOCKS"],     "LDG  ": ["LODGE", "LDG", "LDGE", "LODG", "LODGE"],     "LOOP  ": ["LOOP", "LOOP", "LOOPS"],     "MALL  ": ["MALL", "MALL"],     "MNR  ": ["MANOR", "MNR", "MANOR"],     "MNRS  ": ["MANORS", "MANORS", "MNRS"],     "MDW  ": ["MEADOW", "MEADOW"],     "MDWS  ": ["MEADOWS", "MDW", "MDWS", "MEADOWS", "MEDOWS"],     "MEWS  ": ["MEWS", "MEWS"],     "ML  ": ["MILL", "MILL"],     "MLS  ": ["MILLS", "MILLS"],     "MSN  ": ["MISSION", "MISSN", "MSSN"],     "MTWY  ": ["MOTORWAY", "MOTORWAY"],     "MT  ": ["MOUNT", "MNT", "MT", "MOUNT"],     "MTN  ": ["MOUNTAIN", "MNTAIN", "MNTN", "MOUNTAIN", "MOUNTIN", "MTIN", "MTN"],     "MTNS  ": ["MOUNTAINS", "MNTNS", "MOUNTAINS"],     "NCK  ": ["NECK", "NCK", "NECK"],     "ORCH  ": ["ORCHARD", "ORCH", "ORCHARD", "ORCHRD"],     "OVAL  ": ["OVAL", "OVAL", "OVL"],     "OPAS  ": ["OVERPASS", "OVERPASS"],     "PARK  ": ["PARKS", "PARKS"],     "PKWY  ": ["PARKWAYS", "PARKWAYS", "PKWYS"],     "PASS  ": ["PASS", "PASS"],     "PSGE  ": ["PASSAGE", "PASSAGE"],     "PATH  ": ["PATH", "PATH", "PATHS"],     "PIKE  ": ["PIKE", "PIKE", "PIKES"],     "PNE   ": ["PINE", "PINE"],     "PNES  ": ["PINES", "PINES", "PNES"],     "PL  ": ["PLACE", "PL"],     "PLN  ": ["PLAIN", "PLAIN", "PLN"],     "PLNS  ": ["PLAINS", "PLAINS", "PLNS"],     "PLZ  ": ["PLAZA", "PLAZA", "PLZ", "PLZA"],     "PT  ": ["POINT", "POINT", "PT"],     "PTS  ": ["POINTS", "POINTS", "PTS"],     "PRT  ": ["PORT", "PORT", "PRT"],     "PRTS  ": ["PORTS", "PORTS", "PRTS"],     "PR  ": ["PRAIRIE", "PR", "PRAIRIE", "PRR"],     "RADL  ": ["RADIAL", "RAD", "RADIAL", "RADIEL", "RADL"],     "RAMP  ": ["RAMP", "RAMP"],     "RNCH  ": ["RANCH", "RANCH", "RANCHES", "RNCH", "RNCHS"],     "RPD  ": ["RAPID", "RAPID", "RPD"],     "RPDS  ": ["RAPIDS", "RAPIDS", "RPDS"],     "RST  ": ["REST", "REST", "RST"],     "RDG  ": ["RIDGE", "RDG", "RDGE", "RIDGE"],     "RDGS  ": ["RIDGES", "RDGS", "RIDGES"],     "RIV  ": ["RIVER", "RIV", "RIVER", "RVR", "RIVR"],     "RD  ": ["ROAD", "RD", "ROAD"],     "RDS  ": ["ROADS", "ROADS", "RDS"],     "RTE  ": ["ROUTE", "ROUTE"],     "ROW  ": ["ROW", "ROW"],     "RUE  ": ["RUE", "RUE"],     "RUN  ": ["RUN", "RUN"],     "SHL  ": ["SHOAL", "SHL", "SHOAL"],     "SHLS  ": ["SHOALS", "SHLS", "SHOALS"],     "SHR  ": ["SHORE", "SHOAR", "SHORE", "SHR"],     "SHRS  ": ["SHORES", "SHOARS", "SHORES", "SHRS"],     "SKWY  ": ["SKYWAY", "SKYWAY"],     "SPG  ": ["SPRING", "SPG", "SPNG", "SPRING", "SPRNG"],     "SPGS  ": ["SPRINGS", "SPGS", "SPNGS", "SPRINGS", "SPRNGS"],     "SPUR  ": ["SPURS", "SPURS"],     "SQ  ": ["SQUARE", "SQ", "SQR", "SQRE", "SQU", "SQUARE"],     "SQS  ": ["SQUARES", "SQRS", "SQUARES"],     "STA  ": ["STATION", "STA", "STATION", "STATN", "STN"],     "STRA  ": ["STRAVENUE",      "STRA",      "STRAV",      "STRAVEN",      "STRAVENUE",      "STRAVN",      "STRVN",      "STRVNUE"],     "STRM  ": ["STREAM", "STREAM", "STREME", "STRM"],     "ST  ": ["STREET", "STREET", "STRT", "ST", "STR"],     "STS  ": ["STREETS", "STREETS"],     "SMT  ": ["SUMMIT", "SMT", "SUMIT", "SUMITT", "SUMMIT"],     "TER  ": ["TERRACE", "TER", "TERR", "TERRACE"],     "TRWY  ": ["THROUGHWAY", "THROUGHWAY"],     "TRCE  ": ["TRACE", "TRACE", "TRACES", "TRCE"],     "TRAK  ": ["TRACK", "TRACK", "TRACKS", "TRAK", "TRK", "TRKS"],     "TRFY  ": ["TRAFFICWAY", "TRAFFICWAY"],     "TRL  ": ["TRAIL", "TRAIL", "TRAILS", "TRL", "TRLS", "TR"],     "TRLR  ": ["TRAILER", "TRAILER", "TRLR", "TRLRS"],     "TUNL  ": ["TUNNEL", "TUNEL", "TUNL", "TUNLS", "TUNNEL", "TUNNELS", "TUNNL"],     "TPKE  ": ["TURNPIKE", "TRNPK", "TURNPIKE", "TURNPK"],     "UPAS  ": ["UNDERPASS", "UNDERPASS"],     "UN  ": ["UNION", "UN", "UNION"],     "UNS  ": ["UNIONS", "UNIONS"],     "VLY  ": ["VALLEY", "VALLEY", "VALLY", "VLLY", "VLY"],     "VLYS  ": ["VALLEYS", "VALLEYS", "VLYS"],     "VIA  ": ["VIADUCT", "VDCT", "VIA", "VIADCT", "VIADUCT"],     "VW  ": ["VIEW", "VIEW", "VW"],     "VWS  ": ["VIEWS", "VIEWS", "VWS"],     "VLG  ": ["VILLAGE", "VILL", "VILLAG", "VILLAGE", "VILLG", "VILLIAGE", "VLG"],     "VLGS  ": ["VILLAGES", "VILLAGES", "VLGS"],     "VL  ": ["VILLE", "VILLE", "VL"],     "VIS  ": ["VISTA", "VIS", "VIST", "VISTA", "VST", "VSTA"],     "WALK  ": ["WALKS", "WALKS"],     "WALL  ": ["WALL", "WALL"],     "WAY  ": ["WAY", "WY", "WAY"],     "WAYS  ": ["WAYS", "WAYS"],     "WL   ": ["WELL", "WELL"],     "WLS  ": ["WELLS", "WELLS", "WLS"]}
st_suffix_syns: MDict = {k.strip().upper(): [w.strip().upper() for w in v] for k,v in __suffix_syns__.items()}
unit_types_lst: List[str] = ["#", "APT", "BLDG", "STE", "UNIT", "RM", "DEPT", "TRLR", "LOT", "FL"]
# fmt: on

st_suffices_dict = {s: [s] for s in st_suffix_syns.keys()}
st_suffices_dict["AVE"].extend(["AVENUE"])
state_set = set(us_states)
st_suffices = [s for s in st_suffices if s not in state_set]

unit_types_set = set(unit_types_lst)

st_NESWs: List[str] = ["NE", "NW", "SE", "SW", "N", "S", "E", "W"]
st_NESW_R = re.compile(regex_or(st_NESWs))


us_state_R = re.compile(regex_or(us_states))

unit_R = re.compile(regex_or(unit_types_lst))
unit_identifier_R = re.compile(r"\#?\s*((\d+[A-Z]?|[A-Z]\d*)|([A-Z]|\d+)-([A-Z]|\d+))")
# unit_identifier_R = re.compile(r"([A-Z]|\d+)-([A-Z]|\d+)")

zip_code_R = re.compile(r"\d{5}(-\d+)?")
_HOUSE_NUMBER_R = re.compile(r"[\d/]+")


def dicts_to_pattern(*ds: Dict[str, List[Union[str, List[str]]]]) -> Pattern[str]:
    f: List[str] = []
    for d in ds:
        for k, row in d.items():
            f.extend(k.split())
            for cell in row:
                if isinstance(cell, str):
                    cell = cell.split()
                f.extend(cell)
    return re.compile(regex_or(set(f)))


st_suffix_R = dicts_to_pattern(st_suffix_syns)


def try_regex(pat: Pattern[str]) -> Fn[[In[str], Fn[[In[str]], None]], Opt[str]]:
    def x(inpt: In[str], save: Fn[[In[str]], None]) -> Opt[str]:
        if inpt.empty():
            return None
        item, rest = inpt.view()
        m = re.match(pat, item)
        if m is not None and m:
            save(rest)
            return m.group(0)
        return None

    return x


def try_full_regex(pat: Pattern[str]) -> Fn[[In[str], Fn[[In[str]], None]], Opt[str]]:
    def x(inpt: In[str], save: Fn[[In[str]], None]) -> Opt[str]:
        if inpt.empty():
            return None
        item, rest = inpt.view()
        m = re.fullmatch(pat, item)
        if m is not None and m:
            save(rest)
            return m.group(0)
        return None

    return x


# TODO don't match bad zips, like 948848-234
zip_code = try_regex(zip_code_R)

K = TypeVar("K")
V = TypeVar("V")


class Mx(NamedTuple):
    pass


class MxEnd(Mx):
    pass


class MxCont(Mx):
    pass


def make_try_syns(
    d: Dict[Tuple[Type[Mx], Seq[str]], str],
    normalizers: List[Fn[[str], Iter[str]]] = [],
) -> Fn[[Type[Mx], Seq[str]], Opt[Tuple[Seq[str], str]]]:
    def x(mx: Type[Mx], items: Seq[str]) -> Opt[Tuple[Seq[str], str]]:
        s = d.get((mx, items), None)
        if s is not None:
            return items, s
        focus = items[-1]
        _items = list(items)
        for n in normalizers:
            for maybe in n(focus):
                _items[-1] = maybe
                s = d.get((mx, tuple(_items)), None)
                if s is not None:
                    return _items, s
        return None

    return x


def from_mealy(
    d: Dict[Tuple[Type[Mx], Seq[str]], str],
    normalizers: Seq[Opt[Dict[str, List[str]]]] = (),
) -> Fn[[In[str], Fn[[In[str]], None]], Opt[str]]:
    """
    the list of values in each syndict in 'normalizers' is like OR
    the list of values in mealy d is like AND
    """
    # TODO make kwarg 'normalizers' have the type Seq[Union[Fn[[str], Iter[str]], Dict[str, Sequence[str]]]] = []
    ns: List[Fn[[str], Iter[str]]] = []
    for n in normalizers:
        if isinstance(n, dict):
            trans: Dict[str, List[str]] = {}
            # n: Dict[str, Iter[str]] = n
            for k, words in n.items():
                if " " in k:
                    raise Exception(f"'{k}' not allowed bc the syns can't have spaces")
                for word in words:
                    trans[word] = trans.get(word, [])
                    trans[word].append(k)
            ns.append(lambda s: trans.get(s, []))
        else:
            pass
    try_syns = make_try_syns(d, ns)

    def run(inpt: In[str], save: Fn[[In[str]], None]) -> Opt[str]:
        l: List[str] = []
        items: Seq[str] = ()
        for s, rest in inpt.as_steps():
            end_items_s = try_syns(MxEnd, (*items, s))
            if end_items_s:
                inpt = rest
                _, s_end = end_items_s
                l.append(s_end)
            cont_items_s = try_syns(MxCont, (*items, s))
            if cont_items_s is None:
                break
            else:
                items, _ = cont_items_s
        if not l:
            return None
        save(inpt)
        return l[-1]

    return run


def to_mealy(
    m: Mapping[str, Iter[Union[str, Iter[str]]]]
) -> Dict[Tuple[Type[Mx], Seq[str]], str]:
    d: Dict[Tuple[Type[Mx], Seq[str]], str] = {}

    def to_list(x: Union[str, Iter[str]]) -> List[str]:
        if isinstance(x, str):
            return x.split()
        return list(x)

    for label, rows in m.items():
        if label not in rows and [label] not in rows:
            rows = list(rows)
            rows.append(label)
        rows = [to_list(row) for row in rows]
        for row in rows:
            row = list(row)
            items: Seq[str] = ()
            d[(MxEnd, tuple(row))] = label
            if len(row) > 1:
                for s in row[:-1]:
                    items = (*items, s)
                    d[(MxCont, items)] = ""
    return d


def to_normalizer(m: MDict) -> Dict[str, List[str]]:
    d: Dict[str, List[str]] = {}
    for k, v in m.items():
        vv: List[str] = []
        for item in v:
            assert isinstance(item, str)
            vv.append(item)
        d[k] = vv
    return d


m = to_mealy(
    {"South Carolina": [["South", "Carolina"]], "South Dakota": [["South", "Dakota"]]}
)


def syns_to_mealy(
    syns_dict: Dict[str, List[str]]
) -> Dict[Tuple[Type[Mx], Seq[str]], str]:
    return to_mealy({label: [syn.split() for syn in syns] for label, syns in syns_dict})


def pad_with_syns(
    word_syns: Dict[str, List[str]], mealy: Dict[Tuple[Type[Mx], Seq[str]], str]
) -> Dict[Tuple[Type[Mx], Seq[str]], str]:
    d: Dict[Tuple[Type[Mx], Seq[str]], str] = {}
    for m_words, label in mealy.items():
        d[m_words] = label
        m, _words = m_words
        words: List[str] = list(_words)
        for idx, word in enumerate(
            words
        ):  ### TODO Enumerate all possible synonym combinations
            for syn in word_syns.get(word, []):
                words[idx] = syn
                d[(m, tuple(words))] = label
                words[idx] = word
    return d


def reverse_dict(d: Dict[str, List[Union[str, List[str]]]]) -> None:
    keys = list(d.keys())

    def reverse(x: Union[str, List[str]]) -> List[str]:
        if isinstance(x, str):
            x = x.split()
            x.reverse()
            return x
        x = x.copy()
        x.reverse()
        return x

    for key in keys:
        d[key] = [reverse(row) for row in d[key]]
    return None


_s = [
    ["Alabama	Al	AL"],
    ["Alaska	Alaska	AK"],
    ["Arizona	Ariz	AZ"],
    ["Arkansas	Ark	AR"],
    ["California	Calif	CA"],
    ["Colorado	Colo	CO"],
    ["Connecticut	Conn	CT"],
    ["Delaware	Del	DE"],
    ["District_of_Columbia	DC	DC"],
    ["Florida	Fla	FL"],
    ["Georgia	Ga	GA"],
    ["Hawaii	Hawaii	HI"],
    ["Idaho	Idaho	ID"],
    ["Illinois	Ill	IL"],
    ["Indiana	Ind	IN"],
    ["Iowa	Iowa	IA"],
    ["Kansas	Kans	KS"],
    ["Kentucky	Ky	KY"],
    ["Louisiana	La	LA"],
    ["Maine	Maine	ME"],
    ["Maryland	Md	MD"],
    ["Massachusetts	Mass	MA"],
    ["Michigan	Mich	MI"],
    ["Minnesota	Minn	MN"],
    ["Mississippi	Miss	MS"],
    ["Missouri	Mo	MO"],
    ["Montana	Mont	MT"],
    ["Nebraska	Nebr	NE"],
    ["Nevada	Nev	NV"],
    ["New_Hampshire	NH	NH"],
    ["New_Jersey	NJ	NJ"],
    ["New_Mexico	NM	NM"],
    ["New_York	NY	NY"],
    ["North_Carolina	NC	NC"],
    ["North_Dakota	ND	ND"],
    ["Ohio	Ohio	OH"],
    ["Oklahoma	Okla	OK"],
    ["Oregon	Ore	OR"],
    ["Pennsylvania	Pa	PA"],
    ["Rhode_Island	RI	RI"],
    ["South_Carolina	SC	SC"],
    ["South_Dakota	SD	SD"],
    ["Tennessee	Tenn	TN"],
    ["Texas	Tex	TX"],
    ["Utah	Utah	UT"],
    ["Vermont	Vt	VT"],
    ["Virginia	Va	VA"],
    ["Washington	Wash	WA"],
    ["West_Virginia	WVa	WV"],
    ["Wisconsin	Wis	WI"],
    ["Wyoming	Wyo	WY"],
]
s: Dict[str, List[Seq[str]]] = {}
for line in _s:
    _l = [cell.replace("_", " ").upper() for cell in line[0].split("\t")]
    l = [cell.split() for cell in _l]
    l[0].reverse()
    abbr: str = l[-1][0]
    to_seq: Fn[[List[str]], Seq[str]] = lambda lst: tuple(lst)
    row: List[Seq[str]] = list(set(map(to_seq, l)))
    s[abbr] = row

["#", "APT", "BLDG", "STE", "UNIT", "RM", "DEPT", "TRLR", "LOT", "FL"]
unit_types: Dict[str, List[str]] = {
    "#": ["#"],
    "APT": ["APARTMENT"],
    "BLDG": ["BUILDING", "BLDNG"],
    "STE": ["SUITE", "SUIT"],
    "UNIT": ["UNIT"],
    "RM": ["ROOM"],
    "DEPT": ["DEPARTMENT"],
    "TRLR": ["TRAILER", "TR"],
    "LOT": ["LOT"],
    "FL": ["FLOOR"],
}
unitary_unit_types = {
    "BSMT": ["BASEMENT"],
    "FRNT": ["FRONT"],
    "LBBY": ["LOBBY"],
    "LOWR": ["LOWER"],
    "OFC": ["OFFICE"],
    "PH": ["PENTHOUSE"],
    "REAR": ["REAR"],
    "SIDE": ["SIDE"],
    "UPPR": ["UPPER"],
}

unit_types.update(unitary_unit_types)
# no_N = re.compile(
# r"#?\b(\d+\|[A-D]|[F-M]|[O-R]|[T-V]|[X-Z])(\d+|[A-D]|[F-M]|[O-R]|[T-V]|[X-Z])?\b"
# )
# no_N = re.compile(r"#?\b(\d+|)?\b")
# TODO BYPASS
# TODO KENTUCKY 440
hwys: MDict = {
    "COUNTY HIGHWAY": ["COUNTY HIGHWAY"],
    "COUNTY ROAD": ["COUNTY ROAD", "CR"],
    "CTH": ["CTH"],
    "STH": ["STH"],
    "EXPRESSWAY": ["EXPRESSWAY"],
    "FM": ["FARM TO MARKET"],
    "ROUTE": ["RTE", "RT"],
    "SR": ["STATE ROAD"],
    "TOWNSHIP ROAD": ["TOWNSHIP ROAD", "TSR"],
    "US": ["US"],
    "HIGHWAY": ["HIGHWAY"],
}

hwys_syns: MDict = {
    "COUNTY": ["CO", "CNTY"],
    "HIGHWAY": ["HWY", "HIWAY"],
    "STATE": ["ST"],
    "ROAD": ["RD"],
    "SR": ["STATE ROAD"],
}

reverse_dict(hwys)

nesw_syns: MDict = {
    "NORTH": ["NORTH", "NTH", "N"],  # THESE ARE LIKE 'OR'
    "EAST": ["EAST", "EST", "E"],
    "SOUTH": ["SOUTH", "STH", "S"],
    "WEST": ["WEST", "WST", "W"],
    "NE": ["NE", "NORTHEAST"],
    "NW": ["NW", "NORTHWEST"],
    "SE": ["SE", "SOUTHEAST"],
    "SW": ["SW", "SOUTHWEST"],
}
nesw_m: MDict = {
    "N": ["NORTH"],
    "E": ["EAST"],
    "S": ["SOUTH"],
    "W": ["WEST"],
    "NE": ["NORTH EAST"],  # THESE ARE LIKE 'AND'
    "NW": ["NORTH WEST"],
    "SE": ["SOUTH EAST"],
    "SW": ["SOUTH WEST"],
}
reverse_dict(nesw_m)


def to_input_lst(s: str) -> List[In[str]]:
    add = s.upper().split()
    add.reverse()
    k = In(add)
    return [k]


def make_mod(f: List[In[str]]) -> Fn[[In[str]], None]:
    def md(d: Any):
        f[0] = d

    return md


def test_state_m(p: Fn[[In[str], Fn[[In[str]], None]], T], f: List[In[str]]) -> Opt[T]:
    md = make_mod(f)
    ret = p(f[0], md)
    if ret:
        return ret
    return None


def get_with_label(
    label: str, p: Fn[[In[str], Fn[[In[str]], None]], Opt[str]]
) -> Fn[[In[str], Fn[[In[str]], None]], Opt[Tuple[str, str]]]:
    def _(inpt: In[str], save: Fn[[In[str]], None]) -> Opt[Tuple[str, str]]:
        x = p(inpt, save)
        if x is not None:
            return label, x
        return None

    return _


def __get_secondary_unit_range__() -> Fn[[In[str], Fn[[In[str]], None]], Opt[str]]:
    is_hwy_or_nesw = try_regex(dicts_to_pattern(hwys_syns, hwys, nesw_m, nesw_syns))

    def x(inpt: In[str], save: Fn[[In[str]], None]) -> Opt[str]:
        if is_hwy_or_nesw(inpt, save):
            save(inpt)
            return None
        if not inpt.empty():
            item = inpt.item()
            if len(item) < 5:
                return item
        return None

    return x


get_unit_type = from_mealy(to_mealy(unit_types))
get_unitary_unit_type = from_mealy(to_mealy(unitary_unit_types))
# get_secondary_range = try_regex(no_N)
get_hwy_name = get_with_label(
    "st_name", from_mealy(to_mealy(hwys), normalizers=[to_normalizer(hwys_syns)])
)
get_st_suffix = get_with_label(
    "st_suffix",
    from_mealy(
        to_mealy(st_suffices_dict),
        normalizers=[to_normalizer(st_suffix_syns)],
    ),
)

get_house_number = get_with_label("house_number", try_regex(_HOUSE_NUMBER_R))

get_dangling_unit = try_regex(unit_R)  # "APT" with no identifer
get_zip_code = get_with_label("zip_code", zip_code)

is_hwy = dicts_to_pattern(hwys, hwys_syns)


def get_unit(inpt: In[str], save: Fn[[In[str]], None]) -> Opt[Tuple[str, str]]:
    single = get_unitary_unit_type(inpt, save)
    if single:
        return ("unit", single)
    # i.e, "3, APT" (because it's parsed from back to from at this point)
    x, xs = inpt.item(), inpt.rest()
    if re.match(st_suffix_R, x):
        return None
    if xs.empty():
        return None
    unit = get_unit_type(xs, save)
    if unit:
        return "unit", f"{unit} {x}"
    if re.match(unit_R, x):
        # TODO raise Exception("DANGLING UNIT")
        save(xs)
        pass
    return None


def get_full_hwy(inpt: In[str], save: Fn[[In[str]], None]) -> Opt[Tuple[str, str]]:
    """
    cnty rd
    county road 410
    """
    if inpt.empty():
        return None
    z, zs = inpt.item(), inpt.rest()
    if not zs.empty():
        y = get_hwy_name(zs, save)
        if y:
            return "st_name", f"{y[1]} {z}"
    return get_hwy_name(inpt, save)


m = to_mealy(s)
syns: Dict[str, List[str]] = {"SOUTH": ["S", "STH"], "NORTH": ["N", "NTH"]}
get_state = get_with_label("us_state", from_mealy(m, normalizers=[syns]))

get_nesw = get_with_label(
    "st_NESW", from_mealy(to_mealy(nesw_m), normalizers=[to_normalizer(nesw_syns)])
)


def every_other(iter: Iter[T], item: T) -> Iter[T]:
    def always_item() -> Iter[T]:
        while True:
            yield item

    return join(zip(iter, always_item()))


def city_mealy(known_cities: Seq[str] = ()) -> Dict[Tuple[Type[Mx], Seq[str]], str]:
    d: Dict[str, List[Union[str, List[str]]]] = {}
    for city in [*known_cities, *default_cities]:
        d[city] = [city.upper().split()]
    for _, city in state_city_pairs:
        city = city.upper()
        d[city] = [city.split()]
    reverse_dict(d)
    return to_mealy(d)


get_city = get_with_label(
    "city",
    from_mealy(city_mealy(), normalizers=[syns]),
)
unit_id_atom = r"(\d+|\d+[A-Z]?|[A-Z]\d+|[A-D]|[F-M]|[O-R]|[T-V]|[X-Z])"
dash = r"\-"
lonely_unit_regex = re.compile(f"^#?{unit_id_atom}({dash}{unit_id_atom})?$")

lonely_unit_id = try_regex(lonely_unit_regex)

get_nesw_single = get_with_label("st_NESW", try_full_regex(st_NESW_R))


def space_join(stream: Iter[str]) -> str:
    return " ".join(filter(None, stream))


def drop_tabs(inpt: In[str], save: Fn[[In[str]], None]) -> None:
    i = inpt
    for cell, rest in inpt.as_steps():
        if cell == "\t":
            i = rest
        else:
            save(i)
            break


def get_city_til_tab(inpt: In[str], save: Fn[[In[str]], None]) -> Iter[str]:
    for cell, rest in inpt.as_steps():
        if cell == "\t":
            save(rest)
            break
        yield cell


starts_with_digit = re.compile(r"^\d")


def merge_rural_hwy(inpt: List[str]) -> List[str]:
    """Detects if an address has the form '123 W 2100 S, Tucson AZ'
    & merges 'W' and '2100' into a single token 'W-2100'
    """
    if re.match(starts_with_digit, inpt[2]):
        # TODO match 'north west 2100' instead of only 'nw 2100'
        if re.fullmatch(st_NESW_R, inpt[1]):
            return [inpt[0], f"{inpt[1]} {inpt[2]}", *inpt[3:]]
    return inpt


class FnsOfParser(Fns_Of):
    @staticmethod
    def get_city(inpt: In[str], save: Fn[[In[str]], None]) -> Opt[Tuple[str, str]]:
        return None


class Parser:
    """
    The parser for addresses.

    ``from address_hammer import Parser, RawAddress``
    ``p = Parser()``
    ``address: RawAddress = p("999 8th blvd California CA 54321")``

    It comes pre-trained, and can recognize nearly all U.S cities. However, if there does happen to be a city it fails on, it can be passed to the ``known_cities`` argument of ``Parser.__init__``
    """

    __fns_of__: FnsOfParser
    known_cities: List[str]

    def __init__(self, known_cities: Seq[str] = ()):
        get_city = get_with_label(
            "city",
            from_mealy(city_mealy(known_cities=known_cities), normalizers=[syns]),
        )

        class __FnsOfParser__(FnsOfParser):
            @staticmethod
            def get_city(
                inpt: In[str], save: Fn[[In[str]], None]
            ) -> Opt[Tuple[str, str]]:
                return get_city(inpt, save)

        self.__fns_of__ = __FnsOfParser__()
        self.known_cities = [x for x in known_cities]

    @property
    def get_city(self) -> Fn[[In[str], Fn[[In[str]], None]], Opt[Tuple[str, str]]]:
        return self.__fns_of__.get_city

    def __tag__(
        self,
        get_inpt: Fn[[], In[str]],
        save: Fn[[In[str]], None],
        city_done: bool = False,
    ) -> Iter[Opt[Tuple[str, str]]]:

        if not city_done:
            yield get_zip_code(get_inpt(), save)
            yield get_state(get_inpt(), save)
            yield self.get_city(get_inpt(), save)
        unit = get_unit(get_inpt(), save)
        if unit:
            yield unit[0], unit[1].replace("#", "")
        yield get_nesw(get_inpt(), save)
        hwy = get_full_hwy(get_inpt(), save)

        if len(get_inpt()) > 2:
            lonely_unit = lonely_unit_id(get_inpt(), save)
            if lonely_unit:
                lonely_unit = lonely_unit.replace("#", "")
                yield "unit", f"UNIT {lonely_unit}"
                yield get_nesw(get_inpt(), save)
        pre_suffixed = get_inpt()  # 123    Fields East    City    IL
        st_suffix = get_st_suffix(get_inpt(), save)

        ######################################
        ######################################
        save(In(list(reversed(list(get_inpt())))))
        house_number: List[str] = []
        st_name: List[str] = []
        hn = get_house_number(get_inpt(), save)

        if hn:
            house_number.append(hn[1])
        else:
            # raise ParseError(a, "house_number")
            pass
        hn = get_house_number(get_inpt(), save)

        if hn:
            if "/" in hn[1]:
                house_number.append(hn[1])
            else:
                st_name.append(hn[1])

        st_nesw = get_nesw_single(get_inpt(), save)

        if st_nesw:
            if get_inpt().empty():  # 123 N Ave NE
                st_name.append(st_nesw[1])
            else:
                yield st_nesw
                st_name.extend(get_inpt())
        else:
            st_name.extend(get_inpt())
        if hwy:
            st_name.append(hwy[1])
        if st_suffix and not st_name:
            st_name = [pre_suffixed.item()]

        else:
            yield st_suffix
        yield "st_name", space_join(st_name)
        yield "house_number", space_join(house_number)

    def tag(self, a: str) -> Iter[Tuple[str, str]]:
        """
        Returns an iter of (label, value) for all parsing steps in ``Parser.__call__``.
        This can be useful for debugging why an address failed.

        ``tags = [t for t in p.tag("777 Collins Southfield Maine")]``
        ``assert tags == [('orig', '777 Collins Southfield Maine'), ('us_state', 'ME'), ('city', 'SOUTHFIELD'), ('st_name', 'COLLINS'), ('house_number', '777')]``
        """
        
        add = re.sub(r"[.,]", " ", a).upper().split()
        add = merge_rural_hwy(add)
        add.reverse()
        k = In(add)
        f: List[In[str]] = [k]

        def save(d: Any, f: List[In[str]] = f):
            f[0] = d

        get_inpt = lambda: f[0]
        yield "orig", a
        for pair in self.__tag__(get_inpt, save):
            if pair:
                pair = (pair[0], pair[1].strip())
                if pair[1]:
                    yield pair

    @staticmethod
    def __collect__(d: Dict[str, str]) -> RawAddress:
        return RawAddress(
            house_number=d["house_number"],
            st_name=d["st_name"],
            st_suffix=d.get("st_suffix", None),
            st_NESW=d.get("st_NESW", None),
            unit=d.get("unit", None),
            city=d["city"],
            us_state=d["us_state"],
            zip_code=d.get("zip_code", None),
            orig=d["orig"],
            batch_checksum="",
        )

    def __tag_row__(self, a: Seq[str]) -> Iter[Tuple[str, str]]:
        """
        Identical to ``Parser.tag``, but used when parsing a list of strings that, together, is an entire address.
        This can increase accuracy by using the pre-existing delimiters in the input.
        For example, the ``known_cities`` arg to ``Parser.__init__`` is not needed to process unseen addresses.
        """
        yield "orig", "\t".join(a)
        row = [x for x in map(lambda s: s.strip(), a) if x]
        to_inpt_lst: Fn[[str], List[In[str]]] = lambda s: [In(s.upper().split())]
        z = to_inpt_lst(row.pop())
        get_z, save_z = lambda: z[0], make_mod(z)
        maybe_zip = get_zip_code(get_z(), save_z)
        if maybe_zip:  # TODO handle 9 digit zips in two different columns
            yield maybe_zip
            z = to_inpt_lst(row.pop())
        maybe_state = get_state(get_z(), save_z)
        if maybe_state:
            yield maybe_state
        else:
            pass  # TODO raise parse error @ us_state
        yield "city", normalize_whitespace(row.pop().upper())
        data = list(join(map(lambda s: s.upper().split(), row)))
        data = merge_rural_hwy(data)
        data.reverse()
        r = [In(data)]
        for pair in self.__tag__(lambda: r[0], make_mod(r), city_done=True):
            if pair:
                pair = (pair[0], pair[1].strip())
                if pair[1]:
                    yield pair

    def __call__(self, s: str) -> RawAddress:
        """Parses an address string and performs normalization in a single pass, returning a ``RawAddress``, possibly throwing a ``ParseError`` on failure.
        Directionals such as ``"South"`` and ``"Nth west"`` will all be normalized to the abbreviated form (except when part of a city name, as in ``"South Haven"``). This is the USPS standardized way to write states, such as ``"N Carolina"``
        """

        try:
            return self.__collect__(dict(self.tag(s)))
        except KeyError as ke:
            raise ParseError(s, ke.args[0])
        except EndOfInputError:
            raise ParseError(s, "End of input")

    def __parse_row__(self, a: Seq[str]) -> RawAddress:
        """
        Identical to ``Parser.__call__``, but used when parsing a list of strings that, together, is an entire address.
        This can increase accuracy by using the pre-existing delimiters in the input.
        For example, the ``known_cities`` arg to ``Parser.__init__`` is not needed to process unseen addresses.
        """
        try:
            return self.__collect__(dict(self.tag_row(a)))
        except KeyError as ke:
            raise ParseError("\t".join(a), ke.args[0])
        except EndOfInputError:
            raise ParseError("\t".join(a), "End of input")


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
            yield a
        except ParseError:
            errs.append(add)
    p = Parser(known_cities=p.known_cities + list(cities))
    fixed = 0
    for add in errs:
        try:
            a = p(add)
            fixed += 1
            yield a
        except ParseError as e:
            report_error(e, add)


__difficult_addresses__ = [
    "000  Plymouth Rd Trlr 113  Ford MI 48000",
    "0 Joy Rd Trlr 105  Red MI 48000",
    "0  Stoepel St #0  Detroit MI 48000",
    "0 W Boston Blvd # 7  Detroit MI 48000",
]
