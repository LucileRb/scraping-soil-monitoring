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
    'Decision tool' # page de l'outils d'aide à la décision
    ])

if app_mode == 'Home':
    st.title('BLABLABLA')

elif app_mode == 'Pokedex':
    st.title('POKEDEX')

elif app_mode == 'Decision tool':
    st.title('OUTILS DE PREDICTION')
    st.divider()
    phrase = '''
    Bonjour,
    merci de remplir les informations suivantes à propos du client afin de déterminer si nous devons acceder à sa demande de prêt
    '''
    st.subheader(phrase)
    st.divider()

    st.sidebar.header('Informations à propos du nouveau client:')

################################################################################################ END ################################################################################################