"""const.py"""

# Define the county to administrative divisions mapping
# https://www.infolex.lt/teise/DocumentSinglePart.aspx?AktoId=125125&StrNr=5#
COUNTY_MUNICIPALITIES = {
    "Alytaus": [
        "Alytaus miesto",
        "Alytaus rajono",
        "Druskininkų",
        "Lazdijų rajono",
        "Varėnos rajono",
    ],
    "Kauno": [
        "Birštono",
        "Jonavos rajono",
        "Kaišiadorių rajono",
        "Kauno miesto",
        "Kauno rajono",
        "Kėdainių rajono",
        "Prienų rajono",
        "Raseinių rajono",
    ],
    "Klaipėdos": [
        "Klaipėdos rajono",
        "Klaipėdos miesto",
        "Kretingos rajono",
        "Neringos",
        "Palangos miesto",
        "Skuodo rajono",
        "Šilutės rajono",
    ],
    "Baltijos priekrantė ir Kuršių marios": [
        "Klaipėdos rajono",
        "Klaipėdos miesto",
        "Neringos",
        "Palangos miesto",
        "Šilutės rajono",
    ],
    "Marijampolės": [
        "Kalvarijos",
        "Kazlų Rūdos",
        "Marijampolės",
        "Šakių rajono",
        "Vilkaviškio rajono",
    ],
    "Panevėžio": [
        "Biržų rajono",
        "Kupiškio rajono",
        "Panevėžio miesto",
        "Panevėžio rajono",
        "Pasvalio rajono",
        "Rokiškio rajono",
    ],
    "Šiaulių": [
        "Joniškio rajono",
        "Kelmės rajono",
        "Pakruojo rajono",
        "Akmenės rajono",
        "Radviliškio rajono",
        "Šiaulių miesto",
        "Šiaulių rajono",
    ],
    "Tauragės": ["Jurbarko rajono", "Pagėgių", "Šilalės rajono", "Tauragės rajono"],
    "Telšių": ["Mažeikių rajono", "Plungės rajono", "Rietavo", "Telšių rajono"],
    "Utenos": [
        "Anykščių rajono",
        "Ignalinos rajono",
        "Molėtų rajono",
        "Utenos rajono",
        "Visagino",
        "Zarasų rajono",
    ],
    "Vilniaus": [
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
        "Baltijos priekrantė ir Kuršių marios": [
            "Klaipėdos rajono",
            "Klaipėdos miesto",
            "Neringos",
            "Palangos miesto",
            "Šilutės rajono",
        ],
    }
)
