# 📊 Tableau de bord Streamlit - Projets ANR France

import streamlit as st
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim

st.set_page_config(layout="wide")
st.title("📊 Tableau de bord des projets financés par l'ANR 2014-2024")

# 🔀 Choix de la source de données
st.sidebar.markdown("## 📂 Choix de la base")
source_choice = st.sidebar.radio(
    "Sélection de la base de données à analyser :",
    ["📘 ANR Global", "🔗 Croisement ANR/CORDIS"]
)

# 📥 Chargement dynamique des données
@st.cache_data
def load_data(source):
    if source == "📘 ANR Global":
        df = pd.read_excel("base18042025_enrichie.xlsx")
    else:
        df = pd.read_excel("ANR_projets_communs_enrichi.xlsx")
    df.columns = df.columns.str.strip().str.lower()
    obj_cols = df.select_dtypes(include="object").columns
    df[obj_cols] = df[obj_cols].astype(str)
    return df

with st.spinner("⚠️ L’application peut prendre 2 à 3 minutes à charger. Merci de patienter 🙏"):
    df = load_data(source_choice)

st.success("✅ Données chargées avec succès !")

# 🔢 Nettoyage des colonnes numériques
num_cols = ["aide_allouee_projet_keuros", "aide_allouee_partenaire", "aide_demandee_partenaire"]
for col in num_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# 🔄 Réinitialisation
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Réinitialiser les filtres"):
    st.rerun()

filtered_reference = df.copy()

# 🎯 Filtres dynamiques
st.sidebar.header("🎯 Filtres")

if "code_projet_anr" in filtered_reference.columns:
    code_projet = st.sidebar.multiselect("Code projet ANR", sorted(filtered_reference["code_projet_anr"].dropna().unique()))
    if code_projet:
        filtered_reference = filtered_reference[filtered_reference["code_projet_anr"].isin(code_projet)]

if "edition" in filtered_reference.columns:
    annees = st.sidebar.multiselect("Année d'édition", sorted(filtered_reference["edition"].dropna().unique()))
    if annees:
        filtered_reference = filtered_reference[filtered_reference["edition"].isin(annees)]

if "intitule_du_comite" in filtered_reference.columns:
    comites = st.sidebar.multiselect("Comité thématique", sorted(filtered_reference["intitule_du_comite"].dropna().unique()))
    if comites:
        filtered_reference = filtered_reference[filtered_reference["intitule_du_comite"].isin(comites)]

if "nom_tutelle_gestionnaire" in filtered_reference.columns:
    tutelles = st.sidebar.multiselect("Tutelle gestionnaire", sorted(filtered_reference["nom_tutelle_gestionnaire"].dropna().unique()))
    if tutelles:
        filtered_reference = filtered_reference[filtered_reference["nom_tutelle_gestionnaire"].isin(tutelles)]

if "categorie_tutelle_hebergeante" in filtered_reference.columns:
    cat_heberg = st.sidebar.multiselect("Catégorie tutelle hébergeante", sorted(filtered_reference["categorie_tutelle_hebergeante"].dropna().unique()))
    if cat_heberg:
        filtered_reference = filtered_reference[filtered_reference["categorie_tutelle_hebergeante"].isin(cat_heberg)]

if "categorie_tutelle_gestionnaire" in filtered_reference.columns:
    cat_gest = st.sidebar.multiselect("Catégorie tutelle gestionnaire", sorted(filtered_reference["categorie_tutelle_gestionnaire"].dropna().unique()))
    if cat_gest:
        filtered_reference = filtered_reference[filtered_reference["categorie_tutelle_gestionnaire"].isin(cat_gest)]

if "instrument_financement" in filtered_reference.columns:
    instrument = st.sidebar.multiselect("Instrument de financement", sorted(filtered_reference["instrument_financement"].dropna().unique()))
    if instrument:
        filtered_reference = filtered_reference[filtered_reference["instrument_financement"].isin(instrument)]

# 📊 Slider de filtrage par nombre de partenaires
st.subheader("📊 Répartition des projets par nombre de partenaires")
if "code_projet_anr" in filtered_reference.columns and "code_partenaire_anr" in filtered_reference.columns:
    projets_groupes_base = filtered_reference.groupby("code_projet_anr").agg(
        nb_partenaire=("code_partenaire_anr", "nunique"),
        financement_unique=("aide_allouee_projet_keuros", "first")
    ).reset_index()

    X = st.slider("Sélectionner un seuil minimal de partenaires :", min_value=1, max_value=16, value=1)
    codes_eligibles = projets_groupes_base[projets_groupes_base["nb_partenaire"] >= X]["code_projet_anr"]
    filtered_df = filtered_reference[filtered_reference["code_projet_anr"].isin(codes_eligibles)]
    projets_groupes = projets_groupes_base[projets_groupes_base["code_projet_anr"].isin(codes_eligibles)]

    if filtered_df.empty:
        st.warning("⚠️ Aucun projet ne correspond aux filtres sélectionnés.")
        st.stop()

    # 🔢 KPIs
    nb_projets = projets_groupes.shape[0]
    total_projets = projets_groupes_base.shape[0]
    nb_projets_pourcent = (nb_projets / total_projets) * 100 if total_projets else 0
    moyenne_partenaire = projets_groupes["nb_partenaire"].mean()

    projet_max = projets_groupes.loc[projets_groupes["nb_partenaire"].idxmax(), "code_projet_anr"] if not projets_groupes.empty else "N/A"
    nb_max = projets_groupes["nb_partenaire"].max() if not projets_groupes.empty else "N/A"

    max_funding = projets_groupes.loc[projets_groupes["financement_unique"].idxmax(), "code_projet_anr"] if not projets_groupes.empty else "N/A"
    min_funding = projets_groupes.loc[projets_groupes["financement_unique"].idxmin(), "code_projet_anr"] if not projets_groupes.empty else "N/A"
    max_funding_amount = projets_groupes["financement_unique"].max() if not projets_groupes.empty else 0
    min_funding_amount = projets_groupes["financement_unique"].min() if not projets_groupes.empty else 0

    st.markdown(f"📊 **{nb_projets_pourcent:.2f}%** des projets ont **au moins {X} partenaires**.")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Nombre de projets", nb_projets)
    k2.metric("Montant total alloué (K€)", f"{projets_groupes['financement_unique'].sum():,.0f}")
    k3.metric("Nombre de tutelles", filtered_df["nom_tutelle_gestionnaire"].nunique())
    k4.metric("Moy. partenaires/projet", f"{moyenne_partenaire:.2f}")

    st.markdown(f"🔍 **Projet avec le plus de partenaires :** `{projet_max}` avec **{nb_max}** partenaires")
    st.markdown(f"💰 **Projet avec le plus de financement :** `{max_funding}` avec **{max_funding_amount:,.0f} K€**")
    st.markdown(f"💸 **Projet avec le moins de financement :** `{min_funding}` avec **{min_funding_amount:,.0f} K€**")

    # 📈 Visualisations
    st.subheader("📈 Visualisations")
    col1, col2 = st.columns(2)

    if "edition" in filtered_df.columns and "aide_allouee_projet_keuros" in filtered_df.columns:
        edition_funding = filtered_df.drop_duplicates(subset="code_projet_anr").groupby("edition")["aide_allouee_projet_keuros"].sum().reset_index()
        fig1 = px.bar(edition_funding, x="edition", y="aide_allouee_projet_keuros", title="Montant alloué par année")
        col1.plotly_chart(fig1, use_container_width=True)

    if "nom_tutelle_gestionnaire" in filtered_df.columns:
        top_tutelles = filtered_df.drop_duplicates(subset="code_projet_anr").groupby("nom_tutelle_gestionnaire")["aide_allouee_projet_keuros"].sum().nlargest(10).reset_index()
        fig2 = px.bar(top_tutelles, x="aide_allouee_projet_keuros", y="nom_tutelle_gestionnaire", orientation="h", title="Top 10 tutelles par financement")
        col2.plotly_chart(fig2, use_container_width=True)

    # 🥧 Pie charts
    if "categorie_tutelle_gestionnaire" in filtered_df.columns:
        st.subheader("📊 Répartition des catégories de tutelles gestionnaires")
        pie_df = filtered_df.drop_duplicates(subset="code_projet_anr")["categorie_tutelle_gestionnaire"].value_counts().reset_index()
        pie_df.columns = ["Catégorie", "Nombre"]
        fig_pie = px.pie(pie_df, names="Catégorie", values="Nombre", title="Catégories de tutelles gestionnaires")
        st.plotly_chart(fig_pie, use_container_width=True)

    if "instrument_financement" in filtered_df.columns:
        st.subheader("📊 Répartition des instruments de financement")
        pie_inst = filtered_df.drop_duplicates(subset="code_projet_anr")["instrument_financement"].value_counts().reset_index()
        pie_inst.columns = ["Instrument", "Nombre"]
        fig_inst = px.pie(pie_inst, names="Instrument", values="Nombre", title="Instruments de financement")
        st.plotly_chart(fig_inst, use_container_width=True)

    if 'lat' in filtered_df.columns and 'long' in filtered_df.columns:
    st.subheader("📍 Carte des lieux avec le plus de projets")
    df_map = filtered_df.groupby(['lat', 'long', 'city'], as_index=False).agg(nb_projets=('id', 'nunique')).dropna()
    fig_map = px.scatter_mapbox(df_map, lat='lat', lon='long', size='nb_projets', color='nb_projets', color_continuous_scale='Viridis', zoom=4, height=600, title="Nombre de projets par localisation", hover_name='city')
    fig_map.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig_map, use_container_width=True)

    # 📋 Tableau des données filtrées
    st.subheader("📋 Données filtrées")
    st.dataframe(filtered_df)

else:
    st.warning("Le jeu de données ne contient pas les colonnes nécessaires à l'analyse.")
