import streamlit as st
import geopandas as gpd
import json
import urllib.request
import pandas as pd
from pathlib import Path
from streamlit_folium import st_folium

caminho = Path(__file__).parent.parent / "data" / "Tabcad_pessoas_2026-06.xlsx"

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
        caminho, sheet_name="Aptos",
        skipfooter=2
    )    

    df["pct_aptos_mun"] = pd.to_numeric(df["pct_aptos_mun"], errors="coerce").round(2)
    df["pct_aptos_go"] = pd.to_numeric(df["pct_aptos_go"], errors="coerce").round(2)

    return df

gdf = carregar_geodados()
df_real = carregar_planilha()

gdf_teste = gdf.merge(
    df_real[["name", "população", "ext_pob",
             "aptos", "pct_aptos_mun", "norm_aptos_mun", "pct_aptos_go", "norm_aptos_go"]],
    on="name", how="left"
)

gdf_teste["população_fmt"] = gdf_teste["população"].apply(fmt_ptbr_int)
gdf_teste["ext_pob_fmt"] = gdf_teste["ext_pob"].apply(fmt_ptbr_int)

gdf_teste["aptos_fmt"] = gdf_teste["aptos"].apply(fmt_ptbr_int)
gdf_teste["pct_aptos_mun_fmt"] = gdf_teste["pct_aptos_mun"].apply(lambda x: fmt_ptbr_num(x, 2))
gdf_teste["pct_aptos_go_fmt"] = gdf_teste["pct_aptos_go"].apply(lambda x: fmt_ptbr_num(x, 2))



with st.sidebar:
    st.header("⚙️ Configurações")

    coluna = st.selectbox(
        "Indicador",
        options=["norm_aptos_mun", "norm_aptos_go"],
        format_func=lambda x: {
            "norm_aptos_mun": "Aptos / Pop. Municipal",
            "norm_aptos_go": "Aptos / Total de Aptos Goiás",
        }[x]
    )

    paleta = st.selectbox(
        "Paleta de cores",
        options=["viridis_r", "RdYlGn_r", "Oranges"],
        format_func=lambda x: {
            "viridis_r": "Viridis (invertido)",
            "RdYlGn_r":  "Vermelho → Amarelo → Verde (invertido)",
            "Oranges": "Escala de Laranja"
        }[x]
    )
    st.caption("Fonte: IBGE Sidra / TRE-GO")

titulos = {
    "norm_aptos_mun": "Percentual de Pessoas Aptas (população municipal)",
    "norm_aptos_go": "Percentual de Pessoas Aptas (Total de aptos em Goiás)",
}
legendas = {
    "norm_aptos_mun": "% Aptos (pop. municipal)",
    "norm_aptos_go": "% Aptos (Total de aptos em Goiás)",
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
        "aptos_fmt",
        "pct_aptos_mun_fmt",
        "pct_aptos_go_fmt"
    ],
    tooltip_kwds={
        "aliases": ["Município", "População", "Ext. pobreza", "Aptos", "% Aptos Pop. Mun.", "% Aptos Total Goiás"],
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
