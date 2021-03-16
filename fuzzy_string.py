from __future__ import annotations
import typing as t

Bow = t.Dict[str, float]
Fn = t.Callable


def skipgram(text: str)->t.Iterable[t.Tuple[str, float]]:
    length = len(text)
    for i in range(length):
        for j in range(i,length):
            if i != j:
                yield text[i] + "_" + text[j], 1.0 #/ float((j - i))# float(2**(j - i))
                #yield text[i] + "_" + text[j], 1.0 / float(1.5**(j - i))



def skipgram_bow(s:str)->Bow:
    d: Bow = {}
    for tg, weight in skipgram(s):
        d[tg] = d.get(tg, 0) + weight
    return d


T  = t.TypeVar("T")

def corresponding_colums(a:t.Dict[T,float], b:t.Dict[T,float])->t.Iterable[t.Tuple[float, float]]:
    "pairwise iterator of the columns of sparse vectors 'a' and 'b'"
    for word, a_val in a.items():
        yield a_val, b.get(word, 0.0)

    for word, b_val in b.items():
        if word not in a:
            yield 0.0, b_val


def weighted_jaccard(a:Bow, b:Bow)->float:
    """
    The weighted Jaccard similary between two sparse vectors
    see https://en.wikipedia.org/wiki/Jaccard_index#Weighted_Jaccard_similarity_and_distance
    """
    from math import nan
    n = 0
    d = 0
    for x, y in corresponding_colums(a, b):
        n = n + min(x, y)
        d = d + max(x, y)
    if d == 0:
        return nan
    return n / d


def level_to_dec(level: float, 
                 __range__:t.Tuple[float, float] = (0.5,1.0))->float:
    l, h = __range__
    delta = h - l
    step = delta / 10.0
    return h - (level * step)

def const_false(_:t.Any)->bool:
    return False

class FixTypos:
    """
    A callable that will correct typos given an inital vocabulary.
    'cuttoff' is an integer between 0-10 (inclusive)
    
    'a' will fix minor typos, 'b' will liberally repair broadly similar words and 'c' will be the identity function:
        a = FixTypos(vocablist, cuttoff = 1 )
        b = FixTypos(vocablist, cuttoff = 10)
        c = FixTypos(vocablist, cuttoff = 0 )
    """
    sims_of: Fn[[str], t.Iterable[t.Tuple[str, float]]]
    should_maybe_fix: Fn[[str], bool]
    cuttoff: float
    def __init__(self, words: t.Iterable[str],
                    cuttoff: float = 5):

        import re
        from itertools import chain
        join = chain.from_iterable

        if cuttoff == 0.0:
            self.should_maybe_fix : Fn[[str],bool] = const_false
            return None
        self.cuttoff = level_to_dec(cuttoff)

        words = list(words)
        words_with: t.Dict[str, t.Set[str]] = {}
        #swm = SubWordModel.new(words, get_features=weighted_skipgram)
        #vec_of = {}
        bow_of: t.Dict[str, Bow] = {}
        #TODO base of frequency and don't recalculate seen words
        #z = np.zeros(swm.n)
        for word in join([words,["QWERTYUIOPASDFGHJKLZXCVBNM "]]):
            tri_bow = skipgram_bow(word)
            #vec_of[word] = swm.word2row(word)
            bow_of[word]  = skipgram_bow(word)
            for tri in tri_bow.keys():
                words_with[tri] = words_with.get(tri, set([]))
                words_with[tri].add(word)
        uppers = re.compile(r"[A-Z]")
        digits = re.compile(r"\d+")

        def should_maybe_fix(s:str)->bool:
            s_uppers = re.findall(uppers, s)
            if len("".join(s_uppers)) < 4:
                return False
            if s in bow_of:
                return False
            return True

        self.should_maybe_fix = should_maybe_fix

        def sims_of(s:str)->t.Iterable[t.Tuple[str, float]]:
            words: t.Set[str] = set([])
            bow = skipgram_bow(s)
            #s_vec = swm.word2row(s)
            s_bow = skipgram_bow(s)
            s_digits = re.findall(digits, s)
            for tri in bow.keys():
                words.update(words_with.get(tri, []))
            return map(lambda w: (w, weighted_jaccard(bow_of[w], s_bow)),
                    filter(
                      lambda w: w != s and s_digits == re.findall(digits, w),
                      words))

        self.sims_of = sims_of

    def __call__(self, s: str)->str:
        from math import sqrt
        s = s.upper()
        if self.should_maybe_fix(s):
            try:
                word, similarity = max(self.sims_of(s), key = lambda x: x[1])
            except ValueError: # self.sims_of(s) was empty
                return s
            similarity = sqrt(similarity)
            #print(s, word, similarity)
            if similarity > self.cuttoff:
                return word
        return s




def test():
    fix_typos = FixTypos("michigan scalifornia ohio ontario numeric12".upper().split())

    # these are close enough they should be repaired with a level 5 out of 10
    a = "mmichyigan ohiao kscaliofornita nmeric12".upper().split()
    for w in a:
        assert a != fix_typos(w)

    # these should be recognized as distinct with a level 5 out of 10
    b = "muichzigaan ohsiao kscaliofyornita numeric21".upper().split()
    for w in b:
        assert w == fix_typos(w)
        pass
