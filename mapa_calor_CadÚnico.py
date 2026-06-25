import streamlit as st
import geopandas as gpd
import json
import urllib.request
import pandas as pd
from streamlit_folium import st_folium
from pathlib import Path

caminho = Path(__file__).parent / "data" / "Tabcad_pessoas_2026-06.xlsx"

def fmt_ptbr_num(valor, casas=2):
    if pd.isna(valor):
        return "-"
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_ptbr_int(valor):
    if pd.isna(valor):
        return "-"
    return f"{int(valor):,}".replace(",", ".")

st.set_page_config(page_title="Mapa Goiás", layout="wide")
#st.title("Mapa Interativo — Municípios de Goiás")

@st.cache_data
def carregar_geodados():
    url = "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-52-mun.json"
    with urllib.request.urlopen(url) as response:
        geojson = json.load(response)
    gdf = gpd.GeoDataFrame.from_features(geojson["features"])
    gdf = gdf.set_crs("EPSG:4326")
    gdf.loc[gdf["name"] == "São Luíz do Norte", "name"] = "São Luiz do Norte"
    return gdf

@st.cache_data
def carregar_planilha():
    df = pd.read_excel(
        caminho, sheet_name="Cad",
        skipfooter=2
    )    

    df["% ext_pob"] = pd.to_numeric(df["% ext_pob"], errors="coerce").round(2)
    df["% pob"] = pd.to_numeric(df["% pob"], errors="coerce").round(2)
    df["% pob_p1_p2"] = pd.to_numeric(df["% pob_p1_p2"], errors="coerce").round(2)
    return df

gdf = carregar_geodados()
df_real = carregar_planilha()

gdf_teste = gdf.merge(
    df_real[["name", "população",
             "ext_pob", "% ext_pob", "norm_ext",
             "pob", "% pob", "norm_pob",
             "pob_p1_p2", "% pob_p1_p2", "norm_pob_p1_p2"]],
    on="name", how="left"
)

gdf_teste["população_fmt"] = gdf_teste["população"].apply(fmt_ptbr_int)

gdf_teste["ext_pob_fmt"] = gdf_teste["ext_pob"].apply(fmt_ptbr_int)
gdf_teste["pct_ext_pob_fmt"] = gdf_teste["% ext_pob"].apply(lambda x: fmt_ptbr_num(x, 2))

gdf_teste["pob_fmt"] = gdf_teste["pob"].apply(fmt_ptbr_int)
gdf_teste["pct_pob_fmt"] = gdf_teste["% pob"].apply(lambda x: fmt_ptbr_num(x, 2))

gdf_teste["pob_p1_p2_fmt"] = gdf_teste["pob_p1_p2"].apply(fmt_ptbr_int)
gdf_teste["pct_pob_p1_p2_fmt"] = gdf_teste["% pob_p1_p2"].apply(lambda x: fmt_ptbr_num(x, 2))

with st.sidebar:
    st.header("⚙️ Configurações")

    coluna = st.selectbox(
        "Indicador",
        options=["norm_ext", "norm_pob", "norm_pob_p1_p2"],
        format_func=lambda x: {
            "norm_ext": "Extrema Pobreza (P1) %",
            "norm_pob": "Pobreza (P2) %",
            "norm_pob_p1_p2": "Pobreza PBF (P1 e P2) %",

        }[x]
    )

    paleta = st.selectbox(
        "Paleta de cores",
        options=["RdYlGn_r", "viridis_r", "plasma_r", "YlOrRd"],
        format_func=lambda x: {
            "RdYlGn_r":  "Vermelho → Amarelo → Verde (invertido)",
            "viridis_r": "Viridis (invertido)",
            "plasma_r": "Plasma Invertido",
            "YlOrRd": "Amarelo -> Vermelho"
        }[x]
    )
    st.caption("Fonte: IBGE Sidra / Tabcad - Jun. 2026")

titulos = {
    "norm_ext": "Percentual de Pessoas Inscritas em Extrema Pobreza (população municipal)",
    "norm_pob": "Percentual de Pessoas Inscritas em Pobreza (população municipal)",
    "norm_pob_p1_p2": "Percentual de Pessoas Inscritas em Pobreza (P1 + P2) (população municipal)",
}
legendas = {
    "norm_ext": "% Extrema Pobreza (pop. municipal)",
    "norm_pob": "% Pobreza (pop. municipal)",
    "norm_pob_p1_p2": "% Pobreza P1+P2 (pop. municipal)",
}

st.subheader(titulos[coluna])

m = gdf_teste.explore(
    column=coluna,
    cmap=paleta,
    vmin=0,
    vmax=0.5,
    tooltip=[
        "name",
        "população_fmt",
        "ext_pob_fmt",
        "pct_ext_pob_fmt",
        "pob_fmt",
        "pct_pob_fmt",
        "pob_p1_p2_fmt",
        "pct_pob_p1_p2_fmt"
    ],
    tooltip_kwds={
        "aliases": ["Município","População", "Ext. pobreza", "% ext. pob.", "Pobreza", "% pob.", "Pobreza (P1+P2)", "% Pob. (P1+P2)"],
        "labels": True,
        "sticky": True,
        "style": """
            background-color: white;
            color: #222;
            font-family: Arial;
            font-size: 23px;
            padding: 10px;
        """
    },
    popup=True,
    legend=True,
    legend_kwds={"caption": legendas[coluna]},
    style_kwds={"weight": 0.5, "color": "#111", "fillOpacity": 0.85},
    highlight_kwds={"weight": 2.5, "color": "#111", "fillOpacity": 0.4},
    tiles="CartoDB positron",
)

st_folium(m, use_container_width=True, height=900, returned_objects=[])
