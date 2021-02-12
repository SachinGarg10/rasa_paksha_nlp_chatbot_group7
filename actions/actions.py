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

class ActionLanguageSearch(Action):

    def name(self) -> Text:
        return "action_lang_search"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        data_path = os.path.join("data", "cldf-datasets-wals-014143f", "cldf", "languages.csv")
        wals_data = pd.read_csv(data_path)
        entities = list(tracker.get_latest_entity_values("language"))

        if len(entities) > 0:
            print("Action lang search: entities: ", entities)
            query_lang = entities.pop()
            #query_lang = query_lang.lower().capitalize()
            print(query_lang)
            query_lang = lang.LANGS.get(query_lang, None)
            
            if not query_lang:
                return []
            
            query_lang = query_lang.lower().capitalize()
            print(query_lang)
            out_row = wals_data[wals_data["Name"] == query_lang].to_dict("records")
            print("Action lang search: out_row: ", out_row)

            if len(out_row) > 0:
                out_row = out_row[0]
                out_text = "%s भाषा %s फैमिली से संबंधित है। \nजिसका जीनस %s हैं \nऔर ISO कोड %s हैं। " % (out_row["Name"], out_row["Family"], out_row["Genus"], out_row["ISO_codes"])
                dispatcher.utter_message(text = out_text)
            else:
                dispatcher.utter_message(text = "Sorry! We don't have records for the language %s" % query_lang)

        return []
