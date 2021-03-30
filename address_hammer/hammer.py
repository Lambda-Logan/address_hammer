from __future__ import annotations
from .__types__ import *
from .address import Address, HashableFactory
from .fuzzy_string import FixTypos
from .parsing import Parser, ParseError, smart_batch

Bag = Dict[str, int]


def _id(t:T)->T:
    return t

def bag_from(ss: Iter[str])->Bag:
    d: Bag = {}
    for s in ss:
        d[s] = d.get(s, 0) + 1
    return d

class Hammer:
    """
    A Hammer normalizes addresses so that all addresses have completed information and are hashable.
    NOTE: You should only have one Hammer instance, and it should be initialized using all addresses the hammer will ever see.

        hammer = Hammer(all_addresses)

    hammer.__getitem__(address) will map a str or RawAddress to zero or one Address, which will be the completed address.
    An address can only be incomplete when compared to other similar addresses seen by the hammer.
    A Hammer cleans the RawAddresses, fixes typos and fills in missing optional fields that are present in similar duplicate addresses.
    
    i.e if a hammer sees both A and B, both addresses will be normalized as C where:
 
        A = "123 W Main    Boston MA"
 
        B = "123   Main St Boston MA" 
 
        C = "123 W Main St Boston MA"

        assert hammer[A] == C and hammer[B] == C

    Or, given A and B above:

        hammer["123 Main Apt 7 Boston MA"] == "123 W Main St Apt 7 Boston MA"
    
    """
    p: Parser
    __repair_st__: Fn[[str], str]
    __repair_city__: Fn[[str], str]
    parse_errors: List[Tuple[ParseError, str]]
    ambigous_address_groups: List[List[Address]]
    __addresses__: Set[Address]
    __hashable_factory__: HashableFactory
    def __init__(self, 
                 input_addresses: Iter[Union[str, Address]],
                 known_cities: Seq[str] = [],
                 known_streets: Seq[str] = [],
                 city_repair_level: int = 5,
                 street_repair_level: int = 5,
                 junk_cities: Seq[str] = [],
                 junk_streets: Seq[str] = []):
        
        if city_repair_level > 10 or city_repair_level < 0:
            raise ValueError("The typo repair level must be between 0-10, not " + str(city_repair_level ))
        
        if street_repair_level > 10 or street_repair_level < 0:
            raise ValueError("The typo repair level must be between 0-10, not " + str(street_repair_level ))
        
        from math import log
        p = Parser(known_cities=list(known_cities))
        address_strings: List[str] = []
        adds: List[Address] = []
        parse_errors: List[Tuple[ParseError, str]] = []
        for address in input_addresses:
            if isinstance(address, str):
                address_strings.append(address)
            else:
                adds.append(address)
        

        def addresses_iter()->Iter[Address]:
            junk_cities_set = set(junk_cities)
            junk_streets_set = set(junk_streets)

            #ok:Fn[[Address], bool] = lambda a: a.city not in junk_cities_set \
            #                                   and a.st_name not in junk_streets_set
            def ok(a: Address)-> bool:
                if a.city in junk_cities_set:
                    parse_errors.append((ParseError(a.orig, "junk city"), a.orig))
                    return False
                if a.st_name in junk_streets_set:
                    parse_errors.append((ParseError(a.orig, "junk street"), a.orig))
                    return False
                return True
            
            report_error : Fn[[ParseError, str], None ]= lambda e,s: parse_errors.append((e,s))
            yield from filter(ok, smart_batch(p, 
                                address_strings,
                                report_error=report_error))
            yield from filter(ok, adds)
        addresses = list(addresses_iter())
        
        cuttoff = log(max(len(addresses), 1))

        city_bag = bag_from(map(Address.Get.city, addresses))

        if city_repair_level == 0:
            self.__repair_city__: Fn[[str], str] = _id
        else:
            
            cities = join([known_cities, 
                        filter(lambda c: cuttoff < city_bag.get(c, 0), city_bag.keys())])
            self.__repair_city__ = FixTypos(cities, cuttoff=city_repair_level)

        if street_repair_level == 0:
            self.__repair_st__: Fn[[str], str] = _id
        else:
            st_name_bag = bag_from(map(Address.Get.st_name, addresses))
            streets = join([known_streets, 
                            filter(lambda s: cuttoff < st_name_bag.get(s, 0), st_name_bag.keys())])
            self.__repair_st__ = FixTypos(streets, cuttoff=street_repair_level)

        addresses = [self.fix_typos(a) for a in addresses]
        self.p = Parser(known_cities=list(city_bag.keys()))
        self.__hashable_factory__ = HashableFactory.from_all_addresses(addresses)
        self.ambigous_address_groups = self.__hashable_factory__.fix_by_hand
        self.__addresses__ = set(join(map(self.zero_or_more, addresses)))
        self.parse_errors = parse_errors

    def fix_typos(self, a:Address)->Address:
        return a.replace(city=self.__repair_city__(a.city),
                         st_name=self.__repair_st__(a.st_name))

        #self.__hashable_factory__.fix_by_hand

    def __getitem__(self, a: Union[Address, str]) -> Address:
        import warnings
        if isinstance(a, str):
            a = self.p(a)
        a = self.fix_typos(a)
        adds = self.__hashable_factory__(a)
        if len(adds) == 0:
            #return None
            raise KeyError(str(a))
        if len(adds) == 1:
            return adds[0]
        else:
            msg = """
            
            The following address was linked to more than one unit in the building.
            Consider using 'hammer.zero_or_more(address)' instead of 'hammer[address]'

            """+a.pretty() + "\n"
            warnings.warn(msg)
            return adds[0].replace(unit=None)

    def __len__(self)->int:
        return len(self.__addresses__)

    def __iter__(self)->Iter[Address]:
        return iter(self.__addresses__)

    def zero_or_more(self, a: Union[Address, str]) -> List[Address]:
        if isinstance(a, str):
            a = self.p(a)
        return self.__hashable_factory__(a)

    def get(self, a: Union[Address, str], d: T)->Union[Address, T]:
        try:
            return self[a]
        except KeyError:
            return d

def test():
    ambigs_1 = [
            "001 Street City MI",
            "001 E Streeet City MI",
            #"001 W Street City MI",
            "001 Street St City MI",
            "001 Street Apt 0 City MI",
            "001 Street Apt 1 Ccity MI",
        ]
    ambigs_2 = ambigs_1 + ["001 W Street City MI"]
    hammer = Hammer(ambigs_1)
    #print(list(map(Address.Get.pretty, set(hammer))))
    #print(list(map(print, map( Address.Get.pretty, join(hammer.ambigous_address_groups)))))
    #print(hammer["001 W Street Ave #4 City MI"].pretty())
test()