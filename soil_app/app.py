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
    st.image('soil_app/app_illustrations/AOE-Blog-Organic-Soil.webp')

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
    options_y_n = ["Yes", "No"]

    st.sidebar.header('Screening for article inclusion:')
    st.write("- Inclusion criteria MRV")

    Inclusion_criteria_Monitoring = st.sidebar.pills("Inclusion criteria Monitoring", options_y_n)
    Inclusion_criteria_Reporting = st.sidebar.pills("Inclusion criteria Reporting", options_y_n)
    Inclusion_criteria_Verification = st.sidebar.pills("Inclusion criteria Verification", options_y_n)
    Inclusion_criteria_About_MRV = st.sidebar.pills("Inclusion criteria About MRV", options_y_n)

    st.write("- Soil")
    Inclusion_criteria_About_Soil = st.sidebar.pills("Inclusion criteria About Soil", options_y_n)

    st.write("- Scope")
    In_Scope = st.sidebar.pills("In Scope", options_y_n)

    st.sidebar.header('Stakeholders:')
    st.write("- Land use")
    Land_Use_Agriculture = st.sidebar.pills("Land Use Agriculture", options_y_n)
    Land_Use_Forest = st.sidebar.pills("Land Use Forest", options_y_n)
    Land_Use_Urban = st.sidebar.pills("Land Use Urban", options_y_n)
    Land_Use_Others = st.sidebar.pills("Land Use Others", options_y_n)
    Land_Use_Others_Precision = st.sidebar.text_input('Please write it with a capital letter and a "_" between words:')

    st.write("- Scale")
    Scale_Local = st.sidebar.pills("Scale Local", options_y_n)
    Scale_Regional = st.sidebar.pills("Scale Regional", options_y_n)
    Scale_National = st.sidebar.pills("Scale National", options_y_n)
    Scale_Continental = st.sidebar.pills("Scale Continental", options_y_n)
    Scale_Global = st.sidebar.pills("Scale Global", options_y_n)

    st.write("- Purpose and driver")
    Purpose = st.sidebar.selectbox('Purpose', ('Certification', 'Compliance_carbon_market', 'Voluntary_carbon_market', 'Other'))
    Puprose_Others_Precision = st.sidebar.text_input('Please write it with a capital letter and a "_" between words:')
    Driver = st.sidebar.text_input('Please write it with a capital letter and a "_" between words:')

    st.write("- Occupation")
    Occupation_Farmers = st.sidebar.pills("Occupation Farmers", options_y_n)
    Occupation_Foresters_Forester_Associations = st.sidebar.pills("Occupation Foresters Forester Associations", options_y_n)
    Occupation_Public_Administrators = st.sidebar.pills("Occupation Public Administrators", options_y_n)
    Occupation_Educational_Institutions_Reasearch = st.sidebar.pills("Occupation Educational Institutions Research", options_y_n)
    Occupation_NGOs = st.sidebar.pills("NGOs", options_y_n)
    Occupation_Agroindustry = st.sidebar.pills("Occupation Agroindustry", options_y_n)
    Occupation_Forestry_Companies = st.sidebar.pills("Occupation Forestry Companies", options_y_n)
    Occupation_Consultancy = st.sidebar.pills("Occupation Consultancy", options_y_n)
    Occupation_Others = st.sidebar.pills("Occupation Others", options_y_n)
    Occupation_Others_Precision = st.sidebar.text_input('Please write it with a capital letter and a "_" between words:')

    st.write("- Cost")
    Cost_MRV = st.sidebar.number_input("Please insert a number", value=None, placeholder="Type a number...")
    Cost_Unit = st.sidebar.text_input('Please indicate the unit i.e. the currency:')

    st.sidebar.header('Monitoring:')
    st.write("- Soil parameters")
    Parameter_Soil_Microorganisms = st.sidebar.pills("Parameter Soil Microorganisms", options_y_n)
    Parameter_Soil_Fauna = st.sidebar.pills("Parameter Soil Fauna", options_y_n)
    Parameter_Soil_pH = st.sidebar.pills("Parameter Soil pH", options_y_n)
    Parameter_Oxygen_content = st.sidebar.pills("Parameter Oxygen content", options_y_n)
    Parameter_Clay_mineralogy = st.sidebar.pills("Parameter Clay mineralogy", options_y_n)
    Parameter_Soil_organic_matter_SOC = st.sidebar.pills("Parameter Soil organic matter SOC", options_y_n)
    Parameter_Soil_CEC = st.sidebar.pills("Parameter Soil CEC", options_y_n)
    Parameter_Soil_moisture = st.sidebar.pills("Parameter Soil moisture", options_y_n)
    Parameter_Soil_temperature = st.sidebar.pills("Parameter Soil temperature", options_y_n)
    Parameter_Particle_size_distribution = st.sidebar.pills("Parameter Particle size distribution", options_y_n)
    Parameter_Soil_porosity = st.sidebar.pills("Parameter Soil porosity", options_y_n)
    Parameter_Soil_diffusivity = st.sidebar.pills("Parameter Soil diffusivity", options_y_n)
    Parameter_Aggregate_stability = st.sidebar.pills("Parameter Aggregate stability", options_y_n)
    Parameter_Soil_compaction = st.sidebar.pills("Parameter Soil compaction", options_y_n)
    Parameter_Nutrient_availability = st.sidebar.pills("Parameter Nutrient availability", options_y_n)
    Parameter_Pollutant_concentration = st.sidebar.pills("Parameter Pollutant concentration", options_y_n)
    Parameter_Soil_depth = st.sidebar.pills("Parameter Soil depth", options_y_n)
    Parameter_Others = st.sidebar.pills("Parameter Others", options_y_n)
    Parameter_Others_Precision = st.sidebar.text_input('PPlease write it with a capital letter and a "_" between words:')

    st.write("- Data type")
    Data_Land_Management = st.sidebar.pills("Data Land Management", options_y_n)
    Data_Spatial_images = st.sidebar.pills("Data Spatial images", options_y_n)
    Data_Soil_samples = st.sidebar.pills("Data Soil samples", options_y_n)
    Data_Modelling = st.sidebar.pills("Data Modelling", options_y_n)

    st.write("- Sampling design")
    Plot_Area = st.sidebar.number_input("Please insert a number", value=None, placeholder="Type a number...")
    Plot_Area_Unit = st.sidebar.text_input('Please indicate the spatial unit i.e. hectares, km2, etc.:')
    Monitoring_frequency = st.sidebar.selectbox('Monitoring frequency', ('Less_5_years', '5_10_years', '10_15_years', 'More_15_years'))
    Methodology_Standard = st.sidebar.pills("Methodology Standard", options_y_n)
    Methodology_Others = st.sidebar.pills("Methodology Others", options_y_n)


elif app_mode == 'Articles':
    st.title('LIBRARY')
    st.divider()
    phrase = '''
    ici soit lister la biblio comme dans l'article, soit mettre menu déroulant avec liste des articles et permettre à l'utilisateur de les afficher (ou peut-être juste l'abstract)
    '''
    st.subheader(phrase)
    st.divider()

################################################################################################ END ################################################################################################