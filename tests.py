
def all_tests():
    import address
    import __zipper__
    import parsing

    address.test()
    __zipper__.test()
    parsing.test()

all_tests()