from __future__ import annotations

import typing as t
from itertools import chain
join = chain.from_iterable
Fn = t.Callable
Opt = t.Optional

SOFT_COMPONENTS = ["st_suffix", "st_NESW", "unit", "zip_code"]
HARD_COMPONENTS = ["house_number", "st_name", "city", "us_state"]


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

    def __hash__(self) -> int:
        return hash((self.hard_components(), self.soft_components()))

    def __eq__(self, other: Address)-> bool:
        if self.__class__ != other.__class__: 
            #don't use isinstance because equality is not defined for Address, RawAddress
            return False
        hards_match = self.hard_components() == other.hard_components()

        if not hards_match:
            return False

        for s_soft, o_soft in zip(self.soft_components(), 
                                  other.soft_components()):
            if s_soft != None and o_soft != None:
                if s_soft != o_soft:
                    return False

        return True

    def hard_components(self)->t.Tuple[str, str, str, str]:
        return (self.house_number, 
                self.st_name, 
                self.city, 
                self.us_state)
    
    def soft_components(self)->t.Sequence[Opt[str]]:
        return (self.st_suffix, self.st_NESW, self.unit, self.zip_code)

    def reparse_test(self, parse: Fn[[str], Address]):
        s: t.Dict[str, str] = self._asdict()
        d: t.Dict[str, str] = parse(self.orig)._asdict()
        for sk, sv in s.items():
            dv = d[sk]
            if sk != "orig" and sv != dv:
                raise Exception("Failed at '{field}':\n\t\t\t{orig}\n\t\t\t'{sv}' != '{dv}'"\
                                .format(field = sk, 
                                        sv = sv, 
                                        dv = dv, 
                                        orig=self.orig))

    def replace(self, **kwargs: t.Dict[str,str])->Address:
        return self._replace(**kwargs)

    def soft_eq(self, other: Address)->bool:
        raise NotImplementedError

    def combine_soft(self, other: Address)->Address:
        if self != other:
            raise Exception("cannot combine_soft two different addresses.")
        # by our definition of equality,
        # there can only be at most one non-None field of each opt-valued pair
        return self.replace(
            **{"st_suffix":opt_sum(self.st_suffix, other.st_suffix), 
               "st_NESW":opt_sum(self.st_NESW, other.st_NESW), 
               "unit":opt_sum(self.unit, other.unit),
               "zip_code":opt_sum(self.zip_code, other.zip_code)})
               
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
            ll = l[0]
            if len(ll)==1:
                a,b = ll, ""
            else:
                a,b = "", ll
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
    class Get:
        house_number: Fn[[Address], str] = lambda a: a.house_number
        st_name: Fn[[Address], str] = lambda a: a.st_name
        st_suffix: Fn[[Address], Opt[str]] = lambda a: a.st_suffix
        st_NESW: Fn[[Address], Opt[str]] = lambda a: a.st_NESW
        unit: Fn[[Address], Opt[str]] = lambda a: a.unit
        city: Fn[[Address], str] = lambda a: a.city
        us_state: Fn[[Address], str] = lambda a: a.us_state
        zip_code: Fn[[Address], Opt[str]] = lambda a: a.zip_code
        orig: Fn[[Address], str] = lambda a: a.orig
        pretty: Fn[[Address], str] = lambda a: a.pretty()


class RawAddress(Address):
    """
    A RawAddress is what is produced by a Parser.
    Because it might have incomplete or missing fields, it is not hashable
    """
    def __hash__(self) -> int:
        raise NotImplementedError("RawAddress is not hashable")







class HashableFactory(t.NamedTuple):
    fill_in_info: Fn[[Address], t.List[Address]]
    fix_by_hand: t.List[t.List[Address]]
    def __call__(self, a:Address)->t.List[Address]:
        return self.fill_in_info(a)

    def hashable_addresses(self, addresses: t.Iterable[Address])->t.Iterable[Address]:
        return join(map(self, addresses))

    @staticmethod
    def from_all_addresses(addresses: t.Iterable[Address])->HashableFactory:
        """
        Each address is mapped to a list of each with more complete (but incompatible) soft elements
        """
        addresses = list(addresses)
        def new_dict()->t.Dict[str, t.Set[Opt[str]]]:
            return {soft:set([]) for soft in SOFT_COMPONENTS}

        d : t.Dict[t.Sequence[str], t.Dict[str, t.Set[Opt[str]]]] = {}
        for a in addresses:
            hards = a.hard_components()
            softs = d.get(hards,new_dict())
            a_dict = a._asdict()
            for k,v in a_dict.items():
                if k in softs:
                    softs[k].add(v)
            d[hards] = softs

        fix_by_hand = {}
        def is_ambig(softs:t.Dict[str, t.Set[Opt[str]]])->bool:
            l = [list(filter(None, v)) for k, v in softs.items() if k != "unit"]
            m = max(map(len, l))

            return m > 1
        for a in addresses:
            hards = a.hard_components()
            softs = d[hards]
            if is_ambig(softs): #cannot have mismatching st_suffix,st_NESW or zip_code
                similar_addresses = fix_by_hand.get(hards, [])
                similar_addresses.append(a)
                fix_by_hand[hards] = similar_addresses
        
        def fix(a:Address)->t.List[Address]:
            ret = []
            hards = a.hard_components()
            softs = d.get(hards, None)
            if not softs:
                return []
            if is_ambig(softs): #cannot have mismatching st_suffix,st_NESW or zip_code
                return []
            else:
                _softs = {}
                for label, soft in softs.items():
                    v = list(softs[label])
                    if not v:
                        _softs[label] = None
                    else:
                        _softs[label] = v[0]
                units = list(filter(None, softs["unit"]))
                with_unit: Fn[[Opt[str]], Address] = lambda unit: Address(
                            house_number=a.house_number,
                            st_name=a.st_name,
                            st_suffix=opt_sum(a.st_suffix, _softs["st_suffix"]),
                            st_NESW=opt_sum(a.st_NESW, _softs["st_NESW"]),
                            unit=opt_sum(a.unit, unit),
                            city=a.city,
                            us_state=a.us_state,
                            zip_code=opt_sum(a.zip_code, _softs["zip_code"]),
                            orig = a.orig)
                if a.unit != None:
                    return [with_unit(a.unit)]
                if not units:
                    units = [None]
                for unit in units:
                    ret.append(with_unit(unit))
            return ret
        return HashableFactory(fill_in_info=fix, 
                               fix_by_hand=list(fix_by_hand.values()))


def merge_duplicates(addresses: t.Iterable[Address])->t.Set[Address]:
    addresses = list(addresses)
    f = HashableFactory.from_all_addresses(addresses)
    return set(join(map(f, addresses)))


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
            st_NESW  = None,
            unit  = None,
            city  = "CITY",
            us_state  = "NY",
            zip_code  = "12123",
            orig = "0 road Rd city NY 12123"),

    Address(    
            house_number  = "1914",
            st_name  = "HASKELL",
            st_suffix  = "LCK",
            st_NESW  = "S",
            unit  = None,
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
        st_suffix  = None,
        st_NESW  = "N",
        unit  = None,
        city  = "ZAMALAKOO",
        us_state  = "MI",
        zip_code  = "00100",
        orig = "0 N Division Zamalakoo MI 00100")]


def test():
    from parsing import Parser
    p = Parser(known_cities=["City"])
    ambigs_1 = [
        "001 Street City MI",
        "001 E Street City MI",
        #"001 W Street City MI",
        "001 Street St City MI",
        "001 Street Apt 0 City MI",
        "001 Street Apt 1 City MI",
    ]
    ambigs_2 = ["0 Main St Smallville AZ",
                "0 Main Rd Smallville AZ"]
    assert 2 == len(merge_duplicates(map(p,ambigs_1)))
    assert 2 == len(HashableFactory.from_all_addresses(map(p, ambigs_2)).fix_by_hand[0])
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
        

