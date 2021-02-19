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
import random

import lang 

from spellchecker import SpellChecker


spell = SpellChecker()
spell.word_frequency.load_words(lang.correct_spell_words)
spell.known(lang.correct_spell_words) 

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
            query_lang_hi = entities.pop()
            #query_lang = query_lang.lower().capitalize()
            print(query_lang_hi)
            query_lang = lang.HI_EN_LANGS.get(query_lang_hi, None)
            query_country = lang.HI_EN_COUNTRIES.get(query_lang_hi, None)
            query_macroarea = lang.HI_EN_MACROAREAS.get(query_lang_hi, None)
            query_genus = lang.HI_EN_GENUS.get(query_lang_hi, None)
            query_family = lang.HI_EN_FAMILY.get(query_lang_hi, None)

            if not query_lang and not query_country and not query_macroarea and not query_genus and not query_family:
                query_lang_hi = spell.correction(str(query_lang_hi))
                print(query_lang_hi)
                query_lang = lang.HI_EN_LANGS.get(query_lang_hi, None)
                query_country = lang.HI_EN_COUNTRIES.get(query_lang_hi, None)
                query_macroarea = lang.HI_EN_MACROAREAS.get(query_lang_hi, None)
                query_genus = lang.HI_EN_GENUS.get(query_lang_hi, None)
                query_family = lang.HI_EN_FAMILY.get(query_lang_hi, None)
            
            if not query_lang and not query_country and not query_macroarea and not query_genus and not query_family:
                print("didn't find hindi entity")
                dispatcher.utter_message(text = "कृपया मुझे माफ़ करे! मेरे पास %s का रिकॉर्ड नहीं हैं।" % query_lang_hi)
                return []
            elif query_country:
                query_lang = query_country.lower().capitalize()
                print(query_lang)
                out_row = language_data_in_eng[language_data_in_eng["country"] == query_lang].to_dict("records")
                # print("Action lang search: out_row: ", out_row)

                if len(out_row) > 0:
                    ln = []
                    for row in out_row:
                        ln.append(row['Name'])

                    ln = list(set(ln))

                    count = 3 
                    if len(ln) < 3:
                        count = len(ln)

                    hi_lang_country = []
                    cn = 0
                    while cn < count:
                        hi_lang_cnt = lang.EN_HI_LANGS.get(str(random.choice(ln)).lower(), None)
                        if not hi_lang_cnt:
                            continue

                        hi_lang_country.append(hi_lang_cnt)
                        cn += 1

                    print("cn:", cn, "count:", count, hi_lang_country, len(hi_lang_country))
                    # out_row = out_row[0]
                    if hi_lang_country:
                        out_text = "%s में %s भाषाएं है। \nइस देश की कुछ भाषाएं इस प्रकार हैं: %s \nक्या इससे आपको मदद मिली?" % \
                            (query_lang_hi, str(len(ln)), str(hi_lang_country))
                    else:
                        out_text = "%s में %s भाषाएं है। \nक्या इससे आपको मदद मिली?" % \
                            (query_lang_hi, str(len(ln)))
                    dispatcher.utter_message(text = out_text)
                else:
                    dispatcher.utter_message(text = "कृपया मुझे माफ़ करे! मेरे पास %s देश के रिकॉर्ड नहीं हैं।" % query_lang_hi)

                return []
            elif query_macroarea:
                query_lang = query_macroarea.lower().capitalize()
                print(query_lang)
                out_row = language_data_in_eng[language_data_in_eng["macroarea"] == query_lang].to_dict("records")
                # print("Action lang search: out_row: ", out_row)

                if len(out_row) > 0:
                    ln = []
                    for row in out_row:
                        ln.append(row['Name'])

                    ln = list(set(ln))

                    count = 3 
                    if len(ln) < 3:
                        count = len(ln)

                    hi_lang_country = []
                    cn = 0
                    while cn < count:
                        hi_lang_cnt = lang.EN_HI_LANGS.get(str(random.choice(ln)).lower(), None)
                        if not hi_lang_cnt:
                            continue

                        hi_lang_country.append(hi_lang_cnt)
                        cn += 1

                    print("cn:", cn, "count:", count, hi_lang_country, len(hi_lang_country))
                    # out_row = out_row[0]
                    if hi_lang_country:
                        out_text = "%s मैक्रो एरिया में %s भाषाएं है। \nइसकी कुछ भाषाएं इस प्रकार हैं: %s \nक्या इससे आपको मदद मिली?" % \
                            (query_lang_hi, str(len(ln)), str(hi_lang_country))
                    else:
                        out_text = "%s मैक्रो एरिया में %s भाषाएं है। \nक्या इससे आपको मदद मिली?" % \
                            (query_lang_hi, str(len(ln)))
                    dispatcher.utter_message(text = out_text)
                else:
                    dispatcher.utter_message(text = "कृपया मुझे माफ़ करे! मेरे पास %s मैक्रो एरिया के रिकॉर्ड नहीं हैं।" % query_lang_hi)

                return []
            elif query_genus:
                query_lang = query_genus.lower().capitalize()
                print(query_lang)
                out_row = language_data_in_eng[language_data_in_eng["Genus"] == query_lang].to_dict("records")
                # print("Action lang search: out_row: ", out_row)

                if len(out_row) > 0:
                    ln = []
                    for row in out_row:
                        ln.append(row['Name'])

                    ln = list(set(ln))

                    count = 3 
                    if len(ln) < 3:
                        count = len(ln)

                    hi_lang_country = []
                    cn = 0
                    while cn < count:
                        hi_lang_cnt = lang.EN_HI_LANGS.get(str(random.choice(ln)).lower(), None)
                        if not hi_lang_cnt:
                            continue

                        hi_lang_country.append(hi_lang_cnt)
                        cn += 1

                    print("cn:", cn, "count:", count, hi_lang_country, len(hi_lang_country))
                    # out_row = out_row[0]
                    if hi_lang_country:
                        out_text = "%s जीनस में %s भाषाएं है। \nइसकी कुछ भाषाएं इस प्रकार हैं: %s \nक्या इससे आपको मदद मिली?" % \
                            (query_lang_hi, str(len(ln)), str(hi_lang_country))
                    else:
                        out_text = "%s जीनस में %s भाषाएं है। \nक्या इससे आपको मदद मिली?" % \
                            (query_lang_hi, str(len(ln)))
                    dispatcher.utter_message(text = out_text)
                else:
                    dispatcher.utter_message(text = "कृपया मुझे माफ़ करे! मेरे पास %s जीनस का रिकॉर्ड नहीं हैं।" % query_lang_hi)

                return []
            elif query_family:
                query_lang = query_family.lower().capitalize()
                print(query_lang)
                out_row = language_data_in_eng[language_data_in_eng["Family"] == query_lang].to_dict("records")
                # print("Action lang search: out_row: ", out_row)

                if len(out_row) > 0:
                    ln = []
                    for row in out_row:
                        ln.append(row['Name'])

                    ln = list(set(ln))

                    count = 3 
                    if len(ln) < 3:
                        count = len(ln)

                    hi_lang_country = []
                    cn = 0
                    while cn < count:
                        hi_lang_cnt = lang.EN_HI_LANGS.get(str(random.choice(ln)).lower(), None)
                        if not hi_lang_cnt:
                            continue

                        hi_lang_country.append(hi_lang_cnt)
                        cn += 1

                    print("cn:", cn, "count:", count, hi_lang_country, len(hi_lang_country))
                    # out_row = out_row[0]
                    if hi_lang_country:
                        out_text = "%s फैमिली में %s भाषाएं है। \nइसकी कुछ भाषाएं इस प्रकार हैं: %s \nक्या इससे आपको मदद मिली?" % \
                            (query_lang_hi, str(len(ln)), str(hi_lang_country))
                    else:
                        out_text = "%s फैमिली में %s भाषाएं है। \nक्या इससे आपको मदद मिली?" % \
                            (query_lang_hi, str(len(ln)))
                    dispatcher.utter_message(text = out_text)
                else:
                    dispatcher.utter_message(text = "कृपया मुझे माफ़ करे! मेरे पास %s फैमिली का रिकॉर्ड नहीं हैं।" % query_lang_hi)

                return []

            query_lang = query_lang.lower().capitalize()
            print(query_lang)
            out_row = language_data_in_eng[language_data_in_eng["Name"] == query_lang].to_dict("records")
            print("Action lang search: out_row: ", out_row)

            if len(out_row) > 0:
                out_row = out_row[0]
                out_text = "%s भाषा %s फैमिली से संबंधित है। \nजिसका जीनस %s हैं \nऔर आई एस ओ कोड %s हैं और मैक्रो एरिया %s हैं। \nक्या इससे आपको मदद मिली?" % \
                    (query_lang_hi, out_row["Family"], out_row["Genus"], out_row["iso_codes"], lang.EN_HI_MACROAREAS.get(str(out_row['macroarea']), out_row['macroarea']))
                dispatcher.utter_message(text = out_text)
            else:
                dispatcher.utter_message(text = "कृपया मुझे माफ़ करे! मेरे पास %s भाषा के रिकॉर्ड नहीं हैं।" % query_lang_hi)
        else:
            print("didn't find entity")
            dispatcher.utter_message(text = "कृपया मुझे माफ़ करें। मैं इसका उत्तर नहीं दे पाउँगा।")

        return []



