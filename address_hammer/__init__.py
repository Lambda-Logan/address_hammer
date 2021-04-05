from .address import Address, RawAddress, InvalidAddressError
from .parsing import Parser, ParseError, EndOfAddressError
from .hammer import Hammer
"""
p = Parser(known_cities="Houston Dallas".split())
        

a =  ["123 Straight Houston TX",        # no identifier bewteen street and city (BUT a known city)
        
        "123 8th Ave NE Ste A Dallas TX", # nothing to see here, normal address
        
        "123 Dallas Rd Houston TX"       ]# the street would be recognized as a city (BUT fortunately there is an identifier bewteen the street and city)



b =  ["123 Straight Houuston TX", #typo

        "123 Straight Austin TX",   #(1) unknown city and (2) no identifier bewteen street and city
        
        "123 Dallas Houston TX" ]
"""
#TODO make way to toggle if addresses should be compared
#shoud_compare_batch_hashes = Address.__should_compare_batch_hashes

(EndOfAddressError, Address, Parser, ParseError, RawAddress, InvalidAddressError, Hammer)