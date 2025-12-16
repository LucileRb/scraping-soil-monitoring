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
    phrase = '''
    Hello,
    gnagnagnagnagnagnagnagnagnagnagnagna

    mettre abstract de l'article ici ? ou au moins résumé / explication de l'outils
    '''
    st.subheader(phrase)
    st.divider()

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