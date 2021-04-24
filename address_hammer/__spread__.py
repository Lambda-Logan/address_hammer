from __future__ import annotations
from .__types__ import Tuple, Seq, Iter, List, NamedTuple, Dict, Fn, Opt
from .__hammer__ import Hammer
from .__address__ import RawAddress, Address
from .__parsing__ import Parser, ParseError


class Row(NamedTuple):
    left: List[str]
    address: RawAddress
    right: List[str]


class Spread:
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

    def combined(self) -> Iter[List[str]]:
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


import csv

# fmt: off
names = ["Garcia", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Perez", "Sanchez", "Ramirez", "Torres", "Flores", "Rivera", "Gomez", "Diaz", "Reyes", "Morales", "Cruz", "Ortiz", "Gutierrez", "Chavez", "Ramos", "Gonzales", "Ruiz", "Alvarez", "Mendoza", "Vasquez", "Castillo", "Jimenez", "Moreno", "Romero", "Herrera", "Medina", "Aguilar", "Garza", "Castro", "Vargas", "Fernandez", "Guzman", "Munoz", "Mendez", "Salazar", "Soto", "Delgado", "Pena", "Rios", "Alvarado", "Sandoval", "Contreras", "Valdez", "Guerrero", "Ortega", "Estrada", "Nunez", "Maldonado", "Vega", "Vazquez", "Santiago", "Dominguez", "Espinoza", "Silva", "Padilla", "Marquez", "Cortez", "Rojas", "Acosta", "Figueroa", "Luna", "Juarez", "Navarro", "Campos", "Molina", "Avila", "Ayala", "Mejia", "Carrillo", "Duran", "Santos", "Salinas", "Robles", "Solis", "Lara", "Cervantes", "Aguirre", "Deleon", "Ochoa", "Miranda", "Cardenas", "Trujillo", "Velasquez", "Fuentes", "Cabrera", "Leon", "Rivas", "Montoya", "Calderon", "Colon", "Serrano", "Gallegos", "Rosales", "Castaneda", "Villarreal", "Guerra", "Trevino", "Pacheco", "Ibarra", "Valencia", "Macias", "Camacho", "Salas", "Orozco", "Roman", "Zamora", "Suarez", "Franco", "Barrera", "Mercado", "Santana", "Valenzuela", "Escobar", "Rangel", "Melendez", "Velez", "Lozano", "Velazquez", "Arias", "Mora", "Delacruz", "Galvan", "Zuniga", "Cantu", "Villanueva", "Meza", "Acevedo", "Cisneros", "Arroyo", "Pineda", "Andrade", "Tapia", "Sosa", "Villa", "Rocha", "Rubio", "Zavala", "Montes", "Ponce", "Bonilla", "Arellano", "Rosario", "Davila", "Villegas", "Huerta", "Mata", "Beltran", "Barajas", "Benitez", "Esparza", "Cordova", "Murillo", "Salgado", "Rosas", "Cuevas", "Palacios", "Guevara", "Quintero", "Lucero", "Medrano", "Bautista", "Lugo", "Dejesus", "Espinosa", "Marin", "Cortes", "Magana", "Quintana", "Corona", "Trejo", "Bernal", "Nieves", "Villalobos", "Enriquez", "Reyna", "Jaramillo", "Saenz", "Quinones", "Delarosa", "Avalos", "Esquivel", "Nava", "Cano", "Bravo", "Duarte", "Galindo", "Correa", "Parra", "Rodriquez", "Saldana", "Leal", "Sierra", "Blanco", "Becerra", "Carrasco", "Portillo", "Tovar", "Alfaro", "Vera", "Zapata", "Muniz", "Cardona", "Vigil", "Saucedo", "Baez", "Hurtado", "Amaya", "Escobedo", "Peralta", "Arredondo", "Aguilera", "Zepeda", "Rosado", "Hinojosa", "Renteria", "Gallardo", "Barrios", "Felix", "Castellanos", "Baca", "Segura", "Guillen", "Cordero", "Chacon", "Valle", "Coronado", "Delatorre", "Vela", "Moran", "Alonso", "Velasco", "Madrigal", "Carranza", "Quiroz", "Romo", "Madrid", "Montano", "Serna", "Ybarra", "Caballero", "Burgos", "Ventura", "Olvera", "Rosa", "Varela", "Leyva", "Quezada", "Bermudez", "Benavides", "Aragon", "Aviles", "Uribe", "Pagan", "Paredes", "Osorio", "Yanez", "Nieto", "Carmona", "Granados", "Gil", "Montalvo", "Casillas", "Lujan", "Bustamante", "Rico", "Barron", "Anaya", "Ornelas", "Olivares", "Canales", "Gamez", "Cuellar", "Lemus", "Prado", "Barragan", "Paz", "Pina", "Reynoso", "Valadez", "Navarrete", "Otero", "Aleman", "Marrero", "Olivas", "Ojeda", "Arevalo", "Fonseca", "Quintanilla", "Solano", "Escamilla", "Feliciano", "Tellez", "Sepulveda", "Orellana", "Arreola", "Betancourt", "Carbajal", "Amador", "Sotelo", "Hidalgo", "Ocampo", "Rendon", "Venegas", "Negron", "Banuelos", "Patino", "Cavazos", "Torrez", "Matos", "Casas", "Godinez", "Valdes", "Longoria", "Ledesma", "Alaniz", "Aranda", "Prieto", "Vallejo", "Polanco", "Zarate", "Pulido", "Arce", "Barraza", "Mena", "Alonzo", "Gamboa", "Arteaga", "Escalante", "Valentin", "Galvez", "Brito", "Cerda", "Zaragoza", "Nevarez", "Chavarria", "Saldivar", "Corral", "Saavedra", "Marroquin", "Chapa", "Mireles", "Crespo", "Arriaga", "Covarrubias", "Salcedo", "Holguin", "Moya", "Alcala", "Linares", "Heredia", "Ceja", "Barrientos", "Aponte", "Montanez", "Najera", "Rodrigues", "Cornejo", "Alarcon", "Ontiveros", "Anguiano", "Soriano", "Pimentel", "Elizondo", "Zambrano", "Rincon", "Mondragon", "Cazares", "Robledo", "Acuna", "Bueno", "Bustos", "Adame", "Balderas", "Delossantos", "Toledo", "Valdivia", "Naranjo", "Perales", "Delgadillo", "Puente", "Frias", "Vidal", "Guajardo", "Negrete", "Collazo", "Abreu", "Ceballos", "Jaimes", "Batista", "Irizarry", "Espinal", "Carrera", "Tamayo", "Pantoja", "Oliva", "Espino", "Benavidez", "Ordonez", "Noriega", "Almanza", "Urbina", "Limon", "Gaytan", "Montero", "Archuleta", "Armenta", "Banda", "Farias", "Tejeda", "Mojica", "Fierro", "Solorzano", "Villasenor", "Mesa", "Mares", "Tirado", "Lira", "Aguayo", "Lerma", "Argueta", "Palma", "Jaime", "Aquino", "Alicea", "Soria", "Solorio", "Jasso", "Valles", "Garibay", "Cintron", "Centeno", "Preciado", "Loera", "Machado", "Henriquez", "Briones", "Armendariz", "Giron", "Lomeli", "Caraballo", "Elias", "Berrios", "Barbosa", "Garay", "Tejada", "Loya", "Angulo", "Regalado", "Apodaca", "Mota", "Duenas", "Jauregui", "Segovia", "Ulloa", "Araujo", "Monroy", "Roldan", "Porras", "Padron", "Cadena", "Vergara", "Alcantar", "Delagarza", "Ferrer", "Delvalle", "Munguia", "Fajardo", "Pedraza", "Santillan", "Razo", "Aparicio", "Cabral", "Rosario", "Feliz", "Alcantara", "Valoy", "Veras", "Estevez", "Nunez", "Corniel", "Caba", "Capellan", "De La Rosa", "Abreu", "Guzman", "Sarante", "Mercedes", "Pimental", "Polanco", "Belliard", "Pena", "Matos", "Marte", "Peralta", "Urena", "Olivo", "Andujar", "Veloz", "Inoa", "Gratereaux", "Suriel", "Lantigua", "Zorilla", "Berroa", "Lebron", "Payano", "Figuereo", "Camilo", "Aybar", "Montas", "Silverio", "Moreta", "Luciano", "Pujols", "Cuello", "Rijo", "German", "Genao", "Valerio", "Villar", "Collado", "Terrero", "Disla", "Jaquez", "Fermin", "Ferreras", "Liriano", "Ogando", "Nuez", "Severino", "Beltre", "Adames", "Toribio", "Morillo", "Javier", "Estrella", "Almanzar", "Quezada", "Grullon", "Pea", "Frias", "Lora", "Peguero", "Cuevas", "Reynoso", "Pichardo", "Encarnacion", "Mateo", "Espinal", "Paulino", "Valdez", "Baez", "Almonte", "Santana", "De La Cruz", "Tavarez", "Suero", "Tejada"]
# fmt: on
hispnames = set(map(lambda x: x.lower(), names))

# meaningful aliases for the indices
name_1, name_2, phone_1, phone_2, email = 0, 1, 9, 10, 11


def is_hisp_line(line: List[str]) -> bool:
    def clean(s: str) -> List[str]:
        s = s.replace("-", " ").lower()
        return s.split()

    o = False

    for word in [*clean(line[name_1]), *clean(line[name_2])]:
        o = o or word in hispnames
        if o:
            return True
    return o


with open("/home/logan/Dropbox/temp/Proud_lake_2021_04.csv") as csvfile:
    spamreader = csv.reader(csvfile, delimiter="\t")
    spread = Spread((2, 9), filter(is_hisp_line, spamreader))

    l = list(spread.combined())
    print(len(l))
    l.sort(key=lambda row: row[1].count("&"), reverse=True)
    with open(
        "/home/logan/Dropbox/temp/proud_lake_2021_04_24.tsv", "w", newline=""
    ) as csvfile:
        spamwriter = csv.writer(
            csvfile, delimiter="\t", quotechar="|", quoting=csv.QUOTE_MINIMAL
        )
        spamwriter.writerows(l)
