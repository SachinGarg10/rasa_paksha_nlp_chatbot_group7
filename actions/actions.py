# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

import pandas as pd
import os

import lang 

def wals_data():
    data_path1 = os.path.join("data", "cldf-datasets-wals-014143f", "raw" , "walslanguage.csv")
    wals_data1 = pd.read_csv(data_path1)
    # print("wals_data1.head():", wals_data1.head(), wals_data1.shape, sep='\n')

    data_path2 = os.path.join("data", "cldf-datasets-wals-014143f", "cldf", "languages.csv")
    wals_data2 = pd.read_csv(data_path2)
    # print("wals_data2.head()", wals_data2.head(), wals_data2.shape, sep='\n')

    wals_data1['iso_codes_copy'] = wals_data1.apply(lambda row: row.iso_codes, axis = 1)
    wals_data2['ISO_codes_copy'] = wals_data2.apply(lambda row: row.ISO_codes, axis = 1)

    wals_data = pd.read_csv(os.path.join("data", "cldf-datasets-wals-014143f", "cldf", "languages.csv"))
    # print("wals_data.shape:", wals_data.shape)

    df = wals_data2.set_index('ISO_codes_copy').join(wals_data1.set_index('iso_codes_copy'))
    # print("df.head()", df.head(), df.shape, sep='\n')

    wals = df.drop(columns=['Glottocode', 'ISO639P3code', 'Samples_100', 'Samples_200', 'Macroarea', 'samples_100', 'samples_200'])
    # print("wals.head()", wals.head(), wals.shape, sep='\n')

    data_path3 = os.path.join("data", "cldf-datasets-wals-014143f", "raw", "countrylanguage.csv")
    wals_data3 = pd.read_csv(data_path3)
    # print("wals_data3.head()", wals_data3.head(), wals_data3.shape, sep='\n')

    wals = wals.reset_index(drop=True)

    wals['lang_pk'] = wals.apply(lambda row: row.pk, axis = 1)

    wals_data3 = wals_data3.drop(columns=['pk'])
    df = wals.set_index('pk').join(wals_data3.set_index('language_pk'))

    df = df.drop(columns=['jsondata'])
    wals_df = df.copy()

    wals_df['count_pk'] = wals_df.apply(lambda row: row.country_pk, axis = 1)

    data_path4 = os.path.join("data", "cldf-datasets-wals-014143f", "raw", "country.csv")
    wals_data4 = pd.read_csv(data_path4)
    # print("wals_data4.head()", wals_data4.head(), wals_data4.shape, sep='\n')

    wals_data4['country_pk'] = wals_data4.apply(lambda row: row.pk, axis = 1)
    wals_data4 = wals_data4.drop(columns=['jsondata', 'description', 'markup_description', 'id'])

    df = wals_df.set_index('country_pk').join(wals_data4.set_index('pk'))

    wals = df.drop(columns=['ID', 'Subfamily', 'ISO_codes'])

    wals['country'] = wals.apply(lambda row: row['name'], axis = 1) 

    wals = wals.drop(columns=['name'])

    return wals

language_data_in_eng = wals_data() 
# ['Name', 'Latitude', 'Longitude', 'Family', 'Genus', 'ascii_name', 'genus_pk', 
# 'iso_codes', 'macroarea', 'lang_pk', 'count_pk', 'continent', 'country_pk', 'country']


class ActionLanguageSearch(Action):

    def name(self) -> Text:
        return "action_lang_search"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # data_path = os.path.join("data", "cldf-datasets-wals-014143f", "cldf", "languages.csv")
        # wals_data = pd.read_csv(data_path)
        entities = list(tracker.get_latest_entity_values("language"))

        if len(entities) > 0:
            print("Action lang search: entities: ", entities)
            query_lang = entities.pop()
            #query_lang = query_lang.lower().capitalize()
            print(query_lang)
            query_lang = lang.HI_EN_LANGS.get(query_lang, None)
            
            if not query_lang:
                print("didn't find hindi entity")
                dispatcher.utter_message(text = "कृपया मुझे माफ़ करें। मैं इसका उत्तर नहीं दे पाउँगा।")
                return []
            
            query_lang = query_lang.lower().capitalize()
            print(query_lang)
            out_row = language_data_in_eng[language_data_in_eng["Name"] == query_lang].to_dict("records")
            print("Action lang search: out_row: ", out_row)

            if len(out_row) > 0:
                out_row = out_row[0]
                out_text = "%s भाषा %s फैमिली से संबंधित है। \nजिसका जीनस %s हैं \nऔर ISO कोड %s हैं। \nक्या इससे आपको मदद मिली?" % \
                    (lang.EN_HI_LANGS.get(str(out_row["Name"]).lower(), out_row["Name"]).lower(), out_row["Family"], out_row["Genus"], out_row["iso_codes"])
                dispatcher.utter_message(text = out_text)
            else:
                dispatcher.utter_message(text = "कृपया मुझे माफ़ करे! मेरे पास %s भाषा के रिकॉर्ड नहीं हैं।" % lang.EN_HI_LANGS.get(str(out_row["Name"]).lower()))
        else:
            print("didn't find entity")
            dispatcher.utter_message(text = "कृपया मुझे माफ़ करें। मैं इसका उत्तर नहीं दे पाउँगा।")

        return []



