
import streamlit as st
from datetime import time, timedelta, datetime
from pathlib import Path
from math import ceil

import hashlib
import numpy as np
import pandas as pd
from openpyxl import load_workbook
import matplotlib.pyplot as plt  # au cas où
import plotly.express as px
import plotly.graph_objects as go

from Panelverlust import dr, du, A  # comme dans ta page 02

from pathlib import Path
import hashlib
import streamlit as st

from pathlib import Path
import hashlib
import streamlit as st

# =========================
# ✅ VERSIONING PERSISTANT
# =========================

VERSION_FILE      = Path("version.txt")
SCRIPT_FILE       = Path(__file__)
HASH_FILE         = Path(".last_hash")
LAST_VERSION_FILE = Path(".last_version")  # ✅ nouveau

def normalize_version(v: str) -> str:
    v = (v or "").strip()
    if not v:
        return "V2.0"
    if not v.upper().startswith("V"):
        v = "V" + v
    body = v[1:]
    if "." not in body:
        return f"V{body}.0"          # ex: V3 -> V3.0
    major, minor = body.split(".", 1)
    if minor == "":
        minor = "0"
    return f"V{int(major)}.{int(minor)}"

# 1) init version si absent
if not VERSION_FILE.exists():
    VERSION_FILE.write_text("V2.0")

current_version = normalize_version(VERSION_FILE.read_text())

# 2) hash du script
current_hash = hashlib.sha256(SCRIPT_FILE.read_bytes()).hexdigest()
last_hash = HASH_FILE.read_text().strip() if HASH_FILE.exists() else ""

# 3) détecter changement manuel de version.txt → reset hash (pas d’incrément)
last_version_seen = LAST_VERSION_FILE.read_text().strip() if LAST_VERSION_FILE.exists() else ""
if last_version_seen != current_version:
    # ✅ tu as modifié V2 -> V3, ou V2.17 -> V3.0 etc.
    HASH_FILE.write_text(current_hash)          # reset: considérer le script "déjà pris en compte"
    LAST_VERSION_FILE.write_text(current_version)
    last_hash = current_hash                    # empêche un bump immédiat

# 4) éviter les bumps multiples dus aux reruns Streamlit
if "last_bumped_hash" not in st.session_state:
    st.session_state["last_bumped_hash"] = None

# 5) bump minor uniquement si le script a changé
if (current_hash != last_hash) and (st.session_state["last_bumped_hash"] != current_hash):
    major, minor = current_version.replace("V", "").split(".")
    new_version = f"V{int(major)}.{int(minor) + 1}"

    VERSION_FILE.write_text(new_version)
    HASH_FILE.write_text(current_hash)
    LAST_VERSION_FILE.write_text(new_version)

    current_version = new_version
    st.session_state["last_bumped_hash"] = current_hash

st.sidebar.markdown(f"### 🧾 Version : {current_version}")

# ========================= CONFIG GLOBALE =========================

st.set_page_config(
    page_title="Dashboard Überschuss Produzent – Abnehmer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ========================= STYLES =========================

def apply_global_style():
    st.markdown(
        """
        <style>
        html, body, [class*="css"]  {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
        }

        .main > div {
            max-width: 1200px;
            margin: 0 auto;
        }

        .big-title {
            font-size: 2.4rem;
            font-weight: 700;
            margin-bottom: 0.3rem;
        }

        .subtitle {
            color: #5f6368;
            font-size: 0.95rem;
            margin-bottom: 1.5rem;
        }

        .metric-card {
            padding: 0.9rem 1.1rem;
            border-radius: 0.9rem;
            border: 1px solid #e3e7ef;
            background: linear-gradient(135deg, #fafbff, #f3f4ff);
            box-shadow: 0 2px 6px rgba(15, 23, 42, 0.08);
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .metric-card .stMetric {
            text-align: center;
        }

        .metric-kwh {
            background: linear-gradient(135deg, #e8f2ff, #dbe9ff);
            border: 1px solid #c5d9ff;
            box-shadow: 0 2px 5px rgba(0, 64, 160, 0.15);
        }

        .metric-chf {
            background: linear-gradient(135deg, #e9fbe8, #d8f7d4);
            border: 1px solid #b7ecb0;
            box-shadow: 0 2px 5px rgba(0, 140, 40, 0.15);
        }

        div[data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
            font-weight: 600 !important;
        }

        div[data-testid="stMetricLabel"] {
            font-size: 0.7rem !important;
        }

        .stTabs [data-baseweb="tab"] {
            font-size: 1.1rem;
            font-weight: 600;
        }
        .stTabs [data-baseweb="tab"] p {
            font-size: 1.1rem;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

apply_global_style()

st.markdown('<div class="big-title">Dashboard Produzent – Abnehmer</div>', unsafe_allow_html=True)


# ========================= BASE DIR =========================

BASE_DIR = Path(__file__).resolve().parent

# ========================= FONCTIONS CACHÉES =========================

@st.cache_data
def load_verbrauch_kunden(base_dir: Path) -> pd.DataFrame:
    return pd.read_excel(base_dir / "Verbrauch_Kunden.xlsx", usecols="A:B")

@st.cache_data
def load_verbrauch_LEG(base_dir: Path) -> pd.DataFrame:
    df = pd.read_excel(base_dir / "PK.xlsx", usecols=["Date-Time", "Moyenne"])

    df["Date-Time"] = pd.to_datetime(df["Date-Time"], errors="coerce")
    df["Moyenne"] = pd.to_numeric(df["Moyenne"], errors="coerce")

    df = df.dropna(subset=["Date-Time"]).set_index("Date-Time")
    df = df.rename(columns={"Moyenne": "LEG"})

    return df.sort_index()

def load_verbrauch_LEG(base_dir: Path) -> pd.DataFrame:
    df = pd.read_excel(base_dir / "PK.xlsx", usecols=["Date-Time", "Moyenne"])

    df["Date-Time"] = pd.to_datetime(df["Date-Time"], errors="coerce")
    df["Moyenne"] = pd.to_numeric(df["Moyenne"], errors="coerce")

    df = df.dropna(subset=["Date-Time"]).set_index("Date-Time")
    df = df.rename(columns={"Moyenne": "LEG"})  

    return df.sort_index()

@st.cache_data
def load_ueberschuss_produzent(base_dir: Path) -> pd.DataFrame:
    dP = pd.read_excel(base_dir / "Gifas1.xlsx", usecols="A:B", index_col=0)
    dP.index = pd.to_datetime(dP.index, errors="coerce")
    dP.index.name = "dateTime"
    return dP

@st.cache_data
def load_tarif_table(base_dir: Path) -> pd.DataFrame:
    return pd.read_excel(base_dir / "Tarif.xlsx", sheet_name="Rheineck", usecols="B")

@st.cache_data
def load_tarif_workbook_values(base_dir: Path):
    wb_tarif = load_workbook(base_dir / "Tarif.xlsx")
    sheet_tarif = wb_tarif["Rheineck"]
    TZ1E  = sheet_tarif["H8"].value        
    TZ2E  = sheet_tarif["H9"].value
    TZ1H  = sheet_tarif["H10"].value
    TZ2H  = sheet_tarif["H11"].value
    TZ1EP = sheet_tarif["J8"].value
    TZ2EP = sheet_tarif["J9"].value
    TZ1HP = sheet_tarif["J10"].value
    TZ2HP = sheet_tarif["J11"].value
    DE1   = sheet_tarif["F17"].value
    DE2   = sheet_tarif["H17"].value
    DH11  = sheet_tarif["F18"].value
    DH12  = sheet_tarif["H18"].value
    DH21  = sheet_tarif["F19"].value
    DH22  = sheet_tarif["H19"].value

# Netztarif Standard(ohne Swissgrid)
    Tnetz      = sheet_tarif["J15"].value
# Netztarif
    Tnetzpro   = sheet_tarif["H15"].value
    Tabgabepro = sheet_tarif["H14"].value

    

    return TZ1E, TZ2E, TZ1H, TZ2H, TZ1EP, TZ2EP, TZ1HP, TZ2HP, DE1, DE2, DH11, DH12, DH21, DH22, Tnetz,Tnetzpro,Tabgabepro


# ========================= PARAMÈTRES DE BASE =========================


mo_default    = "März"
topic_default = "Produzent: Uberschuss"
pr            = -0.005                     # 0.5 % Leistungsverlust per annum
Jahr          = 1

dM = pd.DataFrame({
    "Label": [
        "Produzent: Uberschuss",
        "Energielieferung Rheineck an KMU (ohne Drittproduzent)",
        "Energielieferung Produzent an KMU",
        "Zusatzenergielieferung Rheineck an KMU",
        "Produzent: Restüberschuss nach Energie Lieferung an KMUs"
    ]
})

dM.columns = ["libelle"]
dM["abbrev"] = [
    "UG1",
    "kWh_EVU_KMU",
    "kWh_Produzent_KMU",
    "kWh_EVU_Produzent_KMU",
    "Rest_U",
]
dico = pd.Series(dM["abbrev"].values, index=dM["libelle"]).to_dict()

mois_liste = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
]
themes_liste = list(dico.keys())

# ========================= SIDEBAR – PARAMÈTRES COMMUNS =========================

st.sidebar.markdown("## ⚙️ Bruttodaten – erstes Jahr ")

# --- Paramètres techniques (Rohdaten) ---
with st.sidebar.expander("KMUs Energieverbrauch", expanded=True):

    mode_label = st.radio(
        "Modus",
        ["vZEV / EVG", "LEG"],
        index=0,
        horizontal=True,
        key="mode_label",
    )
    mode_leg = 1 if mode_label == "LEG" else 0  # 0/1

    if mode_leg == 0:
        # vZEV / EVG : un seul slider
        kp1 = st.slider(
            "Energieverbrauch KMU (MWh/a)",
            min_value=0.0,
            max_value=100.0,
            value=20.0,
            step=10.0,
            key="kp1",
        )
        # kp2 forcé à 0 (et stocké aussi dans session_state pour cohérence)
        st.session_state["kp2"] = 0.0
        kp2 = 0.0

    else:
        # LEG : deux sliders
        kp1 = st.slider(
            "Energieverbrauch KMU 40% LEG (MWh/a)",
            min_value=0.0,
            max_value=100.0,
            value=20.0,
            step=10.0,
            key="kp1",
        )
        kp2 = st.slider(
            "Energieverbrauch KMU 20% LEG (MWh/a)",
            min_value=0.0,
            max_value=100.0,
            value=20.0,
            step=10.0,
            key="kp2",
        )
    
# --- Tarife (Bruttodaten + 15 ans) ---
with st.sidebar.expander("💶 Tarifparameter – Jahr 1", expanded=True):
    tt = st.slider(
        "Ratio Tarif Pro Produzent/TB Rheineck",
        min_value=0.20,
        max_value=1.00,
        value=0.50,
        step=0.05,
        key="tt",
        help="0.50 = Produzent Tarif: 50% TB Rheineck Tarif"
    )

    tleg = st.slider(
        "Ratio Tarif Standard Produzent/TB Rheineck",
        min_value=0.20,
        max_value=1.00,
        value=0.50,
        step=0.05,
        key="tleg",
        help="0.50 = Produzent Tarif: 50% TB Rheineck Tarif"
    )

    VG = st.slider(
        "Vergütungstarif (Rp./kWh)",
        min_value=0.0,
        max_value=10.0,
        value=6.0,
        step=0.01,
        key="VG",
    )

# --- RLEG ---
with st.sidebar.expander("LEG Kunden", expanded=True):
    RLEG = st.slider(
        "Anzahl LEG Kunden",
        min_value=0,
        max_value=20,
        value=5,
        step=1,
        key="RLEG",
        help="10 = 10 LEG Kunden",
    )

# --- Thème ---
with st.sidebar.expander("Tagesprofil ", expanded=True):
    topic = st.selectbox(
        "Thema auswählen",
        themes_liste,
        index=themes_liste.index(topic_default) if topic_default in themes_liste else 0,
        key="topic_select",
    )

# --- Période & heure ---
with st.sidebar.expander("🕒 Auswertungszeitraum", expanded=True):
    mo = st.selectbox(
        "Monat auswählen",
        mois_liste,
        index=mois_liste.index(mo_default) if mo_default in mois_liste else 0,
        key="mois_select",
    )

    heure_debut, heure_fin = st.slider(
        "Stunden auswählen",
        min_value=0,
        max_value=23,
        value=(5, 20),
        step=1,
        key="heure_range",
    )

if heure_debut > heure_fin:
    heure_debut, heure_fin = heure_fin, heure_debut

H1 = f"{int(heure_debut):02d}:00"
H2 = f"{int(heure_fin):02d}:00"


abbr = dico.get(topic, "Abréviation inconnue")
if abbr == "Abréviation inconnue":
    st.sidebar.warning("Abréviation inconnue pour ce thème.\nVérifiez le fichier Excel.")

# ========================= PARAMÈTRES SUPPL. – SIMULATION 15 ANS =========================
st.sidebar.markdown("### 💰 Wirtschaftliche Simulation - 10Jahre + ")

Pp             = 0.0              # Power Peak
PK             = 3_000            # Projektkosten bestehend aus Kundenprojekt und Infrastrukturprojekt
PVrealisierung = 0.0              # Kosten des Infrastrukturprojektes (zum Beispiel Offerteanfrage für PV)
ES_default     = 0.20
Sa_default     = 0.20
Un_rate        = 3 / 1000         # Panelverlust
N_YEARS        = 15



with st.sidebar.expander("Annuitäten", expanded=True):
   

    # --- Valeur par défaut basée sur Pp ---
    IK_default_sim = int(0)

    # --- Initialisation ---
    if "IK_sim" not in st.session_state:
        st.session_state["IK_sim"] = IK_default_sim

    # --- Synchronisation automatique ---
    if st.session_state["IK_sim"] != IK_default_sim:
        st.session_state["IK_sim"] = IK_default_sim

    # --- NUMBER INPUT IK ---
    IK_sim = st.number_input(
    "Investition ",
    min_value=0,
    max_value=200_000,
    step=5_000,
    key="IK_sim",
    format="%d"
    )
    st.caption('Als Standardwert wird eine Investition von 1’000 CHF/kWp angenommen')

    P_sim = st.slider(
        "Abschreibungsdauer (Jahre)",
        min_value=5,
        max_value=25,
        value=10,
        step=1,
        key="P_sim",
    )
    z_sim = st.slider(
        "Zinssatz (%)",
        min_value=0.0,
        max_value=5.0,
        value=1.0,
        step=0.25,
        key="z_sim",
    )

with st.sidebar.expander("Tarife & Kosten (15 Jahre)", expanded=True):
    
    tevu_sim = st.slider(
        "Tarifentwicklung TB Rheineck  p.a.",
        min_value=0.0,
        max_value=0.05,
        value=0.02,
        step=0.005,
        key="tevu_sim",
    )

    st.caption("Betriebskosten: 2 Rp./kWh bei Verkauf an Dritte (nicht parametrierbar)")
    tbet_sim = 0.02

    st.caption("Jährlicher PV Verlust: fix 0.5 % (nicht parametrierbar)")
    pr_sim = -0.005

    st.caption("Steuersatz: 20 % (nicht parametrierbar)")

# conversions
SV_sim = 322 * Pp            # SV  Subvention (berechnet nach Promovo)
r_sim  = z_sim / 100.0
tgra_change = tevu_sim
tleg_change = tevu_sim

st.sidebar.markdown("---")


#======================================
#        LADEN ROHDATEN – Erstes Jahr 
#======================================


# --- KMU ---

dE                    = load_verbrauch_kunden(BASE_DIR)
dE["Zeitstempel"]     = pd.to_datetime(dE["Zeitstempel"], errors="coerce")
dE["Wert [kWh]"]      = pd.to_numeric(dE["Wert"], errors="coerce")
dE                    = dE.rename(columns={"Wert": "kWh_EVU_KMU", "Zeitstempel": "dateTime"})
dE.set_index("dateTime", inplace=True)


dE_h                  = dE.resample("h").agg({"kWh_EVU_KMU": lambda x: x.sum() * 1})
dE_h                  = dE_h[dE_h.index < pd.to_datetime("2025-1-1 00:00")]
EVUEKW                = round(dE_h["kWh_EVU_KMU"].sum(), 0)
dE_h["kWh_EVU_KMU"]   = dE_h["kWh_EVU_KMU"] / EVUEKW

# ---- LEG Kunden ---

df                     = load_verbrauch_LEG (BASE_DIR)
df                     = df.resample("h").agg({"LEG": lambda x: x.sum() * 1})      
dE_h["kWh_LEG"]        = (df["LEG"].reindex(dE_h.index).fillna(0))

# --- Produzent ---

dP                       = load_ueberschuss_produzent(BASE_DIR)
dP                       = dP.resample("h").agg({"Ueberschuss": lambda x: x.sum() * 1})      
dE_h["kWh_EV Produzent"] = (dP["Ueberschuss"].reindex(dE_h.index).fillna(0))


# --- Tarife EVU / Produzent / Privat / LEG ---

dates = pd.date_range(start="2024-01-01 00:00", periods=168, freq="h")
dt_tarif = load_tarif_table(BASE_DIR)

end_date   = "2024-12-31 23:00"
total_hours = int((pd.to_datetime(end_date) - dates[0]).total_seconds() / 3600) + 1

dt_tarif = pd.concat([dt_tarif] * ((total_hours + 164) // len(dt_tarif)), ignore_index=True)
dt_tarif = dt_tarif.iloc[:total_hours]
timeframe = pd.date_range(start="2024-01-01 00:00", end="2024-12-31 23:00", freq="h")
dt_tarif.insert(0, "timeframe", timeframe)
dt_tarif = dt_tarif.dropna(subset=["timeframe"]).sort_values("timeframe").set_index("timeframe")

(
    TZ1E, TZ2E, TZ1H, TZ2H, TZ1EP, TZ2EP, TZ1HP, TZ2HP,
    DE1, DE2, DH11, DH12, DH21, DH22, Tnetz,Tnetzpro,Tabgabepro
) = load_tarif_workbook_values(BASE_DIR)

# EVU Pro
dt_tarif.loc[(dt_tarif.index >= DE1) & (dt_tarif.index <= DE2) & (dt_tarif["Tarif"] == '"TZ2"'), "Tarif"] = TZ2E
dt_tarif.loc[(dt_tarif.index >= DE1) & (dt_tarif.index <= DE2) & (dt_tarif["Tarif"] == '"TZ1"'), "Tarif"] = TZ1E
dt_tarif.loc[(dt_tarif.index >= DH11) & (dt_tarif.index <= DH12) & (dt_tarif["Tarif"] == '"TZ2"'), "Tarif"] = TZ2H
dt_tarif.loc[(dt_tarif.index >= DH11) & (dt_tarif.index <= DH12) & (dt_tarif["Tarif"] == '"TZ1"'), "Tarif"] = TZ1H
dt_tarif.loc[(dt_tarif.index >= DH21) & (dt_tarif.index <= DH22) & (dt_tarif["Tarif"] == '"TZ2"'), "Tarif"] = TZ2H
dt_tarif.loc[(dt_tarif.index >= DH21) & (dt_tarif.index <= DH22) & (dt_tarif["Tarif"] == '"TZ1"'), "Tarif"] = TZ1H

dE_h["Tarif CHF"] = pd.to_numeric(
    dt_tarif["Tarif"].reindex(dE_h.index),
    errors="coerce"
)
dt_base = dt_tarif.copy()

# Tarif Produzent Pro
TZ1EG = tt * TZ1E
TZ2EG = tt * TZ2E
TZ1HG = tt * TZ1H
TZ2HG = tt * TZ2H

dt_G = dt_base.copy()
dt_G.loc[(dt_G.index >= DE1) & (dt_G.index <= DE2) & (dt_G["Tarif"] == TZ2E), "Tarif"]   = TZ2EG
dt_G.loc[(dt_G.index >= DE1) & (dt_G.index <= DE2) & (dt_G["Tarif"] == TZ1E), "Tarif"]   = TZ1EG
dt_G.loc[(dt_G.index >= DH11) & (dt_G.index <= DH12) & (dt_G["Tarif"] == TZ2H), "Tarif"] = TZ2HG
dt_G.loc[(dt_G.index >= DH11) & (dt_G.index <= DH12) & (dt_G["Tarif"] == TZ1H), "Tarif"] = TZ1HG
dt_G.loc[(dt_G.index >= DH21) & (dt_G.index <= DH22) & (dt_G["Tarif"] == TZ2H), "Tarif"] = TZ2HG
dt_G.loc[(dt_G.index >= DH21) & (dt_G.index <= DH22) & (dt_G["Tarif"] == TZ1H), "Tarif"] = TZ1HG

dE_h["Tarif CHF_G"] = pd.to_numeric(
    dt_G["Tarif"].reindex(dE_h.index),
    errors="coerce"
)

# Tarif EVU Privat
# Netz Tarif
dt_P = dt_base.copy()
dt_P.loc[(dt_P.index >= DE1) & (dt_P.index <= DE2) & (dt_P["Tarif"] == TZ2E), "Tarif"] = TZ2EP
dt_P.loc[(dt_P.index >= DE1) & (dt_P.index <= DE2) & (dt_P["Tarif"] == TZ1E), "Tarif"] = TZ1EP
dt_P.loc[(dt_P.index >= DH11) & (dt_P.index <= DH12) & (dt_P["Tarif"] == TZ2H), "Tarif"] = TZ2HP
dt_P.loc[(dt_P.index >= DH11) & (dt_P.index <= DH12) & (dt_P["Tarif"] == TZ1H), "Tarif"] = TZ1HP
dt_P.loc[(dt_P.index >= DH21) & (dt_P.index <= DH22) & (dt_P["Tarif"] == TZ2H), "Tarif"] = TZ2HP
dt_P.loc[(dt_P.index >= DH21) & (dt_P.index <= DH22) & (dt_P["Tarif"] == TZ1H), "Tarif"] = TZ1HP

dE_h["Tarif CH_P"] = pd.to_numeric(dt_P["Tarif"].reindex(dE_h.index),errors="coerce")


# Tarif Produzent Standard
dE_h["Tarif LEG"] = tleg * dE_h["Tarif CH_P"]

#=============================================
#  ERGEBNISSE DES ERSTEN BETRIEBSJAHRES
#=============================================

# Die Solarenergieerzeugung der Photovoltaikmodule kann x Jahre nach der Inbetriebnahme geschätzt werden (verlust pr per annum)
# Die daraus abgeleiteten Variablen werden entsprechend angepasst.
JahrX = 1

# EVUECHF: Rechnung EVU an KMU ohne Stromlieferung von Produzent
dE_h["kWh_EVU_KMU"]  = 1000*(kp1+kp2)*(dE_h["kWh_EVU_KMU"])
dE_h["CHF_EVU_KMU"]  = dE_h["kWh_EVU_KMU"] * dE_h["Tarif CHF"]
EVUEKWH              = round(dE_h["kWh_EVU_KMU"].sum(),0)    
EVUECHF              = round(dE_h["CHF_EVU_KMU"].sum(), 0)

# UG1: Überschuss Produzent und Vergütung EVUPCH
dE_h["kWh_EV Produzent"]= 200000/281473 * dE_h["kWh_EV Produzent"]
dE_h["UG1"]             = dE_h["kWh_EV Produzent"]         # Grobe Schätzuzng vom Überschutz basierend auf PV Produktion
monthly_sum_UG1         = dE_h["UG1"].resample("ME").sum()
UG                      = round(dE_h["UG1"].sum(), 0)
dE_h["EVUPCH"]          = dE_h["kWh_EV Produzent"]*VG/100
EVUPCH                  = round(dE_h["EVUPCH"].sum(),0)

# Rest_U: Restüberschuss nach Lieferung Produzent → KMU
dE_h["Rest_U"]     = (dE_h["UG1"] - dE_h["kWh_EVU_KMU"]).clip(lower=0)
monthly_sum_RestU  = dE_h["Rest_U"].resample("ME").sum()
RestU              = round(dE_h["Rest_U"].sum(), 0)


# GE: Energielieferung Produzent → KMU (kWh)
dE_h["kWh_Produzent_KMU"] = dE_h["UG1"] - dE_h["Rest_U"]
monthly_sum_GE            = dE_h["kWh_Produzent_KMU"].resample("ME").sum()
GE                        = round(dE_h["kWh_Produzent_KMU"].sum(), 0)

# G1: Rechnung  Produzent → KMU 
dE_h["GewinnProduzent"]     = dE_h["kWh_Produzent_KMU"] * dE_h["Tarif CHF_G"]
monthly_sum_P1              = dE_h["GewinnProduzent"].resample("ME").sum()
G1                          = round(dE_h["GewinnProduzent"].sum(), 0)

# G11: Rechnung EVU für KMU LEG 40%
G11  =mode_leg*kp1/(kp1+kp2)*GE * (0.6*Tnetzpro + Tabgabepro)

# G111 Total Rechnung an KMU LEG 40%
G111 =kp1/(kp1+kp2)*G1 + G11

# G12 Rechnung EVU für KMU 20%
G12  =mode_leg*kp2/(kp1+kp2)*GE * (0.8*Tnetzpro + Tabgabepro)

# G112 Total Rechnung an KMU 20%
G112 =kp2/(kp1+kp2)*G1 + G12


# GEPK: Energie Lieferung Produzent an LEG Kunden
dE_h["V_U"]                 = (dE_h["Rest_U"] - RLEG*dE_h["kWh_LEG"]).clip(lower=0)   # RLEG : Anzahl LEG Kunden
dE_h["Produzent_kWh_LEG"]   = dE_h["Rest_U"]-dE_h["V_U"] 
ULEG                        = round(dE_h["Produzent_kWh_LEG"].sum(),0)                     

# G2: Rechnung Produzent  Standard Kunden
dE_h["CHF_LEG"]             = dE_h["Produzent_kWh_LEG"] * dE_h["Tarif LEG"]
G2                          = round(dE_h["CHF_LEG"].sum(), 0)

# G3 Vergütung Verbeibender Überschuss 
Ver_U                       = round(dE_h["V_U"].sum(), 0)
G3                          = round(Ver_U * VG / 100, 0)

# EVUGE: EVU Energie Lieferung an KMU als Ergänzung zur Produzent Energie Lieferung
dE_h["kWh_EVU_Produzent_KMU"]  = dE_h["kWh_EVU_KMU"] - dE_h["kWh_Produzent_KMU"]
monthly_sum_EVUGE              = dE_h["kWh_EVU_Produzent_KMU"].resample("ME").sum()
EVUGE                          = round(dE_h["kWh_EVU_Produzent_KMU"].sum(), 0)

# EVUGECH: EVU Rechung an KMU als Ergänzung zur Energielieferung Drittproduzent
dE_h["CHF-EVU-Produzent_KMU"] = dE_h["kWh_EVU_Produzent_KMU"] * dE_h["Tarif CHF"]
EVUGECH                       = round(dE_h["CHF-EVU-Produzent_KMU"].sum(), 0)

# Gewinn
GewinnE = EVUECHF - EVUGECH - G111 - G112          # Gewinn KMU
GewinnG = G1 + G2 + G3 - EVUPCH                    # Gewinn Produzent


# ------------------------------- LEG --------------------


# Tarifgrenze Standard vEVG, LEG 40%(2), LEG 20% Rabatte (3)
lg0     = round(TZ1EP*Tnetz*tt,2)                 # vZEV oder vEVG
lg1     = round((TZ1EP-(60/100)*Tnetz)*tt,2)      # LEG 40% Rabatte
lg2     = round ((TZ1EP-(80/100)*Tnetz)*tt,2)     # LEG 20% Rabatte

# tleg max
tleg0max=1.0
tleg1max=1.0-0.6*Tnetz/TZ1EP
tleg2max=1.0-0.8*Tnetz/TZ1EP

# Gewin in % Standard LEG Kunden  

Gewinnleg0 = round(TZ1EP * (1.0 - tleg),2)
Gewinnleg0 = Gewinnleg0 if Gewinnleg0 >= 0 else np.nan

Gewinnleg1 = round(Gewinnleg0 - 0.6 * Tnetz,2)
Gewinnleg1 = Gewinnleg1 if Gewinnleg1 >= 0 else np.nan

Gewinnleg2   = round(Gewinnleg0 - 0.8 * Tnetz,2)   
Gewinnleg2   = Gewinnleg2 if Gewinnleg2 >= 0 else np.nan
GewinnPrivat = round(TZ1EP-VG/100-0.8*Tnetz,2)


#=================================================================================
#                        FUNKTIONSANALYSE BRUTTODATEN (erstes Betriebsjahr)
#=================================================================================

def run_analysis(mo: str, topic: str, abbr: str, H1: str, H2: str):
    if abbr not in dE_h.columns:
        st.error(f"❌ La colonne '{abbr}' n'existe pas dans les données. Choisissez un autre thème.")
        return None, None, None

    mois_map = {
        "Januar": 1, "Februar": 2, "März": 3, "April": 4,
        "Mai": 5, "Juni": 6, "Juli": 7, "August": 8,
        "September": 9, "Oktober": 10, "November": 11, "Dezember": 12
    }

    dE_h["month"] = dE_h.index.month
    dE_hs = {i: dE_h[dE_h["month"] == i] for i in range(1, 13)}

    i = mois_map[mo]

    weekdays = dE_hs[i][dE_hs[i].index.dayofweek < 5]
    weekends = dE_hs[i][dE_hs[i].index.dayofweek >= 5]

    if weekdays.empty and weekends.empty:
        st.error("❌ Pas de données pour le mois sélectionné.")
        return None, None, None

    df_filtered1 = weekdays[abbr].between_time(H1, H2) if not weekdays.empty else pd.Series(dtype=float)
    df_filtered2 = weekends[abbr].between_time(H1, H2) if not weekends.empty else pd.Series(dtype=float)

    if df_filtered1.empty and df_filtered2.empty:
        st.error("❌ Pas de données dans la plage horaire sélectionnée.")
        return None, None, None

    hourly_avg1 = df_filtered1.groupby(df_filtered1.index.hour).mean()
    hourly_avg2 = df_filtered2.groupby(df_filtered2.index.hour).mean()

    all_hours = sorted(set(hourly_avg1.index.tolist()) | set(hourly_avg2.index.tolist()))
    hourly_avg1 = hourly_avg1.reindex(all_hours)
    hourly_avg2 = hourly_avg2.reindex(all_hours)

    heures_reelles = np.array(all_hours, dtype=int)

    df_plot1 = pd.DataFrame({
        "Heure": np.concatenate([heures_reelles, heures_reelles]),
        "Valeur": np.concatenate([
            hourly_avg1.values.astype(float),
            hourly_avg2.values.astype(float)
        ]),
        "Type": (["Weekdays"] * len(heures_reelles)) + (["Weekends"] * len(heures_reelles)),
    })
    
    fig1 = px.bar(
        df_plot1,
        x="Heure",
        y="Valeur",
        color="Type",
        barmode="group",
        labels={"Heure": "Stunden", "Valeur": "kWh"},
        title=f"{topic} – Tagesprofil ({mo}) [{H1}–{H2}]"
    )
    fig1.update_layout(
        xaxis=dict(dtick=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=16)),
        margin=dict(t=60, b=40, l=40, r=10),
        title_font=dict(size=20),
    )

    x_labels = np.array([
        "Januar", "Februar", "März", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Dezember"
    ])
    y1m = np.array(monthly_sum_UG1.values)
    y2m = np.array(monthly_sum_RestU.values)

    df_plot2 = pd.DataFrame({
        "Monat": np.concatenate([x_labels, x_labels]),
        "kWh": np.concatenate([y1m, y2m]),
        "Typ": (["Vorlieferung "] * len(x_labels)) + (["Nachlieferung"] * len(x_labels)),
    })

    fig2 = px.bar(
        df_plot2,
        x="Monat",
        y="kWh",
        color="Typ",
        barmode="group",
        labels={"Monat": "Monat", "kWh": "Monatliche Leistung (kWh)"},
        title="Überschuss Produzent:  Vor- und Nachlieferung an KMUs "
    )
    fig2.update_layout(
        xaxis=dict(dtick=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=16)),
        margin=dict(t=60, b=40, l=40, r=10),
        title_font=dict(size=20),
    )

    y3m = np.array(monthly_sum_GE.values)
    y4m = np.array(monthly_sum_EVUGE.values)

    df_plot3 = pd.DataFrame({
        "Monat": np.concatenate([x_labels, x_labels]),
        "kWh": np.concatenate([y3m, y4m]),
        "Quelle": (["Produzent (Solar)"] * len(x_labels)) + (["EVU"] * len(x_labels)),
    })

    fig3 = px.bar(
        df_plot3,
        x="Monat",
        y="kWh",
        color="Quelle",
        barmode="group",
        labels={"Monat": "Monat", "kWh": "Monatliche Leistung (kWh)"},
        title="Energie Verbrauch KMU: Lieferung Produzent & Lieferung EVU"
    )
    fig3.update_layout(
        xaxis=dict(dtick=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=16)),
        margin=dict(t=60, b=40, l=40, r=10),
        title_font=dict(size=20),
    )

    return fig1, fig2, fig3


#=================================================================================
#                   FONCTION DE PROJECTION 15 ANS
#=================================================================================

def compute_projection(
    val_EVUECHF, val_EVUPCH,
    IK,kp1,kp2, P, z, r, ES, Sa, SV,
    PK, Un_rate, tevu, tgra, tleg, tbet, pr,
    N_YEARS, VG, val_EVUGECH,
    val_G1, val_G2, val_G3, val_GE,
):

    Jahre = range(1, N_YEARS + 1)
    df = pd.DataFrame(index=Jahre)
    df.index.name = "Jahr"
   
    # ✅ Construction des coefficients a, b, c dans dr
    
    for col in du.columns:
        y = du[col].values.astype(float)
        a, b, c = np.linalg.solve(A, y)
        dr.loc["a", col] = a
        dr.loc["b", col] = b
        dr.loc["c", col] = c
   
    # ✅ Fonction sécurisée d'évaluation
   
    def y_for_x(dr_local, col_name, x_val):

        if col_name not in dr_local.columns:
            raise ValueError(f"❌ Colonne inexistante dans dr : {col_name}")

        if not all(k in dr_local.index for k in ["a", "b", "c"]):
            raise ValueError("❌ dr doit contenir les lignes 'a', 'b', 'c'")

        a = float(dr_local.loc["a", col_name])
        b = float(dr_local.loc["b", col_name])
        c = float(dr_local.loc["c", col_name])

        return a * x_val**2 + b * x_val + c
 
    # ✅ NORMALISATION DES GRANDEURS
 
    # --- EVUECHF ---
    PW_EVUECHF = [val_EVUECHF * ((1 + tevu) ** (jahr - 1)) for jahr in Jahre]

    # --- G1 ---
    G1_ref = y_for_x(dr, "G1", 1)
    scale_G1 = val_G1 / G1_ref if G1_ref != 0 else 0

    PW_G1 = [
        scale_G1 * y_for_x(dr, "G1", jahr) * ((1 + tgra) ** (jahr - 1))
        for jahr in Jahre
    ]

    # --- G2 ---
    G2_ref = y_for_x(dr, "G2", 1)
    scale_G2 = val_G2 / G2_ref if G2_ref != 0 else 0

    PW_G2 = [
        scale_G2 * y_for_x(dr, "G2", jahr) * ((1 + tleg) ** (jahr - 1))
        for jahr in Jahre
    ]

    # --- G3 ---
    G3_ref = y_for_x(dr, "G3", 1)
    scale_G3 = val_G3 / G3_ref if G3_ref != 0 else 0

    PW_G3 = [
        scale_G3 * y_for_x(dr, "G3", jahr)
        for jahr in Jahre
    ]

    # --- EVUGECH ---
    EVUGECH_ref = y_for_x(dr, "EVUGECH", 1)
    scale_EVUGECH = val_EVUGECH / EVUGECH_ref if EVUGECH_ref != 0 else 0

    PW_EVUGECH = [
        scale_EVUGECH * y_for_x(dr, "EVUGECH", jahr) * ((1 + tevu) ** (jahr - 1))
        for jahr in Jahre
    ]

    # --- GE 
    GE_ref = y_for_x(dr, "GE", 1)
    scale_GE = val_GE / GE_ref if GE_ref != 0 else 0

    PW_GE = [
        scale_GE * y_for_x(dr, "GE", jahr)
        for jahr in Jahre
    ]

    # --- RestU
    #ULEG_ref = y_for_x(dr, "RestU", 1)
    #scale_RestU = val_RestU/ RestU_ref if RestU_ref != 0 else 0

    #PW_RestU = [
    #    scale_RestU * y_for_x(dr, "RestU", jahr)
    #    for jahr in Jahre
    #]

    #---- EVUCHP
    PW_EVUPCH = [val_EVUPCH*(1+pr)**jahr for jahr in Jahre]

    # ✅ Construction du DataFrame
 
    df["EVUECHF"]  = PW_EVUECHF
    df["EVUGECH"]  = PW_EVUGECH
    df["G1"]       = PW_G1
    df["G2"]       = PW_G2
    df["G3"]       = PW_G3
    df["GE"]       = PW_GE
    #df["RestU"]    = PW_RestU
    df["EVUPCH"]   = PW_EVUPCH

    df = df.round(0).reset_index()
 
    # ✅ Résultats économiques
 
    df["UmsatzG"]     = df["G1"] + df["G2"] + df["G3"]

    df["Cash in"]     = df["G1"] + df["G2"] + df["G3"]

    # ✅ Tableau d’amortissement

    def tableau_amortissement(C, P, r):
        capital = C
        amort_base = C / P
        data = []

        for jahr in range(1, P + 1):
            zins = capital * r
            ann = amort_base + zins
            capital -= amort_base
            data.append([jahr, capital, zins, ann])

        dc = pd.DataFrame(data, columns=["Jahr", "Kapital_rest", "Zins", "Annuität"])
        return dc

    dc = tableau_amortissement(IK + PK - SV, P, r).round(0)

    df = df.merge(dc[["Jahr", "Annuität", "Zins", "Kapital_rest"]],
                  on="Jahr", how="left")

    df["Annuität"] = df["Annuität"].fillna(0)
    df["Zins"]     = df["Zins"].fillna(0)

    # ✅ Charges, impôts, profits

    df["Betrieb"]   = (df["GE"] + ULEG)*tbet


    df["Kosten"]    = df["Annuität"] + df["Betrieb"]
   

    # Delta Steuer 
    df["Steuer"]    = ((df["Cash in"] - df["Zins"] - df["Betrieb"] - df["EVUPCH"]) * Sa).clip(lower=0)


    # Produzent
    df["Profit_Produzent"]      = df["UmsatzG"] - df["Kosten"] - df["Steuer"] - df["EVUPCH"]
   

    df["Cumulate_Produzent"]    = df["Profit_Produzent"].cumsum()

    # KMU
    df["G1"]                    = df["G1"]+ df["GE"]*mode_leg*((kp1/(kp2+kp1)*(0.6*Tnetzpro+Tabgabepro)+ kp2/(kp1+kp2)*(0.8*Tnetzpro+Tabgabepro)))
    df["Profit_KMU"]            = df["EVUECHF"] - df["EVUGECH"] - df["G1"]
    df["Cumulate_KMU"]          = df["Profit_KMU"].cumsum()
   

    return df

# ========================= CALCUL SIMULATION 15 ANS =========================

df_15 = compute_projection(
    val_EVUECHF=EVUECHF,
    val_EVUGECH=EVUGECH,
    val_EVUPCH=EVUPCH,


    IK=IK_sim,
    P=P_sim,
    z=z_sim,
    r=r_sim,
    ES=ES_default,
    Sa=Sa_default,
    SV=SV_sim,

    kp1=kp1,
    kp2=kp2,
    PK=PK,
    Un_rate=Un_rate,

    tevu=tevu_sim,
    tgra=tgra_change,
    tleg=tleg_change,
    tbet=tbet_sim,
    pr=pr_sim,

    N_YEARS=N_YEARS,
    VG=VG,

    val_GE=GE,
    val_G1=G1,
    val_G2=G2,
    val_G3=G3,
)

df_10 = df_15[df_15["Jahr"] <= 10].copy()

if len(df_10) > 0:
    kpi_grab_10     = df_10["Cumulate_Produzent"].iloc[-1]
    kpi_grab_15     = df_15["Cumulate_Produzent"].iloc[-1]
    kpi_eugster_10  = df_10["Cumulate_KMU"].iloc[-1]
else:
    kpi_grab_10 = kpi_grab_15 = kpi_eugster_10 = np.nan

if not np.isnan(kpi_grab_10) and IK_sim > 0:
    kpi_rendite_10 = (1 + kpi_grab_10 / (IK_sim + PK)) ** (1/10) - 1
else: 
    kpi_rendite_10 = np.nan

if not np.isnan(kpi_grab_15) and IK_sim > 0:
    kpi_rendite_15 = (1 + kpi_grab_15 / (IK_sim + PK)) ** (1/15) - 1
else:
    kpi_rendite_15 = np.nan


# ========================= LAYOUT AVEC ONGLET BRUTTODATEN / 15 ANS =========================

tab_roh = st.tabs([
    "📊 Wirtschaftlichkeitsrechnung",
])[0]

# ---------- ONGLET BRUTTODATEN ----------
with tab_roh:
    fig1, fig2, fig3 = run_analysis(mo, topic, abbr, H1, H2)

    if fig1 is not None:
        st.markdown("### erstes Betriebsjahr")

        indic1 = GE
        indic2 = UG
        indic3 = EVUEKWH
        indic4 = GewinnE
        indic5 = GewinnG
        indic6 = ULEG

        colp1, colp2, colp3, colp4, colp5, colp6 = st.columns(6)

        with colp1:
            st.markdown('<div class="metric-card metric-kwh">', unsafe_allow_html=True)
            st.metric("Überschuss Gifas", f"{indic2:,.0f} kWh".replace(",", "’"))
            st.markdown('</div>', unsafe_allow_html=True)

        with colp2:
            st.markdown('<div class="metric-card metric-kwh">', unsafe_allow_html=True)
            st.metric("Verbrauch KMUs", f"{indic3:,.0f}".replace(",", "’") + " kWh")
            st.markdown('</div>', unsafe_allow_html=True)

        with colp3:
            st.markdown('<div class="metric-card metric-kwh">', unsafe_allow_html=True)
            st.metric("Lieferung Gifas an KMUs", f"{indic1:,.0f} kWh".replace(",", "’"))
            st.markdown('</div>', unsafe_allow_html=True)


        with colp4:   # ⬅️ CHANGÉ ICI
            st.markdown('<div class="metric-card metric-kwh">', unsafe_allow_html=True)
            st.metric("Lieferung Gifas an Privatkunden", f"{indic6:,.0f} kWh".replace(",", "’"))
            st.markdown('</div>', unsafe_allow_html=True)

        with colp5:
            st.markdown('<div class="metric-card metric-chf">', unsafe_allow_html=True)
            st.metric("Nettogewinn KMU", f"{indic4:,.0f} CHF".replace(",", "’"))
            st.markdown('</div>', unsafe_allow_html=True)

        with colp6:
            st.markdown('<div class="metric-card metric-chf">', unsafe_allow_html=True)
            st.metric("Bruttogewinn Gifas", f"{indic5:,.0f} CHF".replace(",", "’"))
            st.markdown('</div>', unsafe_allow_html=True)

        subtab1, subtab2, subtab3, subtab4, subtab5 = st.tabs([
                "📈 Tagesprofil",
                "📊 Überschuss (monatlich)",
                "⚡  Stromverbrauch KMU(monatlich)",
                "📑 Jahresergebnis",
                "👤 Privatkunden",
        ])

        with subtab1:
            st.plotly_chart(fig1, use_container_width=True)

        with subtab2:
            st.plotly_chart(fig2, use_container_width=True)

        with subtab3:
            st.plotly_chart(fig3, use_container_width=True)

        st.markdown("---")
        st.markdown("### 10-Jahres-kumulierter Ertrag")

        c1, c2 = st.columns(2)

        with c1:
            st.markdown('<div class="metric-card metric-chf">', unsafe_allow_html=True)
            st.metric("Kumul. Ertrag KMU (10 J.)",
                    f"{kpi_eugster_10:,.0f} CHF".replace(",", "’") if not np.isnan(kpi_eugster_10) else "n/a")
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="metric-card metric-chf">', unsafe_allow_html=True)
            st.metric("Kumul. Ertrag Produzent (10 J.)",
                    f"{kpi_grab_10:,.0f} CHF".replace(",", "’") if not np.isnan(kpi_grab_10) else "n/a")
            st.markdown("</div>", unsafe_allow_html=True)

        # --- Tableaux économiques 
        with subtab4:
            t1 = [
                ["Struktur", "TB Rheineck Pro (CHF/kWh)", "Produzent Pro (CHF/kWh)", "TB Rheineck Standard (CHF/kWh)", "Produzent Standard (CHF/kWh)"],
                ["Tarifzeit 1 Sommer",  TZ1E,  TZ1EG,  TZ1EP, tleg * TZ1EP],
                ["Tarifzeit 2 Sommer",  TZ2E,  TZ2EG, TZ2EP, tleg * TZ2EP],
                ["Tarifzeit 1 Winter",  TZ1H,  TZ1HG, TZ1HP, tleg * TZ2HP],
                ["Tarifzeit 2 Winter",  TZ2H,  TZ2HG, TZ2HP, tleg * TZ2HP],
                ["Vergütung",           VG/100, np.nan, np.nan, np.nan],
            ]

            t2 = [
                ["Lieferung", "Betrag CHF"],
                ["EVU ohne Produzent_Solar", EVUECHF],
                ["EVU mit Produzent_Solar", EVUGECH],
                ["Produzent_Solar", G1],
                ["Total mit Produzent_Solar", EVUGECH + G1],
                ["Gewinn", EVUECHF - EVUGECH - G1],
            ]

            t3 = [
                ["Lieferung", "Betrag CHF"],
                ["Vergütung EVU", EVUPCH],
                ["Verkauf an KMU", G1],
                ["Vergütung EVU", G2 + G3],
                ["Gewinn", G1 + G2 + G3],
            ]

            style_header = [
                {
                    "selector": "th",
                    "props": [
                        ("background-color", "#f0f0f0"),
                        ("font-weight", "bold"),
                        ("text-align", "center"),
                        ("padding", "6px 8px"),
                        ("white-space", "nowrap"),
                    ],
                },
                {"selector": ".row_heading", "props": [("display", "none")]},
                {"selector": ".blank", "props": [("display", "none")]},
            ]

            common_cell_style = {
                "text-align": "left",
                "padding": "4px 8px",
                "border": "1px solid #ddd",
            }

            st.subheader("Tarif Struktur")
            st.markdown(
                f"**Pro Produzent/ TB Rheineck : {tt:.2f}** &nbsp;&nbsp;&nbsp; "
                f"**Standard Produzent/TB Rheineck: {tleg:.2f}**"
            )

            df_t1 = pd.DataFrame(t1[1:], columns=t1[0])
            df_t1_styled = (
                df_t1.style
                .set_table_styles(style_header)
                .set_properties(**common_cell_style)
                .format(
                    subset=[
                        "TB Rheineck Pro (CHF/kWh)",
                        "Produzent Pro (CHF/kWh)",
                        "TB Rheineck Standard (CHF/kWh)",
                        "Produzent Standard (CHF/kWh)"
                    ],
                    formatter="{:,.3f}".format,
                    na_rep=""
                )
            )
            st.table(df_t1_styled)

            st.markdown("---")

            col_left, col_right = st.columns(2)

            # KMU - Jahresbilanz
            with col_left:
                st.subheader("KMU – Jahresergebnis")

                df_t2 = pd.DataFrame(t2[1:], columns=t2[0]).copy()
                df_t2["Betrag CHF"] = pd.to_numeric(df_t2["Betrag CHF"], errors="coerce")

                evu_ohne = df_t2.loc[df_t2["Lieferung"] == "EVU ohne Produzent_Solar", "Betrag CHF"].iloc[0]
                evu_mit = df_t2.loc[df_t2["Lieferung"] == "EVU mit Produzent_Solar", "Betrag CHF"].iloc[0]
                grab_solar = df_t2.loc[df_t2["Lieferung"] == "Produzent_Solar", "Betrag CHF"].iloc[0]
                total_mit = df_t2.loc[df_t2["Lieferung"] == "Total mit Produzent_Solar", "Betrag CHF"].iloc[0]
                gain_val  = df_t2.loc[df_t2["Lieferung"] == "Gewinn", "Betrag CHF"].iloc[0]

                x_vals_all = [1, 2, 3, 4, 5]
                ticktext = ["EVU", "EVU", "Einkauf Produzent", "Total", "Gewinn"]

                fig_eugster = go.Figure()
                blues = px.colors.sequential.Blues
                greens = px.colors.sequential.Greens

                fig_eugster.add_trace(go.Bar(
                    name="ohne Produzent",
                    x=[1],
                    y=[evu_ohne],
                    base=[0],
                    marker_color=blues[6],
                    text=[evu_ohne],
                    texttemplate="%{text:.0f}",
                    textposition="outside",
                ))

                x_mit = [2, 3, 4, 5]
                y_mit = [evu_mit, grab_solar, total_mit, gain_val]
                base_mit = [0, evu_mit, 0, total_mit]

                color_main = blues[3]
                color_gain = greens[3]
                colors_mit = [color_main, color_main, color_main, color_gain]

                fig_eugster.add_trace(go.Bar(
                    name="mit Produzent",
                    x=x_mit,
                    y=y_mit,
                    base=base_mit,
                    marker_color=colors_mit,
                    text=y_mit,
                    texttemplate="%{text:.0f}",
                    textposition="outside",
                ))

                fig_eugster.update_layout(
                    barmode="overlay",
                    xaxis=dict(tickmode="array", tickvals=x_vals_all, ticktext=ticktext, title=""),
                    yaxis=dict(title="CHF"),
                    legend=dict(
                        title="",
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                        font=dict(size=20),
                    ),
                    margin=dict(t=20, b=40, l=40, r=10),
                    bargap=0.3,
                    height=400,
                )

                st.plotly_chart(fig_eugster,  width="stretch")

            # Produzent – Jahresbilanz
            with col_right:
                st.subheader("Produzent – Jahresergebnis")

                df_t3 = pd.DataFrame(t3[1:], columns=t3[0]).copy()
                df_t3["Betrag CHF"] = pd.to_numeric(df_t3["Betrag CHF"], errors="coerce")
                verkauf = df_t3.loc[df_t3["Lieferung"] == "Verkauf an KMU", "Betrag CHF"].iloc[0]
                verguetung = df_t3.loc[df_t3["Lieferung"] == "Vergütung EVU", "Betrag CHF"].iloc[0]
                gewinn = df_t3.loc[df_t3["Lieferung"] == "Gewinn", "Betrag CHF"].iloc[0]

                x_ohne = [1]
                y_ohne = [EVUPCH]

                col2 = verkauf 
                col3 = G2
                col4 = G3
                col5 = EVUPCH-verkauf-G2-G3

                x_mit = [2, 3, 4, 5]
                y_mit = [col2, col3, col4, col5]
                base_mit = [0, col2, col2 + col3, col2 + col3 + col4]

                blues = px.colors.sequential.Blues
                greens = px.colors.sequential.Greens
                color_ohne = blues[6]
                colors_mit = [blues[3], blues[3], blues[3], greens[3]]

                def fmt(v):
                    return f"{v:,.0f}".replace(",", "’")

                fig_grab = go.Figure()

                fig_grab.add_trace(go.Bar(
                    name="nur EVU",
                    x=x_ohne,
                    y=y_ohne,
                    base=[0],
                    marker_color=color_ohne,
                    text=[fmt(y_ohne[0])],
                    textposition="outside",
                ))

                fig_grab.add_trace(go.Bar(
                    name="mit KMU und LEG",
                    x=x_mit,
                    y=y_mit,
                    base=base_mit,
                    marker_color=colors_mit,
                    text=[fmt(v) for v in y_mit],
                    textposition="outside",
                ))

                fig_grab.update_layout(
                    barmode="overlay",
                    xaxis=dict(
                        tickmode="array",
                        tickvals=[1, 2, 3, 4, 5],
                        ticktext=["EVU", "Verkauf KMU", "Verkauf LEG ", "Restüberschuss", "Gewinn"],
                        title="",
                    ),
                    yaxis=dict(title="CHF"),
                    legend=dict(
                        title="",
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                        font=dict(size=20),
                    ),
                    margin=dict(t=20, b=40, l=40, r=10),
                    bargap=0.3,
                    height=400,
                )
                st.plotly_chart(fig_grab,  width="stretch")

            with subtab5:
                    
                st.subheader("Privatkunden – Variantenvergleich")
                st.markdown(
                        f"""
            **Tarif TB Rheineck Standard :** {TZ1EP:.3f} CHF/kWh  
            **Tarif TB Produzent Standard :** {(tleg * TZ1EP):.3f} CHF/kWh – Dieser Wert ist einstellbar mit dem Schieberegler «Ratio Tarif Standard»
            """
                )

                # 1) DF "calcul" (types numériques propres)
                df_privat = pd.DataFrame(
                    [
                        ["vEGB",     round(tleg * TZ1EP, 3), round(tleg0max * TZ1EP, 3), Gewinnleg0],
                        ["LEG 40%",  round(tleg * TZ1EP, 3), round(tleg1max * TZ1EP, 3), Gewinnleg1],
                        ["LEG 20%",  round(tleg * TZ1EP, 3), round(tleg2max * TZ1EP, 3), Gewinnleg2],
                        ["Privatverbrauch Produzent",   np.nan,               np.nan,               GewinnPrivat],
                    ],
                    columns=[
                        "Variante",
                        "Standard Tarif Produzent (CHF/kWh)",
                        "Maximaler anwendbarer Tarif (CHF/kWh)",
                        "Kundengewinn CHF/kWh",
                    ],
                )

                # 2) DF "affichage" (strings → plus d'erreur Arrow)
                df_show = df_privat.copy()

                def fmt_num(v, nd=3):
                    return "nicht anwendbar" if pd.isna(v) else f"{v:.{nd}f}"

                df_show["Standard Tarif Produzent (CHF/kWh)"] = df_show["Standard Tarif Produzent (CHF/kWh)"].map(lambda v: fmt_num(v, 3))
                df_show["Maximaler anwendbarer Tarif (CHF/kWh)"] = df_show["Maximaler anwendbarer Tarif (CHF/kWh)"].map(lambda v: fmt_num(v, 3))
                df_show["Kundengewinn CHF/kWh"] = df_show["Kundengewinn CHF/kWh"].map(lambda v: fmt_num(v, 3))

                # ✅ 3) Remplacement de width
                st.dataframe(df_show, hide_index=True, width="stretch")
    else:
      st.info("Ajustez les paramètres dans la barre latérale.")

# ---------- ONGLET SIMULATION 15 ANS ----------
   


st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #f9fafb;
        color: #6b7280;
        text-align: center;
        padding: 8px;
        font-size: 12px;
        border-top: 1px solid #e5e7eb;
        z-index: 999;
    }
    </style>

    <div class="footer">
        © 2026 – Tarif TB Rheineck: Jahr 2026 (ohne MWST) - Neukalibrierung der Messwerte des Stromverbrauchs von Gifas per 1. Januar 2024, KMUs: entweder im EVG oder vZEV, Privatkunden: entweder EVG oder LEG. Lastprofil Privatkunden :EKZ Wietikon 2012.
    </div>
    """,
    unsafe_allow_html=True
)