from __future__ import annotations

from .__types__ import (
    join,
    List,
    Set,
    Iter,
    TypeVar,
    T,
    Opt,
    Dict,
    Fn,
    Seq,
    Tuple,
    NamedTuple,
    Any,
    id_,
)

SOFT_COMPONENTS = ["st_suffix", "st_NESW", "unit", "zip_code"]
HARD_COMPONENTS = ["house_number", "st_name", "city", "us_state"]

COMPARE_BATCH_HASHES = True


class InvalidAddressError(Exception):
    orig: str

    def __init__(self, orig: str):
        self.orig = orig


def opt_sum(a: Opt[T], b: Opt[T]) -> Opt[T]:
    "The monoidal sum of two optional values"
    if a != None:
        return a
    return b


K = TypeVar("K")
V = TypeVar("V")


def get(d: Dict[K, V], k: K, v: V) -> V:
    ".get method of dicts sometimes doesn't typecheck correctly"
    try:
        return d[k]
    except KeyError:
        return v


CHECKSUM_IGNORE = ""


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
    batch_checksum: str = ""

    def __hash__(self) -> int:
        return hash((self.hard_components(), self.soft_components()))

    def __eq__(self, other: Address) -> bool:
        if self.__class__ != other.__class__:
            # don't use isinstance because equality is not defined for Address, RawAddress
            return False
        hards_match = self.hard_components() == other.hard_components()

        if not hards_match:
            return False

        for s_soft, o_soft in zip(self.soft_components(), other.soft_components()):

            if s_soft != None and o_soft != None:
                if s_soft != o_soft:
                    return False
        return True

    def __ne__(self, other: Address) -> bool:
        return not (self == other)

    def __str_softs__(self) -> List[str]:
        def x(s: Opt[str]) -> str:
            if not s:
                return ""
            return s

        return list(map(x, self.soft_components()))

    def __gt__(self, other: Address) -> bool:
        # TODO use soft components in __lt__ and __gt__
        a = self.hard_components()  # , self.__str_softs__()
        b = other.hard_components()  # , other.__str_softs__()
        return a > b

    def __lt__(self, other: Address) -> bool:
        a = self.hard_components()  # , self.soft_components()
        b = other.hard_components()  # , other.soft_components()
        return a < b

    def hard_components(self) -> Tuple[str, str, str, str]:
        return (self.house_number, self.st_name, self.city, self.us_state)

    def soft_components(self) -> Seq[Opt[str]]:
        return (self.st_suffix, self.st_NESW, self.unit, self.zip_code)

    def to_dict(self) -> Dict[str, str]:
        d = self._asdict()
        if isinstance(self, RawAddress):
            d["is_raw"] = True
        else:
            d["is_raw"] = False
        return d

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> Address:
        is_raw: Any = d["is_raw"]
        del d["is_raw"]
        if is_raw == True:
            r = RawAddress(**d)
        elif is_raw == False:
            r = Address(**d)
        else:
            raise Exception("invalid dict format for Address")
        d["is_raw"] = is_raw
        return r

    def reparse_test(self, parse: Fn[[str], Address]):
        s: Dict[str, str] = self._asdict()
        d: Dict[str, str] = parse(self.orig)._asdict()
        for sk, sv in s.items():
            dv = d[sk]
            if sk != "orig" and sv != dv:
                raise Exception(
                    "Failed at '{field}':\n\t\t\t{orig}\n\t\t\t'{sv}' != '{dv}'".format(
                        field=sk, sv=sv, dv=dv, orig=self.orig
                    )
                )

    def replace(self, **kwargs: Dict[str, str]) -> Address:
        return self._replace(**kwargs)

    def soft_eq(self, other: Address) -> bool:
        raise NotImplementedError

    def combine_soft(self, other: Address) -> Address:
        """
        Combines the soft components of each address, prefering the left address.
        """
        if self != other:
            raise Exception("cannot combine_soft two different addresses.")
        # by our definition of equality,
        # there can only be at most one non-None field of each opt-valued pair
        return self.replace(
            **{
                "st_suffix": opt_sum(self.st_suffix, other.st_suffix),
                "st_NESW": opt_sum(self.st_NESW, other.st_NESW),
                "unit": opt_sum(self.unit, other.unit),
                "zip_code": opt_sum(self.zip_code, other.zip_code),
            }
        )

    def combine_soft_dict(self, other: Dict[str, Opt[str]]) -> Address:
        f: Fn[[str], Opt[str]] = lambda label: get(other, label, None)
        return self.replace(
            **{
                "st_suffix": opt_sum(self.st_suffix, f("st_suffix")),
                "st_NESW": opt_sum(self.st_NESW, f("st_NESW")),
                "unit": opt_sum(self.unit, f("unit")),
                "zip_code": opt_sum(self.zip_code, f("zip_code")),
            }
        )

    def __as_address__(self) -> Address:
        if isinstance(self, RawAddress):
            return Address(
                house_number=self.house_number,
                st_name=self.st_name,
                st_suffix=self.st_suffix,
                st_NESW=self.st_NESW,
                unit=self.unit,
                city=self.city,
                us_state=self.us_state,
                zip_code=self.zip_code,
                orig=self.orig,
                batch_checksum=self.batch_checksum,
            )
        return self

    def pretty(self) -> str:
        from .__regex__ import normalize_whitespace

        as_dict = self._asdict()
        softs = {"st_NESW": "", "st_suffix": "", "unit": "", "zip_code": ""}

        for k in softs.keys():
            if as_dict[k] != None:
                softs[k] = as_dict[k]

        l = sorted(softs["st_NESW"].split(), key=len)
        if len(l) > 2:
            raise InvalidAddressError("NESW of " + self.orig)
        elif len(l) == 2:
            a, b = l
            if len(a) > 1 and len(b) > 1:
                raise InvalidAddressError("NESW of " + self.orig)
        elif len(l) == 1:
            ll = l[0]
            if len(ll) == 1:
                a, b = ll, ""
            else:
                a, b = "", ll
        else:  # len(l) == 0
            a, b = "", ""
        u = softs["unit"].split()
        if len(u) == 0:
            unit = ""
        elif len(u) == 2:
            unit = u[0].capitalize() + " " + u[1].upper()
        else:
            raise InvalidAddressError("Unit of " + self.orig)

        return normalize_whitespace(
            " ".join(
                [
                    self.house_number,
                    a,
                    " ".join([w.capitalize() for w in self.st_name.split()]),
                    softs["st_suffix"].capitalize(),
                    b,
                    unit,
                    " ".join([w.capitalize() for w in self.city.split()]),
                    self.us_state.upper(),
                    softs["zip_code"],
                ]
            )
        )

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
        dict: Fn[[Address], Dict[str, Any]] = lambda a: a.to_dict()
        batch_checksum: Fn[[Address], str] = lambda a: a.batch_checksum

    class Set(NamedTuple):
        house_number: Fn[[str], str] = id_
        st_name: Fn[[str], str] = id_
        st_suffix: Fn[[Opt[str]], Opt[str]] = id_
        st_NESW: Fn[[Opt[str]], Opt[str]] = id_
        unit: Fn[[Opt[str]], Opt[str]] = id_
        city: Fn[[str], str] = id_
        us_state: Fn[[str], str] = id_
        zip_code: Fn[[Opt[str]], Opt[str]] = id_
        orig: Fn[[str], str] = id_
        batch_checksum: Fn[[str], str] = id_

        def __call__(self, a: Address) -> Address:
            return a._replace(
                house_number=self.house_number(a.house_number),
                st_name=self.st_name(a.st_name),
                st_suffix=self.st_suffix(a.st_suffix),
                st_NESW=self.st_NESW(a.st_NESW),
                unit=self.unit(a.unit),
                city=self.city(a.city),
                us_state=self.us_state(a.us_state),
                zip_code=self.zip_code(a.zip_code),
                orig=self.orig(a.orig),
                batch_checksum=self.batch_checksum(a.batch_checksum),
            )

        @staticmethod
        def ignore_checksum(a: Address) -> Address:
            return a._replace(batch_checksum=CHECKSUM_IGNORE)


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

    def __call__(self, a: Address) -> List[Address]:
        s = self.fill_in_info(a)
        return s

    def hashable_addresses(self, addresses: Iter[Address]) -> Iter[Address]:
        return join(map(self, addresses))

    @staticmethod
    def from_all_addresses(addresses: Iter[Address]) -> HashableFactory:
        """
        Each address is mapped to a list of each with more complete (but incompatible) soft elements
        """
        addresses = list(addresses)

        _SOFT_COMPONENTS = [label for label in SOFT_COMPONENTS if label != "unit"]

        def new_dict() -> Dict[str, Set[str]]:
            return {soft: set([]) for soft in _SOFT_COMPONENTS}

        d: Dict[Seq[str], Dict[str, Set[str]]] = {}

        unit_store: Dict[Seq[str], Dict[str, List[Address]]] = {}
        #             dict[hards, dict[unit, addresses]]
        for a in addresses:
            hards = a.hard_components()
            softs = d.get(hards, new_dict())
            a_dict = a._asdict()
            # softs["st_NESW"] = set(["E", "W"])
            # print("SOFTS", softs)
            for k, v in a_dict.items():
                # print(k in softs, k, a.pretty())
                if k in softs and v:  # softs[k]:

                    softs[k].add(v)
            d[hards] = softs

            if a.unit:
                u_adds: Dict[str, List[Address]] = unit_store.get(hards, {})
                adds = u_adds.get(a.unit, [])
                adds.append(a)
                u_adds[a.unit] = adds
                unit_store[hards] = u_adds

        # should go in Address class?
        idx_of: Dict[str, int] = {
            field: int for int, field in enumerate(Address._fields)
        }

        def fill_in(a: Address) -> Opt[List[Address]]:
            hards = a.hard_components()
            d_softs: Dict[str, Set[str]] = d[hards]

            a_dict: Dict[str, Opt[str]] = {label: None for label in _SOFT_COMPONENTS}

            for label in _SOFT_COMPONENTS:
                vals = d_softs.get(label, set([]))
                val = a[idx_of[label]]
                if val:  # it is specified in 'a'
                    vals.add(val)
                    a_dict[label] = val
                elif (
                    len(vals) == 1
                ):  # it's not specified in 'a', but there's only 1 option it could be
                    a_dict[label] = list(vals)[0]
                elif len(vals) > 1:  # it's ambigous and not specified in 'a'
                    return None

            # this is where filling units shoud be toggled
            ret: List[Address] = []

            if a.unit:
                return [a.combine_soft_dict(a_dict).__as_address__()]
            else:
                empty_d: Dict[str, List[Address]] = {}
                units: Dict[str, List[Address]] = get(unit_store, hards, empty_d)
                if not units:
                    return [a.combine_soft_dict(a_dict).__as_address__()]
                for adds in units.values():
                    ret.extend(
                        [a.combine_soft(b).__as_address__() for b in adds if a == b]
                    )
                return ret

        # remove ambigous apt addresses
        for hards, u_adds in unit_store.items():
            for unit, adds in u_adds.items():
                unit_store[hards][unit] = list(join(filter(None, map(fill_in, adds))))

        def is_ambig(softs: Dict[str, Set[Opt[str]]]) -> bool:
            """
            Is there more that one value for any given soft component? (except unit)
            ...
            The (less readable) definition was the following:
            --l = [list(filter(None, v)) for k, v in softs.items() if k != "unit"]
            --m = max(map(len, l))
            --return m > 1
            """
            for label, vals in softs.items():
                n_vals: int = len(list(filter(None, vals)))
                if label != "unit" and n_vals > 1:
                    return True
            return False

        fix_by_hand: Dict[Tuple[str, str, str, str], List[Address]] = {}

        for a in addresses:
            hards = a.hard_components()
            softs = d[hards]
            if is_ambig(softs):  # cannot have mismatching st_suffix,st_NESW or zip_code
                similar_addresses = fix_by_hand.get(hards, [])
                similar_addresses.append(a)
                fix_by_hand[hards] = similar_addresses

        def fix(a: Address) -> List[Address]:
            adds = fill_in(a)
            if adds == None:
                return []
            return adds

        return HashableFactory(fill_in_info=fix, fix_by_hand=list(fix_by_hand.values()))


def merge_duplicates(addresses: Iter[Address]) -> Set[Address]:
    addresses = list(addresses)
    f = HashableFactory.from_all_addresses(addresses)
    return set(join(map(f, addresses)))


example_addresses = [
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
]
