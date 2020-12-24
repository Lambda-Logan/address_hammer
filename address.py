from __future__ import annotations

import typing as t

Fn = t.Callable
Opt = t.Optional

SOFT_COMPONENTS = ["st_suffix", "st_NESW", "unit"]
HARD_COMPONENTS = ["house_number", "st_name", "city", "us_state", "zip_code"]


class InvalidAddressError(Exception):
    orig: str
    def __init__(self, orig:str):
        self.orig = orig
T = t.TypeVar("T")

def opt_sum(a: Opt[T], b: Opt[T])->Opt[T]:
    "The monoidal sum of two optional values"
    if a != None:
        return a
    return b

class Address(t.NamedTuple):
    house_number: str
    st_name: str
    st_suffix: Opt[str]
    st_NESW: Opt[str]
    unit: Opt[str]
    city: str
    us_state: str
    zip_code: Opt[str]
    orig: str

    def __eq__(self, other: Address)-> bool:
        if self.__class__ != other.__class__:
            return False
        hards_match = self.__hard_components() == other.__hard_components()

        if not hards_match:
            return False

        for s_soft, o_soft in zip(self.__soft_components(), 
                                  other.__soft_components()):
            if s_soft != None and o_soft != None:
                if s_soft != o_soft:
                    return False

        return True

    def __hash__(self) -> int:
        return hash(self.__hard_components())

    def __hard_components(self)->t.Tuple[str, str, str, str]:
        return (self.house_number, 
                self.st_name, 
                self.city, 
                self.us_state)
    
    def __soft_components(self)->t.Sequence[Opt[str]]:
        return (self.st_suffix, self.st_NESW, self.unit, self.zip_code)

    def reparse_test(self, parse: Fn[[str], Address]):
        s: t.Dict[str, str] = self._asdict()
        d: t.Dict[str, str] = parse(self.orig)._asdict()
        for sk, sv in s.items():
            dv = d[sk]
            if sv != "" and sk != "orig" and sv != dv:
                raise Exception("Failed at '{field}':\n\t\t\t{orig}\n\t\t\t{sv} != {dv}"\
                                .format(field = sk, 
                                        sv = sv, 
                                        dv = dv, 
                                        orig=self.orig))

    def replace(self, **kwargs: t.Dict[str,str])->Address:
        return self._replace(**kwargs)

    def soft_eq(self, other: Address)->bool:
        raise NotImplementedError

    def combine_soft(self, other: Address)->Address:
        if self.__hard_components() != other.__hard_components():
            raise Exception("cannot combine_soft two different addresses.")
        s_st_suffix, s_st_NESW, s_unit = self.__soft_components()
        o_st_suffix, o_st_NESW, o_unit = other.__soft_components()

        return self.replace(
            **{"st_suffix":opt_sum(s_st_suffix, o_st_suffix), 
               "st_NESW":opt_sum(s_st_NESW, o_st_NESW), 
               "unit":opt_sum(s_unit, o_unit)})
               
    def jsonize(self)->t.Dict[str,str]:
        return self._asdict()

    def pretty(self)->str:
        from __regex__ import normalize_whitespace
        as_dict = self._asdict()
        softs = {"st_NESW":"",
                 "st_suffix":"",
                 "unit":"",
                 "zip_code":""}

        for k in softs.keys():
            if as_dict[k] != None:
                softs[k] = as_dict[k]

        l = sorted(softs["st_NESW"].split(), key = len)
        if len(l) > 2:
            raise InvalidAddressError("NESW of " +self.orig)
        elif len(l) == 2:
            a,b = l
            if len(a)>1 and len(b)>1:
                raise InvalidAddressError("NESW of " +self.orig)
        elif len(l) == 1:
            a,b = "", l[0]
        else: #len(l) == 0
            a, b = "", ""
        u = softs["unit"].split()
        if len(u)==0:
            unit = ""
        elif len(u)==2:
            unit = u[0].capitalize() + " " + u[1].upper()
        else:
            raise InvalidAddressError("Unit of " + self.orig)

        return normalize_whitespace(" ".join([
                         self.house_number,
                         a,
                         " ".join([w.capitalize() for w in self.st_name.split()]),
                         softs["st_suffix"].capitalize(),
                         b,
                         unit,
                         " ".join([w.capitalize() for w in self.city.split()]),
                         self.us_state.upper(),
                         softs["zip_code"]
                         ]))


example_addresses = [    Address(    
        house_number  = "3710",
        st_name  = "MICHIGANE",
        st_suffix  = "AVE",
        st_NESW  = "SW",
        unit  = "APT 447",
        city  = "GRAND RAPIDS",
        us_state  = "MI",
        zip_code  = "49588",
        orig = "3710 Michigane AVE SW apt #447 Grand Rapids MI 49588"),


    Address(    
                house_number  = "343",
                st_name  = "FULLY FULTON",
                st_suffix  = "ST",
                st_NESW  = "E",
                unit  = "APT 1",
                city  = "BLABLAVILLE",
                us_state  = "AZ",
                zip_code  = "00000",
                orig = "343 Fully Fulton st E APT 1 Blablaville AZ 00000"),

    Address(    
            house_number  = "0",
            st_name  = "ROAD",
            st_suffix  = "RD",
            st_NESW  = "",
            unit  = "",
            city  = "CITY",
            us_state  = "NY",
            zip_code  = "12123",
            orig = "0 road Rd city NY 12123"),

    Address(    
            house_number  = "1914",
            st_name  = "HASKELL",
            st_suffix  = "LCK",
            st_NESW  = "S",
            unit  = "",
            city  = "RUSTY TOWN",
            us_state  = "NY",
            zip_code  = "12123",
            orig = "1914 S Haskell Lck  Rusty Town NY 12123"),


    
    Address(    
            house_number  = "5431",
            st_name  = "MONROE",
            st_suffix  = "LN",
            st_NESW  = "N",
            unit  = "APT 5",
            city  = "BRONX",
            us_state  = "OH",
            zip_code  = "54321",
            orig = "5431 N Monroe Ln APT 5 Bronx OH 54321"),
    
    Address(    
                house_number  = "5242",
                st_name  = "PLAINFIELD INSURANCE",
                st_suffix  = "BLVD",
                st_NESW  = "NW",
                unit  = "STE B",
                city  = "PALM SPRINGS",
                us_state  = "CA",
                zip_code  = "01234",
                orig = "5242 Plainfield Insurance Blvd NW Ste B Palm Springs CA 01234"),

    Address(    
        house_number  = "0",
        st_name  = "DIVISION",
        st_suffix  = "",
        st_NESW  = "N",
        unit  = "",
        city  = "ZAMALAKOO",
        us_state  = "MI",
        zip_code  = "00100",
        orig = "0 N Division Zamalakoo MI 00100")]

def test():
    for a in example_addresses:

        assert a == a
        soft_sames: t.List[t.Tuple[Opt[str],Opt[str]]] = [(None, "X"),  ("X", None)]
        sames: t.List[t.Tuple[Opt[str],Opt[str]]]      = [(None, None), ("X","X")]

        for x, y in soft_sames + sames:
            for soft in SOFT_COMPONENTS:
                #print(x,"and", y)
                assert(a.replace(**{soft:x}) == a.replace(**{soft:y})) 
                assert(a.replace(**{soft:"X"}) != a.replace(**{soft:"Y"}))

        for hard in HARD_COMPONENTS:
            for x, y in soft_sames:
                assert(a.replace(**{hard:x}) != a.replace(**{hard:y}))
            for x, y in sames:
                assert(a.replace(**{hard:x}) == a.replace(**{hard:y}))

            assert(a.replace(**{hard:"X"}) != a.replace(**{hard:"Y"}))
        

