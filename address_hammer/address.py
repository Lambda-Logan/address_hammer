from __future__ import annotations

from .__types__ import *

SOFT_COMPONENTS = ["st_suffix", "st_NESW", "unit", "zip_code"]
HARD_COMPONENTS = ["house_number", "st_name", "city", "us_state"]

COMPARE_BATCH_HASHES = True

class InvalidAddressError(Exception):
    orig: str
    def __init__(self, orig:str):
        self.orig = orig

def opt_sum(a: Opt[T], b: Opt[T])->Opt[T]:
    "The monoidal sum of two optional values"
    if a != None:
        return a
    return b
K = TypeVar("K")
V = TypeVar("V")

def get(d: Dict[K, V], k: K, v: V)-> V:
    ".get method of dicts sometimes doesn't typecheck correctly"
    try:
        return d[k]
    except KeyError:
        return v

def __compare_batch_hashes__(s: Address, other: Address):
    from warnings import warn
    if s.batch_hash == "" or other.batch_hash == "":
        msg = f"Tried operation on two addresses without using the same 'Hammer' instance: '{s.batch_hash}' and '{other.batch_hash}'"
        #warn(msg)
    elif s.batch_hash != other.batch_hash:
        msg = f"Tried operation on two addresses from different batches: '{s.batch_hash}' and '{other.batch_hash}'"
        warn(msg)
class Address(NamedTuple):
    house_number: str
    st_name: str
    st_suffix: Opt[str]
    st_NESW: Opt[str]
    unit: Opt[str]
    city: str
    us_state: str
    zip_code: Opt[str]
    orig: str
    batch_hash: str = ""

    def __hash__(self) -> int:
        return hash((self.hard_components(), self.soft_components()))

    def __eq__(self, other: Address)-> bool:
        Address.__compare_batch_hashes(self, other)
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

    def __ne__(self, other: Address)-> bool:
        return not (self == other)

    def __str_softs__(self)->List[str]:
        return list(filter(None, self.soft_components()))

    def __gt__(self, other: Address)->bool:
        a:bool = self.hard_components() > other.hard_components()
        b:bool = self.__str_softs__() > other.__str_softs__()
        return a and b 

    def __lt__(self, other: Address)->bool:
        a:bool = self.hard_components() < other.hard_components()
        b:bool = self.__str_softs__() < other.__str_softs__()
        return a and b 

    @staticmethod
    def __compare_batch_hashes(s: Address, other: Address)->None:
        __compare_batch_hashes__(s,other)
        return None

    @staticmethod
    def __should_compare_batch_hashes(should:bool)->None:
        if should:
            Address.__compare_batch_hashes = __compare_batch_hashes
        else:
            Address.__compare_batch_hashes = lambda _,__: None

    def hard_components(self)->Tuple[str, str, str, str]:
        return (self.house_number, 
                self.st_name, 
                self.city, 
                self.us_state)
    
    def soft_components(self)->Seq[Opt[str]]:
        return (self.st_suffix, self.st_NESW, self.unit, self.zip_code)

    def reparse_test(self, parse: Fn[[str], Address]):
        s: Dict[str, str] = self._asdict()
        d: Dict[str, str] = parse(self.orig)._asdict()
        for sk, sv in s.items():
            dv = d[sk]
            if sk != "orig" and sv != dv:
                raise Exception("Failed at '{field}':\n\t\t\t{orig}\n\t\t\t'{sv}' != '{dv}'"\
                                .format(field = sk, 
                                        sv = sv, 
                                        dv = dv, 
                                        orig=self.orig))

    def replace(self, **kwargs: Dict[str,str])->Address:
        return self._replace(**kwargs)

    def soft_eq(self, other: Address)->bool:
        raise NotImplementedError

    def combine_soft(self, other: Address)->Address:
        """
        Combines the soft components of each address, prefering the left address.
        """
        if self != other:
            raise Exception("cannot combine_soft two different addresses.")
        # by our definition of equality,
        # there can only be at most one non-None field of each opt-valued pair
        return self.replace(
            **{"st_suffix":opt_sum(self.st_suffix, other.st_suffix), 
               "st_NESW":opt_sum(self.st_NESW, other.st_NESW), 
               "unit":opt_sum(self.unit, other.unit),
               "zip_code":opt_sum(self.zip_code, other.zip_code)})
    def combine_soft_dict(self, other: Dict[str, Opt[str]])->Address:
        f: Fn[[str], Opt[str]] = lambda label: get(other, label, None)
        return self.replace(
            **{"st_suffix":opt_sum(self.st_suffix, f("st_suffix")), 
               "st_NESW":opt_sum(self.st_NESW, f("st_NESW")), 
               "unit":opt_sum(self.unit, f("unit")),
               "zip_code":opt_sum(self.zip_code, f("zip_code"))})
    



    def pretty(self)->str:
        from .__regex__ import normalize_whitespace
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







class HashableFactory(NamedTuple):
    fill_in_info: Fn[[Address], List[Address]]
    fix_by_hand: List[List[Address]]
    def __call__(self, a:Address)->List[Address]:
        s = self.fill_in_info(a)
        return s

    def hashable_addresses(self, addresses: Iter[Address])->Iter[Address]:
        return join(map(self, addresses))

    @staticmethod
    def from_all_addresses(addresses: Iter[Address])->HashableFactory:
        """
        Each address is mapped to a list of each with more complete (but incompatible) soft elements
        """
        addresses = list(addresses)

        _SOFT_COMPONENTS = [label for label in SOFT_COMPONENTS if label != "unit"]

        def new_dict()->Dict[str, Set[str]]:
            return {soft:set([]) for soft in _SOFT_COMPONENTS}

        d : Dict[Seq[str], Dict[str, Set[str]]] = {}

        unit_store: Dict[Seq[str], Dict[str, List[Address]]] = {}
        #             dict[hards, dict[unit, addresses]]
        for a in addresses:
            hards = a.hard_components()
            softs = d.get(hards,new_dict())
            a_dict = a._asdict()
            #softs["st_NESW"] = set(["E", "W"])
            #print("SOFTS", softs)
            for k,v in a_dict.items():
                #print(k in softs, k, a.pretty())
                if k in softs and v:# softs[k]:

                    softs[k].add(v)
            d[hards] = softs

            if a.unit:
                u_adds: Dict[str, List[Address]] = unit_store.get(hards, {})
                adds = u_adds.get(a.unit, [])
                adds.append(a)
                u_adds[a.unit] = adds
                unit_store[hards] = u_adds

        #should go in Address class?
        idx_of: Dict[str, int] = {field:int for int, field in enumerate(Address._fields)}

        def fill_in(a: Address)->Opt[List[Address]]:
            hards = a.hard_components()
            d_softs: Dict[str, Set[str]] = d[hards]

            a_dict: Dict[str, Opt[str]] = {label: None for label in _SOFT_COMPONENTS}

            for label in _SOFT_COMPONENTS:
                vals = d_softs.get(label, set([]))
                val = a[idx_of[label]]
                if val: # it is specified in 'a'
                    vals.add(val)
                    a_dict[label] = val
                elif len(vals) == 1: # it's not specified in 'a', but there's only 1 option it could be
                    a_dict[label] = list(vals)[0]
                elif len(vals) > 1: #it's ambigous and not specified in 'a'
                    return None


            # this is where filling units shoud be toggled
            ret: List[Address] = []
            hashable: Fn[[Address], Address] = lambda a: Address(*a)
            if a.unit:
                return [hashable(a.combine_soft_dict(a_dict))]
            else:
                units: Dict[str, List[Address]]  = get(unit_store, hards, set([]))
                if not units:
                    return [hashable(a.combine_soft_dict(a_dict))]
                for adds in units.values():
                    ret.extend([hashable(a.combine_soft(b)) for b in adds if a==b])
                return ret



        #remove ambigous apt addresses
        for hards, u_adds in unit_store.items():
            for unit, adds in u_adds.items():
                unit_store[hards][unit] = list(join(filter(None, map(fill_in, adds))))




        def is_ambig(softs:Dict[str, Set[Opt[str]]])->bool:
            """
            Is there more that one value for any given soft component? (except unit)
            ...
            The (less readable) definition was the following:
            --l = [list(filter(None, v)) for k, v in softs.items() if k != "unit"]
            --m = max(map(len, l))
            --return m > 1
            """
            for label, vals in softs.items():
                n_vals:int = len(list(filter(None, vals)))
                if label != "unit" and n_vals > 1:
                    return True
            return False

        fix_by_hand: Dict[Tuple[str, str, str, str], List[Address]] = {}

        for a in addresses:
            hards = a.hard_components()
            softs = d[hards]
            if is_ambig(softs): #cannot have mismatching st_suffix,st_NESW or zip_code
                similar_addresses = fix_by_hand.get(hards, [])
                similar_addresses.append(a)
                fix_by_hand[hards] = similar_addresses

        def fix(a:Address)->List[Address]:
            adds = fill_in(a)
            if adds == None:
                return []
            return adds
            
        return HashableFactory(fill_in_info=fix, 
                               fix_by_hand=list(fix_by_hand.values()))


def merge_duplicates(addresses: Iter[Address])->Set[Address]:
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

class UniqTest(NamedTuple):
    """
    this is a helper class to facilitate testing removal of duplicate addresses
    xs should be mapped to ys, otherwise it fails
    """
    from .parsing import Parser
    p: Parser
    xs: Seq[Address]
    ys: Seq[Address]

    @staticmethod
    def new(p:Parser)->UniqTest:
        return UniqTest(p=p,xs=(), ys=())

    def run(self):
        #we can't use set equality because RawAddress doesn't support hashing
        ys = merge_duplicates(self.xs)
        for y in ys:
            if y not in ys:
                raise Exception(f"{y.pretty()} not in self.ys")
        assert len(ys) == len(self.ys)

    
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
                    raise Exception(f"{a.pretty()} not in output: {list(map(Address.Get.pretty, adds))}")


    def with_x(self, x:Address)->UniqTest:
        return self._replace(xs=(x,*self.xs))

    def with_y(self, y:Address)->UniqTest:
        return self._replace(ys=(y,*self.ys))

    def without_x(self, x:Address)->UniqTest:
        return self._replace(xs=(a for a in self.xs if a != x))
    
    def without_y(self, y:Address)->UniqTest:
        return self._replace(ys=(a for a in self.ys if a != y))

def json_test():
    for a in example_addresses:
        assert Address.f

def test():
    from .parsing import Parser
    p = Parser(known_cities=["City"])
    ambigs_1 = [
        "001 Street City MI",
        "001 Street St City MI",
        "001 E Street City MI",
        "001 Street Apt 0 City MI",
        "001 Street Apt 1 City MI",
    ]
    ambigs_2 = ["0 Main St Smallville AZ",
                "0 Main Rd Smallville AZ"]

    UniqTest(
        xs=tuple(map(p,ambigs_1)), 
        ys = [p("001 E Street Apt 1 City MI"), 
              p("001 E Street Apt 0 City MI")],
        p=p).run()

    assert 2 == len(HashableFactory\
                    .from_all_addresses(map(p, ambigs_2))\
                    .fix_by_hand[0])
    
 
    UniqTest(
        p=p, 
        xs = tuple(map(p, ambigs_1)), 
        ys=())\
        .with_x(p("001 W Street City MI"))\
        .run()
    
    a = UniqTest(
        p=p,
        xs=tuple(map(p, ambigs_1)),
        ys=()
    )

    sorted(example_addresses)
    sorted(example_addresses, reverse=True)
    #TODO pass the following test
    #a.run_with({"001 e street  st city mi":["001 E Street St Apt 1 City MI", "001 E Street St Apt 0 City MI"]})

    for a in example_addresses:

        assert a == a
        soft_sames: List[Tuple[Opt[str],Opt[str]]] = [(None, "X"),  ("X", None)]
        sames: List[Tuple[Opt[str],Opt[str]]]      = [(None, None), ("X","X")]

        for x, y in soft_sames + sames:
            for soft in SOFT_COMPONENTS:
                assert(a.replace(**{soft:x}) == a.replace(**{soft:y})) 
                assert(a.replace(**{soft:"X"}) != a.replace(**{soft:"Y"}))

        for hard in HARD_COMPONENTS:
            for x, y in soft_sames:
                assert(a.replace(**{hard:x}) != a.replace(**{hard:y}))
            for x, y in sames:
                assert(a.replace(**{hard:x}) == a.replace(**{hard:y}))

            assert(a.replace(**{hard:"X"}) != a.replace(**{hard:"Y"}))