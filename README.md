

# address_hammer
> _Hammer messy addresses into something beautiful._

This is a robust and simple tool for parsing and normalizing U.S residential addresses, especially in a messy real-word context. Given enough addresses, it can correct minor typos, fill in missing info and merge all duplicate addresses without loss of information. It's written 100% in strictly statically type checked python, has zero external dependencies and makes it possible to have more transparent errors than a deep-learning approach.

# Address Hammer might be useful if you...
- have ever wanted to **remove duplicate addresses** from a list or spreadsheet
- have ever wanted to **safely hash messy addresses** that have missing information
- have an advertising or volunteer outreach campaign involving many U.S residential addresses in the same general area

# Try it out!
`pip3 install git+https://github.com/Lambda-Logan/address_hammer.git` 

or

`pip install git+https://github.com/Lambda-Logan/address_hammer.git`



# There are two main tools: **`Hammer`** and **`Parser`**. 
- A `Parser` takes a string and produces a `RawAddress` (which isn't hashable because it still might have typos and missing info).
- A `Hammer` is trained on an iter of address strings and produces multiple `Address` (see below). As it already uses `Parser` internally, you should prefer using `Hammer` to `Parser`. The `Hammer` instance in your program will also remove duplicates and combine info bewteen equivalent addresses.








# `Hammer`
```python

from address_hammer import Hammer

addresses = ["123 W Main    Boston MA",
             "123   Main St Boston MA"]
 
 
# info from both addresses will be combined
hammer = Hammer(addresses)

assert len(hammer) == 1

for address in hammer:
    print(address.pretty())  
# >> "123 W Main St Boston MA"
```


Seen addresses will be used to fill in missing info from other incomplete versions of the same address.
For example, given an unseen and incomplete version of the above address:
```python
a = hammer["123 Main Boston MA"] 
assert a.st_suffix == "ST"
assert a.st_NESW   == "W"
```

The weak guarantee is that hammered addresses will be 100% complete for the life of the program.
The `Hammer` must thus be initialized with all addresses the program will ever see
```python
hammer["321 Fake St Lot 446 Phoenix AZ"]
# >> KeyError !!!

addresses = ["123 W Main    Boston MA",
             "123   Main St Boston MA",
             "321 Fake St Lot 446 Phoenix AZ"]
             
hammer = Hammer(addresses)

print(hammer["321 Fake St Lot 446 Phoenix AZ"])
# >> Address(house_number='321', st_name='FAKE', st_suffix='ST', st_NESW=None, unit='LOT 446', city='PHOENIX', us_state='AZ', zip_code=None, orig='321 Fake St Lot 446 Phoenix AZ')
# :-D
```

All parse errors are stored in `hammer.parse_errors`, which has the type `List[Tuple[ParseError, str]]`.
```python
h = Hammer(["Junk address string wooohoooo"])

for error, bad_address in h.parse_errors:
    print(bad_address)
    raise error
# >> 'Junk address string wooohoooo'
# EndOfInputError !
```


# `Address`
An `Address` is only produced by using `Hammer`. It is fully hashable and has no missing info for the life of the program. Anything not required by USPS postal standards is optional. The simplified definition of `Address` is roughly the following:
```python
from typing import NamedTuple, Optional

class Address(NamedTuple):
    house_number: str
    st_name: str
    st_suffix: Optional[str]
    st_NESW: Optional[str]
    unit: Optional[str]
    city: str
    us_state: str
    zip_code: Optional[str]
    orig: str
 ```
 Two addresses can still be equal even with missing information, with the rule that all info that is present in both addresses must be equal (except `orig`). 
 
 All attributes are available as a first class function via `Address.Get`. For example: `map(Address.Get.house_number, hammer)`






# `Parser`
If you don't need to hash addresses, correct minor typos or merge duplicates, use `Parser`. Directly using `Parser` will produce a `RawAddress`. `RawAddress` is unhashable because it still might have missing info or typos.
```python
from address_hammer import Parser

p = Parser()
print(p("999 8th blvd California CA 54321"))
# >> RawAddress(city='CALIFORNIA', us_state='CA', house_number='999', st_name='8TH', st_suffix='BLVD', st_NESW=None, unit=None, zip_code='54321', orig='999 8th blvd California CA')
```
Directly using `Parser` has the limitation that all address strings must either have something between the street name and the city (such as a unit or a street suffix), OR have the city passed in the `known_cities` parameter of the `Parser`. Using a `Hammer` doesn't have these limitations, as well as `Parser.parse_row`.

```python
p = Parser()
p2 = Parser(known_cities=["City"])

trouble_address = "123 Street City NY"

#these will work
p("123 Street St City NY")
p("123 Street E City NY")
p("123 Street Apt 512 City NY")

p2(trouble_address) 

#this won't
# p(trouble_address)
```

Also, directly using a `Parser` has the limitation that a known city cannot be part of a street name if there is no unit or street suffix. The following will not work:
```python
p = Parser(known_cities=["Grandville"])
p("128 E Grandville Grandville MI")
```



# Parsing addresses from a spreadsheet
Addresses in a spreadsheet are already usually semi-parsed. If your data is coming from a spreadsheet or csv, please use `Parser.parse_row`

```python
from address_hammer import Parser
row = ["123 Foo", "Barville AZ"]
s = "123 Foo Barville AZ"
p = Parser()

#this will parse correctly, because we have a separation between the street_name and city
address = p.parse_row(row)

#this will not
address = p(s)
```

# Debugging

The main debugging tool is `log_parse_steps_using`.

```python
from address_hammer import Parser, RawAddress, log_parse_steps_using
p = Parser()
with log_parse_steps_using(print):
    p("9393 Pretty Cloud Rd, Sky Town WY")
```
... will print the following
```python
ParseStep(label='house_number', value='9393')
ParseStep(label='st_name', value='PRETTY')
ParseStep(label='st_name', value='CLOUD')
ParseStep(label='st_suffix', value='RD')
ParseStep(label='city', value='SKY')
ParseStep(label='city', value='TOWN')
ParseStep(label='us_state', value='WY')
```

This is useful to find out why an address didn't parse correctly. For example, if we had use the string `"123 Foo Barville AZ"`, then it would print the following and then raise a `ParseError`

```python
with log_parse_steps_using(print):
    p("123 Foo Barville AZ")
```

will print the following and then raise an error
```python
ParseStep(label='house_number', value='123')
ParseStep(label='st_name', value='FOO')
ParseStep(label='st_name', value='BARVILLE') # st_name never stops because there is nothing between the st_name and the city
ParseStep(label='st_name', value='AZ')

>>> ParseError: @ Could not identify us_state: 123 Foo Barville AZ
```


# Performance
`address_hammer` is designed for simplicity, robustness and type safety. If you need to process millions of addresses, you may need some patience or another library. However, on my machine `Parser` will parse about 2,400 addresses per second and has been tested on 500K+ real-world addresses.





# Limitations
To verify addresses, use https://pypi.org/project/usps-api/

To geocode, use https://geocoder.readthedocs.io/

P.O box is not yet supported

No full street suffices or state names are automaticallly abbreviated and all address strings need a valid U.S state. e.i "michigan" will not become "MI" and "street" will not be coerced to "ST".

The `Hammer` class provides support for modest **typo correction** of streets and cities. It uses weighted Jaccard distance of skipgrams and **is not a fully developed feature at this point**. It is very conservative and will only correct minor typos in long street names or cities.

Only 5 digit zip codes are supported so far.

# You can help
If there is any unexpected result, please file a bug. This is especially important if you run into a USPS compliant address that is incorrectly parsed.
