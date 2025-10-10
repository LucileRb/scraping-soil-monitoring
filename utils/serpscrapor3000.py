########## IMPORTS ##########
# General Imports
import pandas as pd
import random

# Dates
import time
from datetime import date
from datetime import datetime

# Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

########## FONCTION ##########

def scrapator(search_terms, client_name):

    start_time = datetime.now()
    print(f'Début du programme : {start_time}\n')

    df = pd.DataFrame()

    # initier webdriver
    options = webdriver.ChromeOptions()
    #options.headless = True # marche pas ??
    driver = webdriver.Chrome(options = options)

    print('***** scrapping en cours *****')

    # boucle sur search terms
    for term in search_terms:

        print(f'\n**** search term - {term} ****\n')

        # aller sur google
        driver.get('https://google.com')
        try:
            # accepter conditions
            WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button#L2AGLb.tHlp8d'))).click()
        except:
            pass

        # trouver la search bar
        elem = driver.find_element(By.NAME, 'q')
        elem.clear() # pour la vider si elle est pas vide

        # entrer l'element de recherche souhaité dans la search bar
        elem.send_keys(term)

        # petite pause
        time.sleep(round(random.uniform(1, 10), 1))

        # récupérer les suggestions
        suggestions = driver.find_elements(By.CLASS_NAME, 'sbct')

        ### extraire le texte des suggestions
        # créer des listes vides pour stocker l'information
        position = 0
        page_pos = []
        phrases = []

        # itérer sur les suggestions à tester
        for sug in suggestions:
            try:
                # texte
                mots_clefs = sug.find_element(By.CLASS_NAME, 'wM6W7d')
                phrases.append(mots_clefs.text)
                print(mots_clefs.text)

                # position
                position += 1
                page_pos.append(position)
            except:
                print(f'<!> Warning - Problème avec {sug} <!>')

        # mettre le tout dans un df
        df_term = pd.DataFrame()
        df_term['Suggestions'] = phrases
        df_term['Position'] = page_pos
        df_term['Mots clefs'] = term

        # Merger avec les données des suggestions précédents
        df = pd.concat([df, df_term], ignore_index = True)
        df['Date'] = date.today().strftime('%d/%m/%y')
        df['Client'] = client_name

        print(f'\nFin du scrapping pour le search term : {term} ')

    # quitter driver
    driver.close()

    # Mettre à jours infos du runs sur google sheet de suivi
    print('Mise à jour du fichier de suivi')
    url_runs = 'https://docs.google.com/spreadsheets/d/1w9-z_bZuTkSZUKsbnztqjkrQ_YWbRp_V2TQlrgqnFUk/edit#gid=1455637252'
    df_runs = ggsheet.googleSheetImport(url_runs)
    #print(df_runs)

    # 'calcul' des variables
    date_run = datetime.now().strftime('%d/%m/%y')
    heure_run = datetime.now().strftime('%H:%M:%S')
    jour_run = datetime.now().strftime('%A')

    # mettre sous forme de df
    df_runs_updated = pd.concat([df_runs, pd.DataFrame({'Date' : date_run, 'Heure' : heure_run, 'Mots clefs' : [search_terms], 'Jour' : jour_run, 'Client' : client_name})], ignore_index = True)

    # Convertir en str (sinon pb lors de l'export des mots clefs sous forme de liste)
    df_runs_updated_str = df_runs_updated.astype(str)

    # Export df mis à jour
    ggsheet.googleSheetExport(url_runs, df_runs_updated_str)

    end_time = datetime.now() # à formater
    print('Duration: {}'.format(end_time - start_time))

    return df



def find_position(row):
    if row['Client'].lower() in row['Suggestions'].lower():
        return row['Position']
    else:
        return 0
    

def add_scoring(row):
    scoring = 0
    if row['Client'].lower() in row['Suggestions'].lower():
        scoring += 1
    return scoring

########## END ##########