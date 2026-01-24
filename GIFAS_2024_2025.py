import pandas as pd
from pathlib import Path
import streamlit as st

BASE_DIR = Path(__file__).parent

# Lire UNE seule fois, avec un chemin robuste
dE = pd.read_excel(BASE_DIR / "Rheineck_Gifas.xlsx", usecols="A:B")

dE = pd.read_excel(
    BASE_DIR / "Rheineck_Gifas.xlsx",
    usecols="A:B"
)

print(dE.columns)

# Mettre la date en datetime puis en index
dE["Zeitstempel"] = pd.to_datetime(dE["Date"], errors="coerce")
dE = dE.set_index("Zeitstempel").sort_index()


# supprimer la colonne Date
dE = dE.drop(columns=["Date"])

year_2024 = int(dE.index.min().year)
year_2025 = year_2024 + 1

part1 = dE.loc[

    (dE.index >= f"{year_2025}-01-01") &
    (dE.index <= f"{year_2025}-08-31 23:45")
]

part2 = dE.loc[
    (dE.index >= f"{year_2024}-09-01") &
    (dE.index <= f"{year_2024}-12-31 23:45")
]

dE_norm = pd.concat([part1, part2])

# recréer un index basé sur 2024 (pas 2025)
new_index = pd.date_range(
    start="2024-01-01",
    periods=len(dE_norm),
    freq="15min"
)

dE_norm = dE_norm.copy()
dE_norm.index = new_index

somme = dE_norm.sum()
st.write(somme)


# Export du résultat (pas dE)
dE_norm.to_excel(BASE_DIR / "Gifas1.xlsx", index=True)

