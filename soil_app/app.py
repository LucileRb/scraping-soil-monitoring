import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from PIL import Image

# Absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# List JPG files
JPG_FILES = []
if os.path.exists(os.path.join(BASE_DIR, 'app_illustrations')):
    JPG_FILES = sorted([f for f in os.listdir(os.path.join(BASE_DIR, 'app_illustrations')) if f.endswith('.jpg')])

if JPG_FILES:
    LOGO_PATH = os.path.join(BASE_DIR, 'app_illustrations', JPG_FILES[0])
else:
    LOGO_PATH = None

@st.cache_resource
def get_cropped_image(image_path, target_w, target_h):
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        with Image.open(image_path) as img:
            img_w, img_h = img.size
            target_ratio = target_w / target_h
            current_ratio = img_w / img_h
            
            if current_ratio > target_ratio:
                new_w = int(img_h * target_ratio)
                left = (img_w - new_w) // 2
                right = left + new_w
                top = 0
                bottom = img_h
            else:
                new_h = int(img_w / target_ratio)
                top = (img_h - new_h) // 2
                bottom = top + new_h
                left = 0
                right = img_w
                
            img_cropped = img.crop((left, top, right, bottom))
            img_resized = img_cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
            img_resized.load()
            return img_resized
    except Exception as e:
        try:
            return Image.open(image_path)
        except Exception:
            return None

@st.cache_data
def get_base64_image(image_path):
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
    except Exception:
        return ""

def calculate_hp(mrv_data):
    if isinstance(mrv_data, dict):
        mrv_data = pd.Series(mrv_data)
    yes_count = 0
    for col in mrv_data.index:
        if (col.startswith('Parameter_') or col.startswith('Land_use_') or col.startswith('Scale_') or col.startswith('Data_')) and mrv_data[col] == 'Yes':
            yes_count += 1
    return min(60 + yes_count * 10, 150)

def translate_val(val):
    # Always English mapping
    mapping = {
        'Implemented': 'Implemented',
        'implemented': 'Implemented',
        'Project': 'Project',
        'project': 'Project',
        'Internal': 'Internal',
        'External': 'External',
        'Yes': 'Yes',
        'No': 'No',
        'Literature (Scopus)': 'Literature (Scopus)',
        'AI Search': 'AI Search',
        'Webscraping': 'Webscraping',
        'Unknown': 'Unknown',
        'All': 'All',
        'Depends/Flexible': 'Depends/Flexible'
    }
    return mapping.get(str(val), val)

def generate_pokemon_card_html(mrv_data, clickable=False):
    if isinstance(mrv_data, dict):
        mrv_data = pd.Series(mrv_data)
        
    land_uses = []
    lu_names = [
        ('Agriculture', 'Land_use_Agriculture'),
        ('Forest', 'Land_use_Forest'),
        ('Urban', 'Land_use_Urban'),
        ('Degraded', 'Land_use_Degraded_land'),
        ('Wetland', 'Land_use_Peatland_Wetland')
    ]
    for lu_lbl, col in lu_names:
        if mrv_data.get(col) == 'Yes':
            land_uses.append(lu_lbl)
    land_uses_str = ", ".join(land_uses) if land_uses else "None"
    
    scales = []
    scale_names = [
        ('Local', 'Scale_Local'),
        ('Regional', 'Scale_Regional'),
        ('National', 'Scale_National'),
        ('Continental', 'Scale_Continental'),
        ('Global', 'Scale_Global')
    ]
    for sc_lbl, col in scale_names:
        if mrv_data.get(col) == 'Yes':
            scales.append(sc_lbl)
    scales_str = ", ".join(scales) if scales else "None"
    
    occupations = []
    for occ_lbl, col in OCCUPATION_MAP.items():
        if mrv_data.get(col) == 'Yes':
            occupations.append(occ_lbl)
    occupations_str = ", ".join(occupations) if occupations else "None"
    
    drivers = []
    for drv_lbl, col in DRIVER_MAP.items():
        if mrv_data.get(col) == 'Yes':
            drivers.append(drv_lbl)
    drivers_str = ", ".join(drivers) if drivers else "None"
    
    params = []
    for col in mrv_data.index:
        if col.startswith('Parameter_') and not col.endswith('_Precision') and col != 'Parameter_Others':
            if mrv_data.get(col) == 'Yes':
                label = col.replace('Parameter_Soil_', '').replace('Parameter_', '').replace('_', ' ')
                params.append(label)
    params_str = ", ".join(params) if params else "None"
    
    data_types = []
    for col in mrv_data.index:
        if col.startswith('Data_') and col != 'Data_Sharing':
            if mrv_data.get(col) == 'Yes':
                label = col.replace('Data_', '').replace('_', ' ')
                data_types.append(label)
    data_str = ", ".join(data_types) if data_types else "None"
    
    formats = []
    for col in ['Format_Document', 'Format_Online']:
        if mrv_data.get(col) == 'Yes':
            formats.append(col.replace('Format_', ''))
    formats_str = ", ".join(formats) if formats else "None"
    
    threshold = mrv_data.get('Threshold', 'N/A')
    
    schemes = []
    for col in ['Action_based', 'Result_based']:
        if mrv_data.get(col) == 'Yes':
            schemes.append(col.replace('_based', '-based'))
    schemes_str = ", ".join(schemes) if schemes else "None"
    
    auditor = mrv_data.get('Auditor', 'N/A')
    impl = mrv_data.get('Implementation', 'Project')
    sharing = mrv_data.get('Data_Sharing', 'No')
    
    mrv_id = mrv_data.get('ID_MRV', 'N/A')
    mrv_name = mrv_data.get('MRV_Name', 'Framework')
    author = mrv_data.get('Pub_Author', 'Unknown')
    year = mrv_data.get('Pub_Year', '2025')
    country = mrv_data.get('Country', 'Global')
    purpose = mrv_data.get('Purpose', 'Not specified')
    pub_link = mrv_data.get('Pub_Link', '#')
    
    html = (
        f'<div class="mrv-custom-card">'
        f'<div class="card-header-custom">'
        f'<span class="card-header-id">{mrv_id}</span>'
        f'<span class="card-header-name">{mrv_name} 🌱</span>'
        f'</div>'
        f'<div class="card-mrv-block">'
        f'<div class="card-mrv-monitoring">'
        f'<div class="block-title">Monitoring</div>'
        f'<div class="block-text">'
        f'Parameters : {params_str}<br>'
        f'Data : {data_str}<br>'
        f'Frequency : {mrv_data.get("Monitoring_frequency", "N/A")}<br>'
        f'Standards use : {mrv_data.get("Methodology_Standard", "N/A")}'
        f'</div>'
        f'</div>'
        f'<div class="card-mrv-rep-ver">'
        f'<div class="card-mrv-reporting">'
        f'<div class="block-title">Reporting</div>'
        f'<div class="block-text">'
        f'Format : {formats_str}<br>'
        f'Uncertainty: {mrv_data.get("Uncertainty", "N/A")}<br>'
        f'Threshold : {threshold}'
        f'</div>'
        f'</div>'
        f'<div class="card-mrv-verification">'
        f'<div class="block-title">Verification</div>'
        f'<div class="block-text">'
        f'Sheme : {schemes_str}<br>'
        f'Methodology : {mrv_data.get("Verification_methodology", "N/A")}<br>'
        f'Auditor : {auditor}<br>'
        f'Automatization : {mrv_data.get("Verification_automatization", "N/A")}<br>'
        f'Open-access : {sharing}'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'<div class="card-impl-bar">'
        f'Implementation | <span class="impl-country">{country} |</span>'
        f'</div>'
        f'<div class="card-section-box">'
        f'<div class="section-box-title">Where ?</div>'
        f'<div class="section-box-text">'
        f'Land use: {land_uses_str}<br>'
        f'Geographical scale : {scales_str}'
        f'</div>'
        f'</div>'
        f'<div class="card-section-box">'
        f'<div class="section-box-title">Who ?</div>'
        f'<div class="section-box-text">'
        f'Occupation : {occupations_str}'
        f'</div>'
        f'</div>'
        f'<div class="card-section-box">'
        f'<div class="section-box-title">Why ?</div>'
        f'<div class="section-box-text">'
        f'Purpose : {purpose}<br>'
        f'Actions : {drivers_str}'
        f'</div>'
        f'</div>'
        f'<div class="card-links-box">'
        f'<div class="card-link-item"><a href="{pub_link}" target="_blank">SOURCE (with URL link)</a></div>'
        f'<div class="card-link-item"><a href="{pub_link}" target="_blank">Title of our article (with URL link)</a></div>'
        f'</div>'
        f'</div>'
    )
    if clickable:
        html = f'<a href="?focus={mrv_id}" target="_self" style="text-decoration: none; color: inherit; display: block;">{html}</a>'
    return html

def render_mrv_details(mrv_data):
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 General & Source",
        "🌍 Context & Stakeholders",
        "🔬 Monitoring",
        "📊 Reporting & Verification"
    ])
    
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
            
            st.markdown("<div class='section-header'>Application Scale</div>", unsafe_allow_html=True)
            st.markdown(f"- Local: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Scale_Local') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Scale_Local') == 'Yes' else '#C62828'}'>{mrv_data.get('Scale_Local', 'No')}</span>", unsafe_allow_html=True)
            st.markdown(f"- Regional: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Scale_Regional') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Scale_Regional') == 'Yes' else '#C62828'}'>{mrv_data.get('Scale_Regional', 'No')}</span>", unsafe_allow_html=True)
            st.markdown(f"- National: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Scale_National') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Scale_National') == 'Yes' else '#C62828'}'>{mrv_data.get('Scale_National', 'No')}</span>", unsafe_allow_html=True)
            st.markdown(f"- Continental: <span class='badge-yes' style='background-color: {'#E8F5E9' if mrv_data.get('Scale_Continental') == 'Yes' else '#FFEBEE'}; color: {'#1B5E20' if mrv_data.get('Scale_Continental') == 'Yes' else '#C62828'}'>{mrv_data.get('Scale_Continental', 'No')}</span>", unsafe_allow_html=True)
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
                st.write("**Targeted Practices / Drivers:**")
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
            st.markdown(f"- On-site scanner imagery: {mrv_data.get('Data_on_site_images', 'No')}")
            
            st.markdown("<div class='section-header'>Sampling Plan</div>", unsafe_allow_html=True)
            st.write(f"**Monitoring frequency:** {mrv_data['Monitoring_frequency']}")
            st.write(f"**Average plot area:** {mrv_data.get('Plot_Area', 'N/A')} {mrv_data.get('Plot_Area_Unit', '')}")
            st.write(f"**Standardized methodology:** {mrv_data.get('Methodology_Standard', 'No')}")

    with tab4:
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown("<div class='section-header'>Reporting & Uncertainty</div>", unsafe_allow_html=True)
            st.write(f"**Report format:** Document: {mrv_data.get('Format_Document', 'No')} | Online: {mrv_data.get('Format_Online', 'No')}")
            st.write(f"**Uncertainty calculation:** {mrv_data['Uncertainty']}")
            st.write(f"**Threshold method:** {mrv_data['Threshold']}")
            
        with col_right:
            st.markdown("<div class='section-header'>Verification & Governance</div>", unsafe_allow_html=True)
            st.write(f"**Action-based scheme:** {mrv_data.get('Action_based', 'No')}")
            st.write(f"**Result-based scheme:** {mrv_data.get('Result_based', 'No')}")
            st.write(f"**Auditor:** {mrv_data['Auditor']}")
            st.write(f"**Data sharing:** {mrv_data.get('Data_Sharing', 'No')}")

# Page config
st.set_page_config(
    page_title='Soil Monitoring & Decision Tool (MRV)',
    page_icon='🌱',
    layout='wide'
)

# Matplotlib config
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

@st.cache_data
def load_and_clean_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    
    variables_path = os.path.join(data_dir, 'variables.json')
    variables = []
    if os.path.exists(variables_path):
        with open(variables_path, 'r', encoding='utf-8') as f:
            variables = json.load(f)
            
    txt_files = ['db_articles-11-04-26.txt', 'db_webscraping-27-04-26.txt', 'db_AI-13-04-26.txt']
    dfs = []
    
    for fn in txt_files:
        path = os.path.join(data_dir, fn)
        if not os.path.exists(path):
            continue
            
        df = pd.read_csv(path, sep='\t')
        df.columns = [c.strip() for c in df.columns]
        
        if 'In_Scope' in df.columns:
            df['In_Scope_Clean'] = df['In_Scope'].astype(str).str.strip().str.lower()
            df_yes = df[df['In_Scope_Clean'] == 'yes'].copy()
            df_yes['Source_File'] = fn
            
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
        
    combined['Purpose'] = combined['Purpose'].astype(str).str.strip()
    combined['Purpose'] = combined['Purpose'].replace({'nan': 'Unknown', '': 'Unknown', 'NA': 'Unknown'})
    
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
    
    combined['Uncertainty'] = combined['Uncertainty'].astype(str).str.strip()
    combined['Uncertainty'] = combined['Uncertainty'].replace({'nan': 'Unknown', '': 'Unknown', 'NA': 'Unknown'})
    
    combined['Threshold'] = combined['Threshold'].astype(str).str.strip()
    combined['Threshold'] = combined['Threshold'].replace({'nan': 'Unknown', '': 'Unknown', 'NA': 'Unknown'})
    
    combined['Auditor'] = combined['Auditor'].astype(str).str.strip()
    combined['Auditor'] = combined['Auditor'].replace({'nan': 'Unknown', '': 'Unknown', 'NA': 'Unknown'})
    
    combined['Implementation'] = combined['Implementation'].astype(str).str.strip()
    combined['Implementation'] = combined['Implementation'].replace({'nan': 'Unknown', '': 'Unknown', 'NA': 'Unknown'})
    
    combined['MRV_Name'] = combined['MRV_Name'].fillna('').astype(str).str.strip()
    combined['MRV_Name'] = combined.apply(
        lambda r: r['ID_MRV'] if not r['MRV_Name'] or r['MRV_Name'].lower() == 'na' else r['MRV_Name'], 
        axis=1
    )
    
    pub_title = []
    pub_author = []
    pub_year = []
    pub_link = []
    
    for idx, r in combined.iterrows():
        t = r.get('Title')
        if pd.notna(t) and str(t).strip() != '' and str(t).strip().lower() != 'nan':
            title_val = str(t).strip()
        else:
            title_val = r['MRV_Name'] if r['Source'] == 'Webscraping' else 'Source URL'
        pub_title.append(title_val)
        
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
        
        y = r.get('Year')
        py = r.get('Publication_Year')
        if pd.notna(y) and str(y).replace('.0','').strip().isdigit():
            year_val = str(int(float(y)))
        elif pd.notna(py) and str(py).replace('.0','').strip().isdigit():
            year_val = str(int(float(py)))
        else:
            dt = r.get('Date')
            if pd.notna(dt) and '/' in str(dt):
                year_val = str(dt).split('/')[-1].strip()
            else:
                year_val = '2025'
        pub_year.append(year_val)
        
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

variables, combined_df = load_and_clean_data()

# CSS Styling (English dark mode & premium looks)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary-color: #52B788;
        --secondary-color: #DAB254;
        --bg-color: #0E1612;
        --sidebar-bg: #15221B;
        --card-bg: #1B2B22;
        --text-color: #E2E8F0;
        --text-muted: #94A3B8;
        --border-color: #24352C;
    }
    
    .stApp {
        font-family: 'Outfit', sans-serif !important;
        background-color: var(--bg-color) !important;
        color: var(--text-color) !important;
    }
    
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
    
    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
        border-right: 1px solid var(--border-color);
    }
    [data-testid="stSidebar"] * {
        color: var(--text-color) !important;
    }
    
    .badge-yes { background-color: #1C4532; color: #9AE6B4; font-size: 11px; font-weight: bold; border-radius: 4px; padding: 2px 6px; }
    .badge-no { background-color: #742A2A; color: #FEB2B2; font-size: 11px; font-weight: bold; border-radius: 4px; padding: 2px 6px; }
    
    .section-header {
        color: var(--primary-color) !important;
        font-size: 18px;
        font-weight: 700;
        border-bottom: 2px solid var(--primary-color);
        padding-bottom: 6px;
        margin-top: 24px;
        margin-bottom: 12px;
    }
    
    .pokemon-card-wrapper {
        display: flex;
        justify-content: center;
        margin-bottom: 24px;
        perspective: 1000px;
    }
    
    .mrv-custom-card {
        background: #0E1612;
        border: 4.5px solid #c89d3c;
        border-radius: 18px;
        padding: 15px;
        box-sizing: border-box;
        width: 100%;
        max-width: 360px;
        margin: 0 auto;
        font-family: 'Outfit', sans-serif !important;
        box-shadow: 0 15px 35px rgba(0,0,0,0.6);
    }
    
    .card-header-custom {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        padding-bottom: 4px;
    }
    
    .card-header-id {
        background: #242526;
        border-radius: 4px;
        padding: 4px 10px;
        font-weight: 700;
        color: #fff !important;
        font-size: 13px;
    }
    
    .card-header-name {
        background: #242526;
        border-radius: 4px;
        padding: 4px 10px;
        color: #ef4444 !important;
        font-weight: bold;
        font-size: 13px;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    
    .card-mrv-block {
        border: 2px solid #c89d3c;
        border-radius: 8px;
        display: flex;
        overflow: hidden;
        margin-bottom: 10px;
        background: #15221B;
    }
    
    .card-mrv-monitoring {
        width: 50%;
        border-right: 2px solid #c89d3c;
        padding: 8px;
    }
    
    .card-mrv-rep-ver {
        width: 50%;
        display: flex;
        flex-direction: column;
    }
    
    .card-mrv-reporting {
        border-bottom: 2px solid #c89d3c;
        padding: 8px;
        flex: 1;
    }
    
    .card-mrv-verification {
        padding: 8px;
        flex: 1.2;
    }
    
    .block-title {
        font-size: 13px;
        font-weight: bold;
        color: #fff !important;
        margin-bottom: 6px;
        border-bottom: 1px solid rgba(255,255,255,0.15);
        padding-bottom: 2px;
        text-align: center;
    }
    
    .block-text {
        font-size: 9.5px;
        line-height: 1.35;
        color: #E2E8F0 !important;
    }
    
    .block-text b {
        color: #dab254 !important;
    }
    
    .card-impl-bar {
        background: #dab254;
        color: #0E1612 !important;
        font-size: 10.5px;
        font-weight: bold;
        text-align: center;
        padding: 4px 8px;
        border-radius: 4px;
        margin-bottom: 10px;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 6px;
    }
    
    .impl-country {
        background: rgba(0, 0, 0, 0.15);
        border: 1px solid rgba(0, 0, 0, 0.25);
        padding: 1px 6px;
        border-radius: 3px;
        display: inline-block;
        color: #0E1612 !important;
    }
    
    .card-section-box {
        background: #111e16;
        border-radius: 6px;
        padding: 8px 10px;
        margin-bottom: 8px;
        border: 1px solid rgba(255,255,255,0.05);
    }
    
    .section-box-title {
        color: #dab254 !important;
        font-size: 12px;
        font-weight: bold;
        margin-bottom: 4px;
    }
    
    .section-box-text {
        font-size: 10px;
        color: #E2E8F0 !important;
        line-height: 1.3;
    }
    
    .section-box-text b {
        color: #64748b !important;
    }
    
    .card-links-box {
        margin-top: 10px;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    
    .card-link-item {
        background: #242526;
        border-radius: 4px;
        padding: 6px;
        font-size: 9px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .card-link-item a {
        color: #dab254 !important;
        text-decoration: none;
        font-weight: bold;
    }

    /* Step-based Welcome Screen Annotated Card Layout */
    .annotated-container {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 20px;
        background: #111e16;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #24352C;
    }
    .annotation-panel {
        flex: 1;
        background: rgba(0, 0, 0, 0.4);
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #2c5e43;
    }
    .annotation-item {
        margin-bottom: 12px;
        font-size: 13px;
        line-height: 1.4;
    }
    .annotation-title {
        color: #dab254;
        font-weight: 600;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# Data maps
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

# Session state initialization
if 'step' not in st.session_state:
    st.session_state.step = 'page_1'

# Handle query parameters for clickable cards
if "focus" in st.query_params:
    st.session_state.selected_mrv_id = st.query_params["focus"]
    st.session_state.step = 'page_4'

defaults = {
    'filter_lu_agri': False,
    'filter_lu_forest': False,
    'filter_lu_urban': False,
    'filter_lu_peat': False,
    'filter_sc_local': False,
    'filter_sc_regional': False,
    'filter_sc_national': False,
    'filter_sc_continental': False,
    'filter_sc_global': False,
    'filter_occupation': 'All',
    'filter_purpose': 'All',
    'filter_driver': 'All',
    'filter_search_mode': '⭐ Matching Score (Recommended)',
    'selected_mrv_id': None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Sidebar Layout
if LOGO_PATH:
    sidebar_cropped = get_cropped_image(LOGO_PATH, 300, 500)
    if sidebar_cropped:
        st.sidebar.image(sidebar_cropped, use_column_width=True)
st.sidebar.markdown("<div style='text-align: center; font-size: 11px; color: #94A3B8; margin-top: 5px; font-style: italic;'>Photos credits : Camille Imbert</div>", unsafe_allow_html=True)



# Helper function to render filters
def draw_filter_widgets(in_sidebar=False):
    container = st.sidebar if in_sidebar else st
    
    container.markdown("### WHERE ?")
    container.markdown("**Land Uses**")
    container.checkbox("Agriculture", key="filter_lu_agri")
    container.checkbox("Forest", key="filter_lu_forest")
    container.checkbox("Urban", key="filter_lu_urban")
    container.checkbox("Peatland / Wetland", key="filter_lu_peat")
    
    container.markdown("**Geographical scale**")
    container.checkbox("Local Scale", key="filter_sc_local")
    container.checkbox("Regional Scale", key="filter_sc_regional")
    container.checkbox("National Scale", key="filter_sc_national")
    container.checkbox("Continental Scale", key="filter_sc_continental")
    container.checkbox("Global Scale", key="filter_sc_global")
    
    container.markdown("### WHO ?")
    occupations = ['All'] + sorted(list(OCCUPATION_MAP.keys()))
    container.selectbox("Stakeholder Occupations", occupations, key="filter_occupation")
    
    container.markdown("### WHY ?")
    purposes = ['All'] + sorted([p for p in combined_df['Purpose'].unique() if pd.notna(p) and p != 'Unknown'])
    container.selectbox("Purpose", purposes, key="filter_purpose")
    
    drivers = ['All'] + sorted(list(DRIVER_MAP.keys()))
    container.selectbox("Actions to implement", drivers, key="filter_driver")
    
    container.markdown("### Search Mode")
    container.radio(
        "Search Mode Select",
        ["⭐ Matching Score (Recommended)", "🔒 Strict Filtering (AND)"],
        key="filter_search_mode",
        label_visibility="collapsed"
    )

# Compute active filters and filter dataframe
active_filters = {}
if st.session_state.filter_lu_agri: active_filters['Land_use_Agriculture'] = 'Yes'
if st.session_state.filter_lu_forest: active_filters['Land_use_Forest'] = 'Yes'
if st.session_state.filter_lu_urban: active_filters['Land_use_Urban'] = 'Yes'
if st.session_state.filter_lu_peat: active_filters['Land_use_Peatland_Wetland'] = 'Yes'

if st.session_state.filter_sc_local: active_filters['Scale_Local'] = 'Yes'
if st.session_state.filter_sc_regional: active_filters['Scale_Regional'] = 'Yes'
if st.session_state.filter_sc_national: active_filters['Scale_National'] = 'Yes'
if st.session_state.filter_sc_continental: active_filters['Scale_Continental'] = 'Yes'
if st.session_state.filter_sc_global: active_filters['Scale_Global'] = 'Yes'

if st.session_state.filter_occupation != 'All':
    active_filters[OCCUPATION_MAP[st.session_state.filter_occupation]] = 'Yes'
if st.session_state.filter_purpose != 'All':
    active_filters['Purpose'] = st.session_state.filter_purpose
if st.session_state.filter_driver != 'All':
    active_filters[DRIVER_MAP[st.session_state.filter_driver]] = 'Yes'

df_results = combined_df.copy()
if "🔒 Strict" in st.session_state.filter_search_mode:
    for col, val in active_filters.items():
        df_results = df_results[df_results[col] == val]
    df_results['Match_Score'] = 100
else:
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

# Sidebar filter rendering for page_3 and page_4
if st.session_state.step in ['page_3', 'page_4']:
    st.sidebar.markdown("<div style='color: #dab254; font-size: 20px; font-weight: bold; margin-top: 25px; border-bottom: 2px solid #dab254; padding-bottom: 5px;'>YOUR CONTEXT :</div>", unsafe_allow_html=True)
    with st.sidebar:
        draw_filter_widgets(in_sidebar=True)

# ----------------- PAGE 1: WELCOMING PAGE -----------------
if st.session_state.step == 'page_1':
    st.markdown("<h1>Find your soil MRV procedure adapted to your context</h1>", unsafe_allow_html=True)
    st.markdown("""
    **Monitoring Reporting and Verification (MRV)** procedures give guidelines to assess the action of an activity, in a robust and transparent soil parameters. 
    Within the scientific project BENCHMARKS, we reviewed all the existing MRV procedures including soil parameters in the scientific article *Title and URL link to add*. 
    This interactive application allows you to navigate in our list of MRV procedures and to select those that are the most adapted to your context. 
    The MRV procedures are presented as cards, including all the information we found.
    
    More info about our data collection methodology : *Title of the scientific article and URL link to add*
    """)
    
    col_btn_l, col_btn_c, col_btn_r = st.columns([2, 1, 2])
    with col_btn_c:
        if st.button("Let's start", use_container_width=True):
            st.query_params.clear()
            st.session_state.step = 'page_2'
            st.rerun()
            
    st.divider()
    st.markdown("<h3>Example of MRV card</h3>", unsafe_allow_html=True)
    
    # Render annotated example card
    st.markdown("""
    <style>
        .schema-grid {
            display: grid;
            grid-template-columns: 1.2fr 1fr 1.2fr;
            gap: 20px;
            align-items: stretch;
            margin-top: 20px;
        }
        .schema-col-left {
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            text-align: right;
            padding-right: 15px;
            border-right: 2px dashed #dab254;
        }
        .schema-col-right {
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            text-align: left;
            padding-left: 15px;
            border-left: 2px dashed #dab254;
        }
        .schema-item {
            background: rgba(0, 0, 0, 0.2);
            padding: 8px 12px;
            border-radius: 6px;
            margin-bottom: 8px;
            border: 1px solid rgba(82, 183, 136, 0.1);
        }
        .schema-title {
            color: #dab254;
            font-weight: bold;
            font-size: 13px;
        }
        .schema-desc {
            font-size: 11px;
            color: #E2E8F0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col_layout_l, col_layout_c, col_layout_r = st.columns([1.2, 1, 1.2])
    
    with col_layout_l:
        st.markdown("""
        <div class="schema-col-left">
            <div class="schema-item">
                <span class="schema-title">Type of Soil Parameters ───►</span>
                <p class="schema-desc">Soil organic carbon, pH, bulk density, etc., measured in-situ or in lab.</p>
            </div>
            <div class="schema-item">
                <span class="schema-title">Type of Data Used ───►</span>
                <p class="schema-desc">Self-reported farming surveys, satellite imagery, physical soil cores, or models.</p>
            </div>
            <div class="schema-item">
                <span class="schema-title">Time Range / Frequency ───►</span>
                <p class="schema-desc">Time gap required between two consecutive soil monitoring sessions.</p>
            </div>
            <div class="schema-item">
                <span class="schema-title">Methodology Standard ───►</span>
                <p class="schema-desc">If a recognized methodology standard (ISO, IPCC, Verra) is required.</p>
            </div>
            <div class="schema-item">
                <span class="schema-title">Where? Land Use ───►</span>
                <p class="schema-desc">Cropland, forestry, grasslands, peatlands, or degraded lands.</p>
            </div>
            <div class="schema-item">
                <span class="schema-title">Geographical Scale ───►</span>
                <p class="schema-desc">Application scope: Local, Regional, National, Continental, or Global.</p>
            </div>
            <div class="schema-item">
                <span class="schema-title">Who? Targeted Stakeholders ───►</span>
                <p class="schema-desc">Targeted user role (Farmers, Foresters, NGOs, Project developers, etc.).</p>
            </div>
            <div class="schema-item">
                <span class="schema-title">Why? Market Purpose ───►</span>
                <p class="schema-desc">Target markets like Voluntary Carbon Markets, Compliance, or public incentives.</p>
            </div>
            <div class="schema-item">
                <span class="schema-title">Actions to Implement ───►</span>
                <p class="schema-desc">Specific soil practices targeting carbon accumulation or restoration.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_layout_c:
        # Example card content
        example_data = pd.Series({
            'Source': 'Literature (Scopus)',
            'Land_use_Agriculture': 'Yes',
            'Land_use_Forest': 'Yes',
            'Land_use_Urban': 'No',
            'Land_use_Degraded_land': 'No',
            'Land_use_Peatland_Wetland': 'No',
            'Scale_Local': 'Yes',
            'Scale_Regional': 'No',
            'Scale_National': 'No',
            'Scale_Continental': 'No',
            'Scale_Global': 'No',
            'Parameter_Soil_organic_matter_SOC': 'Yes',
            'Parameter_Soil_pH': 'Yes',
            'Parameter_Soil_moisture': 'Yes',
            'Data_Soil_samples': 'Yes',
            'Data_Modelling': 'Yes',
            'Format_Document': 'Yes',
            'Format_Online': 'No',
            'Threshold': 'Relative Change',
            'Action_based': 'Yes',
            'Result_based': 'Yes',
            'Auditor': 'External',
            'Implementation': 'Implemented',
            'Data_Sharing': 'Yes',
            'ID_MRV': 'MRV-01',
            'MRV_Name': 'Example Framework',
            'Pub_Author': 'Camille Imbert',
            'Pub_Year': '2025',
            'Country': 'Global',
            'Purpose': 'Voluntary carbon market'
        })
        card_html = generate_pokemon_card_html(example_data)
        st.markdown(card_html, unsafe_allow_html=True)
        
        # Matching score bar below the card
        st.markdown("""
        <div style="font-size: 11px; text-align: center; font-weight: bold; color: #ffffff; margin-top: 15px; width: 100%; max-width: 360px; margin-left: auto; margin-right: auto;">
            Matching Score: 100%
            <div style="background-color: #24352C; border-radius: 4px; height: 6px; width: 100%; margin-top: 4px; overflow: hidden;">
                <div style="background-color: #52B788; width: 100%; height: 100%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_layout_r:
        st.markdown("""
        <div class="schema-col-right">
            <div class="schema-item">
                <span class="schema-title">◄─── Final Product / Format</span>
                <p class="schema-desc">Reporting output format: Document reports (PDF, Word) or Online dashboards.</p>
            </div>
            <div class="schema-item">
                <span class="schema-title">◄─── Uncertainty Computation</span>
                <p class="schema-desc">Statistical methods used to measure and adjust for results uncertainty.</p>
            </div>
            <div class="schema-item">
                <span class="schema-title">◄─── Threshold Values</span>
                <p class="schema-desc">Baseline/threshold methodology (Fixed vs Relative change).</p>
            </div>
            <div class="schema-item">
                <span class="schema-title">◄─── Verification Scheme</span>
                <p class="schema-desc">Whether validation is based on actions performed or measured results.</p>
            </div>
            <div class="schema-item">
                <span class="schema-title">◄─── Verification Auditor</span>
                <p class="schema-desc">Validation entity: Internal project auditor or Independent third-party.</p>
            </div>
            <div class="schema-item">
                <span class="schema-title">◄─── Automatization</span>
                <p class="schema-desc">If reporting and verification are handled manually or automated.</p>
            </div>
            <div class="schema-item">
                <span class="schema-title">◄─── Open Access Data</span>
                <p class="schema-desc">If final project data is shared publicly or remains private/internal.</p>
            </div>
            <div class="schema-item">
                <span class="schema-title">◄─── Implementation Status</span>
                <p class="schema-desc">Geographic coverage and status (Implemented project or theoretical concept).</p>
            </div>
            <div class="schema-item">
                <span class="schema-title">◄─── Source Link</span>
                <p class="schema-desc">Clickable URL linking to the original public dataset or methodology page.</p>
            </div>
            <div class="schema-item">
                <span class="schema-title">◄─── Our Article Link</span>
                <p class="schema-desc">Clickable URL pointing directly to our published literature review paper.</p>
            </div>
            <div class="schema-item">
                <span class="schema-title">◄─── Matching Score Bar</span>
                <p class="schema-desc">Visual percentage showing how well the card fits your filter requests.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ----------------- PAGE 2: FILTER SELECTION -----------------
elif st.session_state.step == 'page_2':
    st.markdown("<h1>Find your soil MRV procedure adapted to your context</h1>", unsafe_allow_html=True)
    st.markdown("This interactive application allows you to navigate in our list of MRV procedures and to select those that are the most adapted to your context :")
    
    st.divider()
    
    col_filters_l, col_filters_c, col_filters_r = st.columns(3)
    
    with col_filters_l:
        st.markdown("### WHERE ?")
        st.markdown("**Land Uses**")
        st.checkbox("Agriculture", key="filter_lu_agri")
        st.checkbox("Forest", key="filter_lu_forest")
        st.checkbox("Urban", key="filter_lu_urban")
        st.checkbox("Peatland / Wetland", key="filter_lu_peat")
        
        st.markdown("**Geographical scale**")
        st.checkbox("Local Scale", key="filter_sc_local")
        st.checkbox("Regional Scale", key="filter_sc_regional")
        st.checkbox("National Scale", key="filter_sc_national")
        st.checkbox("Continental Scale", key="filter_sc_continental")
        st.checkbox("Global Scale", key="filter_sc_global")
        
    with col_filters_c:
        st.markdown("### WHO ?")
        occupations = ['All'] + sorted(list(OCCUPATION_MAP.keys()))
        st.selectbox("Stakeholder Occupations", occupations, key="filter_occupation")
        
        st.markdown("### Search Mode")
        st.radio(
            "Search Mode Select",
            ["⭐ Matching Score (Recommended)", "🔒 Strict Filtering (AND)"],
            key="filter_search_mode",
            label_visibility="collapsed"
        )
        
    with col_filters_r:
        st.markdown("### WHY ?")
        purposes = ['All'] + sorted([p for p in combined_df['Purpose'].unique() if pd.notna(p) and p != 'Unknown'])
        st.selectbox("Purpose", purposes, key="filter_purpose")
        
        drivers = ['All'] + sorted(list(DRIVER_MAP.keys()))
        st.selectbox("Actions to implement", drivers, key="filter_driver")
        
    st.divider()
    
    col_btn_l, col_btn_c, col_btn_r = st.columns([2, 1, 2])
    with col_btn_c:
        if st.button("Get the MRV procedures", use_container_width=True):
            st.query_params.clear()
            st.session_state.step = 'page_3'
            st.rerun()

# ----------------- PAGE 3 & 4: RESULTS & DETAIL VIEW -----------------
elif st.session_state.step in ['page_3', 'page_4']:
    st.markdown("<h1>Find your soil MRV procedure adapted to your context</h1>", unsafe_allow_html=True)
    st.markdown("Here are the MRV procedures fitted with your requirements :")
    
    st.divider()
    
    if df_results.empty:
        st.info("No MRV procedures matched your strict filters. Try switching to 'Matching Score' mode.")
    else:
        # Display top cards in a 3-column grid
        # Limit to top 15 results for performance, let user browse via scroll
        top_n = min(15, len(df_results))
        cols = st.columns(3)
        for idx in range(top_n):
            mrv_row = df_results.iloc[idx]
            col_idx = idx % 3
            with cols[col_idx]:
                score = mrv_row.get('Match_Score', 100)
                card_html = generate_pokemon_card_html(mrv_row, clickable=True)
                st.markdown(card_html, unsafe_allow_html=True)
                
                # Render matching score below the card
                bar_color = "#52B788" if score > 70 else ("#DAB254" if score > 40 else "#EF4444")
                st.markdown(f"""
                <div style="font-size: 11.5px; text-align: center; font-weight: bold; color: #ffffff; margin-top: 10px; margin-bottom: 15px; width: 100%; max-width: 360px; margin-left: auto; margin-right: auto;">
                    Matching Score: {score}%
                    <div style="background-color: #24352C; border-radius: 4px; height: 6px; width: 100%; margin-top: 4px; overflow: hidden;">
                        <div style="background-color: {bar_color}; width: {score}%; height: 100%;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<div style='margin-bottom: 75px;'></div>", unsafe_allow_html=True)

        # Page 4: Detailed view of focus card
        if st.session_state.step == 'page_4' and st.session_state.selected_mrv_id:
            focused_rows = combined_df[combined_df['ID_MRV'] == st.session_state.selected_mrv_id]
            if not focused_rows.empty:
                focused_mrv = focused_rows.iloc[0]
                st.divider()
                st.markdown(f"<h2>Focus on {focused_mrv['MRV_Name']} ({focused_mrv['ID_MRV']}) :</h2>", unsafe_allow_html=True)
                
                col_det_l, col_det_r = st.columns([1.5, 2.5])
                with col_det_l:
                    focused_score = df_results[df_results['ID_MRV'] == st.session_state.selected_mrv_id].iloc[0].get('Match_Score', 100)
                    card_html_focused = generate_pokemon_card_html(focused_mrv)
                    st.markdown(card_html_focused, unsafe_allow_html=True)
                    
                    # Render matching score below focused card
                    focused_bar_color = "#52B788" if focused_score > 70 else ("#DAB254" if focused_score > 40 else "#EF4444")
                    st.markdown(f"""
                    <div style="font-size: 11.5px; text-align: center; font-weight: bold; color: #ffffff; margin-top: 10px; margin-bottom: 25px; width: 100%; max-width: 360px; margin-left: auto; margin-right: auto;">
                        Matching Score: {focused_score}%
                        <div style="background-color: #24352C; border-radius: 4px; height: 6px; width: 100%; margin-top: 4px; overflow: hidden;">
                            <div style="background-color: {focused_bar_color}; width: {focused_score}%; height: 100%;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_det_r:
                    render_mrv_details(focused_mrv)