from __future__ import annotations
from .__types__ import Tuple, Seq, Iter, List, NamedTuple, Dict, Fn, Opt
from .__hammer__ import Hammer
from .__address__ import RawAddress, Address
from .__parsing__ import Parser, ParseError


class Row(NamedTuple):
    left: List[str]
    address: RawAddress
    right: List[str]


class Sheet:
    hammer: Hammer
    rows: List[Row]
    address_idxs: Tuple[int, int]
    right_len: int

    def __init__(
        self,
        address_idxs: Tuple[int, int],
        rows: Iter[List[str]],
        known_cities: Seq[str] = (),
        known_streets: Seq[str] = (),
        city_repair_level: int = 5,
        street_repair_level: int = 5,
        junk_cities: Seq[str] = (),
        junk_streets: Seq[str] = (),
        make_batch_checksum: bool = True,
    ):
        i, j = address_idxs
        self.address_idxs = address_idxs
        p = Parser(known_cities=known_cities)
        parse_errors: List[Tuple[ParseError, str]] = []

        def parse_row(row: List[str]) -> Opt[Row]:
            address_str = row[i:j]
            try:
                address = p.parse_row(address_str)
                return Row(left=row[:i], address=address, right=row[j:])
            except ParseError as e:
                parse_errors.append((e, "\t".join(row)))
                return None

        self.rows = list(filter(None, map(parse_row, rows)))

        self.hammer = Hammer(
            map(lambda row: row.address, self.rows),
            known_cities=known_cities,
            known_streets=known_streets,
            city_repair_level=city_repair_level,
            street_repair_level=street_repair_level,
            junk_cities=junk_cities,
            junk_streets=junk_streets,
            make_batch_checksum=make_batch_checksum,
        )

        self.right_len = max(*map(len, map(lambda row: row.right, self.rows)))

    def combine_cells(self, idx: int, cells: List[str]) -> str:
        return " & ".join(sorted(set(filter(None, map(lambda s: s.strip(), cells)))))

    def merge_duplicates(self) -> Iter[List[str]]:
        from collections import defaultdict

        i, _ = self.address_idxs

        new_pair: Fn[[], Tuple[List[List[str]], List[List[str]]]] = lambda: (
            [[] for _ in range(i)],
            [[] for _ in range(self.right_len)],
        )
        d: Dict[Address, Tuple[List[List[str]], List[List[str]]]] = defaultdict(
            new_pair
        )

        for _left, _address, _right in self.rows:
            address = self.hammer[_address]
            left, right = d[address]
            for idx, item in enumerate(_left):
                left[idx].append(item)

            for idx, item in enumerate(_right):
                right[idx].append(item)

        def merge_cells(row: List[List[str]]) -> Iter[str]:
            for idx, cells in enumerate(row):
                yield self.combine_cells(idx, cells)

        for address, (left, right) in d.items():

            yield [*merge_cells(left), *address.as_row(), *merge_cells(right)]
