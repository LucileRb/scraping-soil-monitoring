########## IMPORTS ##########
import numpy as np
import pandas as pd
from utils import ggsheet, fonctions
import multiprocessing
from IPython.display import display
from urllib.parse import urlparse
import tldextract
from tqdm import tqdm

def main():

    url = 'https://docs.google.com/spreadsheets/d/1EeGOSl4xZWfIHXmiVRgywSQbnW6gmEFzRTL19LvXsOM/edit?gid=1388196829#gid=1388196829'
    df = ggsheet.googleSheetImport(url)

    df_unknown = df.loc[(df['Urls'] == 'absent')]

    print('* début du scraping\n')
    print(f'-> {df_unknown.shape[0]} societés à scraper...\n')

    url_list = df_unknown['Societes'].tolist()

    # Number of processes to be equal to the number of CPU cores
    num_processes = multiprocessing.cpu_count() - 1

    # Create a semaphore to limit concurrency to the number of available CPU cores
    semaphore = multiprocessing.Semaphore(num_processes)

    # Create a manager to handle shared data between processes (list of DataFrames)
    manager = multiprocessing.Manager()
    results_list = manager.list()  # Shared list to store results from all processes

    # Split the list of URLs into chunks for each process
    url_chunks = np.array_split(url_list, num_processes)

    # Create and start worker processes
    processes = []
    for chunk in url_chunks:
        process = multiprocessing.Process(target = fonctions.worker_function, args = (chunk, semaphore, results_list))
        process.start()
        processes.append(process)

    # Wait for all processes to finish
    for process in processes:
        process.join()

    # Combine all DataFrames in the shared list into a final DataFrame
    final_df = pd.concat(results_list, ignore_index = True)

    df_export = pd.concat([df, final_df])
    df_export = df_export.sort_values(by = ['Societes', 'Urls'], ascending = False)
    df_export = df_export.drop_duplicates(subset = ['Societes'], keep = 'first')
    df_export = df_export.sort_index()

    # Export du résultat sur ggsheet
    ggsheet.googleSheetExport(url, df_export)
    print('* done !')

    print('* Export des données avec détail...')
    try:
        df_export['Company'] = df_export['Urls'].apply(lambda x : tldextract.extract(x).domain)
    except:
        print('error company')
        pass
    df_export['Domain'] = df_export['Urls'].apply(lambda x : urlparse(x).netloc)

    # Export du résultat sur autre ggsheet
    #url_export_recap = 'https://docs.google.com/spreadsheets/d/1nPWWKzcTd5Z13WgoqT8u5_6KH2F3IkUr9EHMtPFFvw4/edit?gid=1578537328#gid=1578537328'
    #ggsheet.googleSheetExport(url_export_recap, df_export)
    #print('* done !')

    # Ajouter alerte mail ?

if __name__ == '__main__':
    main()


########## END ##########