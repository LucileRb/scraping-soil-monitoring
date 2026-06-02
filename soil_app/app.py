################################################################################################ IMPORTS ################################################################################################
import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from PIL import Image

# Chemins absolus des illustrations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Liste des fichiers JPG d'illustrations
JPG_FILES = []
if os.path.exists(os.path.join(BASE_DIR, 'app_illustrations')):
    JPG_FILES = sorted([f for f in os.listdir(os.path.join(BASE_DIR, 'app_illustrations')) if f.endswith('.jpg')])

# Définir le chemin de la bannière Home et du logo de la barre latérale à partir des fichiers JPG
if os.path.exists(os.path.join(BASE_DIR, 'app_illustrations', '1000129996.jpg')):
    BANNER_PATH = os.path.join(BASE_DIR, 'app_illustrations', '1000129996.jpg')
elif JPG_FILES:
    BANNER_PATH = os.path.join(BASE_DIR, 'app_illustrations', JPG_FILES[0])
else:
    BANNER_PATH = None

if JPG_FILES:
    logo_name = JPG_FILES[1] if len(JPG_FILES) > 1 else JPG_FILES[0]
    LOGO_PATH = os.path.join(BASE_DIR, 'app_illustrations', logo_name)
else:
    LOGO_PATH = None

@st.cache_resource
def get_cropped_image(image_path, target_w, target_h):
    """
    Découpe et redimensionne une image pour correspondre au ratio cible,
    puis la redimensionne aux dimensions cibles.
    Met en cache le résultat pour un chargement instantané.
    """
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        with Image.open(image_path) as img:
            img_w, img_h = img.size
            target_ratio = target_w / target_h
            current_ratio = img_w / img_h
            
            if current_ratio > target_ratio:
                # Plus large que le ratio cible : recadrer les côtés
                new_w = int(img_h * target_ratio)
                left = (img_w - new_w) // 2
                right = left + new_w
                top = 0
                bottom = img_h
            else:
                # Plus haut que le ratio cible : recadrer le haut/bas
                new_h = int(img_w / target_ratio)
                top = (img_h - new_h) // 2
                bottom = top + new_h
                left = 0
                right = img_w
                
            img_cropped = img.crop((left, top, right, bottom))
            img_resized = img_cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
            img_resized.load()  # Charger les pixels en mémoire
            return img_resized
    except Exception as e:
        try:
            return Image.open(image_path)
        except Exception:
            return None

@st.cache_data
def get_base64_image(image_path):
    """
    Charge une image, la recadre en 3:2, la redimensionne à 300x200,
    puis renvoie sa chaîne Base64 pour l'injecter dans le HTML de la carte Pokemon.
    """
    if not image_path or not os.path.exists(image_path):
        return ""
    try:
        import io
        img = get_cropped_image(image_path, 300, 200)
        if img is None:
            return ""
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception as e:
        return ""

def calculate_hp(mrv_data):
    """
    Calcule les PV (HP) d'un framework en comptant le nombre de critères 'Yes'
    dans les caractéristiques principales (usages, échelles, paramètres, données).
    Base de 60 HP + 10 HP par critère actif, plafonné à 150 HP.
    """
    yes_count = 0
    for col in mrv_data.index:
        if (col.startswith('Parameter_') or col.startswith('Land_use_') or col.startswith('Scale_') or col.startswith('Data_')) and mrv_data[col] == 'Yes':
            yes_count += 1
    return min(60 + yes_count * 10, 150)

def generate_pokemon_card_html(mrv_data):
    """
    Génère le code HTML complet pour afficher un framework MRV sous la forme
    d'une carte Pokemon personnalisée avec un encadré de caractéristiques techniques au lieu d'une image.
    """
    src = mrv_data.get('Source', 'AI Search')
    hp = calculate_hp(mrv_data)
    
    if src == 'Literature (Scopus)':
        card_type = 'grass'
        type_emoji = '🌱'
        energy_cost_2 = '🌱🌱'
    elif src == 'Webscraping':
        card_type = 'water'
        type_emoji = '💧'
        energy_cost_2 = '💧💧'
    else:
        card_type = 'psychic'
        type_emoji = '🔮'
        energy_cost_2 = '🔮🔮'
        
    # Usages (English)
    land_uses = []
    for lu_label, col in [('Agriculture', 'Land_use_Agriculture'), ('Forest', 'Land_use_Forest'), ('Urban', 'Land_use_Urban'), ('Degraded', 'Land_use_Degraded_land'), ('Wetland', 'Land_use_Peatland_Wetland')]:
        if mrv_data.get(col) == 'Yes':
            land_uses.append(lu_label)
    land_uses_str = ", ".join(land_uses) if land_uses else "None"
    
    # Échelles (English)
    scales = []
    for sc_label, col in [('Local', 'Scale_Local'), ('Regional', 'Scale_Regional'), ('National', 'Scale_National'), ('Global', 'Scale_Global')]:
        if mrv_data.get(col) == 'Yes':
            scales.append(sc_label)
    scales_str = ", ".join(scales) if scales else "None"
    
    # Paramètres (English)
    params = []
    for p_label, col in [('SOC', 'Parameter_Soil_organic_matter_SOC'), ('pH', 'Parameter_Soil_pH'), ('Moisture', 'Parameter_Soil_moisture'), ('Temperature', 'Parameter_Soil_temperature'), ('Microorg.', 'Parameter_Soil_Microorganisms'), ('GHG', 'Parameter_GHG')]:
        if mrv_data.get(col) == 'Yes':
            params.append(p_label)
    params_str = ", ".join(params) if params else "None"
    
    # Données (English)
    data_types = []
    for d_label, col in [('Management', 'Data_Land_Management'), ('Spatial/Sat', 'Data_Spatial_images'), ('Samples', 'Data_Soil_samples'), ('Models', 'Data_Modelling')]:
        if mrv_data.get(col) == 'Yes':
            data_types.append(d_label)
    data_str = ", ".join(data_types) if data_types else "None"
    
    # Stats (English)
    uncertainty = mrv_data.get('Uncertainty', 'N/A')
    if str(uncertainty).lower() in ['nan', 'unknown', '']:
        uncertainty = 'Standard'
        
    auditor = mrv_data.get('Auditor', 'N/A')
    if str(auditor).lower() in ['nan', 'unknown', '']:
        auditor = 'Internal'
    elif auditor == 'Interne':
        auditor = 'Internal'
    elif auditor == 'Externe':
        auditor = 'External'
        
    impl = mrv_data.get('Implementation', 'Project')
    sharing = mrv_data.get('Data_Sharing', 'No')
    threshold = mrv_data.get('Threshold', 'N/A')
    if str(threshold).lower() in ['nan', 'unknown', '']:
        threshold = 'Standard'
    
    retreat_stars = '⭐' if impl == 'Implemented' else '⭐⭐⭐'
    
    mrv_id = mrv_data.get('ID_MRV', 'N/A')
    mrv_name = mrv_data.get('MRV_Name', 'Framework')
    author = mrv_data.get('Pub_Author', 'Unknown')
    year = mrv_data.get('Pub_Year', '2025')
    country = mrv_data.get('Country', 'Global')
    purpose = mrv_data.get('Purpose', 'Not specified')
    
    display_name = mrv_name[:24] + '...' if len(mrv_name) > 26 else mrv_name
    
    html = (
        f'<div class="pokemon-card-wrapper">'
        f'<div class="pokemon-card card-{card_type}">'
        f'<div class="pokemon-card-header">'
        f'<span class="pokemon-card-name">{display_name}</span>'
        f'<span class="pokemon-card-hp">{hp} HP {type_emoji}</span>'
        f'</div>'
        f'<div class="pokemon-card-img-container">'
        f'<div class="pokemon-card-specs-box">'
        f'<div class="pokemon-spec-row"><span class="pokemon-spec-label">Status:</span><span class="pokemon-spec-val">{impl}</span></div>'
        f'<div class="pokemon-spec-row"><span class="pokemon-spec-label">Auditor:</span><span class="pokemon-spec-val">{auditor}</span></div>'
        f'<div class="pokemon-spec-row"><span class="pokemon-spec-label">Data Sharing:</span><span class="pokemon-spec-val">{sharing}</span></div>'
        f'<div class="pokemon-spec-row"><span class="pokemon-spec-label">Threshold:</span><span class="pokemon-spec-val">{threshold}</span></div>'
        f'</div>'
        f'<div class="pokemon-card-img-caption">No. {mrv_id} | {country} | Author: {author} ({year})</div>'
        f'</div>'
        f'<div class="pokemon-card-body">'
        f'<div class="pokemon-card-ability">'
        f'<span class="pokemon-ability-cost">{type_emoji}</span>'
        f'<span class="pokemon-ability-name">Land Uses & Scales</span>'
        f'<div class="pokemon-ability-desc">Uses: <b>{land_uses_str}</b><br>Scale: <b>{scales_str}</b></div>'
        f'</div>'
        f'<div class="pokemon-card-ability">'
        f'<span class="pokemon-ability-cost">{energy_cost_2}</span>'
        f'<span class="pokemon-ability-name">Parameters & Data</span>'
        f'<div class="pokemon-ability-desc">Params: <b>{params_str}</b><br>Data: <b>{data_str}</b></div>'
        f'</div>'
        f'</div>'
        f'<div class="pokemon-card-footer">'
        f'<div class="pokemon-footer-item">'
        f'<span class="pokemon-footer-label">Weakness</span>'
        f'<span class="pokemon-footer-value">{uncertainty}</span>'
        f'</div>'
        f'<div class="pokemon-footer-item">'
        f'<span class="pokemon-footer-label">Resistance</span>'
        f'<span class="pokemon-footer-value">{auditor}</span>'
        f'</div>'
        f'<div class="pokemon-footer-item">'
        f'<span class="pokemon-footer-label">Retreat</span>'
        f'<span class="pokemon-footer-value">{retreat_stars}</span>'
        f'</div>'
        f'</div>'
        f'<div class="pokemon-card-flavor">{purpose}</div>'
        f'</div>'
        f'</div>'
    )
    return html

# Page configuration
st.set_page_config(
    page_title = 'Soil Monitoring & Decision Tool (MRV)',
    page_icon = '🌱',
    layout = 'wide'
)

# Configurer le style de matplotlib pour le thème de l'application
sns.set_theme(style="white")
plt.rcParams.update({
    'font.family': 'sans-serif',
    'text.color': '#E2E8F0',
    'axes.labelcolor': '#E2E8F0',
    'xtick.color': '#94A3B8',
    'ytick.color': '#94A3B8',
    'figure.facecolor': 'none',
    'axes.facecolor': 'none',
    'axes.edgecolor': '#24352C',
    'grid.color': '#1B2922',
})

################################################################################################ DATA LOADER ################################################################################################

@st.cache_data
def load_and_clean_data():
    # Définir le chemin des données relatif au workspace
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    
    # 1. Charger la structure des variables (Readme)
    variables_path = os.path.join(data_dir, 'variables.json')
    variables = []
    if os.path.exists(variables_path):
        with open(variables_path, 'r', encoding='utf-8') as f:
            variables = json.load(f)
            
    # 2. Charger et fusionner les 3 fichiers textes
    txt_files = ['db_articles-11-04-26.txt', 'db_webscraping-27-04-26.txt', 'db_AI-13-04-26.txt']
    dfs = []
    
    for fn in txt_files:
        path = os.path.join(data_dir, fn)
        if not os.path.exists(path):
            continue
            
        df = pd.read_csv(path, sep='\t')
        df.columns = [c.strip() for c in df.columns]
        
        # Filtrer par In_Scope == Yes (insensible à la casse, espaces nettoyés)
        if 'In_Scope' in df.columns:
            df['In_Scope_Clean'] = df['In_Scope'].astype(str).str.strip().str.lower()
            df_yes = df[df['In_Scope_Clean'] == 'yes'].copy()
            df_yes['Source_File'] = fn
            
            # Ajouter une colonne source propre
            if fn == 'db_articles-11-04-26.txt':
                df_yes['Source'] = 'Literature (Scopus)'
            elif fn == 'db_webscraping-27-04-26.txt':
                df_yes['Source'] = 'Webscraping'
            else:
                df_yes['Source'] = 'AI Search'
                
            dfs.append(df_yes)
            
    if not dfs:
        return variables, pd.DataFrame()
        
    combined = pd.concat(dfs, ignore_index=True, sort=False)
    combined.columns = [c.strip() for c in combined.columns]
    
    # 3. Standardiser les colonnes binaires (Yes/No)
    binary_prefixes = ['Land_use_', 'Scale_', 'Parameter_', 'Data_', 'Format_', 'Verification_', 'Methodology_']
    binary_exacts = ['Action_based', 'Result_based', 'Data_Sharing']
    
    binary_cols = []
    for col in combined.columns:
        if any(col.startswith(p) for p in binary_prefixes) or col in binary_exacts:
            if not any(word in col.lower() for word in ['precision', 'unit', 'frequency', 'other', 'comments']):
                binary_cols.append(col)
                
    for col in binary_cols:
        combined[col] = combined[col].astype(str).str.strip().str.lower()
        combined[col] = combined[col].apply(lambda x: 'Yes' if x == 'yes' else 'No')
        
    # 4. Standardiser les variables catégorielles
    # Purpose
    combined['Purpose'] = combined['Purpose'].astype(str).str.strip()
    combined['Purpose'] = combined['Purpose'].replace({'nan': 'Unknown', '': 'Unknown', 'NA': 'Unknown'})
    
    # Monitoring frequency
    combined['Monitoring_frequency'] = combined['Monitoring_frequency'].astype(str).str.strip()
    freq_map = {
        'Less_5_years': 'Less than 5 years',
        'Less_5_years ': 'Less than 5 years',
        '5_10_years': '5 to 10 years',
        '10_15_years': '10 to 15 years',
        'More_15_years': 'More than 15 years',
        'nan': 'Unknown',
        'NA': 'Unknown',
        '': 'Unknown',
        'Depends': 'Depends/Flexible'
    }
    combined['Monitoring_frequency'] = combined['Monitoring_frequency'].replace(freq_map)
    combined['Monitoring_frequency'] = combined['Monitoring_frequency'].fillna('Unknown')
    
    # Uncertainty
    combined['Uncertainty'] = combined['Uncertainty'].astype(str).str.strip()
    combined['Uncertainty'] = combined['Uncertainty'].replace({'nan': 'Unknown', '': 'Unknown', 'NA': 'Unknown'})
    
    # Threshold
    combined['Threshold'] = combined['Threshold'].astype(str).str.strip()
    combined['Threshold'] = combined['Threshold'].replace({'nan': 'Unknown', '': 'Unknown', 'NA': 'Unknown'})
    
    # Auditor
    combined['Auditor'] = combined['Auditor'].astype(str).str.strip()
    combined['Auditor'] = combined['Auditor'].replace({'nan': 'Unknown', '': 'Unknown', 'NA': 'Unknown'})
    
    # Implementation
    combined['Implementation'] = combined['Implementation'].astype(str).str.strip()
    combined['Implementation'] = combined['Implementation'].replace({'nan': 'Unknown', '': 'Unknown', 'NA': 'Unknown'})
    
    # 5. Corriger les noms des MRVs
    combined['MRV_Name'] = combined['MRV_Name'].fillna('').astype(str).str.strip()
    combined['MRV_Name'] = combined.apply(
        lambda r: r['ID_MRV'] if not r['MRV_Name'] or r['MRV_Name'].lower() == 'na' else r['MRV_Name'], 
        axis=1
    )
    
    # 6. Créer des colonnes consolidées pour l'affichage des sources
    pub_title = []
    pub_author = []
    pub_year = []
    pub_link = []
    
    for idx, r in combined.iterrows():
        # Title
        t = r.get('Title')
        if pd.notna(t) and str(t).strip() != '' and str(t).strip().lower() != 'nan':
            title_val = str(t).strip()
        else:
            title_val = r['MRV_Name'] if r['Source'] == 'Webscraping' else 'Source URL'
        pub_title.append(title_val)
        
        # Author
        a = r.get('First_Author')
        if pd.notna(a) and str(a).strip() != '' and str(a).strip().lower() != 'nan':
            author_val = str(a).strip()
        else:
            comp = r.get('company')
            if pd.notna(comp) and str(comp).strip() != '' and str(comp).strip().lower() != 'nan':
                author_val = str(comp).strip().capitalize()
            else:
                tool = r.get('AI_Tool')
                if pd.notna(tool) and str(tool).strip() != '' and str(tool).strip().lower() != 'nan':
                    author_val = str(tool).strip()
                else:
                    author_val = 'Unknown'
        pub_author.append(author_val)
        
        # Year
        y = r.get('Year')
        py = r.get('Publication_Year')
        if pd.notna(y) and str(y).replace('.0','').strip().isdigit():
            year_val = str(int(float(y)))
        elif pd.notna(py) and str(py).replace('.0','').strip().isdigit():
            year_val = str(int(float(py)))
        else:
            # Essayer d'extraire de Date pour le webscraping
            dt = r.get('Date')
            if pd.notna(dt) and '/' in str(dt):
                year_val = str(dt).split('/')[-1].strip()
            else:
                year_val = '2025'
        pub_year.append(year_val)
        
        # Link
        d = r.get('DOI')
        url_col = r.get('url')
        url_col_cap = r.get('URL')
        
        if pd.notna(d) and str(d).strip() != '' and str(d).strip().lower() != 'nan':
            doi_val = str(d).strip()
            link_val = doi_val if doi_val.startswith('http') else f"https://doi.org/{doi_val}"
        elif pd.notna(url_col) and str(url_col).strip() != '' and str(url_col).strip().lower() != 'nan':
            link_val = str(url_col).strip()
        elif pd.notna(url_col_cap) and str(url_col_cap).strip() != '' and str(url_col_cap).strip().lower() != 'nan':
            link_val = str(url_col_cap).strip()
        else:
            link_val = ''
        pub_link.append(link_val)
        
    combined_copy = combined.copy()
    combined_copy['Pub_Title'] = pub_title
    combined_copy['Pub_Author'] = pub_author
    combined_copy['Pub_Year'] = pub_year
    combined_copy['Pub_Link'] = pub_link
    
    return variables, combined_copy

# Charger les données globales
variables, combined_df = load_and_clean_data()

################################################################################################ STYLE CSS ################################################################################################

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Variables CSS - Dark Mode */
    :root {
        --primary-color: #52B788;
        --secondary-color: #DAB254;
        --bg-color: #0E1612;
        --sidebar-bg: #15221B;
        --card-bg: #1B2B22;
        --text-color: #E2E8F0;
        --text-muted: #94A3B8;
        --border-color: #24352C;
        --accent-light: #2C5E43;
    }
    
    /* Config générale */
    .stApp {
        font-family: 'Outfit', sans-serif !important;
        background-color: var(--bg-color) !important;
        color: var(--text-color) !important;
    }
    
    /* Forcer la couleur du texte pour le markdown et les paragraphes */
    .stApp p, .stApp span, .stApp li, .stApp label, .stApp div {
        color: var(--text-color);
    }
    
    .stApp [data-testid="stWidgetLabel"] p {
        color: var(--text-color) !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        color: var(--primary-color) !important;
        font-weight: 700 !important;
    }
    
    /* Barre latérale */
    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
        border-right: 1px solid var(--border-color);
    }
    [data-testid="stSidebar"] * {
        color: var(--text-color) !important;
    }
    
    /* Cartes KPI */
    .kpi-container {
        display: flex;
        gap: 16px;
        flex-wrap: wrap;
        margin-bottom: 24px;
    }
    .kpi-card {
        background: var(--card-bg) !important;
        padding: 20px 24px;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        border-left: 6px solid var(--primary-color);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        flex: 1;
        min-width: 200px;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 25px rgba(82, 183, 136, 0.15);
    }
    .kpi-num {
        font-size: 32px;
        font-weight: 700;
        color: var(--primary-color) !important;
        line-height: 1.2;
    }
    .kpi-label {
        font-size: 13px;
        color: var(--text-muted) !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 6px;
        font-weight: 500;
    }
    
    /* Badges */
    .mrv-badge {
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        display: inline-block;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .badge-lit { background-color: #1A365D; color: #90CDF4; border: 1px solid #2B6CB0; }
    .badge-web { background-color: #1C4532; color: #9AE6B4; border: 1px solid #2F855A; }
    .badge-ai { background-color: #4A1248; color: #FBB6CE; border: 1px solid #B83280; }
    
    .badge-yes { background-color: #1C4532; color: #9AE6B4; font-size: 11px; font-weight: bold; border-radius: 4px; padding: 2px 6px; }
    .badge-no { background-color: #742A2A; color: #FEB2B2; font-size: 11px; font-weight: bold; border-radius: 4px; padding: 2px 6px; }
    
    /* Titres de section */
    .section-header {
        color: var(--primary-color) !important;
        font-size: 18px;
        font-weight: 700;
        border-bottom: 2px solid var(--primary-color);
        padding-bottom: 6px;
        margin-top: 24px;
        margin-bottom: 12px;
    }
    
    /* Fiches MRV */
    .mrv-profile-card {
        background: var(--card-bg) !important;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        border: 1px solid var(--border-color);
        margin-bottom: 20px;
    }
    
    /* Progress bar pour les correspondances */
    .match-container {
        background-color: var(--border-color);
        border-radius: 8px;
        height: 8px;
        width: 100%;
        margin-top: 8px;
        overflow: hidden;
    }
    .match-bar {
        height: 100%;
        border-radius: 8px;
    }
    
    /* --- SYSTEM DE CARTES POKEMON --- */
    .pokemon-card-wrapper {
        display: flex;
        justify-content: center;
        margin-bottom: 24px;
        perspective: 1000px;
    }
    
    .pokemon-card {
        width: 100%;
        max-width: 350px;
        background: #111;
        border-radius: 18px;
        padding: 12px 14px 14px 14px;
        box-sizing: border-box;
        transition: all 0.5s cubic-bezier(0.23, 1, 0.320, 1);
        position: relative;
        overflow: hidden;
        border: 4px solid #c89d3c;
    }
    
    .pokemon-card:hover {
        transform: translateY(-8px) rotateY(2deg);
    }
    
    .card-grass {
        background: linear-gradient(135deg, #1b3a24, #0e1e13);
        box-shadow: 0 15px 35px rgba(0,0,0,0.6), 0 0 15px rgba(82, 183, 136, 0.4);
    }
    
    .card-water {
        background: linear-gradient(135deg, #142f44, #0b1a26);
        box-shadow: 0 15px 35px rgba(0,0,0,0.6), 0 0 15px rgba(59, 130, 246, 0.4);
    }
    
    .card-psychic {
        background: linear-gradient(135deg, #2b1836, #160c1c);
        box-shadow: 0 15px 35px rgba(0,0,0,0.6), 0 0 15px rgba(167, 139, 250, 0.4);
    }
    
    .pokemon-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
        border-bottom: 2px solid rgba(255, 255, 255, 0.15);
        padding-bottom: 4px;
    }
    
    .pokemon-card-name {
        font-size: 15px;
        font-weight: 700;
        color: #FFFFFF !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    .pokemon-card-hp {
        font-size: 14px;
        font-weight: 700;
        color: #ff5555 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
        white-space: nowrap;
    }
    
    .pokemon-card-img-container {
        background: #000;
        border: 3px solid #c89d3c;
        border-radius: 8px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        align-items: center;
        box-shadow: inset 0 0 12px rgba(0,0,0,0.8);
        margin-bottom: 8px;
    }
    
    .pokemon-card-img {
        width: 100%;
        height: 160px;
        object-fit: cover;
        display: block;
    }
    
    .pokemon-card-no-img {
        width: 100%;
        height: 160px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 48px;
        background: #1c1d1a;
    }
    
    .pokemon-card-img-caption {
        background: linear-gradient(90deg, #c89d3c, #dab254);
        color: #0b1612 !important;
        font-size: 9px;
        font-weight: 700;
        width: 100%;
        text-align: center;
        padding: 2px 0;
        border-top: 2px solid #c89d3c;
        text-shadow: none;
    }
    
    .pokemon-card-body {
        padding: 2px 0;
    }
    
    .pokemon-card-ability {
        margin-bottom: 6px;
        padding: 6px 8px;
        border-radius: 8px;
        background: rgba(0,0,0,0.3);
        border: 1px solid rgba(255, 255, 255, 0.07);
    }
    
    .pokemon-ability-cost {
        font-size: 13px;
        margin-right: 6px;
        display: inline-block;
        vertical-align: middle;
    }
    
    .pokemon-ability-name {
        font-weight: 700;
        color: #dab254 !important;
        font-size: 12px;
        display: inline-block;
        vertical-align: middle;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.8);
    }
    
    .pokemon-ability-desc {
        font-size: 10px;
        color: #e2e8f0 !important;
        margin-top: 3px;
        line-height: 1.35;
    }
    
    .pokemon-card-footer {
        display: flex;
        justify-content: space-between;
        border-top: 1px solid rgba(255, 255, 255, 0.15);
        padding-top: 6px;
        margin-top: 6px;
        font-size: 10px;
        color: #94a3b8;
    }
    
    .pokemon-footer-item {
        text-align: center;
        flex: 1;
    }
    
    .pokemon-footer-label {
        display: block;
        font-size: 8px;
        text-transform: uppercase;
        color: #64748b;
        font-weight: 600;
        margin-bottom: 2px;
    }
    
    .pokemon-footer-value {
        font-weight: 700;
        color: #e2e8f0 !important;
    }
    
    .pokemon-card-flavor {
        font-style: italic;
        font-size: 9px;
        color: #a1a1aa !important;
        text-align: center;
        margin-top: 6px;
        padding: 4px 6px;
        background: rgba(0, 0, 0, 0.25);
        border-radius: 4px;
        border-left: 3px solid #dab254;
        line-height: 1.3;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    .pokemon-card-specs-box {
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        background: rgba(0, 0, 0, 0.4);
        padding: 10px 12px;
        height: 160px;
        box-sizing: border-box;
        width: 100%;
    }
    
    .pokemon-spec-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        padding-bottom: 3px;
        margin-bottom: 3px;
    }
    
    .pokemon-spec-row:last-child {
        border-bottom: none;
        padding-bottom: 0;
        margin-bottom: 0;
    }
    
    .pokemon-spec-label {
        font-size: 10px;
        color: #dab254;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .pokemon-spec-val {
        font-size: 10px;
        color: #e2e8f0;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

################################################################################################ DASHBOARD ################################################################################################

# Page configuration and sidebar navigation
if LOGO_PATH:
    st.sidebar.image(LOGO_PATH, use_column_width=True)
st.sidebar.markdown(f"<div style='text-align: center; color: #2C5E43; font-weight: bold; margin-bottom: 15px;'>Soil & MRV Database</div>", unsafe_allow_html=True)

app_mode = st.sidebar.selectbox('Navigation Menu', [
    '🏠 Home',
    '🔎 Decision Tool',
    '🗂️ Pokedex',
    '📚 Articles',
    '📊 MRV Guide'
])

# Clean the emoji and text for routing
mode_clean = app_mode.replace('🏠 ', '').replace('🔎 ', '').replace('🗂️ ', '').replace('📚 ', '').replace('📊 ', '')

# ----------------- HOME PAGE -----------------
if mode_clean == 'Home':
    st.markdown(f"<h1>Soil Health & MRV Exploration Tool</h1>", unsafe_allow_html=True)
    st.markdown("""
    This interactive application allows you to explore and filter **Monitoring, Reporting, and Verification (MRV)** methodologies applied to soil carbon and quality assessment.
    The data combines publications from a systematic literature review (**Scopus**), **web scraping** of certification platforms and methodologies, and **AI-assisted** research.
    """)
    if BANNER_PATH:
        banner_cropped = get_cropped_image(BANNER_PATH, 1200, 250)
        if banner_cropped:
            st.image(banner_cropped, use_column_width=True)
    st.divider()
    
    # 1. KPIs
    st.markdown(f"<h3>Database Statistics</h3>", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-num">96</div>
            <div class="kpi-label">MRV Frameworks</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-num">26</div>
            <div class="kpi-label">Literature Reviews</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-num">69</div>
            <div class="kpi-label">Web Scraping</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-num">1</div>
            <div class="kpi-label">AI Search</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.divider()
    
    # 2. Charts
    st.markdown(f"<h3>Framework Distribution</h3>", unsafe_allow_html=True)
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("<p style='font-weight: 600; color: #52B788;'>Distribution by Land Use</p>", unsafe_allow_html=True)
        # Calculate the number of Yes for each Land Use type
        lu_columns = {
            'Agriculture': 'Land_use_Agriculture',
            'Forest': 'Land_use_Forest',
            'Urban': 'Land_use_Urban',
            'Degraded Land': 'Land_use_Degraded_land',
            'Peatland/Wetland': 'Land_use_Peatland_Wetland'
        }
        lu_counts = {}
        for label, col in lu_columns.items():
            if col in combined_df.columns:
                lu_counts[label] = (combined_df[col] == 'Yes').sum()
                
        fig, ax = plt.subplots(figsize=(6, 3.5))
        y_pos = np.arange(len(lu_counts))
        ax.barh(y_pos, list(lu_counts.values()), color='#52B788', height=0.6, edgecolor='none')
        ax.set_yticks(y_pos)
        ax.set_yticklabels(list(lu_counts.keys()), fontsize=10, fontweight='medium')
        ax.invert_yaxis()  # top-down
        ax.set_xlabel("Number of Frameworks", fontsize=9)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#24352C')
        ax.spines['bottom'].set_color('#24352C')
        plt.tight_layout()
        st.pyplot(fig)
        
    with col_chart2:
        st.markdown("<p style='font-weight: 600; color: #52B788;'>Distribution by Spatial Scale</p>", unsafe_allow_html=True)
        scale_columns = {
            'Local': 'Scale_Local',
            'Regional': 'Scale_Regional',
            'National': 'Scale_National',
            'Continental': 'Scale_Continental',
            'Global': 'Scale_Global'
        }
        scale_counts = {}
        for label, col in scale_columns.items():
            if col in combined_df.columns:
                scale_counts[label] = (combined_df[col] == 'Yes').sum()
                
        fig, ax = plt.subplots(figsize=(6, 3.5))
        y_pos = np.arange(len(scale_counts))
        ax.barh(y_pos, list(scale_counts.values()), color='#DAB254', height=0.6, edgecolor='none')
        ax.set_yticks(y_pos)
        ax.set_yticklabels(list(scale_counts.keys()), fontsize=10, fontweight='medium')
        ax.invert_yaxis()
        ax.set_xlabel("Number of Frameworks", fontsize=9)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#24352C')
        ax.spines['bottom'].set_color('#24352C')
        plt.tight_layout()
        st.pyplot(fig)
        
    st.divider()
    
    # 3. Decision Tool variables structure (variables.json)
    st.markdown(f"<h3>Decision Variables Structure</h3>", unsafe_allow_html=True)
    st.write("This table details the descriptors used in the database. You can search by keyword.")
    
    if variables:
        df_vars = pd.DataFrame(variables)
        df_vars.columns = ['Variable', 'Category', 'Sub-Category', 'Modalities', 'Explanation']
        
        # Search query
        search_query = st.text_input("🔍 Search for a variable...", placeholder="E.g., SOC, Agriculture, Uncertainty...")
        if search_query:
            df_filtered_vars = df_vars[
                df_vars['Variable'].str.contains(search_query, case=False, na=False) |
                df_vars['Category'].str.contains(search_query, case=False, na=False) |
                df_vars['Explanation'].str.contains(search_query, case=False, na=False)
            ]
        else:
            df_filtered_vars = df_vars
            
        st.dataframe(
            df_filtered_vars,
            column_config={
                "Variable": st.column_config.TextColumn("Variable", help="Technical name of the column", width="medium"),
                "Category": st.column_config.TextColumn("Category", width="small"),
                "Sub-Category": st.column_config.TextColumn("Sub-Category", width="small"),
                "Modalities": st.column_config.TextColumn("Modalities", width="medium"),
                "Explanation": st.column_config.TextColumn("Explanation", width="large"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("The variables.json structure file was not found. Please check the data folder.")
        
    # 4. Illustration Gallery
    if JPG_FILES:
        st.divider()
        st.markdown("<h3>📷 Soil Illustration Gallery</h3>", unsafe_allow_html=True)
        st.write("Overview of agricultural landscapes and soil studies in the `app_illustrations` folder:")
        
        cols_per_row = 6
        for idx in range(0, len(JPG_FILES), cols_per_row):
            chunk = JPG_FILES[idx : idx + cols_per_row]
            cols = st.columns(cols_per_row)
            for j, img_name in enumerate(chunk):
                with cols[j]:
                    img_path = os.path.join(BASE_DIR, 'app_illustrations', img_name)
                    img_cropped = get_cropped_image(img_path, 300, 200)
                    if img_cropped:
                        st.image(img_cropped, caption=img_name.split('.')[0], use_column_width=True)

# ----------------- DECISION TOOL PAGE -----------------
elif mode_clean == 'Decision Tool':
    st.markdown(f"<h1>MRV Decision Support Tool</h1>", unsafe_allow_html=True)
    st.markdown("Use the sidebar filters to find MRV frameworks that match your needs.")
    
    # Sidebar Filters construction
    st.sidebar.markdown("<div class='section-header'>Filter Configuration</div>", unsafe_allow_html=True)
    
    # Search mode
    filter_mode = st.sidebar.radio(
        "Search Mode",
        ["⭐ Matching Score (Recommended)", "🔒 Strict Filtering (AND)"],
        help="The matching score ranks results from best to worst, avoiding 0 results if you select multiple criteria."
    )
    
    # 1. Context & Land Uses
    st.sidebar.subheader("🌱 Context & Land Uses")
    
    selected_land_uses = []
    if st.sidebar.checkbox("Agriculture", value=False): selected_land_uses.append('Land_use_Agriculture')
    if st.sidebar.checkbox("Forest", value=False): selected_land_uses.append('Land_use_Forest')
    if st.sidebar.checkbox("Urban", value=False): selected_land_uses.append('Land_use_Urban')
    if st.sidebar.checkbox("Degraded Land", value=False): selected_land_uses.append('Land_use_Degraded_land')
    if st.sidebar.checkbox("Peatland / Wetland", value=False): selected_land_uses.append('Land_use_Peatland_Wetland')
    
    selected_scales = []
    if st.sidebar.checkbox("Local Scale", value=False): selected_scales.append('Scale_Local')
    if st.sidebar.checkbox("Regional Scale", value=False): selected_scales.append('Scale_Regional')
    if st.sidebar.checkbox("National Scale", value=False): selected_scales.append('Scale_National')
    if st.sidebar.checkbox("Global Scale", value=False): selected_scales.append('Scale_Global')
    
    purpose_options = ['All'] + list(combined_df['Purpose'].unique())
    selected_purpose = st.sidebar.selectbox("Purpose", purpose_options)
    
    # 2. Soil Parameters & Data
    st.sidebar.subheader("🔬 Soil Parameters & Data")
    
    selected_params = []
    if st.sidebar.checkbox("Soil Organic Carbon (SOC)", value=False): selected_params.append('Parameter_Soil_organic_matter_SOC')
    if st.sidebar.checkbox("Soil pH", value=False): selected_params.append('Parameter_Soil_pH')
    if st.sidebar.checkbox("Soil Moisture", value=False): selected_params.append('Parameter_Soil_moisture')
    if st.sidebar.checkbox("Soil Temperature", value=False): selected_params.append('Parameter_Soil_temperature')
    if st.sidebar.checkbox("Organic Matter / Microorganisms", value=False): selected_params.append('Parameter_Soil_Microorganisms')
    if st.sidebar.checkbox("Greenhouse Gases (GHG)", value=False): selected_params.append('Parameter_GHG')
    
    selected_data_types = []
    if st.sidebar.checkbox("Land Management Data", value=False): selected_data_types.append('Data_Land_Management')
    if st.sidebar.checkbox("Spatial / Satellite Imagery", value=False): selected_data_types.append('Data_Spatial_images')
    if st.sidebar.checkbox("Physical Soil Sampling", value=False): selected_data_types.append('Data_Soil_samples')
    if st.sidebar.checkbox("Numerical Modelling", value=False): selected_data_types.append('Data_Modelling')
    
    # 3. Reporting & Verification
    st.sidebar.subheader("📝 Reporting & Verification")
    
    selected_verif_schemes = []
    if st.sidebar.checkbox("Action-based Scheme", value=False): selected_verif_schemes.append('Action_based')
    if st.sidebar.checkbox("Result-based Scheme", value=False): selected_verif_schemes.append('Result_based')
    
    auditor_options = ['All', 'External', 'Internal']
    selected_auditor = st.sidebar.selectbox("Auditor", auditor_options)
    
    sharing_options = ['All', 'Yes', 'No']
    selected_sharing = st.sidebar.selectbox("Data Sharing", sharing_options)
    
    state_options = ['All', 'Implemented', 'Project']
    selected_state = st.sidebar.selectbox("Implementation Status", state_options)

    # Calcul des filtres actifs
    active_filters = {}
    for col in selected_land_uses: active_filters[col] = 'Yes'
    for col in selected_scales: active_filters[col] = 'Yes'
    for col in selected_params: active_filters[col] = 'Yes'
    for col in selected_data_types: active_filters[col] = 'Yes'
    for col in selected_verif_schemes: active_filters[col] = 'Yes'
    
    if selected_purpose != 'All': active_filters['Purpose'] = selected_purpose
    if selected_auditor != 'All': active_filters['Auditor'] = selected_auditor
    if selected_sharing != 'All': active_filters['Data_Sharing'] = selected_sharing
    if selected_state != 'All': active_filters['Implementation'] = selected_state

    # 4. Appliquer le Filtrage
    df_results = combined_df.copy()
    
    if "🔒 Filtrage Strict (ET)" in filter_mode:
        # Filtrer strictement
        for col, val in active_filters.items():
            df_results = df_results[df_results[col] == val]
        df_results['Match_Score'] = 100
    else:
        # Score de correspondance
        if active_filters:
            scores = []
            for idx, row in df_results.iterrows():
                pts = 0
                for col, val in active_filters.items():
                    if str(row.get(col, '')).strip().lower() == val.lower():
                        pts += 1
                scores.append(round((pts / len(active_filters)) * 100))
            df_results['Match_Score'] = scores
        else:
            df_results['Match_Score'] = 100
            
        df_results = df_results.sort_values(by=['Match_Score', 'ID_MRV'], ascending=[False, True])

    # Search stats display
    num_matches = len(df_results)
    if "🔒 Strict Filtering" in filter_mode:
        st.markdown(f"<h3>{num_matches} frameworks match your criteria exactly</h3>", unsafe_allow_html=True)
    else:
        st.markdown(f"<h3>Ranking of 96 frameworks by match level</h3>", unsafe_allow_html=True)
        
    st.divider()
    
    # Results table
    display_cols = ['ID_MRV', 'MRV_Name', 'Source', 'Match_Score', 'Purpose', 'Implementation']
    df_table = df_results[display_cols].copy()
    df_table.columns = ['ID', 'Framework Name', 'Data Source', 'Matching Score (%)', 'Purpose', 'Implementation']
    
    st.dataframe(
        df_table,
        column_config={
            "Matching Score (%)": st.column_config.ProgressColumn(
                "Matching Score (%)",
                help="Percentage of validated criteria",
                format="%d%%",
                min_value=0,
                max_value=100
            ),
            "ID": st.column_config.TextColumn("ID", width="small"),
            "Framework Name": st.column_config.TextColumn("Framework Name", width="medium"),
            "Data Source": st.column_config.TextColumn("Data Source", width="small"),
            "Purpose": st.column_config.TextColumn("Purpose", width="small"),
            "Implementation": st.column_config.TextColumn("Implementation", width="small"),
        },
        hide_index=True,
        use_container_width=True
    )
    
    st.divider()
    
    # Select an MRV to view its profile
    if not df_results.empty:
        st.markdown(f"<h3>Detailed profile of the selected framework</h3>", unsafe_allow_html=True)
        
        mrv_options = df_results['ID_MRV'] + " - " + df_results['MRV_Name']
        selected_mrv_str = st.selectbox("Select a framework to inspect:", mrv_options)
        
        selected_mrv_id = selected_mrv_str.split(" - ")[0]
        mrv_data = df_results[df_results['ID_MRV'] == selected_mrv_id].iloc[0]
        
        # Draw detailed profile
        with st.container():
            # Determine source badge class
            src = mrv_data['Source']
            badge_class = "badge-lit"
            if src == 'Webscraping': badge_class = "badge-web"
            elif src == 'AI Search': badge_class = "badge-ai"
            
            if JPG_FILES:
                img_idx = abs(hash(str(mrv_data['ID_MRV']))) % len(JPG_FILES)
                img_name = JPG_FILES[img_idx]
                img_path = os.path.join(BASE_DIR, 'app_illustrations', img_name)
                
                col_card_text, col_card_img = st.columns([3, 1])
                with col_card_text:
                    st.markdown(f"""
                    <div class="mrv-profile-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 24px; font-weight: bold; color: #2C5E43;">{mrv_data['MRV_Name']}</span>
                            <span class="mrv-badge {badge_class}">{src}</span>
                        </div>
                        <div style="color: #666; margin-top: 4px;">Framework ID: <b>{mrv_data['ID_MRV']}</b></div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_card_img:
                    st.image(img_path, caption=f"Illustr. {mrv_data['ID_MRV']}", use_column_width=True)
            else:
                st.markdown(f"""
                <div class="mrv-profile-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 24px; font-weight: bold; color: #2C5E43;">{mrv_data['MRV_Name']}</span>
                        <span class="mrv-badge {badge_class}">{src}</span>
                    </div>
                    <div style="color: #666; margin-top: 4px;">Framework ID: <b>{mrv_data['ID_MRV']}</b></div>
                </div>
                """, unsafe_allow_html=True)
            
            # Tabs for structuring information
            tab1, tab2, tab3, tab4 = st.tabs(["📝 General & Source", "🌍 Context & Stakeholders", "🔬 Monitoring", "📊 Reporting & Verification"])
            
            with tab1:
                col_left, col_right = st.columns(2)
                with col_left:
                    st.write(f"**Publication / Source:** {mrv_data['Pub_Title']}")
                    st.write(f"**Author / Platform:** {mrv_data['Pub_Author']}")
                    st.write(f"**Year:** {mrv_data['Pub_Year']}")
                with col_right:
                    st.write(f"**Country:** {mrv_data.get('Country', 'N/A')}")
                    st.write(f"**Continent:** {mrv_data.get('Continent', 'N/A')}")
                    if mrv_data['Pub_Link']:
                        st.markdown(f"[🔗 Access Original Source]({mrv_data['Pub_Link']})")
                    else:
                        st.write("*Source link unavailable*")
                        
            with tab2:
                col_left, col_right = st.columns(2)
                with col_left:
                    st.markdown("<div class='section-header'>Land Uses</div>", unsafe_allow_html=True)
                    st.markdown(f"- Agriculture: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Land_use_Agriculture') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Land_use_Agriculture') == 'Yes' else '#C62828'}'>{mrv_data.get('Land_use_Agriculture', 'No')}</span>", unsafe_allow_html=True)
                    st.markdown(f"- Forest: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Land_use_Forest') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Land_use_Forest') == 'Yes' else '#C62828'}'>{mrv_data.get('Land_use_Forest', 'No')}</span>", unsafe_allow_html=True)
                    st.markdown(f"- Urban: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Land_use_Urban') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Land_use_Urban') == 'Yes' else '#C62828'}'>{mrv_data.get('Land_use_Urban', 'No')}</span>", unsafe_allow_html=True)
                    st.markdown(f"- Degraded Land: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Land_use_Degraded_land') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Land_use_Degraded_land') == 'Yes' else '#C62828'}'>{mrv_data.get('Land_use_Degraded_land', 'No')}</span>", unsafe_allow_html=True)
                    st.markdown(f"- Peatland / Wetland: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Land_use_Peatland_Wetland') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Land_use_Peatland_Wetland') == 'Yes' else '#C62828'}'>{mrv_data.get('Land_use_Peatland_Wetland', 'No')}</span>", unsafe_allow_html=True)
                    if mrv_data.get('Land_use_Others_ Precision') and str(mrv_data['Land_use_Others_ Precision']).lower() != 'nan':
                        st.write(f"- Other details: *{mrv_data['Land_use_Others_ Precision']}*")
                        
                    st.markdown("<div class='section-header'>Application Scale</div>", unsafe_allow_html=True)
                    st.markdown(f"- Local: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Scale_Local') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Scale_Local') == 'Yes' else '#C62828'}'>{mrv_data.get('Scale_Local', 'No')}</span>", unsafe_allow_html=True)
                    st.markdown(f"- Regional: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Scale_Regional') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Scale_Regional') == 'Yes' else '#C62828'}'>{mrv_data.get('Scale_Regional', 'No')}</span>", unsafe_allow_html=True)
                    st.markdown(f"- National: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Scale_National') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Scale_National') == 'Yes' else '#C62828'}'>{mrv_data.get('Scale_National', 'No')}</span>", unsafe_allow_html=True)
                    st.markdown(f"- Global: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Scale_Global') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Scale_Global') == 'Yes' else '#C62828'}'>{mrv_data.get('Scale_Global', 'No')}</span>", unsafe_allow_html=True)

                with col_right:
                    st.markdown("<div class='section-header'>Objectives & Drivers</div>", unsafe_allow_html=True)
                    st.write(f"**Market purpose:** {mrv_data['Purpose']}")
                    st.write(f"**Implementation status:** {mrv_data['Implementation']}")
                    
                    # Find active drivers
                    active_drivers = []
                    for c in mrv_data.index:
                        if c.startswith('Driver_') and mrv_data[c] == 'Yes':
                            active_drivers.append(c.replace('Driver_', '').replace('_', ' '))
                    if active_drivers:
                        st.write("**Targeted Agricultural Practices / Drivers:**")
                        for d in active_drivers:
                            st.markdown(f"- {d.capitalize()}")
                    else:
                        st.write("*No specific driver listed*")
                        
            with tab3:
                col_left, col_right = st.columns(2)
                with col_left:
                    st.markdown("<div class='section-header'>Measured Soil Parameters</div>", unsafe_allow_html=True)
                    active_params = []
                    for c in mrv_data.index:
                        if c.startswith('Parameter_') and mrv_data[c] == 'Yes':
                            active_params.append(c.replace('Parameter_', '').replace('_', ' '))
                    if active_params:
                        for p in active_params:
                            st.markdown(f"- {p.capitalize()}")
                    else:
                        st.write("*No standard parameter specified*")
                        
                with col_right:
                    st.markdown("<div class='section-header'>Used Data Types</div>", unsafe_allow_html=True)
                    st.markdown(f"- Management surveys: {mrv_data.get('Data_Land_Management', 'No')}")
                    st.markdown(f"- Satellite / spatial imagery: {mrv_data.get('Data_Spatial_images', 'No')}")
                    st.markdown(f"- Physical soil samples: {mrv_data.get('Data_Soil_samples', 'No')}")
                    st.markdown(f"- Modelling: {mrv_data.get('Data_Modelling', 'No')}")
                    
                    st.markdown("<div class='section-header'>Sampling Plan</div>", unsafe_allow_html=True)
                    st.write(f"**Monitoring frequency:** {mrv_data['Monitoring_frequency']}")
                    st.write(f"**Average plot area:** {mrv_data.get('Plot_Area', 'N/A')} {mrv_data.get('Plot_Area_Unit', '')}")
                    st.write(f"**Standardized methodology:** {mrv_data.get('Methodology_Standard', 'No')}")

            with tab4:
                col_left, col_right = st.columns(2)
                with col_left:
                    st.markdown("<div class='section-header'>Reporting & Uncertainty</div>", unsafe_allow_html=True)
                    st.write(f"**Report format:** Standard document: {mrv_data.get('Format_Document', 'No')} | Online: {mrv_data.get('Format_Online', 'No')}")
                    st.write(f"**Uncertainty calculation method:** {mrv_data['Uncertainty']}")
                    st.write(f"**Threshold calculation method:** {mrv_data['Threshold']}")
                    
                with col_right:
                    st.markdown("<div class='section-header'>Verification</div>", unsafe_allow_html=True)
                    st.write(f"**Action-based scheme:** {mrv_data.get('Action_based', 'No')}")
                    st.write(f"**Result-based scheme:** {mrv_data.get('Result_based', 'No')}")
                    st.write(f"**Auditor:** {mrv_data['Auditor']}")
                    st.write(f"**Data sharing:** {mrv_data.get('Data_Sharing', 'No')}")

# ----------------- POKEDEX (MRV EXPLORER) PAGE -----------------
elif mode_clean == 'Pokedex':
    st.markdown(f"<h1>Framework Explorer (MRV Pokedex)</h1>", unsafe_allow_html=True)
    st.markdown("View and explore all 96 MRV frameworks in our database.")
    st.divider()
    
    # Framework Selector
    mrv_options = combined_df['ID_MRV'] + " - " + combined_df['MRV_Name']
    selected_mrv_str = st.selectbox("Select a framework to inspect:", mrv_options)
    
    selected_mrv_id = selected_mrv_str.split(" - ")[0]
    mrv_data = combined_df[combined_df['ID_MRV'] == selected_mrv_id].iloc[0]
    
    # Technical profile layout (Two-column: Pokemon Card & Technical Specifications)
    col_card, col_details = st.columns([2, 3])
    
    with col_card:
        # Custom Pokemon card HTML display
        card_html = generate_pokemon_card_html(mrv_data)
        st.markdown(card_html, unsafe_allow_html=True)
        
    with col_details:
        # Tabs for technical specs
        tab1, tab2, tab3, tab4 = st.tabs(["📝 General & Source", "🌍 Context & Stakeholders", "🔬 Monitoring", "📊 Reporting & Verification"])
        
        with tab1:
            col_left, col_right = st.columns(2)
            with col_left:
                st.write(f"**Publication / Source:** {mrv_data['Pub_Title']}")
                st.write(f"**Author / Platform:** {mrv_data['Pub_Author']}")
                st.write(f"**Year:** {mrv_data['Pub_Year']}")
            with col_right:
                st.write(f"**Country:** {mrv_data.get('Country', 'N/A')}")
                st.write(f"**Continent:** {mrv_data.get('Continent', 'N/A')}")
                if mrv_data['Pub_Link']:
                    st.markdown(f"[🔗 Access Original Source]({mrv_data['Pub_Link']})")
                else:
                    st.write("*Source link unavailable*")
                    
        with tab2:
            col_left, col_right = st.columns(2)
            with col_left:
                st.markdown("<div class='section-header'>Land Uses</div>", unsafe_allow_html=True)
                st.markdown(f"- Agriculture: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Land_use_Agriculture') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Land_use_Agriculture') == 'Yes' else '#C62828'}'>{mrv_data.get('Land_use_Agriculture', 'No')}</span>", unsafe_allow_html=True)
                st.markdown(f"- Forest: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Land_use_Forest') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Land_use_Forest') == 'Yes' else '#C62828'}'>{mrv_data.get('Land_use_Forest', 'No')}</span>", unsafe_allow_html=True)
                st.markdown(f"- Urban: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Land_use_Urban') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Land_use_Urban') == 'Yes' else '#C62828'}'>{mrv_data.get('Land_use_Urban', 'No')}</span>", unsafe_allow_html=True)
                st.markdown(f"- Degraded Land: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Land_use_Degraded_land') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Land_use_Degraded_land') == 'Yes' else '#C62828'}'>{mrv_data.get('Land_use_Degraded_land', 'No')}</span>", unsafe_allow_html=True)
                st.markdown(f"- Peatland / Wetland: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Land_use_Peatland_Wetland') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Land_use_Peatland_Wetland') == 'Yes' else '#C62828'}'>{mrv_data.get('Land_use_Peatland_Wetland', 'No')}</span>", unsafe_allow_html=True)
                if mrv_data.get('Land_use_Others_ Precision') and str(mrv_data['Land_use_Others_ Precision']).lower() != 'nan':
                    st.write(f"- Other details: *{mrv_data['Land_use_Others_ Precision']}*")
                    
                st.markdown("<div class='section-header'>Application Scale</div>", unsafe_allow_html=True)
                st.markdown(f"- Local: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Scale_Local') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Scale_Local') == 'Yes' else '#C62828'}'>{mrv_data.get('Scale_Local', 'No')}</span>", unsafe_allow_html=True)
                st.markdown(f"- Regional: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Scale_Regional') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Scale_Regional') == 'Yes' else '#C62828'}'>{mrv_data.get('Scale_Regional', 'No')}</span>", unsafe_allow_html=True)
                st.markdown(f"- National: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Scale_National') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Scale_National') == 'Yes' else '#C62828'}'>{mrv_data.get('Scale_National', 'No')}</span>", unsafe_allow_html=True)
                st.markdown(f"- Global: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Scale_Global') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Scale_Global') == 'Yes' else '#C62828'}'>{mrv_data.get('Scale_Global', 'No')}</span>", unsafe_allow_html=True)

            with col_right:
                st.markdown("<div class='section-header'>Objectives & Drivers</div>", unsafe_allow_html=True)
                st.write(f"**Market purpose:** {mrv_data['Purpose']}")
                st.write(f"**Implementation status:** {mrv_data['Implementation']}")
                
                active_drivers = []
                for c in mrv_data.index:
                    if c.startswith('Driver_') and mrv_data[c] == 'Yes':
                        active_drivers.append(c.replace('Driver_', '').replace('_', ' '))
                if active_drivers:
                    st.write("**Targeted Agricultural Practices / Drivers:**")
                    for d in active_drivers:
                        st.markdown(f"- {d.capitalize()}")
                else:
                    st.write("*No specific driver listed*")
                    
        with tab3:
            col_left, col_right = st.columns(2)
            with col_left:
                st.markdown("<div class='section-header'>Measured Soil Parameters</div>", unsafe_allow_html=True)
                active_params = []
                for c in mrv_data.index:
                    if c.startswith('Parameter_') and mrv_data[c] == 'Yes':
                        active_params.append(c.replace('Parameter_', '').replace('_', ' '))
                if active_params:
                    for p in active_params:
                        st.markdown(f"- {p.capitalize()}")
                else:
                    st.write("*No standard parameter specified*")
                    
            with col_right:
                st.markdown("<div class='section-header'>Used Data Types</div>", unsafe_allow_html=True)
                st.markdown(f"- Management surveys: {mrv_data.get('Data_Land_Management', 'No')}")
                st.markdown(f"- Satellite / spatial imagery: {mrv_data.get('Data_Spatial_images', 'No')}")
                st.markdown(f"- Physical soil samples: {mrv_data.get('Data_Soil_samples', 'No')}")
                st.markdown(f"- Modelling: {mrv_data.get('Data_Modelling', 'No')}")
                
                st.markdown("<div class='section-header'>Sampling Plan</div>", unsafe_allow_html=True)
                st.write(f"**Monitoring frequency:** {mrv_data['Monitoring_frequency']}")
                st.write(f"**Average plot area:** {mrv_data.get('Plot_Area', 'N/A')} {mrv_data.get('Plot_Area_Unit', '')}")
                st.write(f"**Standardized methodology:** {mrv_data.get('Methodology_Standard', 'No')}")

        with tab4:
            col_left, col_right = st.columns(2)
            with col_left:
                st.markdown("<div class='section-header'>Reporting & Uncertainty</div>", unsafe_allow_html=True)
                st.write(f"**Report format:** Standard document: {mrv_data.get('Format_Document', 'No')} | Online: {mrv_data.get('Format_Online', 'No')}")
                st.write(f"**Uncertainty calculation method:** {mrv_data['Uncertainty']}")
                st.write(f"**Threshold calculation method:** {mrv_data['Threshold']}")
                
            with col_right:
                st.markdown("<div class='section-header'>Verification</div>", unsafe_allow_html=True)
                st.write(f"**Action-based scheme:** {mrv_data.get('Action_based', 'No')}")
                st.write(f"**Result-based scheme:** {mrv_data.get('Result_based', 'No')}")
                st.write(f"**Auditor:** {mrv_data['Auditor']}")
                st.write(f"**Data sharing:** {mrv_data.get('Data_Sharing', 'No')}")

# ----------------- PAGE ARTICLES (BIBLIOGRAPHY) -----------------
elif mode_clean == 'Articles':
    st.markdown(f"<h1>Publications & Sources Library</h1>", unsafe_allow_html=True)
    st.markdown("Browse and search original publications and websites referenced in our database.")
    st.divider()
    
    # Extract unique publications
    pub_df = combined_df[['Pub_Title', 'Pub_Author', 'Pub_Year', 'Pub_Link', 'Source']].drop_duplicates(subset=['Pub_Title', 'Pub_Author'])
    
    # Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        search_pub = st.text_input("🔍 Search for a publication...", placeholder="Title, author, platform...")
    with col_f2:
        source_filter = st.selectbox("Filter by source type:", ['All', 'Literature (Scopus)', 'Webscraping', 'AI Search'])
        
    filtered_pubs = pub_df.copy()
    if search_pub:
        filtered_pubs = filtered_pubs[
            filtered_pubs['Pub_Title'].str.contains(search_pub, case=False, na=False) |
            filtered_pubs['Pub_Author'].str.contains(search_pub, case=False, na=False)
        ]
    if source_filter != 'All':
        filtered_pubs = filtered_pubs[filtered_pubs['Source'] == source_filter]
        
    st.markdown(f"<h4>{len(filtered_pubs)} publications or sources found</h4>", unsafe_allow_html=True)
    st.write("")
    
    for idx, row in filtered_pubs.iterrows():
        # Determine source badge class
        src = row['Source']
        badge_class = "badge-lit"
        if src == 'Webscraping': badge_class = "badge-web"
        elif src == 'AI Search': badge_class = "badge-ai"
        
        # Find MRV frameworks associated with this publication
        associated_mrvs = combined_df[
            (combined_df['Pub_Title'] == row['Pub_Title']) & 
            (combined_df['Pub_Author'] == row['Pub_Author'])
        ]
        
        with st.container():
            title_html = f'<a href="{row["Pub_Link"]}" target="_blank" style="text-decoration: none; color: var(--primary-color); font-size: 18px; font-weight: 700; hover: underline;">{row["Pub_Title"]} 🔗</a>' if row['Pub_Link'] else f'<span style="font-size: 18px; font-weight: 700; color: var(--text-color);">{row["Pub_Title"]}</span>'
            article_html = (
                f'<div style="background: var(--card-bg); padding: 20px; border-radius: 12px; border: 1px solid var(--border-color); margin-bottom: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">'
                f'<div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px;">'
                f'{title_html}'
                f'<span class="mrv-badge {badge_class}" style="white-space: nowrap;">{src}</span>'
                f'</div>'
                f'<div style="color: var(--text-muted); margin-top: 6px; font-size: 13px;">'
                f'Author/Publisher: <b style="color: var(--text-color);">{row["Pub_Author"]}</b> &nbsp;|&nbsp; Year: <b style="color: var(--text-color);">{row["Pub_Year"]}</b>'
                f'</div>'
                f'</div>'
            )
            st.markdown(article_html, unsafe_allow_html=True)
            
            # Show associated frameworks in an expander
            mrv_names_list = ", ".join([f"{m['ID_MRV']} ({m['MRV_Name']})" for i, m in associated_mrvs.iterrows()])
            with st.expander(f"🔍 Associated MRV Frameworks ({len(associated_mrvs)})"):
                st.write(f"**List of frameworks:** {mrv_names_list}")
                
                # Summary table for associated frameworks
                df_assoc_table = associated_mrvs[['ID_MRV', 'MRV_Name', 'Purpose', 'Implementation']].copy()
                df_assoc_table.columns = ['ID', 'Framework Name', 'Purpose', 'Implementation']
                st.dataframe(df_assoc_table, hide_index=True, use_container_width=True)
                
                if row['Pub_Link']:
                    st.markdown(f"[🔗 Open source online]({row['Pub_Link']})")

# ----------------- PAGE MRV (GUIDE DES FILTRES) -----------------
elif mode_clean == 'MRV Guide':
    st.markdown(f"<h1>Decision Base Filter Guide</h1>", unsafe_allow_html=True)
    st.markdown("""
    This page presents all available filters in the **Decision Support Tool**.
    For each filter, you will find its technical definition, categories, and real-time distribution statistics calculated across the 96 in-scope frameworks.
    """)
    st.divider()
    
    # Definition of filter groups and their metadata
    filters_info = {
        "🌱 Context & Land Uses (Land Use)": [
            {
                "name": "Agriculture",
                "col": "Land_use_Agriculture",
                "desc": "Determines whether the MRV monitoring protocol applies to cropland, livestock, or market gardening.",
                "type": "binary"
            },
            {
                "name": "Forest",
                "col": "Land_use_Forest",
                "desc": "Determines whether the framework applies to forest or wooded areas, or agroforestry projects.",
                "type": "binary"
            },
            {
                "name": "Urban",
                "col": "Land_use_Urban",
                "desc": "Indicates whether the protocol can be used in urban or peri-urban areas (anthropogenic soils).",
                "type": "binary"
            },
            {
                "name": "Degraded Land",
                "col": "Land_use_Degraded_land",
                "desc": "Indicates whether the method is specific to the ecological restoration of degraded, mining, or contaminated soils.",
                "type": "binary"
            },
            {
                "name": "Peatland/Wetland",
                "col": "Land_use_Peatland_Wetland",
                "desc": "Determines whether the framework is suitable for monitoring wetlands or peatlands (water-saturated soils with high organic carbon content).",
                "type": "binary"
            }
        ],
        "🌍 Spatial Scales (Scale)": [
            {
                "name": "Local Scale",
                "col": "Scale_Local",
                "desc": "Monitoring applies locally, typically at the field or farm level.",
                "type": "binary"
            },
            {
                "name": "Regional Scale",
                "col": "Scale_Regional",
                "desc": "Monitoring is carried out at the scale of a large territory, region, or watershed.",
                "type": "binary"
            },
            {
                "name": "National Scale",
                "col": "Scale_National",
                "desc": "The methodology is designed for national GHG inventories or public policies at a country's scale.",
                "type": "binary"
            },
            {
                "name": "Global Scale",
                "col": "Scale_Global",
                "desc": "The monitoring protocol is universal, applicable at an international or global level.",
                "type": "binary"
            }
        ],
        "🔬 Soil Parameters": [
            {
                "name": "Soil Organic Carbon (SOC)",
                "col": "Parameter_Soil_organic_matter_SOC",
                "desc": "Quantitative measurement of soil organic matter or soil organic carbon (SOC). It is the main parameter for carbon sequestration.",
                "type": "binary"
            },
            {
                "name": "Soil pH",
                "col": "Parameter_Soil_pH",
                "desc": "Measurement of soil pH, which directly influences nutrient availability and microbiological activity.",
                "type": "binary"
            },
            {
                "name": "Soil Moisture",
                "col": "Parameter_Soil_moisture",
                "desc": "Monitoring of soil water content, a key parameter for assessing water stress or biological activity.",
                "type": "binary"
            },
            {
                "name": "Soil Temperature",
                "col": "Parameter_Soil_temperature",
                "desc": "Monitoring of surface layer temperature, playing a major role in the mineralization rate of organic matter.",
                "type": "binary"
            },
            {
                "name": "Microbial Activity / Microorganisms",
                "col": "Parameter_Soil_Microorganisms",
                "desc": "Biological monitoring that measures the diversity or biomass of microbial fauna (bacteria, fungi) present in the soil.",
                "type": "binary"
            },
            {
                "name": "Greenhouse Gas Fluxes (GHG)",
                "col": "Parameter_GHG",
                "desc": "Measurement or modelling of CO2, N2O, or CH4 emissions associated with soils.",
                "type": "binary"
            }
        ],
        "📊 Data Types Used (Data Type)": [
            {
                "name": "Land Management Data",
                "col": "Data_Land_Management",
                "desc": "Self-reported data collected from farmers (cropping history, fertilization, tillage, cover crops).",
                "type": "binary"
            },
            {
                "name": "Spatial / Satellite Imagery",
                "col": "Data_Spatial_images",
                "desc": "Use of satellite or drone imagery to map or monitor crop condition and soil cover remotely.",
                "type": "binary"
            },
            {
                "name": "Physical Soil Sampling",
                "col": "Data_Soil_samples",
                "desc": "Physical retrieval of soil cores in the field followed by laboratory physicochemical analyses.",
                "type": "binary"
            },
            {
                "name": "Numerical Modelling",
                "col": "Data_Modelling",
                "desc": "Mathematical and computer models simulating variations in soil organic carbon over time.",
                "type": "binary"
            }
        ],
        "📝 Reporting & Uncertainty": [
            {
                "name": "Uncertainty Assessment Method",
                "col": "Uncertainty",
                "desc": "Statistical algorithm used to estimate error margins of the sequestered carbon quantity (e.g., Bayesian analysis, Monte Carlo simulations, quantiles).",
                "type": "categorical"
            },
            {
                "name": "Threshold Calculation",
                "col": "Threshold",
                "desc": "Method for establishing baseline reference or threshold values (fixed literature thresholds, regional distribution, relative changes).",
                "type": "categorical"
            }
        ],
        "🔒 Verification Schemes & Governance": [
            {
                "name": "Action-based Verification",
                "col": "Action_based",
                "desc": "Validation conditional on following recommended cultural practices (e.g., planting cover crops) without measuring final stock.",
                "type": "binary"
            },
            {
                "name": "Result-based Verification",
                "col": "Result_based",
                "desc": "Validation conditional on outcomes measured in-situ (e.g., tons of carbon stored increase).",
                "type": "binary"
            },
            {
                "name": "Auditor Type",
                "col": "Auditor",
                "desc": "Indicates whether the final validation is performed by an independent third-party body (External) or internally (Internal).",
                "type": "categorical"
            },
            {
                "name": "Data Sharing",
                "col": "Data_Sharing",
                "desc": "Policy for sharing obtained data: open/shared access (Yes) or confidential/private (No).",
                "type": "categorical"
            },
            {
                "name": "Implementation Status",
                "col": "Implementation",
                "desc": "Maturity status of the framework: already operational and applied in the field (Implemented) or still theoretical (Project).",
                "type": "categorical"
            }
        ]
    }
    
    # Display by sections
    for group_name, list_filters in filters_info.items():
        st.markdown(f"<div class='section-header'>{group_name}</div>", unsafe_allow_html=True)
        
        for f in list_filters:
            col_name = f['col']
            desc = f['desc']
            name = f['name']
            
            # Dynamic stats based on combined_df
            if f['type'] == 'binary':
                if col_name in combined_df.columns:
                    yes_count = (combined_df[col_name] == 'Yes').sum()
                    no_count = (combined_df[col_name] == 'No').sum()
                    pct_yes = round((yes_count / len(combined_df)) * 100)
                else:
                    yes_count, no_count, pct_yes = 0, 0, 0
                
                stat_html = f"""
                <div style="margin-top: 8px; font-size: 13px; color: var(--text-muted);">
                    Database distribution (out of {len(combined_df)} frameworks):
                    <span class="mrv-badge badge-web" style="margin-left: 8px;">Yes: {yes_count} ({pct_yes}%)</span>
                    <span class="mrv-badge badge-no" style="background-color: #581c1c; color: #fecaca; border: 1px solid #991b1b; padding: 4px 10px; border-radius: 20px;">No: {no_count} ({100 - pct_yes}%)</span>
                </div>
                """
            else:
                # Categorical
                if col_name in combined_df.columns:
                    val_counts = combined_df[col_name].value_counts()
                    badges = []
                    for val, count in val_counts.items():
                        pct = round((count / len(combined_df)) * 100)
                        badges.append(f'<span class="mrv-badge badge-lit" style="background-color: #1e293b; color: #e2e8f0; border: 1px solid #475569; padding: 4px 10px; border-radius: 20px;">{val} : {count} ({pct}%)</span>')
                    stat_html = f"""
                    <div style="margin-top: 8px; font-size: 13px; color: var(--text-muted); display: flex; flex-wrap: wrap; align-items: center; gap: 4px;">
                        Database distribution: {"".join(badges)}
                    </div>
                    """
                else:
                    stat_html = ""
            
            with st.expander(f"🔍 {name} (Technical variable: `{col_name}`)"):
                st.markdown(f"""
                <div style="padding: 5px 0;">
                    <p style="margin: 0; font-size: 14px; line-height: 1.6; color: var(--text-color);">{desc}</p>
                    {stat_html}
                </div>
                """, unsafe_allow_html=True)

################################################################################################ END ################################################################################################