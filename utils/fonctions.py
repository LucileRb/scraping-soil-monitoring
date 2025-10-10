########## IMPORTS ##########
import pandas as pd
from bs4 import BeautifulSoup
import requests
import random
import time
from urllib.parse import urlparse
import re
from IPython.display import display


#### to avoid error 429 (too many requests):
# -> Use Session with Connection Pooling
# Using an HTTP session for repeated requests to the same server improves performance and makes requests less aggressive.
# The session automatically reuses the same underlying TCP connection, which is less likely to trigger anti-scraping defenses.
session = requests.Session()

def remove_punctuation(text):
    # Use regex to match all characters that are not word characters or spaces
    cleaned_text = re.sub(r"[^\w\s\d'-]", ' ', text)
    return cleaned_text.lower()

def shorten_url(url):
    # Parse the URL using urlparse
    parsed_url = urlparse(url)
    # Rebuild the URL with just the scheme and domain (netloc)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/"
    return base_url

# Function to scrape data from a single URL
def scrape_url(keyword):
        time.sleep(round(random.uniform(1, 10), 1))
        df_final = pd.DataFrame(columns = ['Societes', 'Urls'])
        
        # Format the keyword for the URL
        formatted_keyword = keyword.lower().replace('#', '').replace(' ', '').replace('à', 'a').replace('é', 'e').replace('è', 'e').replace('ê', 'e').replace('ù', 'u').replace('ç', 'c').replace('ë', 'e').replace('&', '')

        # Send a GET request to Google
        url = f"https://www.google.com/search?q={formatted_keyword}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = session.get(url, headers = headers)
            if response.status_code == 200:
                 # Parse the HTML content
                time.sleep(round(random.uniform(1, 10), 1))
                soup = BeautifulSoup(response.text, 'html.parser')
                # Look for div elements with data-text-ad attribute
                articles = soup.find_all('div', class_ = 'MjjYud')
                time.sleep(round(random.uniform(1, 10), 1))

                urls = []
                for article in articles[:10]:
                    for a in article.find_all('a', href = True):
                        #print(a['href'])
                        urls.append(a['href'])

                # clean du nom de la société
                society_clean = remove_punctuation(formatted_keyword)
                token_society = set(society_clean.split())

                # dict des urls avec leur similarité
                dict_similarity = dict.fromkeys(urls)

                for url in urls:
                    #print(url)
                    try:
                        domain = urlparse(url).netloc
                        url_clean = remove_punctuation(domain)
                        token_url = set(url_clean.split())

                        # Compute the intersection and union
                        intersection = token_society.intersection(token_url)
                        union = token_society.union(token_url)

                        # Compute and print the Jaccard Similarity
                        J = len(intersection)/len(union)

                        # filtrer les urls qu'on ne veut pas
                        # Construire l'expression régulière à partir de la liste
                        element_to_exclude = [
                            'linkedin', 'wikipedia', 'gouv', 'lerobert', 'facebook', 'pappers', 'instagram', 
                            'google', 'youtube', 'societe', 'amazon', 'allocine', 'linguee', 
                            'service-public', 'onisep', 'wiktionary', 'ausha.co', 'twitter', 
                            'cci', 'microsoft', 'twitch', 'pinterest', 'booknode', 'soundcloud', 
                            'cnrtl', 'codeur', 'ebay', 'apollo', 'journaldunet', 'pagesjaunes', 'lefigaro', 'infonet',
                            'information', 'leboncoin', 'lagazettefrance', 'kompass', 'mappy', 'github', 'gowork',
                            'usinenouvelle', 'spotify', 'lacentrale', 'citroen', 'rubypayeur', 'allogarage',
                            'tiktok', 'copainsdavant', 'indeed', 'kompass', 'mappy', 'tripadvisor', 'trustpilot',
                            'welcometothejungle', 'larousse', 'infoempresa', 'frenchweb', 'fnac', 'filae', 'doctolib',
                            'dailymotion', 'bfmtv'
                        ]
                        # trouver comment ajouter les elements exclus
                        # 

                        # Construire l'expression régulière à partir de la liste échappée
                        pattern = r'(' + '|'.join(element_to_exclude) + ')'

                        # Parcourir les URL
                        if re.search(pattern, str(token_url)):
                            # supprimer l'url du dict
                            dict_similarity.pop(url, None)
                        else:
                            # conserver J dans le dictionnaire
                            dict_similarity[url] = J
                    except:
                        dict_similarity.pop(url, None)

                # Create new row in dataframe
                time.sleep(round(random.uniform(1, 10), 1))
                # Filtrer les urls avec la valeur de similitude la plus élevée puis prendre l'url la plus courte
                #max_value = max(dict_similarity.values())
                #max_value_keys = [key for key, value in dict_similarity.items() if value == max_value] # PAS SURE
                #best_url = min(max_value_keys, key = len)
                best_url = max(dict_similarity, key = dict_similarity.get)
                #print(f'{keyword} ----> {best_url}')
                if re.search(r'http|https|www', str(best_url)):
                    best_url = shorten_url(best_url)
                else:
                    best_url = 'absent'
                print(f'{keyword} ----> {best_url}')
                df_final.loc[-1] = [keyword, best_url]
                df_final.index = df_final.index + 1
                df_final = df_final.sort_index()
                return df_final
            elif response.status_code == 429:
                # Server is asking us to slow down
                print("Received 429 Too Many Requests, sleeping and retrying...")
                retry_after = int(response.headers.get("Retry-After", 60))  # Retry-After header tells us how long to wait
                time.sleep(retry_after)
            else:
                print(f"Failed to retrieve data from {keyword}. Status code: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error scraping data from {keyword}: {str(e)}")
            print(e)
            df_final.loc[-1] = [keyword, "absent"]
            df_final.index = df_final.index + 1
            df_final = df_final.sort_index()
            return df_final


# Parallelized scraping using multiprocessing
def scrape_parallel(urls):
    results = []
    for url in urls:
        result = scrape_url(url)  # Call scrape_url for each URL in the chunk
        results.append(result)
    # Concatenate all DataFrames into a single DataFrame
    final_result = pd.concat(results, ignore_index = True)
    return final_result

def worker_function(url_chunk, semaphore, results_list):
    """
    The worker function that runs in parallel.
    It scrapes URLs and appends the result to the shared list (results_list).
    A semaphore ensures that no more than a certain number of processes run concurrently.
    """
    with semaphore:
        result = scrape_parallel(url_chunk)
        results_list.append(result)