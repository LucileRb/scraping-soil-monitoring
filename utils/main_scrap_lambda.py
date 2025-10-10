########## IMPORTS ##########
import pandas as pd
from utils import ggsheet, fonctions, email_alert
from bs4 import BeautifulSoup
import requests
import random
import time
from urllib.parse import urlparse

# Ajouter alerte mail

def main():

    url_test = 'https://docs.google.com/spreadsheets/d/1EeGOSl4xZWfIHXmiVRgywSQbnW6gmEFzRTL19LvXsOM/edit?gid=0#gid=0'
    df = ggsheet.googleSheetImport(url_test)
    df_unknown = df.loc[df['Urls'] == 'unknown']

    print('* début du scraping\n')
    print(f'-> {df_unknown.shape[0]} societés à scraper...\n')
    scrap_nb = 0

    # Scrap Beautifulsoup

    df_final = pd.DataFrame(columns = ['Societes', 'Urls'])
    for keyword in df_unknown['Societes'].tolist()[:500]:
        scrap_nb += 1
        print(f"----- n°{scrap_nb}/{len(df_unknown['Societes'].tolist()[:500])} : scrap du term {keyword} -----\n")
        # Format the keyword for the URL
        formatted_keyword = keyword.lower().replace(' ', '+')

        # Send a GET request to Google
        url = f"https://www.google.fr/search?q={formatted_keyword}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(url, headers = headers)
            #print(response)
        except Exception as e:
            print(e)

        # Parse the HTML content
        time.sleep(round(random.uniform(1, 10), 1))
        soup = BeautifulSoup(response.text, 'html.parser')

        try:

            # Look for div elements with data-text-ad attribute
            articles = soup.find_all('div', class_='MjjYud')
            time.sleep(round(random.uniform(1, 10), 1))

            urls = []
            for article in articles[:10]:
                for a in article.find_all('a', href=True):
                    #print(a['href'])
                    urls.append(a['href'])

            # clean du nom de la société
            society_clean = fonctions.remove_punctuation(keyword)
            token_society = set(society_clean.split())

            # dict des urls avec leur similarité
            dict_similarity = dict.fromkeys(urls)

            for url in urls:
                try:
                    #print(url)
                    domain = urlparse(url).netloc
                    url_clean = fonctions.remove_punctuation(domain)
                    token_url = set(url_clean.split())

                    # Compute the intersection and union
                    intersection = token_society.intersection(token_url)
                    #print(f"Intersection: {intersection}")

                    union = token_society.union(token_url)
                    #print(f"Union: {union}")

                    # Compute and print the Jaccard Similarity
                    J = len(intersection)/len(union)
                    #print('Jaccard Similarity:', J)

                    # conserver J dans le dictionnaire
                    dict_similarity[url] = J

                except:
                    dict_similarity.pop(url, None)

            # Create new row in dataframe
            best_url = max(dict_similarity, key = dict_similarity.get)
            print(best_url)
            df_final.loc[-1] = [keyword, best_url]
            df_final.index = df_final.index + 1
            df_final = df_final.sort_index()
        except:
            df_final.loc[-1] = [keyword, "fail"]
            df_final.index = df_final.index + 1
            df_final = df_final.sort_index()

        #print(f"----- Fin du scrap pour le term {keyword} -----\n")

        # Pause to avoid too many requests error
        print("---------Pause-------\n")
        time.sleep(round(random.uniform(1, 10), 1))

    # concat avec le df d'origine
    print('* fin du scrap et export des données...')
    df_export = pd.concat([df, df_final])
    df_export = df_export.sort_values(by = ['Societes', 'Urls'], ascending = True)
    df_export = df_export.drop_duplicates(subset = ['Societes'], keep = 'first')
    df_export = df_export.sort_index()

    # Export du résultat sur ggsheet
    url_export = 'https://docs.google.com/spreadsheets/d/1EeGOSl4xZWfIHXmiVRgywSQbnW6gmEFzRTL19LvXsOM/edit?gid=0#gid=0'
    ggsheet.googleSheetExport(url_export, df_export)
    print('* done !')

    # Ajouter alerte mail
    titre = f'Run code scrap url'
    body = f'Tout va bien, {scrap_nb} urls scrapees'
    email_alert.email(titre, body, 'lucile@ads-up.fr')

if __name__ == '__main__':
    main()


########## END ##########