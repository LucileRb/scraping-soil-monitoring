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

def translate_val(val, is_fr):
    if not is_fr:
        return val
    mapping = {
        'Implemented': 'Implémenté',
        'implemented': 'Implémenté',
        'Project': 'Projet',
        'project': 'Projet',
        'Internal': 'Interne',
        'External': 'Externe',
        'Yes': 'Oui',
        'No': 'Non',
        'Literature (Scopus)': 'Littérature (Scopus)',
        'AI Search': 'Recherche IA',
        'Webscraping': 'Webscraping',
        'Unknown': 'Inconnu',
        'All': 'Tous',
        'Depends/Flexible': 'Dépend/Flexible'
    }
    return mapping.get(str(val), val)

def generate_pokemon_card_html(mrv_data, is_fr=True):
    """
    Génère le code HTML complet pour afficher un framework MRV sous la forme
    d'une carte Pokemon personnalisée avec un encadré de caractéristiques techniques.
    """
    src = mrv_data.get('Source', 'AI Search')
    
    if src == 'Literature (Scopus)':
        card_type = 'grass'
        type_emoji = '🌱'
        energy_cost_2 = '🌱🌱'
        energy_cost_3 = '🌱🌱🌱'
    elif src == 'Webscraping':
        card_type = 'water'
        type_emoji = '💧'
        energy_cost_2 = '💧💧'
        energy_cost_3 = '💧💧💧'
    else:
        card_type = 'psychic'
        type_emoji = '🔮'
        energy_cost_2 = '🔮🔮'
        energy_cost_3 = '🔮🔮🔮'
        
    # Usages (Localize labels if necessary, but DB values are Yes/No)
    land_uses = []
    lu_names = [
        ('Agriculture', 'Land_use_Agriculture'),
        ('Forêt' if is_fr else 'Forest', 'Land_use_Forest'),
        ('Urbain' if is_fr else 'Urban', 'Land_use_Urban'),
        ('Dégradé' if is_fr else 'Degraded', 'Land_use_Degraded_land'),
        ('Zones Humides' if is_fr else 'Wetland', 'Land_use_Peatland_Wetland')
    ]
    for lu_lbl, col in lu_names:
        if mrv_data.get(col) == 'Yes':
            land_uses.append(lu_lbl)
    land_uses_str = ", ".join(land_uses) if land_uses else ("Aucun" if is_fr else "None")
    
    # Échelles
    scales = []
    scale_names = [
        ('Locale' if is_fr else 'Local', 'Scale_Local'),
        ('Régionale' if is_fr else 'Regional', 'Scale_Regional'),
        ('Nationale' if is_fr else 'National', 'Scale_National'),
        ('Continentale' if is_fr else 'Continental', 'Scale_Continental'),
        ('Globale' if is_fr else 'Global', 'Scale_Global')
    ]
    for sc_lbl, col in scale_names:
        if mrv_data.get(col) == 'Yes':
            scales.append(sc_lbl)
    scales_str = ", ".join(scales) if scales else ("Aucune" if is_fr else "None")
    
    # 1. Monitoring Component (Parameters & Data Types)
    params = []
    for col in mrv_data.index:
        if col.startswith('Parameter_') and not col.endswith('_Precision') and col != 'Parameter_Others':
            if mrv_data.get(col) == 'Yes':
                label = col.replace('Parameter_Soil_', '').replace('Parameter_', '').replace('_', ' ')
                # Translate parameter label if French
                if is_fr:
                    label = label.replace('organic matter SOC', 'Carbone/Matière Organique (SOC)')
                    label = label.replace('moisture', 'Humidité')
                    label = label.replace('temperature', 'Température')
                    label = label.replace('Microorganisms', 'Micro-organismes')
                    label = label.replace('Fauna', 'Faune')
                    label = label.replace('clay mineralogy', 'Minéralogie des argiles')
                    label = label.replace('compaction Bulk density', 'Compaction / Densité apparente')
                    label = label.replace('Nutrient availability', 'Disponibilité des nutriments')
                    label = label.replace('Pollutant concentration', 'Concentration de polluants')
                    label = label.replace('depth', 'Profondeur')
                    label = label.replace('color', 'Couleur')
                    label = label.replace('type', 'Type de sol')
                    label = label.replace('Water holding capacity', 'Capacité de rétention en eau')
                    label = label.replace('Infiltration rate', 'Taux d\'infiltration')
                    label = label.replace('Electrical conductivity', 'Conductivité électrique')
                params.append(label)
    params_str = ", ".join(params) if params else ("Aucun" if is_fr else "None")
    
    data_types = []
    for col in mrv_data.index:
        if col.startswith('Data_') and col != 'Data_Sharing':
            if mrv_data.get(col) == 'Yes':
                label = col.replace('Data_', '').replace('_', ' ')
                if is_fr:
                    label = label.replace('Land Management', 'Données de gestion')
                    label = label.replace('Spatial images', 'Imagerie satellite')
                    label = label.replace('Soil samples', 'Prélèvements de sol')
                    label = label.replace('Modelling', 'Modélisation')
                    label = label.replace('on site images', 'Scanner de sol / Photos')
                data_types.append(label)
    data_str = ", ".join(data_types) if data_types else ("Aucune" if is_fr else "None")
    
    # 2. Reporting Component (Format & Threshold)
    formats = []
    for col in ['Format_Document', 'Format_Online']:
        if mrv_data.get(col) == 'Yes':
            label = col.replace('Format_', '')
            if is_fr:
                label = label.replace('Document', 'Rapport PDF/Doc').replace('Online', 'Plateforme en ligne')
            formats.append(label)
    formats_str = ", ".join(formats) if formats else ("Aucun" if is_fr else "None")
    
    threshold = mrv_data.get('Threshold', 'N/A')
    threshold_translated = translate_val(threshold, is_fr)
    if is_fr:
        threshold_translated = threshold_translated.replace('Fixed', 'Fixe').replace('Relative_Change', 'Changement Relatif')
        
    # 3. Verification Component (Scheme & Auditor)
    schemes = []
    for col in ['Action_based', 'Result_based']:
        if mrv_data.get(col) == 'Yes':
            label = col.replace('_based', '-based')
            if is_fr:
                label = label.replace('Action-based', 'Basé sur les actions').replace('Result-based', 'Basé sur les résultats')
            schemes.append(label)
    schemes_str = ", ".join(schemes) if schemes else ("Aucun" if is_fr else "None")
    
    auditor = mrv_data.get('Auditor', 'N/A')
    auditor_translated = translate_val(auditor, is_fr)
    
    impl = mrv_data.get('Implementation', 'Project')
    impl_translated = translate_val(impl, is_fr)
    
    sharing = mrv_data.get('Data_Sharing', 'No')
    sharing_translated = translate_val(sharing, is_fr)
    
    mrv_id = mrv_data.get('ID_MRV', 'N/A')
    mrv_name = mrv_data.get('MRV_Name', 'Framework')
    author = mrv_data.get('Pub_Author', 'Unknown')
    year = mrv_data.get('Pub_Year', '2025')
    country = mrv_data.get('Country', 'Global')
    purpose = mrv_data.get('Purpose', 'Not specified')
    purpose_translated = translate_val(purpose, is_fr)
    if is_fr:
        purpose_translated = purpose_translated.replace('Voluntary_carbon_market', 'Marché du carbone volontaire').replace('Compliance_carbon_market', 'Marché du carbone réglementaire')
    
    display_name = mrv_name[:24] + '...' if len(mrv_name) > 26 else mrv_name
    
    # Labels bilingual
    lbl_land_uses = "Usage des sols :" if is_fr else "Land Uses:"
    lbl_scales = "Échelles :" if is_fr else "Scales:"
    lbl_purpose = "Objectif :" if is_fr else "Purpose:"
    lbl_status = "Statut :" if is_fr else "Status:"
    
    lbl_monitoring = "Composant Monitoring" if is_fr else "Monitoring Component"
    lbl_reporting = "Composant Reporting" if is_fr else "Reporting Component"
    lbl_verification = "Composant Vérification" if is_fr else "Verification Component"
    
    lbl_footer_status = "Statut" if is_fr else "Status"
    lbl_footer_source = "Source" if is_fr else "Source"
    lbl_footer_country = "Pays" if is_fr else "Country"
    lbl_sharing = "Partage données : " if is_fr else "Data Sharing: "
    
    html = (
        f'<div class="pokemon-card-wrapper">'
        f'<div class="pokemon-card card-{card_type}">'
        f'<div class="pokemon-card-header">'
        f'<span class="pokemon-card-name">{display_name}</span>'
        f'<span class="pokemon-card-hp">{mrv_id} {type_emoji}</span>'
        f'</div>'
        f'<div class="pokemon-card-img-container">'
        f'<div class="pokemon-card-specs-box">'
        f'<div class="pokemon-spec-row"><span class="pokemon-spec-label">{lbl_land_uses}</span><span class="pokemon-spec-val">{land_uses_str}</span></div>'
        f'<div class="pokemon-spec-row"><span class="pokemon-spec-label">{lbl_scales}</span><span class="pokemon-spec-val">{scales_str}</span></div>'
        f'<div class="pokemon-spec-row"><span class="pokemon-spec-label">{lbl_purpose}</span><span class="pokemon-spec-val">{purpose_translated}</span></div>'
        f'<div class="pokemon-spec-row"><span class="pokemon-spec-label">{lbl_status}</span><span class="pokemon-spec-val">{impl_translated}</span></div>'
        f'</div>'
        f'<div class="pokemon-card-img-caption">No. {mrv_id} | {country} | Author: {author} ({year})</div>'
        f'</div>'
        f'<div class="pokemon-card-body">'
        f'<div class="pokemon-card-ability">'
        f'<span class="pokemon-ability-cost">{type_emoji}</span>'
        f'<span class="pokemon-ability-name">{lbl_monitoring}</span>'
        f'<div class="pokemon-ability-desc">Params: <b>{params_str}</b><br>Data: <b>{data_str}</b></div>'
        f'</div>'
        f'<div class="pokemon-card-ability">'
        f'<span class="pokemon-ability-cost">{energy_cost_2}</span>'
        f'<span class="pokemon-ability-name">{lbl_reporting}</span>'
        f'<div class="pokemon-ability-desc">Format: <b>{formats_str}</b><br>Threshold: <b>{threshold_translated}</b></div>'
        f'</div>'
        f'<div class="pokemon-card-ability">'
        f'<span class="pokemon-ability-cost">{energy_cost_3}</span>'
        f'<span class="pokemon-ability-name">{lbl_verification}</span>'
        f'<div class="pokemon-ability-desc">Scheme: <b>{schemes_str}</b><br>Auditor: <b>{auditor_translated}</b></div>'
        f'</div>'
        f'</div>'
        f'<div class="pokemon-card-footer">'
        f'<div class="pokemon-footer-item">'
        f'<span class="pokemon-footer-label">{lbl_footer_status}</span>'
        f'<span class="pokemon-footer-value">{impl_translated}</span>'
        f'</div>'
        f'<div class="pokemon-footer-item">'
        f'<span class="pokemon-footer-label">{lbl_footer_source}</span>'
        f'<span class="pokemon-footer-value">{translate_val(src, is_fr)}</span>'
        f'</div>'
        f'<div class="pokemon-footer-item">'
        f'<span class="pokemon-footer-label">{lbl_footer_country}</span>'
        f'<span class="pokemon-footer-value">{country}</span>'
        f'</div>'
        f'</div>'
        f'<div class="pokemon-card-flavor">{lbl_sharing}{sharing_translated}</div>'
        f'</div>'
        f'</div>'
    )
    return html

def render_mrv_details(mrv_data, is_fr=True):
    # Helper translations
    def t(fr, en):
        return fr if is_fr else en
        
    # Tabs for structuring information
    tab1, tab2, tab3, tab4 = st.tabs([
        t("📝 Général & Source", "📝 General & Source"),
        t("🌍 Contexte & Acteurs", "🌍 Context & Stakeholders"),
        t("🔬 Monitoring", "🔬 Monitoring"),
        t("📊 Reporting & Vérification", "📊 Reporting & Verification")
    ])
    
    with tab1:
        col_left, col_right = st.columns(2)
        with col_left:
            st.write(f"**{t('Publication / Source :', 'Publication / Source:')}** {mrv_data['Pub_Title']}")
            st.write(f"**{t('Auteur / Plateforme :', 'Author / Platform:')}** {mrv_data['Pub_Author']}")
            st.write(f"**{t('Année :', 'Year:')}** {mrv_data['Pub_Year']}")
        with col_right:
            st.write(f"**{t('Pays :', 'Country:')}** {translate_val(mrv_data.get('Country', 'N/A'), is_fr)}")
            st.write(f"**{t('Continent :', 'Continent:')}** {translate_val(mrv_data.get('Continent', 'N/A'), is_fr)}")
            if mrv_data['Pub_Link']:
                st.markdown(f"[{t('🔗 Accéder à la source originale', '🔗 Access Original Source')}]({mrv_data['Pub_Link']})")
            else:
                st.write(t("*Lien source indisponible*", "*Source link unavailable*"))
                
    with tab2:
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown(f"<div class='section-header'>{t('Usages des Sols', 'Land Uses')}</div>", unsafe_allow_html=True)
            st.markdown(f"- {t('Agriculture :', 'Agriculture:')} <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Land_use_Agriculture') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Land_use_Agriculture') == 'Yes' else '#C62828'}'>{translate_val(mrv_data.get('Land_use_Agriculture', 'No'), is_fr)}</span>", unsafe_allow_html=True)
            st.markdown(f"- {t('Forêt :', 'Forest:')} <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Land_use_Forest') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Land_use_Forest') == 'Yes' else '#C62828'}'>{translate_val(mrv_data.get('Land_use_Forest', 'No'), is_fr)}</span>", unsafe_allow_html=True)
            st.markdown(f"- {t('Urbain :', 'Urban:')} <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Land_use_Urban') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Land_use_Urban') == 'Yes' else '#C62828'}'>{translate_val(mrv_data.get('Land_use_Urban', 'No'), is_fr)}</span>", unsafe_allow_html=True)
            st.markdown(f"- {t('Terre Dégradée :', 'Degraded Land:')} <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Land_use_Degraded_land') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Land_use_Degraded_land') == 'Yes' else '#C62828'}'>{translate_val(mrv_data.get('Land_use_Degraded_land', 'No'), is_fr)}</span>", unsafe_allow_html=True)
            st.markdown(f"- {t('Tourbière / Zone Humide :', 'Peatland / Wetland:')} <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Land_use_Peatland_Wetland') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Land_use_Peatland_Wetland') == 'Yes' else '#C62828'}'>{translate_val(mrv_data.get('Land_use_Peatland_Wetland', 'No'), is_fr)}</span>", unsafe_allow_html=True)
            if mrv_data.get('Land_use_Others_ Precision') and str(mrv_data['Land_use_Others_ Precision']).lower() != 'nan':
                st.write(f"- {t('Autres détails :', 'Other details:')} *{mrv_data['Land_use_Others_ Precision']}*")
            
            label_fr = "Échelle d'Application"
            st.markdown(f"<div class='section-header'>{t(label_fr, 'Application Scale')}</div>", unsafe_allow_html=True)
            st.markdown(f"- {t('Locale :', 'Local:')} <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Scale_Local') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Scale_Local') == 'Yes' else '#C62828'}'>{translate_val(mrv_data.get('Scale_Local', 'No'), is_fr)}</span>", unsafe_allow_html=True)
            st.markdown(f"- {t('Régionale :', 'Regional:')} <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Scale_Regional') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Scale_Regional') == 'Yes' else '#C62828'}'>{translate_val(mrv_data.get('Scale_Regional', 'No'), is_fr)}</span>", unsafe_allow_html=True)
            st.markdown(f"- {t('Nationale :', 'National:')} <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Scale_National') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Scale_National') == 'Yes' else '#C62828'}'>{translate_val(mrv_data.get('Scale_National', 'No'), is_fr)}</span>", unsafe_allow_html=True)
            st.markdown(f"- {t('Continentale :', 'Continental:')} <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Scale_Continental') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Scale_Continental') == 'Yes' else '#C62828'}'>{translate_val(mrv_data.get('Scale_Continental', 'No'), is_fr)}</span>", unsafe_allow_html=True)
            st.markdown(f"- {t('Globale :', 'Global:')} <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Scale_Global') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Scale_Global') == 'Yes' else '#C62828'}'>{translate_val(mrv_data.get('Scale_Global', 'No'), is_fr)}</span>", unsafe_allow_html=True)

        with col_right:
            st.markdown(f"<div class='section-header'>{t('Objectifs & Leviers', 'Objectives & Drivers')}</div>", unsafe_allow_html=True)
            st.write(f"**{t('Objectif de marché :', 'Market purpose:')}** {translate_val(mrv_data['Purpose'], is_fr).replace('Voluntary_carbon_market', 'Marché du carbone volontaire').replace('Compliance_carbon_market', 'Marché du carbone réglementaire')}")
            label_fr = "Statut d'implémentation :"
            st.write(f"**{t(label_fr, 'Implementation status:')}** {translate_val(mrv_data['Implementation'], is_fr)}")
            
            # Find active drivers
            active_drivers = []
            for c in mrv_data.index:
                if c.startswith('Driver_') and mrv_data[c] == 'Yes':
                    drv_name = c.replace('Driver_', '').replace('_', ' ')
                    if is_fr:
                        drv_name = drv_name.replace('Agricultural practices', 'Pratiques agricoles')
                        drv_name = drv_name.replace('Afforestation Reforestation', 'Reboisement / Boisement')
                        drv_name = drv_name.replace('Forest management', 'Gestion forestière')
                        drv_name = drv_name.replace('Land conversion', 'Conversion des terres')
                        drv_name = drv_name.replace('Fire management', 'Gestion du feu')
                    active_drivers.append(drv_name)
            if active_drivers:
                st.write(f"**{t('Pratiques / Leviers ciblés :', 'Targeted Agricultural Practices / Drivers:')}**")
                for d in active_drivers:
                    st.markdown(f"- {d.capitalize()}")
            else:
                st.write(t("*Aucun levier spécifique listé*", "*No specific driver listed*"))
                
    with tab3:
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown(f"<div class='section-header'>{t('Paramètres du Sol Mesurés', 'Measured Soil Parameters')}</div>", unsafe_allow_html=True)
            active_params = []
            for c in mrv_data.index:
                if c.startswith('Parameter_') and mrv_data[c] == 'Yes':
                    p_name = c.replace('Parameter_', '').replace('_', ' ')
                    if is_fr:
                        p_name = p_name.replace('Soil organic matter SOC', 'Carbone / Matière organique (SOC)')
                        p_name = p_name.replace('Soil pH', 'pH du sol')
                        p_name = p_name.replace('Soil moisture', 'Humidité du sol')
                        p_name = p_name.replace('Soil temperature', 'Température du sol')
                        p_name = p_name.replace('Soil Microorganisms', 'Micro-organismes')
                        p_name = p_name.replace('Soil Fauna', 'Faune du sol')
                        p_name = p_name.replace('GHG', 'Flux de GES (CO2, N2O...)')
                    active_params.append(p_name)
            if active_params:
                for p in active_params:
                    st.markdown(f"- {p.capitalize()}")
            else:
                st.write(t("*Aucun paramètre standard spécifié*", "*No standard parameter specified*"))
                
        with col_right:
            st.markdown(f"<div class='section-header'>{t('Types de Données Utilisés', 'Used Data Types')}</div>", unsafe_allow_html=True)
            st.markdown(f"- {t('Données de gestion :', 'Management surveys:')} {translate_val(mrv_data.get('Data_Land_Management', 'No'), is_fr)}")
            st.markdown(f"- {t('Imagerie satellite / spatiale :', 'Satellite / spatial imagery:')} {translate_val(mrv_data.get('Data_Spatial_images', 'No'), is_fr)}")
            st.markdown(f"- {t('Prélèvements de sol :', 'Physical soil samples:')} {translate_val(mrv_data.get('Data_Soil_samples', 'No'), is_fr)}")
            st.markdown(f"- {t('Modélisation :', 'Modelling:')} {translate_val(mrv_data.get('Data_Modelling', 'No'), is_fr)}")
            st.markdown(f"- {t('Scanner de sol (site) :', 'On-site scanner imagery:')} {translate_val(mrv_data.get('Data_on_site_images', 'No'), is_fr)}")
            
            label_fr = "Plan d'Échantillonnage"
            st.markdown(f"<div class='section-header'>{t(label_fr, 'Sampling Plan')}</div>", unsafe_allow_html=True)
            st.write(f"**{t('Fréquence de suivi :', 'Monitoring frequency:')}** {translate_val(mrv_data['Monitoring_frequency'], is_fr)}")
            st.write(f"**{t('Superficie moyenne de parcelle :', 'Average plot area:')}** {mrv_data.get('Plot_Area', 'N/A')} {mrv_data.get('Plot_Area_Unit', '')}")
            st.write(f"**{t('Méthodologie standardisée :', 'Standardized methodology:')}** {translate_val(mrv_data.get('Methodology_Standard', 'No'), is_fr)}")

    with tab4:
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown(f"<div class='section-header'>{t('Reporting & Incertitude', 'Reporting & Uncertainty')}</div>", unsafe_allow_html=True)
            st.write(f"**{t('Format du rapport :', 'Report format:')}** Document: {translate_val(mrv_data.get('Format_Document', 'No'), is_fr)} | Online: {translate_val(mrv_data.get('Format_Online', 'No'), is_fr)}")
            st.write(f"**{t('Méthode de calcul d\'incertitude :', 'Uncertainty calculation method:')}** {translate_val(mrv_data['Uncertainty'], is_fr)}")
            st.write(f"**{t('Méthode de calcul du seuil :', 'Threshold calculation method:')}** {translate_val(mrv_data['Threshold'], is_fr).replace('Fixed', 'Fixe').replace('Relative_Change', 'Changement Relatif')}")
            
        with col_right:
            st.markdown(f"<div class='section-header'>{t('Vérification & Gouvernance', 'Verification & Governance')}</div>", unsafe_allow_html=True)
            st.write(f"**{t('Schéma basé sur les actions :', 'Action-based scheme:')}** {translate_val(mrv_data.get('Action_based', 'No'), is_fr)}")
            st.write(f"**{t('Schéma basé sur les résultats :', 'Result-based scheme:')}** {translate_val(mrv_data.get('Result_based', 'No'), is_fr)}")
            st.write(f"**{t('Auditeur :', 'Auditor:')}** {translate_val(mrv_data['Auditor'], is_fr)}")
            st.write(f"**{t('Partage des données :', 'Data sharing:')}** {translate_val(mrv_data.get('Data_Sharing', 'No'), is_fr)}")

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
        -webkit-perspective: 1000px;
        -moz-perspective: 1000px;
        perspective: 1000px;
    }
    
    .pokemon-card {
        width: 100%;
        max-width: 350px;
        background: #111;
        border-radius: 18px;
        padding: 12px 14px 14px 14px;
        box-sizing: border-box;
        -webkit-transition: all 0.5s cubic-bezier(0.23, 1, 0.320, 1);
        -moz-transition: all 0.5s cubic-bezier(0.23, 1, 0.320, 1);
        -o-transition: all 0.5s cubic-bezier(0.23, 1, 0.320, 1);
        transition: all 0.5s cubic-bezier(0.23, 1, 0.320, 1);
        position: relative;
        overflow: hidden;
        border: 4px solid #c89d3c;
    }
    
    .pokemon-card:hover {
        -webkit-transform: translateY(-8px) rotateY(2deg);
        -moz-transform: translateY(-8px) rotateY(2deg);
        -ms-transform: translateY(-8px) rotateY(2deg);
        -o-transform: translateY(-8px) rotateY(2deg);
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

# Language selector
st.sidebar.markdown("<div class='section-header' style='font-size: 10px; margin-top: 10px; margin-bottom: 5px; color: #dab254; font-weight: 600; text-transform: uppercase;'>🌐 Langue / Language</div>", unsafe_allow_html=True)
lang = st.sidebar.selectbox("Language select", ["Français", "English"], label_visibility="collapsed")
is_fr = (lang == "Français")

def t(fr, en):
    return fr if is_fr else en

app_mode = st.sidebar.selectbox(t('Menu de Navigation', 'Navigation Menu'), [
    t('🏠 Accueil', '🏠 Home'),
    t('🔎 Outil de Décision', '🔎 Decision Tool'),
    t('🗂️ Pokedex', '🗂️ Pokedex'),
    t('📚 Bibliographie', '📚 Articles'),
    t('📊 Guide MRV', '📊 MRV Guide')
])

# Clean the emoji and text for routing
mode_clean = app_mode.replace('🏠 ', '').replace('🔎 ', '').replace('🗂️ ', '').replace('📚 ', '').replace('📊 ', '')
if is_fr:
    mode_clean = mode_clean.replace('Accueil', 'Home').replace('Outil de Décision', 'Decision Tool').replace('Bibliographie', 'Articles').replace('Guide MRV', 'MRV Guide')

# ----------------- HOME PAGE -----------------
if mode_clean == 'Home':
    st.markdown(f"<h1>{t('Explorateur de Systèmes de Suivi, Notification et Vérification (MRV)', 'Soil Health & MRV Exploration Tool')}</h1>", unsafe_allow_html=True)
    st.markdown(t(
        """Cette application interactive vous permet de parcourir et filtrer les méthodologies de **Monitoring, Reporting et Verification (MRV)** appliquées à l'évaluation du carbone et de la qualité des sols.
        Les données proviennent de trois sources : une revue de littérature systématique (**Scopus**), du **web scraping** de plateformes de certification et de méthodologies, et des recherches assistées par **IA**.""",
        """This interactive application allows you to explore and filter **Monitoring, Reporting, and Verification (MRV)** methodologies applied to soil carbon and quality assessment.
        The data combines publications from a systematic literature review (**Scopus**), **web scraping** of certification platforms and methodologies, and **AI-assisted** research."""
    ))
    if BANNER_PATH:
        banner_cropped = get_cropped_image(BANNER_PATH, 1200, 250)
        if banner_cropped:
            st.image(banner_cropped, use_column_width=True)
    st.divider()
    
    # 1. KPIs
    st.markdown(f"<h3>{t('Statistiques de la Base de Données', 'Database Statistics')}</h3>", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-num">96</div>
            <div class="kpi-label">{t('Cadres MRV', 'MRV Frameworks')}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-num">26</div>
            <div class="kpi-label">{t('Revues Littérature', 'Literature Reviews')}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-num">69</div>
            <div class="kpi-label">{t('Web Scraping', 'Web Scraping')}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-num">1</div>
            <div class="kpi-label">{t('Recherche IA', 'AI Search')}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.divider()
    
    # 2. Charts
    st.markdown(f"<h3>{t('Distribution des Cadres MRV', 'Framework Distribution')}</h3>", unsafe_allow_html=True)
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown(f"<p style='font-weight: 600; color: #52B788;'>{t('Distribution par Usage des Sols', 'Distribution by Land Use')}</p>", unsafe_allow_html=True)
        # Calculate the number of Yes for each Land Use type
        lu_columns = {
            t('Agriculture', 'Agriculture'): 'Land_use_Agriculture',
            t('Forêt', 'Forest'): 'Land_use_Forest',
            t('Urbain', 'Urban'): 'Land_use_Urban',
            t('Terres dégradées', 'Degraded Land'): 'Land_use_Degraded_land',
            t('Zones Humides / Tourbières', 'Peatland/Wetland'): 'Land_use_Peatland_Wetland'
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
        ax.set_xlabel(t("Nombre de Cadres", "Number of Frameworks"), fontsize=9)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#24352C')
        ax.spines['bottom'].set_color('#24352C')
        plt.tight_layout()
        st.pyplot(fig)
        
    with col_chart2:
        st.markdown(f"<p style='font-weight: 600; color: #52B788;'>{t('Distribution par Échelle Spatiale', 'Distribution by Spatial Scale')}</p>", unsafe_allow_html=True)
        scale_columns = {
            t('Locale', 'Local'): 'Scale_Local',
            t('Régionale', 'Regional'): 'Scale_Regional',
            t('Nationale', 'National'): 'Scale_National',
            t('Continentale', 'Continental'): 'Scale_Continental',
            t('Globale', 'Global'): 'Scale_Global'
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
        ax.set_xlabel(t("Nombre de Cadres", "Number of Frameworks"), fontsize=9)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#24352C')
        ax.spines['bottom'].set_color('#24352C')
        plt.tight_layout()
        st.pyplot(fig)
        
    st.divider()
    
    # 3. Decision Tool variables structure (variables.json)
    st.markdown(f"<h3>{t('Structure des Variables de Décision', 'Decision Variables Structure')}</h3>", unsafe_allow_html=True)
    st.write(t("Ce tableau détaille les descripteurs utilisés dans la base de données. Vous pouvez effectuer une recherche par mot-clé.", "This table details the descriptors used in the database. You can search by keyword."))
    
    if variables:
        df_vars = pd.DataFrame(variables)
        df_vars.columns = [t('Variable', 'Variable'), t('Catégorie', 'Category'), t('Sous-Catégorie', 'Sub-Category'), t('Modalités', 'Modalities'), t('Explication', 'Explanation')]
        
        # Search query
        search_query = st.text_input(t("🔍 Rechercher une variable...", "🔍 Search for a variable..."), placeholder=t("Ex: SOC, Agriculture, Incertitude...", "E.g., SOC, Agriculture, Uncertainty..."))
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
    st.markdown(f"<h1>{t('Outil d\'Aide à la Décision MRV', 'MRV Decision Support Tool')}</h1>", unsafe_allow_html=True)
    st.markdown(t("Utilisez les filtres de la barre latérale pour trouver les cadres MRV qui correspondent à vos besoins.", "Use the sidebar filters to find MRV frameworks that match your needs."))
    
    # Sidebar Filters construction
    st.sidebar.markdown(f"<div class='section-header'>{t('Configuration des Filtres', 'Filter Configuration')}</div>", unsafe_allow_html=True)
    
    # Search mode
    filter_mode = st.sidebar.radio(
        t("Mode de Recherche", "Search Mode"),
        [t("⭐ Score de Correspondance (Recommandé)", "⭐ Matching Score (Recommended)"), t("🔒 Filtrage Strict (ET)", "🔒 Strict Filtering (AND)")],
        help=t("Le score de correspondance classe les résultats du meilleur au moins bon, évitant les résultats vides.", "The matching score ranks results from best to worst, avoiding 0 results if you select multiple criteria.")
    )
    
    # 1. Context & Land Uses
    st.sidebar.subheader(t("🌱 Contexte & Usages des Sols", "🌱 Context & Land Uses"))
    
    selected_land_uses = []
    if st.sidebar.checkbox(t("Agriculture", "Agriculture"), value=False): selected_land_uses.append('Land_use_Agriculture')
    if st.sidebar.checkbox(t("Forêt", "Forest"), value=False): selected_land_uses.append('Land_use_Forest')
    if st.sidebar.checkbox(t("Urbain", "Urban"), value=False): selected_land_uses.append('Land_use_Urban')
    if st.sidebar.checkbox(t("Terre Dégradée", "Degraded Land"), value=False): selected_land_uses.append('Land_use_Degraded_land')
    if st.sidebar.checkbox(t("Tourbière / Zone Humide", "Peatland / Wetland"), value=False): selected_land_uses.append('Land_use_Peatland_Wetland')
    
    selected_scales = []
    if st.sidebar.checkbox(t("Échelle Locale", "Local Scale"), value=False): selected_scales.append('Scale_Local')
    if st.sidebar.checkbox(t("Échelle Régionale", "Regional Scale"), value=False): selected_scales.append('Scale_Regional')
    if st.sidebar.checkbox(t("Échelle Nationale", "National Scale"), value=False): selected_scales.append('Scale_National')
    if st.sidebar.checkbox(t("Échelle Continentale", "Continental Scale"), value=False): selected_scales.append('Scale_Continental')
    if st.sidebar.checkbox(t("Échelle Globale", "Global Scale"), value=False): selected_scales.append('Scale_Global')
    
    purpose_options = ['All'] + list(combined_df['Purpose'].unique())
    translated_purposes = [t("Tous", "All") if p == 'All' else translate_val(p, is_fr) for p in purpose_options]
    selected_purpose_idx = st.sidebar.selectbox(t("Objectif", "Purpose"), range(len(purpose_options)), format_func=lambda x: translated_purposes[x])
    selected_purpose = purpose_options[selected_purpose_idx]

    # Drivers Map
    DRIVER_MAP = {
        "Agricultural practices": "Driver_Agricultural_practices",
        "Afforestation / Reforestation": "Driver_Afforestation_Reforestation",
        "Biochar": "Driver_Biochar",
        "Forest management": "Driver_Forest_management",
        "Conservation": "Driver_Conservation",
        "Deforestation": "Driver_Deforestation",
        "Restoration": "Driver_Restoration",
        "Weathering": "Driver_Weathering",
        "Grazing": "Driver_Grazing",
        "Irrigation": "Driver_Irrigation",
        "Land conversion": "Driver_Land_conversion",
        "Rewetting": "Driver_Rewetting",
        "Fire management": "Driver_Fire_management"
    }
    DRIVER_MAP_KEYS_FR = {
        "Agricultural practices": "Pratiques agricoles",
        "Afforestation / Reforestation": "Reboisement / Boisement",
        "Biochar": "Biochar",
        "Forest management": "Gestion forestière",
        "Conservation": "Conservation",
        "Deforestation": "Déforestation",
        "Restoration": "Restauration",
        "Weathering": "Altération forcée",
        "Grazing": "Pâturage",
        "Irrigation": "Irrigation",
        "Land conversion": "Conversion des terres",
        "Rewetting": "Remise en eau",
        "Fire management": "Gestion du feu"
    }
    drivers_list = list(DRIVER_MAP.keys())
    translated_drivers = [DRIVER_MAP_KEYS_FR[d] if is_fr else d for d in drivers_list]
    selected_driver_indices = st.sidebar.multiselect(
        t("Leviers / Pratiques agricoles", "Drivers / Management Changes"),
        range(len(drivers_list)),
        format_func=lambda x: translated_drivers[x]
    )
    selected_drivers = [drivers_list[idx] for idx in selected_driver_indices]
    
    # Occupations Map
    OCCUPATION_MAP = {
        "Farmers": "Occupation_Farmers",
        "Foresters & Forester Associations": "Occupation_Foresters_Forester_Associations",
        "Public Administrators": "Occupation_Public_Administrators",
        "Educational & Research Institutions": "Occupation_Educational_Institutions_Research",
        "NGOs": "Occupation_NGOs",
        "Agroindustry": "Occupation_Agroindustry",
        "Forestry Companies": "Occupation_Forestry_Companies",
        "Consultancy": "Occupation_Consultancy",
        "Project Developer": "Occupation_Project_developer",
        "Other Companies": "Occupation_Other_companies",
        "Software Developers": "Occupation_Software_developers"
    }
    OCCUPATION_KEYS_FR = {
        "Farmers": "Agriculteurs",
        "Foresters & Forester Associations": "Forestiers & Associations de forestiers",
        "Public Administrators": "Administrations publiques",
        "Educational & Research Institutions": "Établissements d'enseignement & Recherche",
        "NGOs": "ONG",
        "Agroindustry": "Agro-industrie",
        "Forestry Companies": "Sociétés forestières",
        "Consultancy": "Bureaux de conseil",
        "Project Developer": "Développeurs de projets",
        "Other Companies": "Autres entreprises",
        "Software Developers": "Développeurs de logiciels"
    }
    occupations_list = list(OCCUPATION_MAP.keys())
    translated_occupations = [OCCUPATION_KEYS_FR[o] if is_fr else o for o in occupations_list]
    selected_occupation_indices = st.sidebar.multiselect(
        t("Acteurs / Occupations", "Stakeholder Occupations"),
        range(len(occupations_list)),
        format_func=lambda x: translated_occupations[x]
    )
    selected_occupations = [occupations_list[idx] for idx in selected_occupation_indices]
    
    # 2. Soil Parameters & Data
    st.sidebar.subheader(t("🔬 Paramètres & Données du Sol", "🔬 Soil Parameters & Data"))
    
    PARAM_MAP = {
        "Soil Organic Carbon (SOC)": "Parameter_Soil_organic_matter_SOC",
        "Soil pH": "Parameter_Soil_pH",
        "Soil Moisture": "Parameter_Soil_moisture",
        "Soil Temperature": "Parameter_Soil_temperature",
        "Soil Microorganisms": "Parameter_Soil_Microorganisms",
        "Soil Fauna": "Parameter_Soil_Fauna",
        "Greenhouse Gases (GHG)": "Parameter_GHG",
        "Oxygen Content": "Parameter_Oxygen_content",
        "Clay Mineralogy": "Parameter_Clay_mineralogy",
        "CEC (Cation Exchange Capacity)": "Parameter_CEC",
        "Particle Size Distribution / Texture": "Parameter_Particle_size_distribution_Texture",
        "Soil Porosity": "Parameter_Soil_porosity",
        "Soil Diffusivity": "Parameter_Soil_diffusivity",
        "Aggregate Stability": "Parameter_Aggregate_stability",
        "Soil Compaction / Bulk Density": "Parameter_Soil_compaction_Bulk_density",
        "Nutrient Availability": "Parameter_Nutrient_availability",
        "Pollutant Concentration": "Parameter_Pollutant_concentration",
        "Soil Depth": "Parameter_Soil_depth",
        "Peat Depth": "Parameter_Peat_depth",
        "Soil Color": "Parameter_Soil_color",
        "Soil Type": "Parameter_Soil_type",
        "Subsidence": "Parameter_Subsidence",
        "CaCO3": "Parameter_CaCO3",
        "Electrical Conductivity": "Parameter_Electrical_conductivity",
        "Water Holding Capacity": "Parameter_Water_holding_capacity",
        "Infiltration Rate": "Parameter_Infiltration_rate"
    }
    PARAM_KEYS_FR = {
        "Soil Organic Carbon (SOC)": "Carbone Organique du Sol (SOC)",
        "Soil pH": "pH du sol",
        "Soil Moisture": "Humidité du sol",
        "Soil Temperature": "Température du sol",
        "Soil Microorganisms": "Micro-organismes du sol",
        "Soil Fauna": "Faune du sol",
        "Greenhouse Gases (GHG)": "Gaz à Effet de Serre (GES)",
        "Oxygen Content": "Teneur en oxygène",
        "Clay Mineralogy": "Minéralogie des argiles",
        "CEC (Cation Exchange Capacity)": "Capacité d'échange cationique (CEC)",
        "Particle Size Distribution / Texture": "Texture du sol / Granulométrie",
        "Soil Porosity": "Porosité du sol",
        "Soil Diffusivity": "Diffusivité du sol",
        "Aggregate Stability": "Stabilité des agrégats",
        "Soil Compaction / Bulk Density": "Compaction / Densité apparente",
        "Nutrient Availability": "Disponibilité des nutriments",
        "Pollutant Concentration": "Concentration de polluants",
        "Soil Depth": "Profondeur du sol",
        "Peat Depth": "Profondeur de la tourbe",
        "Soil Color": "Couleur du sol",
        "Soil Type": "Type de sol",
        "Subsidence": "Subsidence",
        "CaCO3": "CaCO3",
        "Electrical Conductivity": "Conductivité électrique",
        "Water Holding Capacity": "Capacité de rétention d'eau",
        "Infiltration Rate": "Taux d'infiltration"
    }
    params_list = list(PARAM_MAP.keys())
    translated_params = [PARAM_KEYS_FR[p] if is_fr else p for p in params_list]
    selected_param_indices = st.sidebar.multiselect(
        t("Paramètres du Sol", "Soil Parameters"),
        range(len(params_list)),
        format_func=lambda x: translated_params[x]
    )
    selected_param_names = [params_list[idx] for idx in selected_param_indices]
    selected_params = [PARAM_MAP[name] for name in selected_param_names]
    
    selected_data_types = []
    if st.sidebar.checkbox(t("Données de gestion des terres", "Land Management Data"), value=False): selected_data_types.append('Data_Land_Management')
    if st.sidebar.checkbox(t("Imagerie Spatiale / Satellite", "Spatial / Satellite Imagery"), value=False): selected_data_types.append('Data_Spatial_images')
    if st.sidebar.checkbox(t("Prélèvements physiques de sol", "Physical Soil Sampling"), value=False): selected_data_types.append('Data_Soil_samples')
    if st.sidebar.checkbox(t("Modélisation numérique", "Numerical Modelling"), value=False): selected_data_types.append('Data_Modelling')
    if st.sidebar.checkbox(t("Scanner de sol sur site", "On-site Imagery (Soil Scanner)"), value=False): selected_data_types.append('Data_on_site_images')
    
    # 3. Reporting & Verification
    st.sidebar.subheader(t("📝 Reporting & Vérification", "📝 Reporting & Verification"))
    
    selected_formats = []
    if st.sidebar.checkbox(t("Rapport de document standard", "Standard Document Report"), value=False): selected_formats.append('Format_Document')
    if st.sidebar.checkbox(t("Saisie sur plateforme en ligne", "Online Platform Entry"), value=False): selected_formats.append('Format_Online')
    
    selected_verif_schemes = []
    if st.sidebar.checkbox(t("Schéma basé sur les actions", "Action-based Scheme"), value=False): selected_verif_schemes.append('Action_based')
    if st.sidebar.checkbox(t("Schéma basé sur les résultats", "Result-based Scheme"), value=False): selected_verif_schemes.append('Result_based')
    
    state_options = ['All', 'Implemented', 'Project']
    translated_states = [t("Tous", "All"), t("Implémenté", "Implemented"), t("Projet", "Project")]
    selected_state_idx = st.sidebar.selectbox(t("Statut d'implémentation", "Implementation Status"), range(len(state_options)), format_func=lambda x: translated_states[x])
    selected_state = state_options[selected_state_idx]

    # Calcul des filtres actifs
    active_filters = {}
    for col in selected_land_uses: active_filters[col] = 'Yes'
    for col in selected_scales: active_filters[col] = 'Yes'
    for name in selected_drivers: active_filters[DRIVER_MAP[name]] = 'Yes'
    for name in selected_occupations: active_filters[OCCUPATION_MAP[name]] = 'Yes'
    for col in selected_params: active_filters[col] = 'Yes'
    for col in selected_data_types: active_filters[col] = 'Yes'
    for col in selected_formats: active_filters[col] = 'Yes'
    for col in selected_verif_schemes: active_filters[col] = 'Yes'
    
    if selected_purpose != 'All': active_filters['Purpose'] = selected_purpose
    if selected_state != 'All': active_filters['Implementation'] = selected_state

    # 4. Appliquer le Filtrage
    df_results = combined_df.copy()
    
    if "🔒 Strict" in filter_mode or "🔒 Filtrage" in filter_mode:
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
    if "🔒 Strict" in filter_mode or "🔒 Filtrage" in filter_mode:
        st.markdown(f"<h3>{t(f'{num_matches} cadres correspondent exactement à vos critères', f'{num_matches} frameworks match your criteria exactly')}</h3>", unsafe_allow_html=True)
    else:
        st.markdown(f"<h3>{t('Classement des 96 cadres par niveau de correspondance', 'Ranking of 96 frameworks by match level')}</h3>", unsafe_allow_html=True)
        
    st.divider()
    
    # Results table
    display_cols = ['ID_MRV', 'MRV_Name', 'Source', 'Match_Score', 'Purpose', 'Implementation']
    df_table = df_results[display_cols].copy()
    # Translate some columns in the table
    df_table['Source'] = df_table['Source'].apply(lambda x: translate_val(x, is_fr))
    df_table['Purpose'] = df_table['Purpose'].apply(lambda x: translate_val(x, is_fr).replace('Voluntary_carbon_market', 'Volontaire').replace('Compliance_carbon_market', 'Réglementaire'))
    df_table['Implementation'] = df_table['Implementation'].apply(lambda x: translate_val(x, is_fr))
    
    df_table.columns = [t('ID', 'ID'), t('Nom du Cadre', 'Framework Name'), t('Source', 'Data Source'), t('Score de Correspondance (%)', 'Matching Score (%)'), t('Objectif', 'Purpose'), t('Implémentation', 'Implementation')]
    
    st.dataframe(
        df_table,
        column_config={
            t('Score de Correspondance (%)', 'Matching Score (%)'): st.column_config.ProgressColumn(
                t('Score de Correspondance (%)', 'Matching Score (%)'),
                help=t("Pourcentage de critères validés", "Percentage of validated criteria"),
                format="%d%%",
                min_value=0,
                max_value=100
            ),
            t('ID', 'ID'): st.column_config.TextColumn(t('ID', 'ID'), width="small"),
            t('Nom du Cadre', 'Framework Name'): st.column_config.TextColumn(t('Nom du Cadre', 'Framework Name'), width="medium"),
            t('Source', 'Data Source'): st.column_config.TextColumn(t('Source', 'Data Source'), width="small"),
            t('Objectif', 'Purpose'): st.column_config.TextColumn(t('Objectif', 'Purpose'), width="small"),
            t('Implémentation', 'Implementation'): st.column_config.TextColumn(t('Implémentation', 'Implementation'), width="small"),
        },
        hide_index=True,
        use_container_width=True
    )
    
    st.divider()
    
    # Select an MRV to view its profile
    if not df_results.empty:
        st.markdown(f"<h3>{t('Profil détaillé du cadre sélectionné', 'Detailed profile of the selected framework')}</h3>", unsafe_allow_html=True)
        
        mrv_options = df_results['ID_MRV'] + " - " + df_results['MRV_Name']
        selected_mrv_str = st.selectbox(t("Sélectionnez un cadre à inspecter :", "Select a framework to inspect:"), mrv_options)
        
        selected_mrv_id = selected_mrv_str.split(" - ")[0]
        mrv_data = df_results[df_results['ID_MRV'] == selected_mrv_id].iloc[0]
        
        # Draw detailed profile
        # Technical profile layout (Two-column: Pokemon Card & Technical Specifications)
        col_card, col_details = st.columns([2, 3])
        
        with col_card:
            # Custom Pokemon card HTML display
            card_html = generate_pokemon_card_html(mrv_data, is_fr=is_fr)
            st.markdown(card_html, unsafe_allow_html=True)
            
        with col_details:
            render_mrv_details(mrv_data, is_fr=is_fr)

# ----------------- POKEDEX (MRV EXPLORER) PAGE -----------------
elif mode_clean == 'Pokedex':
    st.markdown(f"<h1>{t('Explorateur de Cadres (Pokedex MRV)', 'Framework Explorer (MRV Pokedex)')}</h1>", unsafe_allow_html=True)
    st.markdown(t("Visualisez et explorez l'ensemble des 96 cadres MRV de notre base de données.", "View and explore all 96 MRV frameworks in our database."))
    st.divider()
    
    # Framework Selector
    mrv_options = combined_df['ID_MRV'] + " - " + combined_df['MRV_Name']
    selected_mrv_str = st.selectbox(t("Sélectionnez un cadre à inspecter :", "Select a framework to inspect:"), mrv_options)
    
    selected_mrv_id = selected_mrv_str.split(" - ")[0]
    mrv_data = combined_df[combined_df['ID_MRV'] == selected_mrv_id].iloc[0]
    
    # Technical profile layout (Two-column: Pokemon Card & Technical Specifications)
    col_card, col_details = st.columns([2, 3])
    
    with col_card:
        # Custom Pokemon card HTML display
        card_html = generate_pokemon_card_html(mrv_data, is_fr=is_fr)
        st.markdown(card_html, unsafe_allow_html=True)
        
    with col_details:
        render_mrv_details(mrv_data, is_fr=is_fr)

# ----------------- PAGE ARTICLES (BIBLIOGRAPHY) -----------------
elif mode_clean == 'Articles':
    st.markdown(f"<h1>{t('Bibliothèque des Publications & Sources', 'Publications & Sources Library')}</h1>", unsafe_allow_html=True)
    st.markdown(t("Parcourez et recherchez les publications originales et les sites web référencés dans notre base de données.", "Browse and search original publications and websites referenced in our database."))
    st.divider()
    
    # Extract unique publications
    pub_df = combined_df[['Pub_Title', 'Pub_Author', 'Pub_Year', 'Pub_Link', 'Source']].drop_duplicates(subset=['Pub_Title', 'Pub_Author'])
    
    # Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        search_pub = st.text_input(t("🔍 Rechercher une publication...", "🔍 Search for a publication..."), placeholder=t("Titre, auteur, plateforme...", "Title, author, platform..."))
    with col_f2:
        source_options = ['All', 'Literature (Scopus)', 'Webscraping', 'AI Search']
        translated_sources = [t("Tous", "All"), t("Littérature (Scopus)", "Literature (Scopus)"), t("Webscraping", "Webscraping"), t("Recherche IA", "AI Search")]
        source_filter_idx = st.selectbox(t("Filtrer par type de source :", "Filter by source type:"), range(len(source_options)), format_func=lambda x: translated_sources[x])
        source_filter = source_options[source_filter_idx]
        
    filtered_pubs = pub_df.copy()
    if search_pub:
        filtered_pubs = filtered_pubs[
            filtered_pubs['Pub_Title'].str.contains(search_pub, case=False, na=False) |
            filtered_pubs['Pub_Author'].str.contains(search_pub, case=False, na=False)
        ]
    if source_filter != 'All':
        filtered_pubs = filtered_pubs[filtered_pubs['Source'] == source_filter]
        
    st.markdown(f"<h4>{t(f'{len(filtered_pubs)} publications ou sources trouvées', f'{len(filtered_pubs)} publications or sources found')}</h4>", unsafe_allow_html=True)
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
                f'<span class="mrv-badge {badge_class}" style="white-space: nowrap;">{translate_val(src, is_fr)}</span>'
                f'</div>'
                f'<div style="color: var(--text-muted); margin-top: 6px; font-size: 13px;">'
                f'{t("Auteur/Éditeur", "Author/Publisher")}: <b style="color: var(--text-color);">{row["Pub_Author"]}</b> &nbsp;|&nbsp; {t("Année", "Year")}: <b style="color: var(--text-color);">{row["Pub_Year"]}</b>'
                f'</div>'
                f'</div>'
            )
            st.markdown(article_html, unsafe_allow_html=True)
            
            # Show associated frameworks in an expander
            mrv_names_list = ", ".join([f"{m['ID_MRV']} ({m['MRV_Name']})" for i, m in associated_mrvs.iterrows()])
            with st.expander(t(f"🔍 Cadres MRV Associés ({len(associated_mrvs)})", f"🔍 Associated MRV Frameworks ({len(associated_mrvs)})")):
                st.write(f"**{t('Liste des cadres :', 'List of frameworks:')}** {mrv_names_list}")
                
                # Summary table for associated frameworks
                df_assoc_table = associated_mrvs[['ID_MRV', 'MRV_Name', 'Purpose', 'Implementation']].copy()
                df_assoc_table['Purpose'] = df_assoc_table['Purpose'].apply(lambda x: translate_val(x, is_fr).replace('Voluntary_carbon_market', 'Volontaire').replace('Compliance_carbon_market', 'Réglementaire'))
                df_assoc_table['Implementation'] = df_assoc_table['Implementation'].apply(lambda x: translate_val(x, is_fr))
                
                df_assoc_table.columns = [t('ID', 'ID'), t('Nom du Cadre', 'Framework Name'), t('Objectif', 'Purpose'), t('Implémentation', 'Implementation')]
                st.dataframe(df_assoc_table, hide_index=True, use_container_width=True)
                
                if row['Pub_Link']:
                    st.markdown(f"[{t('🔗 Ouvrir la source en ligne', '🔗 Open source online')}]({row['Pub_Link']})")

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
                "name": "Continental Scale",
                "col": "Scale_Continental",
                "desc": "The methodology is applied across a continent's scale.",
                "type": "binary"
            },
            {
                "name": "Global Scale",
                "col": "Scale_Global",
                "desc": "The monitoring protocol is universal, applicable at an international or global level.",
                "type": "binary"
            }
        ],
        "🛠️ Drivers / Management Changes": [
            {
                "name": "Agricultural practices",
                "col": "Driver_Agricultural_practices",
                "desc": "Management changes involving agricultural practices (e.g. crop rotation, cover crops, tillage changes).",
                "type": "binary"
            },
            {
                "name": "Afforestation / Reforestation",
                "col": "Driver_Afforestation_Reforestation",
                "desc": "Management changes involving afforestation or reforestation (planting trees).",
                "type": "binary"
            },
            {
                "name": "Biochar",
                "col": "Driver_Biochar",
                "desc": "Management changes involving application of biochar to soil.",
                "type": "binary"
            },
            {
                "name": "Forest management",
                "col": "Driver_Forest_management",
                "desc": "Management changes involving sustainable forestry or wood harvesting management.",
                "type": "binary"
            },
            {
                "name": "Conservation",
                "col": "Driver_Conservation",
                "desc": "Management changes involving species or habitat conservation.",
                "type": "binary"
            },
            {
                "name": "Deforestation",
                "col": "Driver_Deforestation",
                "desc": "Management changes aimed at reducing/preventing deforestation.",
                "type": "binary"
            },
            {
                "name": "Restoration",
                "col": "Driver_Restoration",
                "desc": "Management changes focused on the ecological restoration of degraded natural habitats.",
                "type": "binary"
            },
            {
                "name": "Weathering",
                "col": "Driver_Weathering",
                "desc": "Management changes involving enhanced rock weathering applications.",
                "type": "binary"
            },
            {
                "name": "Grazing",
                "col": "Driver_Grazing",
                "desc": "Management changes involving livestock grazing or pasture systems.",
                "type": "binary"
            },
            {
                "name": "Irrigation",
                "col": "Driver_Irrigation",
                "desc": "Management changes involving irrigation infrastructure or practice optimization.",
                "type": "binary"
            },
            {
                "name": "Land conversion",
                "col": "Driver_Land_conversion",
                "desc": "Management changes involving direct land use conversion.",
                "type": "binary"
            },
            {
                "name": "Rewetting",
                "col": "Driver_Rewetting",
                "desc": "Management changes involving rewetting of peatlands or organic soils.",
                "type": "binary"
            },
            {
                "name": "Fire management",
                "col": "Driver_Fire_management",
                "desc": "Management changes involving controlled burning or fire protection strategies.",
                "type": "binary"
            }
        ],
        "💼 Stakeholder Occupations": [
            {
                "name": "Farmers",
                "col": "Occupation_Farmers",
                "desc": "Farmers implementing soil management practices.",
                "type": "binary"
            },
            {
                "name": "Foresters & Forester Associations",
                "col": "Occupation_Foresters_Forester_Associations",
                "desc": "Foresters or forest manager cooperatives.",
                "type": "binary"
            },
            {
                "name": "Public Administrators",
                "col": "Occupation_Public_Administrators",
                "desc": "Governmental representatives or public policy makers.",
                "type": "binary"
            },
            {
                "name": "Educational & Research Institutions",
                "col": "Occupation_Educational_Institutions_Research",
                "desc": "Universities, researchers, or extension services.",
                "type": "binary"
            },
            {
                "name": "NGOs",
                "col": "Occupation_NGOs",
                "desc": "Non-governmental organizations operating in climate or soil preservation.",
                "type": "binary"
            },
            {
                "name": "Agroindustry",
                "col": "Occupation_Agroindustry",
                "desc": "Agricultural manufacturers, processors, and food brands.",
                "type": "binary"
            },
            {
                "name": "Forestry Companies",
                "col": "Occupation_Forestry_Companies",
                "desc": "Commercial logging or forestry operations.",
                "type": "binary"
            },
            {
                "name": "Consultancy",
                "col": "Occupation_Consultancy",
                "desc": "Independent carbon or agronomy consultants.",
                "type": "binary"
            },
            {
                "name": "Project Developer",
                "col": "Occupation_Project_developer",
                "desc": "Developers designing and managing VCM carbon credit projects.",
                "type": "binary"
            },
            {
                "name": "Other Companies",
                "col": "Occupation_Other_companies",
                "desc": "Other commercial companies and corporate buyers.",
                "type": "binary"
            },
            {
                "name": "Software Developers",
                "col": "Occupation_Software_developers",
                "desc": "Technology companies building platforms and MRV software.",
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
                "name": "Soil Fauna",
                "col": "Parameter_Soil_Fauna",
                "desc": "Measurement of soil fauna density, diversity, and biological quality.",
                "type": "binary"
            },
            {
                "name": "Greenhouse Gas Fluxes (GHG)",
                "col": "Parameter_GHG",
                "desc": "Measurement or modelling of CO2, N2O, or CH4 emissions associated with soils.",
                "type": "binary"
            },
            {
                "name": "Oxygen Content",
                "col": "Parameter_Oxygen_content",
                "desc": "Measurement of soil aeration and oxygen levels.",
                "type": "binary"
            },
            {
                "name": "Clay Mineralogy",
                "col": "Parameter_Clay_mineralogy",
                "desc": "Physicochemical analysis of clay types and minerals in the soil.",
                "type": "binary"
            },
            {
                "name": "CEC (Cation Exchange Capacity)",
                "col": "Parameter_CEC",
                "desc": "Measurement of soil cation exchange capacity (nutrient retention capacity).",
                "type": "binary"
            },
            {
                "name": "Particle Size Distribution / Texture",
                "col": "Parameter_Particle_size_distribution_Texture",
                "desc": "Quantitative distribution of sand, silt, and clay particles (soil texture).",
                "type": "binary"
            },
            {
                "name": "Soil Porosity",
                "col": "Parameter_Soil_porosity",
                "desc": "Measurement of soil pore space volume and structure.",
                "type": "binary"
            },
            {
                "name": "Soil Diffusivity",
                "col": "Parameter_Soil_diffusivity",
                "desc": "Measurement of gas/solute diffusion properties in soil.",
                "type": "binary"
            },
            {
                "name": "Aggregate Stability",
                "col": "Parameter_Aggregate_stability",
                "desc": "Measurement of soil structural stability and resistance to erosion/slaking.",
                "type": "binary"
            },
            {
                "name": "Soil Compaction / Bulk Density",
                "col": "Parameter_Soil_compaction_Bulk_density",
                "desc": "Measurement of soil physical density and degree of compaction.",
                "type": "binary"
            },
            {
                "name": "Nutrient Availability",
                "col": "Parameter_Nutrient_availability",
                "desc": "Measurement of plant-available nutrients (Nitrogen, Phosphorus, Potassium, etc.).",
                "type": "binary"
            },
            {
                "name": "Pollutant Concentration",
                "col": "Parameter_Pollutant_concentration",
                "desc": "Measurement of heavy metals, pesticides, or other toxic pollutants in soil.",
                "type": "binary"
            },
            {
                "name": "Soil Depth",
                "col": "Parameter_Soil_depth",
                "desc": "Measurement of total depth of the topsoil or soil profile.",
                "type": "binary"
            },
            {
                "name": "Peat Depth",
                "col": "Parameter_Peat_depth",
                "desc": "Measurement of peat deposit depth/thickness in organic soils.",
                "type": "binary"
            },
            {
                "name": "Soil Color",
                "col": "Parameter_Soil_color",
                "desc": "Visual or spectrophotometric classification of soil color.",
                "type": "binary"
            },
            {
                "name": "Soil Type",
                "col": "Parameter_Soil_type",
                "desc": "Pedological classification of soil types.",
                "type": "binary"
            },
            {
                "name": "Subsidence",
                "col": "Parameter_Subsidence",
                "desc": "Measurement of peat subsidence or soil surface level changes over time.",
                "type": "binary"
            },
            {
                "name": "CaCO3",
                "col": "Parameter_CaCO3",
                "desc": "Measurement of calcium carbonate content.",
                "type": "binary"
            },
            {
                "name": "Electrical Conductivity",
                "col": "Parameter_Electrical_conductivity",
                "desc": "Measurement of soil salinity and conductivity.",
                "type": "binary"
            },
            {
                "name": "Water Holding Capacity",
                "col": "Parameter_Water_holding_capacity",
                "desc": "Measurement of soil water retention and holding capacity.",
                "type": "binary"
            },
            {
                "name": "Infiltration Rate",
                "col": "Parameter_Infiltration_rate",
                "desc": "Measurement of water infiltration speed into the soil surface.",
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
            },
            {
                "name": "On-site Imagery (Soil Scanner)",
                "col": "Data_on_site_images",
                "desc": "Use of on-site scanners, portable spectrometers, or field photos for direct soil characterization.",
                "type": "binary"
            }
        ],
        "🔒 Reporting & Verification Schemes": [
            {
                "name": "Standard Document Report",
                "col": "Format_Document",
                "desc": "Whether the results are reported in a standard PDF or document report format.",
                "type": "binary"
            },
            {
                "name": "Online Platform Entry",
                "col": "Format_Online",
                "desc": "Whether reporting is done directly via an online database or web platform.",
                "type": "binary"
            },
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
                "name": "Implementation Status",
                "col": "Implementation",
                "desc": "Maturity status of the framework: already operational and applied in the field (Implemented) or still theoretical (Project).",
                "type": "categorical"
            }
        ]
    }
    
    # Translation dictionaries for guide names & descriptions
    GUIDE_TRANS = {
        'Land_use_Agriculture': ("Agriculture", "Détermine si le protocole de suivi MRV s'applique aux cultures, à l'élevage ou au maraîchage."),
        'Land_use_Forest': ("Forêt", "Détermine si le cadre s'applique aux zones forestières ou boisées, ou aux projets d'agroforesterie."),
        'Land_use_Urban': ("Urbain", "Indique si le protocole peut être utilisé en zone urbaine ou périurbaine (sols anthropiques)."),
        'Land_use_Degraded_land': ("Terres Dégradées", "Indique si la méthode est spécifique à la restauration écologique de sols dégradés, miniers ou contaminés."),
        'Land_use_Peatland_Wetland': ("Tourbières & Zones Humides", "Détermine si le cadre est adapté au suivi des zones humides ou des tourbières (sols gorgés d'eau, riches en carbone)."),
        
        'Scale_Local': ("Échelle Locale", "Le suivi s'applique localement, généralement à l'échelle de la parcelle ou de l'exploitation."),
        'Scale_Regional': ("Échelle Régionale", "Le suivi est réalisé à l'échelle d'un grand territoire, d'une région ou d'un bassin versant."),
        'Scale_National': ("Échelle Nationale", "La méthodologie est conçue pour les inventaires nationaux de GES ou les politiques publiques à l'échelle d'un pays."),
        'Scale_Continental': ("Échelle Continentale", "La méthodologie s'applique à l'échelle d'un continent entier."),
        'Scale_Global': ("Échelle Globale", "Le protocole de suivi est universel, applicable au niveau international ou mondial."),
        
        'Data_Land_Management': ("Données de gestion des terres", "Données déclaratives recueillies auprès des agriculteurs (historique des cultures, travail du sol, couverts)."),
        'Data_Spatial_images': ("Imagerie satellite / spatiale", "Utilisation d'images satellites ou de drones pour cartographier ou surveiller à distance l'état des cultures et du sol."),
        'Data_Soil_samples': ("Prélèvements physiques de sol", "Prélèvement physique de carottes de sol sur le terrain suivi d'analyses physico-chimiques en laboratoire."),
        'Data_Modelling': ("Modélisation numérique", "Modèles mathématiques et informatiques simulant l'évolution du carbone organique du sol dans le temps."),
        'Data_on_site_images': ("Scanner de sol sur site", "Utilisation de scanners sur site, de spectromètres portables ou de photos de terrain pour caractériser directement le sol."),
        
        'Format_Document': ("Rapport document standard", "Indique si les résultats sont rapportés sous forme de document ou rapport standard (PDF, Doc)."),
        'Format_Online': ("Saisie sur plateforme en ligne", "Indique si le reporting se fait directement via une base de données ou un portail web en ligne."),
        'Action_based': ("Vérification basée sur les actions", "Validation conditionnée au respect de pratiques culturales recommandées (ex: semis de couverts) sans mesurer le stock final."),
        'Result_based': ("Vérification basée sur les résultats", "Validation conditionnée aux résultats mesurés in-situ (ex: tonnes de carbone stockées en plus)."),
        'Implementation': ("Statut d'implémentation", "Maturité du cadre : opérationnel et appliqué sur le terrain (Implemented) ou encore théorique (Project).")
    }

    # Display by sections
    for group_name, list_filters in filters_info.items():
        translated_group_name = group_name
        if is_fr:
            translated_group_name = group_name.replace("🌱 Context & Land Uses (Land Use)", "🌱 Contexte & Usages des Sols (Land Use)")
            translated_group_name = translated_group_name.replace("🌍 Spatial Scales (Scale)", "🌍 Échelles Spatiales (Scale)")
            translated_group_name = translated_group_name.replace("🛠️ Drivers / Management Changes", "🛠️ Leviers / Pratiques Agricoles")
            translated_group_name = translated_group_name.replace("💼 Stakeholder Occupations", "💼 Acteurs & Occupations")
            translated_group_name = translated_group_name.replace("🔬 Soil Parameters", "🔬 Paramètres du Sol")
            translated_group_name = translated_group_name.replace("📊 Data Types Used (Data Type)", "📊 Types de Données Utilisés")
            translated_group_name = translated_group_name.replace("🔒 Reporting & Verification Schemes", "🔒 Reporting & Schémas de Vérification")
            
        st.markdown(f"<div class='section-header'>{translated_group_name}</div>", unsafe_allow_html=True)
        
        for f in list_filters:
            col_name = f['col']
            desc = f['desc']
            name = f['name']
            
            # Localize names and descriptions dynamically
            if is_fr:
                if col_name in GUIDE_TRANS:
                    name, desc = GUIDE_TRANS[col_name]
                elif col_name.startswith('Driver_'):
                    orig_key = col_name.replace('Driver_', '').replace('_', ' ')
                    for eng, fr in DRIVER_MAP_KEYS_FR.items():
                        if eng.lower().replace(' / ', ' ').replace(' ', '') == orig_key.lower().replace(' ', ''):
                            name = fr
                            break
                    desc = f"Levier / Pratique : {name}."
                elif col_name.startswith('Occupation_'):
                    orig_key = col_name.replace('Occupation_', '').replace('_', ' ')
                    for eng, fr in OCCUPATION_KEYS_FR.items():
                        if eng.lower().replace(' & ', ' ').replace(' ', '') == orig_key.lower().replace(' ', ''):
                            name = fr
                            break
                    desc = f"Acteur impliqué : {name}."
                elif col_name.startswith('Parameter_'):
                    orig_key = col_name.replace('Parameter_', '').replace('_', ' ')
                    for eng, fr in PARAM_KEYS_FR.items():
                        if eng.lower().replace(' (', ' ').replace(')', '').replace(' / ', ' ').replace(' ', '') == orig_key.lower().replace(' ', ''):
                            name = fr
                            break
                    desc = f"Paramètre physico-chimique ou biologique du sol : {name}."
            
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
                    {t(f"Distribution de la base ({len(combined_df)} cadres) :", f"Database distribution (out of {len(combined_df)} frameworks):")}
                    <span class="mrv-badge badge-web" style="margin-left: 8px;">{t("Oui", "Yes")}: {yes_count} ({pct_yes}%)</span>
                    <span class="mrv-badge badge-no" style="background-color: #581c1c; color: #fecaca; border: 1px solid #991b1b; padding: 4px 10px; border-radius: 20px;">{t("Non", "No")}: {no_count} ({100 - pct_yes}%)</span>
                </div>
                """
            else:
                # Categorical
                if col_name in combined_df.columns:
                    val_counts = combined_df[col_name].value_counts()
                    badges = []
                    for val, count in val_counts.items():
                        pct = round((count / len(combined_df)) * 100)
                        badges.append(f'<span class="mrv-badge badge-lit" style="background-color: #1e293b; color: #e2e8f0; border: 1px solid #475569; padding: 4px 10px; border-radius: 20px;">{translate_val(val, is_fr)} : {count} ({pct}%)</span>')
                    stat_html = f"""
                    <div style="margin-top: 8px; font-size: 13px; color: var(--text-muted); display: flex; flex-wrap: wrap; align-items: center; gap: 4px;">
                        {t("Distribution de la base :", "Database distribution:")} {"".join(badges)}
                    </div>
                    """
                else:
                    stat_html = ""
            
            with st.expander(t(f"🔍 {name} (Variable technique : `{col_name}`)", f"🔍 {name} (Technical variable: `{col_name}`)")):
                st.markdown(f"""
                <div style="padding: 5px 0;">
                    <p style="margin: 0; font-size: 14px; line-height: 1.6; color: var(--text-color);">{desc}</p>
                    {stat_html}
                </div>
                """, unsafe_allow_html=True)

################################################################################################ END ################################################################################################