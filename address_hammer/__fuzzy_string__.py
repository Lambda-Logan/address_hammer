from __future__ import annotations
from math import sqrt, nan
import re
from .__types__ import Dict, Iter, Tuple, Fn, T, Set, Any, join, Fns_Of

Bow = Dict[str, float]


def skipgram(text: str) -> Iter[Tuple[str, float]]:
    length = len(text)
    for i in range(length):
        for j in range(i, length):
            if i != j:
                yield text[i] + "_" + text[
                    j
                ], 1.0  # / float((j - i))# float(2**(j - i))
                # yield text[i] + "_" + text[j], 1.0 / float(1.5**(j - i))


def skipgram_bow(s: str) -> Bow:
    d: Bow = {}
    for tg, weight in skipgram(s):
        d[tg] = d.get(tg, 0) + weight
    return d


def corresponding_colums(
    a: Dict[T, float], b: Dict[T, float]
) -> Iter[Tuple[float, float]]:
    "pairwise iterator of the columns of sparse vectors 'a' and 'b'"
    for word, a_val in a.items():
        yield a_val, b.get(word, 0.0)

    for word, b_val in b.items():
        if word not in a:
            yield 0.0, b_val


def weighted_jaccard(a: Bow, b: Bow) -> float:
    """
    The weighted Jaccard similary between two sparse vectors
    see https://en.wikipedia.org/wiki/Jaccard_index#Weighted_Jaccard_similarity_and_distance
    """

    n = 0.0
    d = 0.0
    for x, y in corresponding_colums(a, b):
        n = n + min(x, y)
        d = d + max(x, y)
    if d == 0:
        return nan
    return n / d


def level_to_dec(level: float, __range__: Tuple[float, float] = (0.5, 1.0)) -> float:
    l, h = __range__
    delta = h - l
    step = delta / 10.0
    return h - (level * step)


def const_false(_: Any) -> bool:
    return False


class Fns_of_FixTypos(Fns_Of):
    @staticmethod
    def sims_of(s: str) -> Iter[Tuple[str, float]]:
        return []

    @staticmethod
    def should_maybe_fix(s: str) -> bool:
        return False


class FixTypos:
    """
    A callable that will correct typos given an inital vocabulary.
    'cuttoff' is an integer between 0-10 (inclusive)

    'a' will fix minor typos, 'b' will liberally repair broadly similar words and 'c' will be the identity function:
        ``a = FixTypos(vocablist, cuttoff = 1 )``
        ``b = FixTypos(vocablist, cuttoff = 10)``
        ``c = FixTypos(vocablist, cuttoff = 0 )``
    """

    cuttoff: float
    __fns__: Fns_of_FixTypos

    @property
    def sims_of(self) -> Fn[[str], Iter[Tuple[str, float]]]:
        return self.__fns__.sims_of

    @property
    def should_maybe_fix(self) -> Fn[[str], bool]:
        return self.__fns__.should_maybe_fix

    def __init__(self, words: Iter[str], cuttoff: float = 5):
        self.__fns__ = Fns_of_FixTypos()
        if cuttoff == 0.0:
            return None
        self.cuttoff = level_to_dec(cuttoff)

        words = list(words)
        words_with: Dict[str, Set[str]] = {}
        # swm = SubWordModel.new(words, get_features=weighted_skipgram)
        # vec_of = {}
        bow_of: Dict[str, Bow] = {}
        # TODO base of frequency and don't recalculate seen words
        # z = np.zeros(swm.n)
        for word in join([words, ["QWERTYUIOPASDFGHJKLZXCVBNM "]]):
            tri_bow = skipgram_bow(word)
            # vec_of[word] = swm.word2row(word)
            bow_of[word] = skipgram_bow(word)
            for tri in tri_bow:
                words_with[tri] = words_with.get(tri, set([]))
                words_with[tri].add(word)
        uppers = re.compile(r"[A-Z]")
        digits = re.compile(r"\d+")

        class __Fns_of_FixTypos__(Fns_of_FixTypos):
            @staticmethod
            def should_maybe_fix(s: str) -> bool:
                s_uppers = re.findall(uppers, s)
                if len("".join(s_uppers)) < 4:
                    return False
                if s in bow_of:
                    return False
                return True

            @staticmethod
            def sims_of(s: str) -> Iter[Tuple[str, float]]:
                words: Set[str] = set([])
                bow = skipgram_bow(s)
                # s_vec = swm.word2row(s)
                s_bow = skipgram_bow(s)
                s_digits = re.findall(digits, s)
                for tri in bow:
                    words.update(words_with.get(tri, []))
                return map(
                    lambda w: (w, weighted_jaccard(bow_of[w], s_bow)),
                    filter(
                        lambda w: w != s and s_digits == re.findall(digits, w), words
                    ),
                )

        self.__fns__ = __Fns_of_FixTypos__()

    def __call__(self, s: str) -> str:

        s = s.upper()
        if self.should_maybe_fix(s):
            try:
                word, similarity = max(self.sims_of(s), key=lambda x: x[1])
            except ValueError:  # self.sims_of(s) was empty
                return s
            similarity = sqrt(similarity)
            # print(s, word, similarity)
            if similarity > self.cuttoff:
                return word
        return s
