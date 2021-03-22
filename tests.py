
def all_tests():
    import address
    import __zipper__
    import parsing
    import fuzzy_string

    address.test()
    __zipper__.test()
    parsing.test()
    fuzzy_string.test()

all_tests()