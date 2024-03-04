import pandas as pd 
import os
import json
import time
import sys
import textdistance as td
from prompt_toolkit import prompt
from tkinter import filedialog
from pathlib import Path
from unidecode import unidecode
from colorama import just_fix_windows_console
from colorama import Fore
from prettytable import PrettyTable

just_fix_windows_console()


ESTAB_FILE_PATH = ""
DEST_FILE_PATH = ""
LOG_PATH = f"{os.getcwd()}/logs.json"
HISTORY = ""
OUTPUT_FOLDER_PATH = ""
OUTPUT_FILENAME = ""

def create_log():
    global ESTAB_FILE_PATH
    global DEST_FILE_PATH
    global LOG_PATH
    global HISTORY
    global OUTPUT_FOLDER_PATH
    global OUTPUT_FILENAME

    if not Path(LOG_PATH).exists():
        HISTORY = {
            "last_dest": 0,
            "dest_path": "",
            "estab_path": "",
            "output_path": os.getcwd(),
            "output_file": "result"
        }
        with open(LOG_PATH, 'w') as openfile:
            openfile.write(json.dumps(HISTORY))

    else:
        HISTORY = json.loads(open(LOG_PATH).read())
        ESTAB_FILE_PATH = HISTORY['estab_path']
        DEST_FILE_PATH = HISTORY['dest_path']
        OUTPUT_FOLDER_PATH = HISTORY['output_path']
        OUTPUT_FILENAME = HISTORY['output_file']


def set_log(new_log:dict):
    with open(LOG_PATH, 'w') as openfile:
        openfile.write(json.dumps(new_log))

def suggest_simillar_word(item_to_find:dict, list_items:list) -> list:
    word_to_find = unidecode(item_to_find['nom_etablissement']).upper()
    first_suggestions = []
    suggestions = []
    reserved_words = [
                        "LES", "LE", "LA", "DES", "DE", "DU", "A",
                        "RESIDENCE", "RESIDENCES", "RÉSIDENCE", "CENTRE", 
                        "CLUB", "HOTEL", "PARKING", "SPI", "&", "AGENCE", "/", 
                        "HÔTEL", "GITE", "GITES","GÎTE", "PARTICULIER", "MVA", "P&V", 
                        "VACANCEOLE", "CITADINES", "REFUGE",
                        "RESIDETUDES", "CITY", "AIRE", "VVF", "VCS"
                    ]
    word_to_find = "".join([x for x in word_to_find.split(' ') if x not in reserved_words])

    for suggestion in list_items:
        suggestion_name = unidecode(str(suggestion['name']).upper())
        suggestion_name = "".join([y for y in suggestion_name.split(' ') if y not in reserved_words])
        similiarity_ratio = td.jaccard(word_to_find, suggestion_name)
        if similiarity_ratio >= 0.65:
            first_suggestions.append(suggestion)

    first_suggestions = [dict(t) for t in {tuple(d.items()) for d in first_suggestions}]

    for suggestion in first_suggestions:
        splitted = item_to_find['nom_etablissement'].split(' ')
        number_of_word = len(splitted)
        correspond_count = 0
        splitted_suggestion = unidecode(suggestion['name'].upper()).split(' ')
        for sp in splitted:
            if sp in splitted_suggestion:
                correspond_count += 1
        
        if correspond_count >= number_of_word - 1 or correspond_count <= number_of_word + 1:
            if unidecode(f"{suggestion['locality']}").lower() in unidecode(str(item_to_find['adresse'])).lower():
                suggestions.insert(0, suggestion)
            suggestions.append(suggestion)

    return suggestions


def save_data(data:dict, filename:str):
    output_file = f"{OUTPUT_FOLDER_PATH}/{filename}.csv"
    if not Path(output_file).exists():
        dfx = pd.DataFrame(columns=['code','id_g2a','name','name_g2a','locality','station', 'station_code'])
        dfx.to_csv(output_file, index=False)
    df = pd.DataFrame([data])
    df.to_csv(output_file, mode='a', index=False, header=False)


def try_int(value) -> int | str:
    try:
        return int(value)
    except:
        return ""


create_log()

if ESTAB_FILE_PATH == "" and DEST_FILE_PATH == "":
    print(Fore.LIGHTMAGENTA_EX + " -->> select etablishement csv files")
    prompt(' -->> press enter to proced ')
    ESTAB_FILE_PATH = filedialog.askopenfilename(initialdir= os.getcwd(),
                                        title= "Please select a file",
                                        filetypes=[('csv', '*.csv')])
    print(Fore.LIGHTMAGENTA_EX + ' -->> select destination csv files')
    prompt(' -->> press enter to proced ')
    DEST_FILE_PATH = filedialog.askopenfilename(initialdir= os.getcwd(),
                                        title= "Please select a file",
                                        filetypes=[('csv', '*.csv')])
    print(Fore.LIGHTMAGENTA_EX + ' -->> select output folder csv path')
    prompt(' -->> press enter to proced ')
    OUTPUT_FOLDER_PATH = filedialog.askdirectory(initialdir= os.getcwd())
    print(Fore.LIGHTMAGENTA_EX + ' -->> output filename ')
    OUTPUT_FILENAME = prompt(' -->> ')

    HISTORY["dest_path"] = DEST_FILE_PATH
    HISTORY['estab_path'] = ESTAB_FILE_PATH
    HISTORY['output_path'] = OUTPUT_FOLDER_PATH
    HISTORY['output_file'] = OUTPUT_FILENAME

    set_log(HISTORY)

print(' --> reading files')
file_1 = pd.read_csv(DEST_FILE_PATH)
file_2 = pd.read_csv(ESTAB_FILE_PATH)

name_correct = []
for x in range(len(file_1)):
    sub = file_1.loc[x].to_dict()
    sub['loc'] = x 
    name_correct.append(sub)

for y in range(HISTORY['last_dest'], len(file_2)):
    current_item = file_2.loc[y]
    print(Fore.LIGHTMAGENTA_EX + f"  --> what is the correct index for:")
    print(Fore.LIGHTGREEN_EX + f" {current_item.to_dict()}")
    new_suggestions = suggest_simillar_word(current_item, name_correct)
    if new_suggestions:
        print(Fore.WHITE + "==> choices: ")
        print(Fore.LIGHTYELLOW_EX + "  --> # to define new destinations")
        table = PrettyTable(['index', 'code', 'station', 'station_code', 'name', 'locality'])
        for i in range(len(new_suggestions)):
            sug = new_suggestions[i]
            table.add_row([i,try_int(sug['code']), sug['station'], try_int(sug['station_code']), sug['name'], sug['locality']])
        print(table)
        choice = prompt("your answer  ==> ")
        match choice:
            case '#':
                print(Fore.RED + '  ==> this functionality is not yet done, press enter to continue')
                prompt('  ==> press enter')
                save_data(current_item, 'no_suggestion')
            case _:
                print(Fore.LIGHTGREEN_EX + f"  ==> You choose {new_suggestions[int(choice)]}") 
                print(Fore.LIGHTGREEN_EX + f"  ==> For {current_item.to_dict()}")

                data = {
                'code' : new_suggestions[int(choice)]['code'],
                'id_g2a' : current_item['id'],
                'name' : new_suggestions[int(choice)]['name'],
                'name_g2a' : current_item['nom_etablissement'],
                'locality' : new_suggestions[int(choice)]['locality'],
                'station' : new_suggestions[int(choice)]['station'],
                'station_code': try_int(new_suggestions[int(choice)]['station_code'])
                }

                print(Fore.LIGHTMAGENTA_EX + f"  ==> data to be saved will be {data}")
                print(Fore.LIGHTGREEN_EX + "  ==> Is it OK ? yes or no")
                yesorno = prompt("  your answer ==> ")
                match yesorno.lower():
                    case 'yes':
                        save_data(data, OUTPUT_FILENAME)
                    case _:
                        print(Fore.RED + 'programme will shut down')
                        time.sleep(2)
                        sys.exit()


    else:
        print(Fore.RED + '   ==> no suggestions, please verify and try again by pressing crt + C or enter to bypass')
        save_data(current_item, 'no_suggestion')
        prompt("  ==> ")
    last_index = HISTORY['last_dest']
    HISTORY['last_dest'] = last_index + 1
    set_log(HISTORY)
        
        






