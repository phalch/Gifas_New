# Fournit sur tableau PK.xlsx la valeur moyenne des quelques 30 mesures effectuées en 2012 par EKZ dans la commune de Wietikon (Profil_Pk.xls)

from pathlib import Path
import pandas as pd

base_dir = Path(__file__).resolve().parent
src = base_dir / "Profil_PK.xlsx"
dst = base_dir / "PK.xlsx"

# 1) Lecture
df = pd.read_excel(src)

# 2) Date-Time
datetime_col = df.columns[0]
dt = pd.to_datetime(df[datetime_col], errors="coerce")

# ✅ Forcer l'année à 2024 (méthode robuste)
dt = pd.to_datetime(df[datetime_col], errors="coerce")
year0 = int(dt.dt.year.iloc[0])          # ici 2012
dt = dt + pd.DateOffset(years=(2024 - year0))

# 3) Moyenne C..CW
moy = (
    df.iloc[:, 2:]
    .apply(pd.to_numeric, errors="coerce")
    .mean(axis=1, skipna=True)
)

# 4) Nouveau DataFrame
pk = pd.DataFrame({
    "Date-Time": dt,
    "Moyenne": moy
})

pk = pk.dropna(subset=["Date-Time"])

# 5) Export
pk.to_excel(dst, index=False)

print("Écrit :", dst)