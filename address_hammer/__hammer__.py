from __future__ import annotations
import warnings
from math import log as math_log
from hashlib import md5
from .__types__ import Union, T, Fn, Seq, List, Tuple, Dict, Set, join, Iter
from .__address__ import Address, HashableFactory, CHECKSUM_IGNORE
from .__fuzzy_string__ import FixTypos
from .__parsing__ import Parser, ParseError, smart_batch

Bag = Dict[str, int]


def bag_from(ss: Iter[str]) -> Bag:
    d: Bag = {}
    for s in ss:
        d[s] = d.get(s, 0) + 1
    return d


MD5_SALT = b"e3737f1156529b4d"


class ChecksumMismatch(Exception):
    msg: str

    def __init__(self, a: str, b: str) -> None:
        msg = f"'{a}' and '{b}'"
        self.msg = msg
        super().__init__(msg)


def check_checksum(a: str, b: str):

    if a == CHECKSUM_IGNORE or b == CHECKSUM_IGNORE:
        return None
    if a != b:
        raise ChecksumMismatch(a, b)
    return None


remove_unit = Address.Set(unit=lambda x: None)


class Hammer:
    """
    A ``Hammer`` normalizes addresses so that all addresses have completed information and are hashable.
    NOTE: You should only have one ``Hammer`` instance, and it should be initialized using all addresses the hammer will ever see.

        ``hammer = Hammer(all_addresses)``

    ``hammer.__getitem__(address)`` will map a str or ``RawAddress`` to zero or one ``Address``, which will be the completed address.

    A ``Hammer`` cleans the ``RawAddresses``, fixes typos and fills in missing optional fields that are present in similar duplicate addresses.

    i.e if a hammer sees both A and B, both addresses will be normalized as C where:
        ``A = "123 W Main    Boston MA"``

        ``B = "123   Main St Boston MA"``

        ``C = "123 W Main St Boston MA"``

        ``assert hammer[A] == C and hammer[B] == C``

    Or, given A and B above:

        ``hammer["123 Main Apt 7 Boston MA"] == "123 W Main St Apt 7 Boston MA"``

    """

    p: Parser
    __repair_st__: FixTypos
    __repair_city__: FixTypos
    parse_errors: List[Tuple[ParseError, str]]
    ambigous_address_groups: List[List[Address]]
    __addresses__: Set[Address]
    __hashable_factory__: HashableFactory
    batch_checksum: str

    def __init__(
        self,
        input_addresses: Iter[Union[str, Address]],
        known_cities: Seq[str] = (),
        known_streets: Seq[str] = (),
        city_repair_level: int = 5,
        street_repair_level: int = 5,
        junk_cities: Seq[str] = (),
        junk_streets: Seq[str] = (),
        make_batch_checksum: bool = True,
    ):

        if city_repair_level > 10 or city_repair_level < 0:
            raise ValueError(
                f"The typo repair level must be between 0-10, not {city_repair_level}"
            )

        if street_repair_level > 10 or street_repair_level < 0:
            raise ValueError(
                f"The typo repair level must be between 0-10, not {street_repair_level}"
            )

        p = Parser(known_cities=list(known_cities))
        address_strings: List[str] = []
        adds: List[Address] = []
        parse_errors: List[Tuple[ParseError, str]] = []
        for address in input_addresses:
            if isinstance(address, str):
                address_strings.append(address)
            else:
                adds.append(address)

        def addresses_iter() -> Iter[Address]:
            junk_cities_set = set(junk_cities)
            junk_streets_set = set(junk_streets)

            # ok:Fn[[Address], bool] = lambda a: a.city not in junk_cities_set \
            #                                   and a.st_name not in junk_streets_set
            def ok(a: Address) -> bool:
                if a.city in junk_cities_set:
                    parse_errors.append((ParseError(a.orig, "junk city"), a.orig))
                    return False
                if a.st_name in junk_streets_set:
                    parse_errors.append((ParseError(a.orig, "junk street"), a.orig))
                    return False
                return True

            report_error: Fn[
                [ParseError, str], None
            ] = lambda e, s: parse_errors.append((e, s))
            yield from filter(
                ok, smart_batch(p, address_strings, report_error=report_error)
            )
            yield from filter(ok, adds)

        addresses = list(addresses_iter())

        cuttoff = math_log(max(len(addresses), 1))

        city_bag = bag_from(map(Address.Get.city, addresses))

        if city_repair_level == 0:
            self.__repair_city__ = FixTypos([], cuttoff=0.0)
        else:

            cities = [
                *known_cities,
                *filter(lambda c: cuttoff < city_bag.get(c, 0), city_bag.keys()),
            ]
            self.__repair_city__ = FixTypos(cities, cuttoff=city_repair_level)

        if street_repair_level == 0:
            self.__repair_st__ = FixTypos([], cuttoff=0.0)
        else:
            st_name_bag = bag_from(map(Address.Get.st_name, addresses))
            streets = [
                *known_streets,
                *filter(lambda s: cuttoff < st_name_bag.get(s, 0), st_name_bag.keys()),
            ]

            self.__repair_st__ = FixTypos(streets, cuttoff=street_repair_level)

        # MD5 SUM
        if not make_batch_checksum:
            checksum = ""
        else:

            m = md5()

            to_hash_str = [junk_cities, junk_streets, known_cities, known_streets]

            for s in join(to_hash_str):
                m.update(s.encode("utf-8"))
            # print(len(list(filter(None, addresses))))
            # print(list(map(Address.Get.pretty, addresses)))
            # addresses = sorted(filter(None, addresses))
            for a in sorted(addresses):
                for s in a.hard_components():
                    m.update(s.encode("utf-8"))
                for _s in a.soft_components():
                    if _s:
                        m.update(_s.encode("utf-8"))

            checksum = m.hexdigest()
        self.batch_checksum = checksum
        self.fix_typos = Address.Set(
            city=self.__repair_city__,
            st_name=self.__repair_st__,
            batch_checksum=lambda _: checksum,
        )
        addresses = [self.fix_typos(a) for a in addresses]
        self.p = Parser(known_cities=list(city_bag.keys()))
        self.__hashable_factory__ = HashableFactory.from_all_addresses(addresses)
        self.ambigous_address_groups = self.__hashable_factory__.fix_by_hand
        self.__addresses__ = set(join(map(self.zero_or_more, addresses)))
        self.parse_errors = parse_errors

        # self.__hashable_factory__.fix_by_hand

    def map(self, f: Fn[[Address], Address]) -> Hammer:
        h = Hammer([])
        h.batch_checksum = self.batch_checksum
        h.parse_errors = self.parse_errors
        h.p = self.p
        h.ambigous_address_groups = self.ambigous_address_groups
        h.__addresses__ = set(map(f, self.__addresses__))
        h.__hashable_factory__ = self.__hashable_factory__
        return h

    def __getitem__(self, a: Union[Address, str]) -> Address:

        if isinstance(a, Address):
            check_checksum(self.batch_checksum, a.batch_checksum)
        if isinstance(a, str):
            a = self.p(a)
        a = self.fix_typos(a)

        adds = self.__hashable_factory__(a)
        if len(adds) == 0:
            # return None
            raise KeyError(str(a))
        if len(adds) == 1:
            return adds[0]
        msg = f"""
            
            The following address was linked to more than one unit in the building.
            Consider using 'hammer.zero_or_more(address)' instead of 'hammer[address]'

            {a.pretty()}
            """
        warnings.warn(msg)
        return remove_unit(adds[0])

    def __len__(self) -> int:
        return len(self.__addresses__)

    def __iter__(self) -> Iter[Address]:
        return iter(self.__addresses__)

    def as_list(self) -> List[Address]:
        return list(self.__addresses__)

    def zero_or_more(self, a: Union[Address, str]) -> List[Address]:
        if isinstance(a, Address):
            check_checksum(self.batch_checksum, a.batch_checksum)
        else:  # isinstance(a, str):
            a = self.p(a)
        return self.__hashable_factory__(a)

    def get(self, a: Union[Address, str], d: T) -> Union[Address, T]:
        try:
            return self[a]
        except KeyError:
            return d
