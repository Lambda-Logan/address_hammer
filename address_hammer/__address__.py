from __future__ import annotations
from .__regex__ import normalize_whitespace
from .__types__ import (
    Union,
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
    # id_,
)


def id_(t: T) -> T:
    return t


SOFT_COMPONENTS = ["st_suffix", "st_NESW", "unit", "zip_code"]
HARD_COMPONENTS = ["house_number", "st_name", "city", "us_state"]

COMPARE_BATCH_HASHES = True


class InvalidAddressError(Exception):
    orig: str

    def __init__(self, orig: str):
        super().__init__(self, orig)
        self.orig = orig


def opt_sum(a: Opt[T], b: Opt[T]) -> Opt[T]:
    "The monoidal sum of two optional values"
    if a is not None:
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
    """
        An ``Address`` is a namedtuple representing a US residential address. It's only produced by using ``Hammer``.

        Unlike a ``RawAddress`` produced from a parser, ``Address`` is fully hashable and has no missing info for the life of the program. Anything not required by USPS postal standards is optional. The simplified definition of ``Address`` is roughly the following:

    from typing import NamedTuple, Optional

    ``class Address(NamedTuple):``
        ``house_number: str``
        ``st_name: str``
        ``st_suffix: Optional[str]``
        ``st_NESW: Optional[str]``
        ``unit: Optional[str]``
        ``city: str``
        ``us_state: str``
        ``zip_code: Optional[str]``
        ``orig: str``

    Two addresses can still be equal even with missing information, with the rule that all info that is present in both addresses must be equal (except orig).

    All attributes are available as a first class function via ``Address.Get``. For example: ``map(Address.Get.house_number, hammer)``
    """

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

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Address):
            raise NotImplementedError
        if self.__class__ != other.__class__:
            # don't use isinstance because equality is not defined for Address, RawAddress
            return False
        hards_match = self.hard_components() == other.hard_components()

        if not hards_match:
            return False

        for s_soft, o_soft in zip(self.soft_components(), other.soft_components()):

            if s_soft is not None and o_soft is not None:
                if s_soft != o_soft:
                    return False
        return True

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __str_softs__(self) -> List[str]:
        def x(s: Opt[str]) -> str:
            if not s:
                return ""
            return s

        return list(map(x, self.soft_components()))

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Address):
            raise NotImplementedError
        # TODO use soft components in __lt__ and __gt__
        a = self.hard_components()  # , self.__str_softs__()
        b = other.hard_components()  # , other.__str_softs__()
        return a > b

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Address):
            raise NotImplementedError
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
    def from_dict(d: Dict[str, Any]) -> Union[Address, RawAddress]:
        is_raw: Any = d["is_raw"]
        del d["is_raw"]
        if is_raw == "false":
            is_raw = False
        elif is_raw == "true":
            is_raw = True
        if not isinstance(is_raw, bool):
            raise Exception("invalid dict format for Address (check 'is_raw')")
        make = Address
        if is_raw is True:
            make = RawAddress
        r = make(**d)
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
        make = Address
        if isinstance(self, RawAddress):
            make = RawAddress

        return make(
            house_number=self.house_number,
            st_name=self.st_name,
            st_suffix=opt_sum(self.st_suffix, other.st_suffix),
            st_NESW=opt_sum(self.st_NESW, other.st_NESW),
            unit=opt_sum(self.unit, other.unit),
            city=self.city,
            us_state=self.us_state,
            zip_code=opt_sum(self.zip_code, other.zip_code),
            orig=self.orig,
            batch_checksum=self.batch_checksum,
        )

    def combine_soft_dict(self, other: Dict[str, Opt[str]]) -> Address:
        f: Fn[[str], Opt[str]] = lambda label: get(other, label, None)
        make = Address
        if isinstance(self, RawAddress):
            make = RawAddress
        return make(
            house_number=self.house_number,
            st_name=self.st_name,
            st_suffix=opt_sum(self.st_suffix, f("st_suffix")),
            st_NESW=opt_sum(self.st_NESW, f("st_NESW")),
            unit=opt_sum(self.unit, f("unit")),
            city=self.city,
            us_state=self.us_state,
            zip_code=opt_sum(self.zip_code, f("zip_code")),
            orig=self.orig,
            batch_checksum=self.batch_checksum,
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

        as_dict = self._asdict()
        softs = {"st_NESW": "", "st_suffix": "", "unit": "", "zip_code": ""}

        for k in softs:
            if as_dict[k] is not None:
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

    def as_row(self) -> List[str]:
        def to_str(s: Opt[str]) -> str:
            if s:
                return s
            return ""

        return [to_str(s) for s in self[:8]]

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

    def with_house_number(self, s: str) -> Address:
        return self._replace(house_number=s)

    def with_st_name(self, s: str) -> Address:
        return self._replace(st_name=s)

    def with_st_suffix(self, s: Opt[str]) -> Address:
        return self._replace(st_suffix=s)

    def with_st_NESW(self, s: Opt[str]) -> Address:
        return self._replace(st_NESW=s)

    def with_unit(self, s: Opt[str]) -> Address:
        return self._replace(unit=s)

    def with_city(self, s: str) -> Address:
        return self._replace(city=s)

    def with_us_state(self, s: str) -> Address:
        return self._replace(us_state=s)

    def with_zip_code(self, s: Opt[str]) -> Address:
        return self._replace(zip_code=s)

    def with_orig(self, s: str) -> Address:
        return self._replace(orig=s)


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
        return join(map(lambda x: self(x), addresses))

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

        unit_store: Dict[Tuple[str, str, str, str], Dict[str, List[Address]]] = {}
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
            empty_d: Dict[str, List[Address]] = {}
            units: Dict[str, List[Address]] = unit_store.get(hards, empty_d)
            if not units:
                return [a.combine_soft_dict(a_dict).__as_address__()]
            for adds in units.values():
                ret.extend([a.combine_soft(b).__as_address__() for b in adds if a == b])
            return ret

        # remove ambigous apt addresses
        for hards, u_adds in unit_store.items():
            for unit, adds in u_adds.items():
                unit_store[hards][unit] = list(join(filter(None, map(fill_in, adds))))

        def is_ambig(softs: Dict[str, Set[str]]) -> bool:
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
            if adds is None:
                return []
            return adds

        return HashableFactory(fill_in_info=fix, fix_by_hand=list(fix_by_hand.values()))


def merge_duplicates(addresses: Iter[Address]) -> Set[Address]:
    addresses = list(addresses)
    f = HashableFactory.from_all_addresses(addresses)
    return set(join(map(lambda x: f(x), addresses)))
