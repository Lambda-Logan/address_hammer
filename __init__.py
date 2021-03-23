from address import Address, RawAddress, InvalidAddressError
from parsing import Parser, ParseError, EndOfAddressError, smart_batch
from hammer import Hammer
"""
p = Parser(known_cities="Houston Dallas".split())
        

a =  ["123 Straight Houston TX",        # no identifier bewteen street and city (BUT a known city)
        
        "123 8th Ave NE Ste A Dallas TX", # nothing to see here, normal address
        
        "123 Dallas Rd Houston TX"       ]# the street would be recognized as a city (BUT fortunately there is an identifier bewteen the street and city)



b =  ["123 Straight Houuston TX", #typo

        "123 Straight Austin TX",   #(1) unknown city and (2) no identifier bewteen street and city
        
        "123 Dallas Houston TX" ]
"""

(EndOfAddressError, Address, Parser, ParseError, RawAddress, InvalidAddressError, Hammer)