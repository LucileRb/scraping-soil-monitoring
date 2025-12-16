################################################################################################ IMPORTS ################################################################################################
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import pyarrow.parquet as pq

################################################################################################ FONCTIONS ################################################################################################



################################################################################################ DATA & OUTILS ################################################################################################




################################################################################################ DASHBOARD ################################################################################################


# Configuration de la page
st.set_page_config(
    page_title = 'Blablablaaaaaaa',
    page_icon = 'soil_app/app_illustrations/image_soil.png',
    layout = 'wide'
    )

# Définition des pages de l'application
st.sidebar.image('soil_app/app_illustrations/image_soil.png')
app_mode = st.sidebar.selectbox('Choix de la page', [
    'Home', # page d'accueil et description des variables
    'Pokedex', # page pour visualiser les groupes de MRVs
    'Decision tool', # page de l'outils d'aide à la décision
    'Articles' # page pour visualiser les articles utilisés ?
    ])

if app_mode == 'Home':
    st.title('BLABLABLA')
    st.divider()
    st.subheader("Hello, gnagnagnagnagnagnagnagnagnagnagnagna - mettre abstract de l'article ici ? ou au moins résumé / explication de l'outils")
    st.divider()
    st.image('scoring_app/app_illustrations/paying-off-a-loan-early.jpg')

    # à défaut d'afficher infos sur jeu de données, décrire les features utilisées:
    st.subheader("Liste des descripteurs utilisés pour prédire gnagna :")

    st.write("- :blue[CNT_CHILDREN]     :     Nombre d'enfants qu'à le/la client(e)")
    st.write("- :blue[CNT_FAM_MEMBERS]     :     Nombre de membres dans la famille")
    st.write("- :blue[PREVIOUS_LOANS_COUNT]     :     Nombre total des précédents crédits pris par chaque client")
    st.write("- :blue[NONLIVINGAREA_MODE]     :     Informations normalisées sur l'immeuble où vit le client (taille, étages, etc...)")
    st.write("- :blue[AMT_REQ_CREDIT_BUREAU_QRT]     :     Nombre de demandes de renseignements auprès du bureau de crédit concernant le client 3 mois avant la demande (à l'exclusion du mois précédant la demande)")
    st.write("- :blue[AMT_REQ_CREDIT_BUREAU_YEAR]     :     Nombre de demandes de renseignements auprès du bureau de crédit concernant le client sur un an (à l'exclusion des 3 derniers mois avant la demande)")
    st.write("- :blue[EXT_SOURCE_3]     :     Score normalisé provenant d'une source de données externe.")
    st.write("- :blue[OBS_30_CNT_SOCIAL_CIRCLE]     :     Nombre d'observations des environs sociaux du client avec un défaut observable de 30 jours de retard (30 DPD).")
    st.write("- :blue[OBS_60_CNT_SOCIAL_CIRCLE]     :     Nombre d'observations des environs sociaux du client avec un défaut observable de 60 jours de retard (30 DPD).")
    st.write("- :blue[DEF_30_CNT_SOCIAL_CIRCLE]     :     Nombre d'observations des environs sociaux du client ont fait défaut avec un retard de paiement de 30 jours (30 DPD)")



elif app_mode == 'Pokedex':
    st.title('POKEDEX')
    st.divider()
    phrase = '''
    ici mettre menu déroulant avec la liste de tous les groupes de MRVs, ou alors mettre toutes les vignettes des groupes de MRVs et quand on clique dessus on a les détails
    '''
    st.subheader(phrase)
    st.divider()

elif app_mode == 'Decision tool':
    st.title('DECISION TOOL')
    st.divider()
    phrase = '''
    Hello,
    Please select the correct infos below to blablabla truc much
    '''
    st.subheader(phrase)
    st.divider()

    st.sidebar.header('MRVs infos:')

elif app_mode == 'Articles':
    st.title('LIBRARY')
    st.divider()
    phrase = '''
    ici soit lister la biblio comme dans l'article, soit mettre menu déroulant avec liste des articles et permettre à l'utilisateur de les afficher (ou peut-être juste l'abstract)
    '''
    st.subheader(phrase)
    st.divider()

################################################################################################ END ################################################################################################