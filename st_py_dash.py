# Tableau de bord interactif des projets H2020 en France

import pandas as pd
import plotly.express as px
import streamlit as st

# Charger les données
@st.cache_data
def load_data():
    df = pd.read_excel("C:\\Users\\abder\\Downloads\\Stage\\Cordis\\created\\projects_topics.xlsx")
    return df

df = load_data()

st.title("Projets H2020 en France 🇫🇷")

# Filtres
st.sidebar.header("Filtres")
ville = st.sidebar.multiselect("Ville", options=df['city'].dropna().unique())
type_org = st.sidebar.multiselect("Type d'organisation", options=df['activityType'].dropna().unique())
appel = st.sidebar.multiselect("Appel à projets (Call)", options=df['masterCall'].dropna().unique())

# Application des filtres
filtered_df = df.copy()
if ville:
    filtered_df = filtered_df[filtered_df['city'].isin(ville)]
if type_org:
    filtered_df = filtered_df[filtered_df['activityType'].isin(type_org)]
if appel:
    filtered_df = filtered_df[filtered_df['masterCall'].isin(appel)]

# Nettoyage des champs numériques
filtered_df['ecMaxContribution'] = pd.to_numeric(filtered_df['ecMaxContribution'], errors='coerce')
filtered_df['ecContribution'] = pd.to_numeric(filtered_df['ecContribution'], errors='coerce')

# KPIs
st.subheader("Résumé des financements")
st.metric("Nombre de projets", filtered_df['id'].nunique())
st.metric("Total financement UE (€)", f"{filtered_df['ecMaxContribution'].sum():,.0f}")
st.metric("Nombre d'organisations", filtered_df['organisationID'].nunique())

# Graphique financement par type d'organisation
st.subheader("Financement par type d'organisation")
fig1 = px.bar(
    filtered_df.groupby('activityType', as_index=False)['ecContribution'].sum().sort_values(by='ecContribution', ascending=False),
    x='activityType', y='ecContribution', labels={'ecContribution': 'Contribution (€)'},
    title="Répartition des financements UE"
)

st.plotly_chart(fig1)

# Carte des projets
st.subheader("Carte des projets")
geo_df = filtered_df.dropna(subset=['geolocation'])
geo_df[['lat', 'lon']] = geo_df['geolocation'].str.extract(r'\((.*), (.*)\)').astype(float)
fig2 = px.scatter_mapbox(
    geo_df, lat="lat", lon="lon", hover_name="name", zoom=5,
    hover_data={"ecContribution": True, "city": True},
    color_discrete_sequence=["blue"], height=500
)
fig2.update_layout(mapbox_style="open-street-map")
st.plotly_chart(fig2)

# Liste des projets
st.subheader("Liste des projets filtrés")
st.dataframe(filtered_df[["acronym", "title_x", "city", "activityType", "ecContribution", "topics"]].sort_values(by="ecContribution", ascending=False))
