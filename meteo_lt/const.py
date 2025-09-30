"""const.py"""

# Define the county to administrative divisions mapping
# https://www.infolex.lt/teise/DocumentSinglePart.aspx?AktoId=125125&StrNr=5#
COUNTY_MUNICIPALITIES = {
    "Alytaus apskritis": [
        "Alytaus miesto",
        "Alytaus rajono",
        "Druskininkų",
        "Lazdijų rajono",
        "Varėnos rajono",
    ],
    "Kauno apskritis": [
        "Birštono",
        "Jonavos rajono",
        "Kaišiadorių rajono",
        "Kauno miesto",
        "Kauno rajono",
        "Kėdainių rajono",
        "Prienų rajono",
        "Raseinių rajono",
    ],
    "Klaipėdos apskritis": [
        "Klaipėdos rajono",
        "Klaipėdos miesto",
        "Kretingos rajono",
        "Neringos",
        "Palangos miesto",
        "Skuodo rajono",
        "Šilutės rajono",
    ],
    "Pietryčių Baltija, Kuršių marios": [
        "Klaipėdos rajono",
        "Klaipėdos miesto",
        "Neringos",
        "Palangos miesto",
        "Šilutės rajono",
    ],
    "Marijampolės apskritis": [
        "Kalvarijos",
        "Kazlų Rūdos",
        "Marijampolės",
        "Šakių rajono",
        "Vilkaviškio rajono",
    ],
    "Panevėžio apskritis": [
        "Biržų rajono",
        "Kupiškio rajono",
        "Panevėžio miesto",
        "Panevėžio rajono",
        "Pasvalio rajono",
        "Rokiškio rajono",
    ],
    "Šiaulių apskritis": [
        "Joniškio rajono",
        "Kelmės rajono",
        "Pakruojo rajono",
        "Akmenės rajono",
        "Radviliškio rajono",
        "Šiaulių miesto",
        "Šiaulių rajono",
    ],
    "Tauragės apskritis": [
        "Jurbarko rajono",
        "Pagėgių",
        "Šilalės rajono",
        "Tauragės rajono",
    ],
    "Telšių apskritis": [
        "Mažeikių rajono",
        "Plungės rajono",
        "Rietavo",
        "Telšių rajono",
    ],
    "Utenos apskritis": [
        "Anykščių rajono",
        "Ignalinos rajono",
        "Molėtų rajono",
        "Utenos rajono",
        "Visagino",
        "Zarasų rajono",
    ],
    "Vilniaus apskritis": [
        "Elektrėnų",
        "Šalčininkų rajono",
        "Širvintų rajono",
        "Švenčionių rajono",
        "Trakų rajono",
        "Ukmergės rajono",
        "Vilniaus miesto",
        "Vilniaus rajono",
    ],
}

# Artificial area for Baltic coast and Curonian Lagoon created by meteo.lt
# Adding separately for better visibility
COUNTY_MUNICIPALITIES.update(
    {
        "Pietryčių Baltija, Kuršių marios": [
            "Klaipėdos rajono",
            "Klaipėdos miesto",
            "Neringos",
            "Palangos miesto",
            "Šilutės rajono",
        ],
    }
)
