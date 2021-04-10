
def all_tests():
    from .address import test as address_test
    from .__zipper__ import test as zipper_test
    from .parsing import test as parsing_test
    from .fuzzy_string import test as fuzzy_string_test
    from .hammer import test as hammer_test
    address_test()
    zipper_test()
    parsing_test()
    fuzzy_string_test()
    hammer_test()

def parse_benchmak():
    from .parsing import Parser
    from .address import example_addresses as exs
    #print(len(exs))
    n = 5000
    p = Parser()
    print(n*len(exs))
    for _ in range(n):
        for a in exs:
            try:
                p(a.orig,checked=True)
            except:
                pass
all_tests()