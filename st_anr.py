# Tableau de bord Streamlit - Projets ANR France

import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide")
st.title("📊 Tableau de bord des projets financés par l'ANR")

# Chargement des données
@st.cache_data

def load_data():
    df = pd.read_excel("C:\\Users\\abder\\Downloads\\Stage\\base1504202025.xlsx")

    return df

df = load_data()

# Nettoyage des données numériques
num_cols = ["aide_allouee_projet_keuros", "aide_allouee_partenaire", "aide_demandee_partenaire"]
for col in num_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Réinitialisation des filtres
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Réinitialiser les filtres"):
    st.rerun()

# Filtrage dynamique
filtered_reference = df.copy()

st.sidebar.header("🎯 Filtres")
code_projet = st.sidebar.multiselect("Code projet ANR", sorted(filtered_reference["code_projet_anr"].dropna().unique()))
if code_projet:
    filtered_reference = filtered_reference[filtered_reference["code_projet_anr"].isin(code_projet)]

annees = st.sidebar.multiselect("Année d'edition", sorted(filtered_reference["edition"].dropna().unique()))
if annees:
    filtered_reference = filtered_reference[filtered_reference["edition"].isin(annees)]

comites = st.sidebar.multiselect("Comité thématique", sorted(filtered_reference["intitule_du_comite"].dropna().unique()))
if comites:
    filtered_reference = filtered_reference[filtered_reference["intitule_du_comite"].isin(comites)]

tutelles = st.sidebar.multiselect("Tutelle gestionnaire", sorted(filtered_reference["nom_tutelle_gestionnaire"].dropna().unique()))
if tutelles:
    filtered_reference = filtered_reference[filtered_reference["nom_tutelle_gestionnaire"].isin(tutelles)]

categorie_hebergeante = st.sidebar.multiselect("Catégorie tutelle hébergeante", sorted(filtered_reference["categorie_tutelle_hebergeante"].dropna().unique()))
if categorie_hebergeante:
    filtered_reference = filtered_reference[filtered_reference["categorie_tutelle_hebergeante"].isin(categorie_hebergeante)]

categorie_gestionnaire = st.sidebar.multiselect("Catégorie tutelle gestionnaire", sorted(filtered_reference["categorie_tutelle_gestionnaire"].dropna().unique()))
if categorie_gestionnaire:
    filtered_reference = filtered_reference[filtered_reference["categorie_tutelle_gestionnaire"].isin(categorie_gestionnaire)]

instrument = st.sidebar.multiselect("Instrument de financement", sorted(filtered_reference["instrument_financement"].dropna().unique()))
if instrument:
    filtered_reference = filtered_reference[filtered_reference["instrument_financement"].isin(instrument)]

# Appliquer les filtres
filtered_df = filtered_reference.copy()

# Statistiques sur les partenaires
projets_groupes = filtered_df.groupby("code_projet_anr").agg(
    nb_partenaire=("code_partenaire_anr", "nunique"),
    financement_unique=("aide_allouee_projet_keuros", "first")
)
moyenne_partenaire = projets_groupes["nb_partenaire"].mean()
nb_projets = projets_groupes.shape[0]
projet_max = projets_groupes["nb_partenaire"].idxmax()
nb_max = projets_groupes["nb_partenaire"].max()

# Projet max/min financement
max_funding = projets_groupes["financement_unique"].idxmax()
min_funding = projets_groupes["financement_unique"].idxmin()
max_funding_amount = projets_groupes["financement_unique"].max()
min_funding_amount = projets_groupes["financement_unique"].min()

# KPIs
st.subheader("🔢 Statistiques descriptives")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Nombre de projets", nb_projets)
k2.metric("Montant total alloué (K€)", f"{projets_groupes['financement_unique'].sum():,.0f}")
k3.metric("Nombre de tutelles", filtered_df["nom_tutelle_gestionnaire"].nunique())
k4.metric("Moy. partenaires/projet", f"{moyenne_partenaire:.2f}")

st.markdown(f"🔍 **Projet avec le plus de partenaires :** `{projet_max}` avec **{nb_max}** partenaires")
st.markdown(f"💰 **Projet avec le plus de financement :** `{max_funding}` avec **{max_funding_amount:,.0f} K€**")
st.markdown(f"💸 **Projet avec le moins de financement :** `{min_funding}` avec **{min_funding_amount:,.0f} K€**")

# Graphiques
st.subheader("📈 Visualisations")
col1, col2 = st.columns(2)

with col1:
    edition_funding = filtered_df.drop_duplicates(subset="code_projet_anr").groupby("edition")["aide_allouee_projet_keuros"].sum().reset_index()
    fig1 = px.bar(edition_funding, x="edition", y="aide_allouee_projet_keuros", title="Montant alloué par année")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    top_tutelles = filtered_df.drop_duplicates(subset="code_projet_anr").groupby("nom_tutelle_gestionnaire")["aide_allouee_projet_keuros"].sum().nlargest(10).reset_index()
    fig2 = px.bar(top_tutelles, x="aide_allouee_projet_keuros", y="nom_tutelle_gestionnaire", orientation="h", title="Top 10 tutelles par financement")
    st.plotly_chart(fig2, use_container_width=True)

# Pie chart des catégories tutelle gestionnaire
st.subheader("📊 Répartition des catégories de tutelles gestionnaires")
if "categorie_tutelle_gestionnaire" in filtered_df.columns:
    pie_df = filtered_df.drop_duplicates(subset="code_projet_anr")["categorie_tutelle_gestionnaire"].value_counts().reset_index()
    pie_df.columns = ["Catégorie", "Nombre"]
    fig_pie = px.pie(pie_df, names="Catégorie", values="Nombre", title="Catégories de tutelles gestionnaires")
    st.plotly_chart(fig_pie, use_container_width=True)

# Pie chart des instruments de financement
st.subheader("📊 Répartition des instruments de financement")
if "instrument_financement" in filtered_df.columns:
    pie_inst = filtered_df.drop_duplicates(subset="code_projet_anr")["instrument_financement"].value_counts().reset_index()
    pie_inst.columns = ["Instrument", "Nombre"]
    fig_inst = px.pie(pie_inst, names="Instrument", values="Nombre", title="Instruments de financement")
    st.plotly_chart(fig_inst, use_container_width=True)

# Carte
st.subheader("🗺️ Répartition géographique (si géolocalisation disponible)")
if "geolocalisation" in filtered_df.columns:
    geo_df = filtered_df.drop_duplicates(subset="code_projet_anr").dropna(subset=['geolocalisation'])
    geo_df[['lat', 'lon']] = geo_df['geolocalisation'].str.extract(r'\((.*), (.*)\)').astype(float)
    fig3 = px.scatter_mapbox(geo_df, lat="lat", lon="lon", hover_name="nom_tutelle_gestionnaire", zoom=5,
                              color="aide_allouee_projet_keuros", size_max=15,
                              mapbox_style="open-street-map", height=500)
    st.plotly_chart(fig3, use_container_width=True)

# Tableau
st.subheader("📋 Données filtrées")
st.dataframe(filtered_df.drop_duplicates(subset="code_projet_anr"))

# Export Excel
st.subheader("📤 Exporter les données filtrées")
output = BytesIO()
filtered_df.drop_duplicates(subset="code_projet_anr").to_excel(output, index=False, engine='openpyxl')
st.download_button("📥 Télécharger en Excel", data=output.getvalue(), file_name="projets_anr_filtrés.xlsx")
