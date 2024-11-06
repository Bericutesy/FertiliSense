from datetime import datetime, timedelta
from typing import Any, Text, Dict, List
import firebase_admin
from firebase_admin import credentials, firestore
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, UserUtteranceReverted
import wikipediaapi
import openai
import requests
import json
import logging
from urllib.parse import quote
from typing import Dict, Text, Any
from rasa_sdk.events import EventType
import re
from typing import List


# Initialize Firebase
cred = credentials.Certificate("fertilisense-f1335-firebase-adminsdk-erc4z-f6c9372187.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize Wikipedia API with a custom user agent
wiki_wiki = wikipediaapi.Wikipedia(
    language='en',
    user_agent='FertiliSense/1.0 (Mobile App; Contact: ybiza2018@gmail.com)'
)

# Set up OpenAI API key
openai.api_key = ''

logger = logging.getLogger(__name__)

class ActionGreet(Action):
    def name(self) -> str:
        return "action_greet"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        dispatcher.utter_message(text="Hello! How can I help you today?")
        return []

class ActionGoodbye(Action):
    def name(self) -> str:
        return "action_goodbye"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        dispatcher.utter_message(text="Goodbye! Have a great day!")
        return []
    
class ActionThankYou(Action):
    def name(self) -> str:
        return "action_thank_you"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        dispatcher.utter_message(text="You're welcome mate!")
        return []

# Actions handle the mood
class ActionHandleMood(Action):    
    def name(self) -> Text:
        return "action_handle_mood"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_ask_mood")

        return []

# Action for getting info on Wikipedia
class ActionQueryWikipedia(Action):
    def name(self) -> str:
        return "action_query_wikipedia"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        topic = tracker.latest_message.get('text').lower()

        # List of topics related to the male reproductive system (anatomy, physiology, diseases)
        male_reproductive_topics = [
            'male reproductive system', 'testosterone', 'spermatogenesis', 'testes', 
            'epididymis', 'vas deferens', 'seminal vesicle', 'prostate', 'penis', 
            'scrotum', 'bulbourethral glands', 'semen', 'sperm', 'ejaculation',
            'erection', 'circumcision', 'foreskin', 'male infertility', 'erectile dysfunction', 
            'prostate cancer', 'benign prostatic hyperplasia', 'varicocele', 'hydrocele', 
            'testicular cancer', 'testicular torsion', 'hypogonadism', 'andropause',
            'oligospermia', 'azoospermia', 'cryptorchidism'
        ]

        # List of topics related to the female reproductive system (anatomy, physiology, diseases)
        female_reproductive_topics = [
            'female reproductive system', 'estrogen', 'progesterone', 'ovulation', 'ovaries', 
            'fallopian tubes', 'uterus', 'endometrium', 'myometrium', 'cervix', 'vagina', 
            'labia', 'clitoris', 'hymen', 'bartholin glands', 'skene glands', 'menstruation', 
            'menstrual cycle', 'follicular phase', 'luteal phase', 'menopause', 
            'perimenopause', 'female infertility', 'polycystic ovary syndrome', 
            'endometriosis', 'uterine fibroids', 'ovarian cysts', 'cervical cancer', 
            'ovarian cancer', 'uterine cancer', 'vaginitis', 'pelvic inflammatory disease', 
            'vulvodynia', 'dyspareunia', 'amenorrhea', 'dysmenorrhea', 'premenstrual syndrome (PMS)',
            'premenstrual dysphoric disorder (PMDD)', 'ectopic pregnancy', 'miscarriage', 
            'menorrhagia', 'polymenorrhea', 'oligomenorrhea'
        ]

        # Reproductive health and fertility-related topics
        fertility_and_health_topics = [
            'fertility', 'infertility', 'fertility treatments', 'IVF', 'artificial insemination',
            'surrogacy', 'fertility preservation', 'egg freezing', 'sperm donation', 
            'egg donation', 'ovarian reserve', 'fertility tests', 'hormonal tests', 
            'semen analysis', 'ultrasound for fertility', 'assisted reproductive technology',
            'contraception', 'birth control', 'condoms', 'oral contraceptives', 
            'intrauterine device (IUD)', 'hormonal implants', 'sterilization', 'vasectomy', 
            'tubal ligation', 'natural family planning', 'emergency contraception', 
            'morning-after pill', 'fertility awareness', 'reproductive rights', 
            'sexual health', 'sexually transmitted infections', 'HIV/AIDS', 'chlamydia', 
            'gonorrhea', 'syphilis', 'herpes', 'human papillomavirus (HPV)', 'hepatitis B', 
            'trichomoniasis', 'genital warts', 'infertility in men', 'infertility in women', 
            'sex education', 'safe sex', 'fertility clinics', 'male contraceptives', 
            'hormone replacement therapy', 'sexual dysfunction', 'libido', 'impotence', 
            'premature ejaculation', 'delayed ejaculation', 'vaginismus', 'reproductive endocrinology',
            'andrology', 'gynecology', 'urology', 'reproductive system'
        ]

        # Pregnancy and childbirth-related topics
        pregnancy_and_childbirth_topics = [
            'pregnancy', 'gestation', 'fertilization', 'zygote', 'embryo', 'fetus', 'prenatal care',
            'antenatal care', 'obstetrics', 'midwifery', 'natural birth', 'cesarean section', 
            'epidural', 'labor and delivery', 'childbirth', 'postpartum period', 'lactation', 
            'breastfeeding', 'colostrum', 'miscarriage', 'stillbirth', 'ectopic pregnancy', 
            'gestational diabetes', 'preeclampsia', 'placenta previa', 'placental abruption', 
            'preterm birth', 'post-term pregnancy', 'in vitro fertilization', 'assisted delivery',
            'home birth', 'water birth', 'doula', 'birth defects', 'genetic counseling', 
            'amniocentesis', 'chorionic villus sampling', 'ultrasound in pregnancy', 'fetal monitoring'
        ]

        # Combine all topics in one list
        reproductive_system_topics = (
            male_reproductive_topics + 
            female_reproductive_topics + 
            fertility_and_health_topics + 
            pregnancy_and_childbirth_topics
        )

        # Check if the topic is relevant to any of the reproductive system topics
        matched_topic = next((t for t in reproductive_system_topics if t in topic), None)

        if matched_topic:
            page = wiki_wiki.page(matched_topic)
            if page.exists():
                dispatcher.utter_message(text=f"{page.summary[:500]}")
            else:
                dispatcher.utter_message(text=f"Sorry, I couldn't find information on {matched_topic}.")
        else:
            dispatcher.utter_message(text="I'm sorry, I don't have information on that topic.")
        
        return []

# Action for getting info on GPT-4
class ActionQueryGPT(Action):
    def name(self) -> str:
        return "action_query_gpt"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        # Get the latest message from the user
        user_query = tracker.latest_message.get('text')
        logger.info(f"User query received: {user_query}")

        # Construct a concise prompt for GPT
        prompt = (
            f"Answer the following question in a complete, concise way without cutting off: {user_query} "
            "Provide a direct answer that addresses all aspects of the question."
        )
        logger.info(f"Prompt constructed: {prompt}")

        try:
            # Call the OpenAI API with GPT-3.5 or GPT-4
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a concise and helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150  # Increased token limit for more comprehensive answers
            )

            # Extract the GPT response
            result = response['choices'][0]['message']['content'].strip()
            logger.info(f"GPT response received: {result}")

            # Send the result back to the user
            dispatcher.utter_message(text=result)

        except Exception as e:
            # Handle potential errors and provide fallback response
            logger.error(f"Error occurred: {e}")
            dispatcher.utter_message(text="Sorry, I couldn't process your request at the moment. Please try again later.")

        return []

# Action for asking user how is their day
class ActionAskDay(Action):
    def name(self) -> Text:
        return "action_ask_day"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_day")

        return []
    
# Actions for handling create symptoms
class ActionCollectStartDates(Action):
    def name(self) -> str:
        return "action_collect_start_dates"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        create_start_date_input = tracker.latest_message.get('text')
        user_id = tracker.sender_id
        
        date_match = re.search(r'\d{2}/\d{2}/\d{4}', create_start_date_input)
        
        if date_match:
            start_date_str = date_match.group()
            try:
                start_date = datetime.strptime(start_date_str, '%d/%m/%Y')
                current_date = datetime.now()
                
                if start_date > current_date:
                    dispatcher.utter_message(text=f"The start date cannot be after today ({current_date.strftime('%d/%m/%Y')}). Please provide a valid start date.")
                    return []
                
                # Fetch existing logs
                doc_ref = db.collection('symptom_logs').document(user_id)
                doc = doc_ref.get()
                if doc.exists:
                    historical_logs = doc.to_dict().get('logs', [])
                else:
                    historical_logs = []
                
                # Check for date overlap in existing logs
                for log in historical_logs:
                    existing_start = datetime.strptime(log['start_dates'], '%d/%m/%Y')
                    existing_end = datetime.strptime(log['end_dates'], '%d/%m/%Y')
                    
                    # Check for any overlap with the existing log
                    if (existing_start <= start_date <= existing_end) or (existing_start <= start_date <= existing_end):
                        dispatcher.utter_message(
                            text=f"Your start date overlaps with an existing log from {log['start_dates']} to {log['end_dates']}. Please choose a different date."
                        )
                        return []

                dispatcher.utter_message(text=f"Start Date recorded: {start_date_str}\nPlease provide the start date of your symptoms?\n Example: End date of symptoms: DD/MM/YYYY")
                return [SlotSet("start_dates", start_date_str)]

            except ValueError:
                dispatcher.utter_message(text="There was an error processing the date. Please try again.")
                return []
        else:
            dispatcher.utter_message(text="Invalid date format. Please provide the date in the format dd/mm/yyyy.")
            return []

class ActionCollectEndDates(Action):
    def name(self) -> str:
        return "action_collect_end_dates"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        create_end_date_input = tracker.latest_message.get('text')
        user_id = tracker.sender_id
        
        date_match = re.search(r'\d{2}/\d{2}/\d{4}', create_end_date_input)
        
        if date_match:
            end_date_str = date_match.group()
            try:
                end_date = datetime.strptime(end_date_str, '%d/%m/%Y')
                current_date = datetime.now()
                
                if end_date > current_date:
                    dispatcher.utter_message(text=f"The end date cannot be after today ({current_date.strftime('%d/%m/%Y')}). Please provide a valid end date.")
                    return []
                
                # Fetch existing logs
                doc_ref = db.collection('symptom_logs').document(user_id)
                doc = doc_ref.get()
                if doc.exists:
                    historical_logs = doc.to_dict().get('logs', [])
                else:
                    historical_logs = []

                # Check for date overlap with the provided start and end dates
                start_dates = tracker.get_slot("start_dates")
                if start_dates:
                    new_start_date = datetime.strptime(start_dates, '%d/%m/%Y')
                    for log in historical_logs:
                        existing_start = datetime.strptime(log['start_dates'], '%d/%m/%Y')
                        existing_end = datetime.strptime(log['end_dates'], '%d/%m/%Y')
                        
                        # Check for any overlap with existing logs
                        if (new_start_date <= existing_end and end_date >= existing_start):
                            dispatcher.utter_message(
                                text=f"Your date range overlaps with an existing log from {log['start_dates']} to {log['end_dates']}. Please choose different dates."
                            )
                            return []

                dispatcher.utter_message(text=f"End Date recorded: {end_date_str}.\nPlease describe your symptoms\nExample: I've got migraine")
                return [SlotSet("end_dates", end_date_str)]

            except ValueError:
                dispatcher.utter_message(text="There was an error processing the date. Please try again.")
                return []
        else:
            dispatcher.utter_message(text="Invalid date format. Please provide the date in the format dd/mm/yyyy.")
            return []

class ActionCollectSymptoms(Action):
    def name(self) -> str:
        return "action_collect_symptoms"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        symptoms = tracker.latest_message.get('text')
        
        dispatcher.utter_message(text=f"Symptoms recorded: {symptoms}.")
        print(f"Collected symptoms: {symptoms}")
        return [SlotSet("symptoms", symptoms)]

class ActionCreateLog(Action):
    def name(self) -> str:
        return "action_create_log"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        intent = tracker.latest_message['intent'].get('name')
        start_dates = tracker.get_slot("start_dates")
        end_dates = tracker.get_slot("end_dates")
        symptoms = tracker.get_slot("symptoms")
        user_id = tracker.sender_id

        print(f"Intent: {intent}")
        print(f"Start Date: {start_dates}")
        print(f"End Date: {end_dates}")
        print(f"Symptoms: {symptoms}")

        try:
            doc_ref = db.collection('symptom_logs').document(user_id)
            doc = doc_ref.get()

            # Fetch historical logs
            historical_logs = doc.to_dict().get('logs', []) if doc.exists else []

            # Append new log entry
            historical_logs.append({
                'start_dates': start_dates,
                'end_dates': end_dates,
                'symptoms': symptoms
            })

            # Sort logs by 'start_dates'
            historical_logs.sort(key=lambda x: datetime.strptime(x['start_dates'], '%d/%m/%Y'))

            # Update Firestore with the sorted logs
            doc_ref.set({'logs': historical_logs}, merge=True)
            dispatcher.utter_message(text="Your symptoms have been logged successfully.")

        except Exception as e:
            dispatcher.utter_message(text="There was an error logging your symptoms.")
            print(f"ERROR: {e}")

        return []

class ActionEvaluateSymptoms(Action):
    def name(self) -> str:
        return "action_evaluate_symptoms"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        symptoms = tracker.get_slot("symptoms")
        
        # Check if symptoms were collected
        if not symptoms:
            dispatcher.utter_message(text="No symptoms logged. Please log symptoms first for evaluation.")
            return []

        # Construct the prompt for GPT, focusing on symptom analysis
        prompt = (
            f"Analyze the following symptoms provided by a user:\n{symptoms}\n"
            "Provide an evaluation based on common health concerns and potential advice. "
            "Answer as a supportive health assistant."
        )

        logger.info(f"Prompt for GPT constructed: {prompt}")

        try:
            # Call OpenAI API with GPT-3.5 or GPT-4 for symptom analysis
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a knowledgeable health assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100  # Set tokens based on desired response length
            )

            # Extract the response and send it to the user
            result = response['choices'][0]['message']['content'].strip()
            dispatcher.utter_message(text=f"Symptom evaluation: {result}")

        except Exception as e:
            logger.error(f"Error in GPT response: {e}")
            dispatcher.utter_message(text="There was an issue with evaluating your symptoms. Please try again later.")
        
        return []

# Actions for handling delete symptoms
class ActionCollectSymptomsDeleteStartDate(Action):
    def name(self) -> str:
        return "action_collect_symptoms_delete_start_date"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        symptom_start_date_input = tracker.latest_message.get('text')
        
        print(f"[DEBUG] Received start date input: {symptom_start_date_input}")  # Debug statement

        date_match = re.search(r'\d{2}/\d{2}/\d{4}', symptom_start_date_input)
        
        if date_match:
            start_date_str = date_match.group()
            try:
                symptoms_delete_start_date = datetime.strptime(start_date_str, '%d/%m/%Y')
                current_date = datetime.now()
                
                if symptoms_delete_start_date > current_date:
                    dispatcher.utter_message(text=f"The start date cannot be after today ({current_date.strftime('%d/%m/%Y')}). Please provide a valid start date.")
                    return []
                else:
                    dispatcher.utter_message(text=f"Start Date recorded: {start_date_str}.")
                    print(f"[DEBUG] Start date slot set: {start_date_str}")  # Debug statement
                    return [SlotSet("symptoms_delete_start_date", start_date_str)]

            except ValueError:
                dispatcher.utter_message(text="There was an error processing the date. Please try again.")
                return []
        else:
            dispatcher.utter_message(text="Invalid date format. Please provide the date in the format dd/mm/yyyy.")
            return []

class ActionCollectSymptomsDeleteEndDate(Action):
    def name(self) -> str:
        return "action_collect_symptoms_delete_end_date"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        symptom_end_date_input = tracker.latest_message.get('text')
        date_match = re.search(r'\d{2}/\d{2}/\d{4}', symptom_end_date_input)

        if date_match:
            end_date_str = date_match.group()
            try:
                symptoms_delete_end_date = datetime.strptime(end_date_str, '%d/%m/%Y')
                current_date = datetime.now()

                if symptoms_delete_end_date > current_date:
                    dispatcher.utter_message(text=f"The end date cannot be after today ({current_date.strftime('%d/%m/%Y')}). Please provide a valid end date.")
                    return []
                else:
                    dispatcher.utter_message(text=f"End Date recorded: {end_date_str}.")
                    return [
                        SlotSet("symptoms_delete_end_date", end_date_str), 
                        FollowupAction("action_delete_symptoms")
                    ]

            except ValueError:
                dispatcher.utter_message(text="There was an error processing the date. Please try again.")
                return []
        else:
            dispatcher.utter_message(text="Invalid date format. Please provide the date in the format dd/mm/yyyy.")
            return []


class ActionDeleteSymptoms(Action):
    def name(self) -> str:
        return "action_delete_symptoms"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        start_date_str = tracker.get_slot("symptoms_delete_start_date")
        end_date_str = tracker.get_slot("symptoms_delete_end_date")
        user_id = tracker.sender_id  # Get unique user ID

        print(f"[DEBUG] Start date from slot: {start_date_str}")  # Debug statement
        print(f"[DEBUG] End date from slot: {end_date_str}")  # Debug statement

        if not start_date_str or not end_date_str:
            dispatcher.utter_message(text="Please provide both start and end dates for deletion.")
            return []

        try:
            symptoms_delete_start_date = datetime.strptime(start_date_str, '%d/%m/%Y')
            symptoms_delete_end_date = datetime.strptime(end_date_str, '%d/%m/%Y')
            current_date = datetime.now()

            # Validate dates
            if symptoms_delete_start_date > symptoms_delete_end_date:
                dispatcher.utter_message(text="The start date cannot be after the end date. Please provide valid dates.")
                print("[DEBUG] Start date is after end date.")  # Debug statement
                return []

            if symptoms_delete_end_date > current_date:
                dispatcher.utter_message(text=f"The end date cannot be after today ({current_date.strftime('%d/%m/%Y')}). Please provide a valid end date.")
                print("[DEBUG] End date is after today's date.")  # Debug statement
                return []

            # Fetch logs from Firestore within the specified date range
            doc_ref = db.collection('symptom_logs').document(user_id)
            doc = doc_ref.get()

            if not doc.exists:
                dispatcher.utter_message(text="No symptoms were found for the specified date range.")
                print("[DEBUG] No document found for user.")  # Debug statement
                return []

            logs = doc.to_dict().get('logs', [])
            print(f"[DEBUG] Retrieved logs: {logs}")  # Debug statement

            logs_to_delete = [
                log for log in logs
                if symptoms_delete_start_date <= datetime.strptime(log['start_dates'], '%d/%m/%Y') <= symptoms_delete_end_date
            ]

            if not logs_to_delete:
                dispatcher.utter_message(text="No symptoms were found for the specified date range.")
                print("[DEBUG] No logs found for the specified date range.")  # Debug statement
                return []

            # Filter out logs to be deleted and update Firestore
            updated_logs = [log for log in logs if log not in logs_to_delete]
            doc_ref.set({'logs': updated_logs}, merge=True)

            dispatcher.utter_message(text=f"Symptoms between {start_date_str} and {end_date_str} have been deleted.")
            print(f"[DEBUG] Symptoms between {start_date_str} and {end_date_str} deleted.")  # Debug statement
            return [SlotSet("symptoms_delete_start_date", None), SlotSet("symptoms_delete_end_date", None)]

        except ValueError:
            dispatcher.utter_message(text="There was an error processing the dates. Please ensure they are in the format dd/mm/yyyy.")
            print("[DEBUG] ValueError when parsing dates.")  # Debug statement
            return []

        except Exception as e:
            dispatcher.utter_message(text="There was an error deleting your symptoms.")
            print(f"[DEBUG] ERROR: {e}")  # Debug statement
            return []
            
# Actions for handling update symptoms
class ActionCollectSymptomsStartDate(Action):
    def name(self) -> str:
        return "action_collect_symptoms_start_date"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        update_symptom_start_date_input = tracker.latest_message.get('text')
        date_match = re.search(r'\d{2}/\d{2}/\d{4}', update_symptom_start_date_input)

        if date_match:
            start_date_str = date_match.group()
            try:
                symptoms_start_date = datetime.strptime(start_date_str, '%d/%m/%Y')
                current_date = datetime.now()

                if symptoms_start_date > current_date:
                    dispatcher.utter_message(text=f"The start date cannot be after today ({current_date.strftime('%d/%m/%Y')}). Please provide a valid start date.")
                    return []
                else:
                    dispatcher.utter_message(text=f"Start Date recorded: {start_date_str}.")
                    return [SlotSet("symptoms_start_date", start_date_str)]

            except ValueError:
                dispatcher.utter_message(text="There was an error processing the date. Please try again.")
                return []
        else:
            dispatcher.utter_message(text="Invalid date format. Please provide the date in the format dd/mm/yyyy.")
            return []

class ActionCollectSymptomsEndDate(Action):
    def name(self) -> str:
        return "action_collect_symptoms_end_date"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        update_symptom_end_date_input = tracker.latest_message.get('text')
        date_match = re.search(r'\d{2}/\d{2}/\d{4}', update_symptom_end_date_input)

        if date_match:
            end_date_str = date_match.group()
            try:
                symptoms_end_date = datetime.strptime(end_date_str, '%d/%m/%Y')
                current_date = datetime.now()

                if symptoms_end_date > current_date:
                    dispatcher.utter_message(text=f"The end date cannot be after today ({current_date.strftime('%d/%m/%Y')}). Please provide a valid end date.")
                    return []
                else:
                    dispatcher.utter_message(text=f"End Date recorded: {end_date_str}. Now, please describe your symptoms that you want to update.\nExample:\nUpdate symptoms to include fatigue")
                    return [SlotSet("symptoms_end_date", end_date_str)]

            except ValueError:
                dispatcher.utter_message(text="There was an error processing the date. Please try again.")
                return []
        else:
            dispatcher.utter_message(text="Invalid date format. Please provide the date in the format dd/mm/yyyy.")
            return []

class ActionCollectUpdatedSymptoms(Action):
    def name(self) -> str:
        return "action_collect_updated_symptoms"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        new_symptoms = tracker.latest_message.get('text')

        # Debug: Print the new symptoms captured
        print(f"DEBUG: New Symptoms captured: {new_symptoms}")

        # Save new symptoms in a slot
        dispatcher.utter_message(text=f"New Symptoms recorded: {new_symptoms}")
        
        return [SlotSet("new_symptoms", new_symptoms)]

class ActionUpdateSymptomsLog(Action):
    def name(self) -> str:
        return "action_update_symptoms_log"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        update_symptom_start_dates = tracker.get_slot("symptoms_start_date")
        update_symptom_end_dates = tracker.get_slot("symptoms_end_date")
        new_symptoms = tracker.get_slot("new_symptoms")  # Changed from "symptoms" to "new_symptoms"
        user_id = tracker.sender_id

        # Parse dates for accurate comparison
        try:
            start_date_obj = datetime.strptime(update_symptom_start_dates, "%d/%m/%Y")
            end_date_obj = datetime.strptime(update_symptom_end_dates, "%d/%m/%Y")
        except ValueError:
            dispatcher.utter_message(text="Invalid date format. Please use dd/mm/yyyy.")
            return []

        try:
            # Retrieve logs
            doc_ref = db.collection('symptom_logs').document(user_id)
            doc = doc_ref.get()

            if not doc.exists:
                dispatcher.utter_message(text="No log found to update for the given dates.")
                print(f"DEBUG: No document found for user {user_id}.")
                return []

            historical_logs = doc.to_dict().get('logs', [])
            found = False

            # Search for entry within the date range
            for log in historical_logs:
                log_start_date = datetime.strptime(log['start_dates'], "%d/%m/%Y")
                log_end_date = datetime.strptime(log['end_dates'], "%d/%m/%Y")

                if log_start_date == start_date_obj and log_end_date == end_date_obj:
                    log['symptoms'] = new_symptoms  # Use the correct key for updating symptoms
                    found = True
                    print(f"DEBUG: Log entry found and updated with new symptoms: {new_symptoms}")
                    break

            if found:
                # Attempt to update the document in Firestore
                doc_ref.set({'logs': historical_logs}, merge=True)
                dispatcher.utter_message(text="Your symptoms log has been successfully updated.")
                print(f"DEBUG: Successfully updated the Firestore document for user {user_id}.")
            else:
                dispatcher.utter_message(text="No log found for the specified date range to update.")
                print(f"DEBUG: No log entry found for the specified dates {update_symptom_start_dates} to {update_symptom_end_dates}.")

        except Exception as e:
            dispatcher.utter_message(text="There was an error updating your symptoms.")
            print(f"Update Error: {e}")

        return []

# Actions for handling create menstrual cycle
class ActionCollectStartDate(Action):
    def name(self) -> str:
        return "action_collect_start_date"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        start_date_input = tracker.latest_message.get('text')  # Get the user's input
        
        # Use regex to find date in the format dd/mm/yyyy in the user input
        date_match = re.search(r'\d{2}/\d{2}/\d{4}', start_date_input)
        
        if date_match:
            start_date_input = date_match.group()  # Extract the actual date part
            try:
                # Convert the date string to a datetime object
                start_date = datetime.strptime(start_date_input, '%d/%m/%Y')
                current_date = datetime.now()

                # Check if the start date is after today
                if start_date > current_date:
                    dispatcher.utter_message(text=f"The start date cannot be after today ({current_date.strftime('%d/%m/%Y')}). Please provide a valid start date.")
                    return []

                # Fetch existing cycles to check for overlapping start dates
                user_id = tracker.sender_id
                doc_ref = db.collection('menstrual_cycles').document(user_id)
                doc = doc_ref.get()

                historical_cycles = doc.to_dict().get('cycles', []) if doc.exists else []

                # Check for overlaps with existing cycles
                for cycle in historical_cycles:
                    cycle_start = datetime.strptime(cycle['start_date'], "%d/%m/%Y")
                    cycle_end = datetime.strptime(cycle['end_date'], "%d/%m/%Y")

                    # Check if the new start date overlaps with an existing cycle
                    if cycle_start <= start_date <= cycle_end:
                        dispatcher.utter_message(text="The start date overlaps with an existing cycle. Please provide a non-overlapping start date.")
                        return []

                # If all checks pass, confirm the start date
                dispatcher.utter_message(text=f"Start Date recorded: {start_date_input}. What is the end date of your cycle?\nExample:\nEnd Date: DD/MM/YYYY")
                return [SlotSet("start_dates", start_date_input)]

            except ValueError:
                dispatcher.utter_message(text="There was an error processing the date. Please try again.")
                return []
        else:
            dispatcher.utter_message(text="Invalid date format. Please provide the date in the format dd/mm/yyyy.")
            return []

class ActionCollectEndDate(Action):
    def name(self) -> str:
        return "action_collect_end_date"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        end_date_input = tracker.latest_message.get('text')  # Get the user's input

        # Use regex to find date in the format dd/mm/yyyy in the user input
        date_match = re.search(r'\d{2}/\d{2}/\d{4}', end_date_input)

        if date_match:
            end_date_input = date_match.group()  # Extract the actual date part
            try:
                # Convert the date string to a datetime object
                end_date = datetime.strptime(end_date_input, '%d/%m/%Y')
                current_date = datetime.now()
                start_date_input = tracker.get_slot("start_dates")  # Get the start date from the slot

                # Check if the end date is after today
                if end_date > current_date:
                    dispatcher.utter_message(text=f"The end date cannot be after today ({current_date.strftime('%d/%m/%Y')}). Please provide a valid end date.")
                    return []

                # Check if start date is available
                if start_date_input:
                    start_date = datetime.strptime(start_date_input, '%d/%m/%Y')

                    # Check if the end date is before the start date
                    if end_date < start_date:
                        dispatcher.utter_message(text="The end date cannot be before the start date. Please provide a valid end date.")
                        return []

                    # Fetch existing cycles to check for overlaps
                    user_id = tracker.sender_id
                    doc_ref = db.collection('menstrual_cycles').document(user_id)
                    doc = doc_ref.get()

                    historical_cycles = doc.to_dict().get('cycles', []) if doc.exists else []

                    # Check for overlaps with existing cycles
                    for cycle in historical_cycles:
                        cycle_start = datetime.strptime(cycle['start_date'], "%d/%m/%Y")
                        cycle_end = datetime.strptime(cycle['end_date'], "%d/%m/%Y")

                        # Check for overlaps
                        if not (end_date < cycle_start or start_date > cycle_end):
                            dispatcher.utter_message(text="The new end date overlaps with an existing cycle. Please provide a non-overlapping end date.")
                            return []

                    # If all checks pass, confirm the end date
                    dispatcher.utter_message(text=f"End Date recorded: {end_date_input}. How long is your cycle duration (in days)?\nCycle duration refers to the total time taken to complete one full cycle of a repeating process or event, often measured from the start of the first phase to the end of the last phase.\n\nExamples: 23 days\n\n(If unsure, you can use the standard cycle of 28 days)")
                    return [SlotSet("end_date", end_date_input)]

                else:
                    dispatcher.utter_message(text="Please provide a valid start date before entering an end date.")
                    return []

            except ValueError:
                dispatcher.utter_message(text="There was an error processing the date. Please try again.")
                return []
        else:
            dispatcher.utter_message(text="Invalid date format. Please provide the date in the format dd/mm/yyyy.")
            return []

class ActionCollectCycleDuration(Action):
    def name(self) -> str:
        return "action_collect_cycle_duration"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        cycle_duration = tracker.get_slot("cycle_duration")  # Check if cycle duration is already collected

        if cycle_duration is None:
            cycle_duration_input = tracker.latest_message.get('text')
            if cycle_duration_input:
                dispatcher.utter_message(text=f"Cycle duration recorded: {cycle_duration_input} days. How long did your period last (in days)?\n\nPeriod duration refers to the length of time that menstruation (the shedding of the uterine lining) lasts within a menstrual cycle.\n\nExamples: Lasted for 4 days")
                return [SlotSet("cycle_duration", cycle_duration_input)]
            else:
                dispatcher.utter_message(text="Please provide a valid cycle duration.")
                return []
        else:
            return []

class ActionCollectPeriodDuration(Action):
    def name(self) -> str:
        return "action_collect_period_duration"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        period_duration = tracker.get_slot("period_duration")  # Check if period duration is already collected

        if period_duration is None:
            period_duration_input = tracker.latest_message.get('text')
            if period_duration_input:
                dispatcher.utter_message(text=f"Period duration recorded: {period_duration_input}")
                return [SlotSet("period_duration", period_duration_input)]
            else:
                dispatcher.utter_message(text="Please provide a valid period duration.")
                return []
        else:
            return []

class ActionCreateLogs(Action):
    def name(self) -> str:
        return "action_create_logs"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        # Get slots
        start_dates = tracker.get_slot("start_dates")
        end_date = tracker.get_slot("end_date")
        cycle_duration = tracker.get_slot("cycle_duration")
        period_duration = tracker.get_slot("period_duration")
        user_id = tracker.sender_id

        # Regex patterns for date and number extraction
        date_pattern = r"\b\d{2}/\d{2}/\d{4}\b"
        number_pattern = r"\b\d+\b"

        # Extract start date
        if start_dates:
            start_date_match = re.search(date_pattern, start_dates)
            if start_date_match:
                start_dates = start_date_match.group()
            else:
                dispatcher.utter_message(text="Please provide a valid start date in the format dd/MM/yyyy.")
                return []

        # Extract end date
        if end_date:
            end_date_match = re.search(date_pattern, end_date)
            if end_date_match:
                end_date = end_date_match.group()
            else:
                dispatcher.utter_message(text="Please provide a valid end date in the format dd/MM/yyyy.")
                return []

        # Extract cycle duration
        if cycle_duration:
            cycle_duration_match = re.search(number_pattern, cycle_duration)
            if cycle_duration_match:
                cycle_duration = int(cycle_duration_match.group())
            else:
                dispatcher.utter_message(text="Please provide a valid cycle duration in days (e.g., 28).")
                return []

        # Extract period duration
        if period_duration:
            period_duration_match = re.search(number_pattern, period_duration)
            if period_duration_match:
                period_duration = int(period_duration_match.group())
            else:
                dispatcher.utter_message(text="Please provide a valid period duration in days (e.g., 5).")
                return []

        if not start_dates or not end_date or not cycle_duration or not period_duration:
            dispatcher.utter_message(text="Please provide all required cycle information: start date, end date, cycle duration, and period duration.")
            return []

        try:
            # Fetch existing cycles
            doc_ref = db.collection('menstrual_cycles').document(user_id)
            doc = doc_ref.get()

            if doc.exists:
                historical_cycles = doc.to_dict().get('cycles', [])
            else:
                historical_cycles = []

            # Add new cycle
            historical_cycles.append({
                'start_date': start_dates,
                'end_date': end_date,
                'cycle_duration': cycle_duration,
                'period_duration': period_duration
            })

             # Sort cycles by start date
            historical_cycles.sort(key=lambda cycle: datetime.strptime(cycle['start_date'], "%d/%m/%Y"))

            # Calculate strong flow durations based on historical data
            strong_flow_durations = []
            for cycle in historical_cycles:
                cycle_start = datetime.strptime(cycle['start_date'], "%d/%m/%Y")
                cycle_end = datetime.strptime(cycle['end_date'], "%d/%m/%Y")
                period_duration_days = (cycle_end - cycle_start).days + 1

                # Strong flow calculations: 2nd and 3rd day of the period
                strong_flow_start = cycle_start + timedelta(days=1)
                strong_flow_end = cycle_start + timedelta(days=2)
                strong_flow_duration = (strong_flow_end - strong_flow_start).days + 1
                strong_flow_durations.append(strong_flow_duration)

            # Average strong flow duration
            average_strong_flow_duration = sum(strong_flow_durations) / len(strong_flow_durations) if strong_flow_durations else 2

            # Calculate predictions based on historical data
            predictions = []
            current_start_date = datetime.strptime(start_dates, "%d/%m/%Y")

            # If there are historical cycles, calculate the next cycle predictions
            if historical_cycles:
                last_cycle = historical_cycles[-1]
                cycle_duration_days = last_cycle['cycle_duration']
                current_start_date = datetime.strptime(last_cycle['start_date'], "%d/%m/%Y") + timedelta(days=cycle_duration_days)

            for _ in range(4):  # Predict for the next four cycles
                cycle_end_date_dt = current_start_date + timedelta(days=period_duration - 1)
                cycle_end_date = cycle_end_date_dt.strftime("%d/%m/%Y")
                next_cycle_start_date_dt = current_start_date + timedelta(days=cycle_duration_days)
                next_cycle_start_date = next_cycle_start_date_dt.strftime("%d/%m/%Y")

                # Ovulation and fertile window calculations
                ovulation_date_dt = next_cycle_start_date_dt - timedelta(days=14)
                ovulation_date = ovulation_date_dt.strftime("%d/%m/%Y")
                fertile_window_start_dt = ovulation_date_dt - timedelta(days=2)
                fertile_window_end_dt = ovulation_date_dt + timedelta(days=2)
                fertile_window_start = fertile_window_start_dt.strftime("%d/%m/%Y")
                fertile_window_end = fertile_window_end_dt.strftime("%d/%m/%Y")

                # Strong flow calculations: 2nd and 3rd day of the period
                strong_flow_start_dt = current_start_date + timedelta(days=1)  # 2nd day
                strong_flow_end_dt = current_start_date + timedelta(days=2)  # 3rd day
                strong_flow_start = strong_flow_start_dt.strftime("%d/%m/%Y")
                strong_flow_end = strong_flow_end_dt.strftime("%d/%m/%Y")

                predictions.append({
                    'cycle_start_date': current_start_date.strftime("%d/%m/%Y"),
                    'cycle_end_date': cycle_end_date,
                    'fertile_window_start': fertile_window_start,
                    'fertile_window_end': fertile_window_end,
                    'ovulation_date': ovulation_date,
                    'strong_flow_start': strong_flow_start,
                    'strong_flow_end': strong_flow_end
                })

                current_start_date = next_cycle_start_date_dt  # Move to the next cycle start date

            # Update Firestore with the new cycle and predictions
            doc_ref.set({
                'cycles': historical_cycles,
                'predictions': predictions
            }, merge=True)

             # Send a success message
            dispatcher.utter_message(text="Your menstrual cycle information has been logged successfully.")

            # Reset slots
            return [SlotSet("start_dates", None), SlotSet("end_date", None), SlotSet("cycle_duration", None), SlotSet("period_duration", None)]

        except Exception as e:
            dispatcher.utter_message(text="There was an error logging your menstrual cycle information. Please try again.")
            print(f"ERROR: {e}")

        return []
    
class ActionLogMenstrualCycle(Action):
    def name(self) -> str:
        return "action_log_menstrual_cycle"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        dispatcher.utter_message(text="Please provide the start date of your cycle?\n\nExample:\nStart Date: DD/MM/YYYY")
        return []
    
# Actions for handling delete menstrual cycle
class ActionDeleteLogMenstrualCycle(Action):
    def name(self) -> str:
        return "action_delete_log_menstrual_cycle"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        dispatcher.utter_message(text="Please provide the start date of the cycle you want to delete?\n\nExample:\nStart Date: DD/MM/YYYY")
        return []
    
class ActionDeleteStartDate(Action):
    def name(self) -> str:
        return "action_delete_start_date"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        delete_start_date_input = tracker.latest_message.get('text')  # Get the user's input
        
        # Use regex to find date in the format dd/mm/yyyy in the user input
        date_match = re.search(r'\d{2}/\d{2}/\d{4}', delete_start_date_input)
        
        if date_match:
            delete_start_date_input = date_match.group()  # Extract the actual date part
            try:
                # Convert the date string to a datetime object
                delete_start_date = datetime.strptime(delete_start_date_input, '%d/%m/%Y')
                current_date = datetime.now()

                # Check if the start date is after today
                if delete_start_date > current_date:
                    dispatcher.utter_message(text=f"The start date cannot be after today ({current_date.strftime('%d/%m/%Y')}). Please provide a valid start date.")
                    return []
                else:
                    dispatcher.utter_message(text=f"Start Date recorded: {delete_start_date_input}. What is the end date of the cycle you want to delete?\nExample:\nEnd Date: DD/MM/YYYY")
                    return [SlotSet("delete_start_dates", delete_start_date_input)]

            except ValueError:
                dispatcher.utter_message(text="There was an error processing the date. Please try again.")
                return []
        else:
            dispatcher.utter_message(text="Invalid date format. Please provide the date in the format dd/mm/yyyy.")
            return []
        
class ActionDeleteEndDate(Action):
    def name(self) -> str:
        return "action_delete_end_date"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        delete_end_date_input = tracker.latest_message.get('text')  # Get the user's input

        # Use regex to find date in the format dd/mm/yyyy in the user input
        date_match = re.search(r'\d{2}/\d{2}/\d{4}', delete_end_date_input)

        if date_match:
            delete_end_date_input = date_match.group()  # Extract the actual date part
            try:
                # Convert the date string to a datetime object
                delete_end_date = datetime.strptime(delete_end_date_input, '%d/%m/%Y')
                current_date = datetime.now()

                # Check if the end date is after today
                if delete_end_date > current_date:
                    dispatcher.utter_message(text=f"The end date cannot be after today ({current_date.strftime('%d/%m/%Y')}). Please provide a valid end date.")
                    return []
                else:
                    dispatcher.utter_message(text=f"End Date recorded: {delete_end_date_input}.")
                    return [SlotSet("delete_end_date", delete_end_date_input)]

            except ValueError:
                dispatcher.utter_message(text="There was an error processing the date. Please try again.")
                return []
        else:
            dispatcher.utter_message(text="Invalid date format. Please provide the date in the format dd/mm/yyyy.")
            return []
        
class ActionDeleteLogMenstrualCycle(Action):
    def name(self) -> str:
        return "action_delete_log_menstrual_cycle"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        dispatcher.utter_message(text="Please provide the start date of the cycle you want to delete?\n\nExample:\nStart Date: DD/MM/YYYY")
        return []
    
class ActionDeleteStartDate(Action):
    def name(self) -> str:
        return "action_delete_start_date"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        delete_start_date_input = tracker.latest_message.get('text')  # Get the user's input
        
        # Use regex to find date in the format dd/mm/yyyy in the user input
        date_match = re.search(r'\d{2}/\d{2}/\d{4}', delete_start_date_input)
        
        if date_match:
            delete_start_date_input = date_match.group()  # Extract the actual date part
            try:
                # Convert the date string to a datetime object
                delete_start_date = datetime.strptime(delete_start_date_input, '%d/%m/%Y')
                current_date = datetime.now()

                # Check if the start date is after today
                if delete_start_date > current_date:
                    dispatcher.utter_message(text=f"The start date cannot be after today ({current_date.strftime('%d/%m/%Y')}). Please provide a valid start date.")
                    return []
                else:
                    dispatcher.utter_message(text=f"Start Date recorded: {delete_start_date_input}. What is the end date of the cycle you want to delete?\nExample:\nEnd Date: DD/MM/YYYY")
                    return [SlotSet("delete_start_dates", delete_start_date_input)]

            except ValueError:
                dispatcher.utter_message(text="There was an error processing the date. Please try again.")
                return []
        else:
            dispatcher.utter_message(text="Invalid date format. Please provide the date in the format dd/mm/yyyy.")
            return []
        
class ActionDeleteEndDate(Action):
    def name(self) -> str:
        return "action_delete_end_date"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        delete_end_date_input = tracker.latest_message.get('text')  # Get the user's input

        # Use regex to find date in the format dd/mm/yyyy in the user input
        date_match = re.search(r'\d{2}/\d{2}/\d{4}', delete_end_date_input)

        if date_match:
            delete_end_date_input = date_match.group()  # Extract the actual date part
            try:
                # Convert the date string to a datetime object
                delete_end_date = datetime.strptime(delete_end_date_input, '%d/%m/%Y')
                current_date = datetime.now()

                # Check if the end date is after today
                if delete_end_date > current_date:
                    dispatcher.utter_message(text=f"The end date cannot be after today ({current_date.strftime('%d/%m/%Y')}). Please provide a valid end date.")
                    return []
                else:
                    dispatcher.utter_message(text=f"End Date recorded: {delete_end_date_input}.")
                    return [SlotSet("delete_end_date", delete_end_date_input)]

            except ValueError:
                dispatcher.utter_message(text="There was an error processing the date. Please try again.")
                return []
        else:
            dispatcher.utter_message(text="Invalid date format. Please provide the date in the format dd/mm/yyyy.")
            return []
        
class ActionDeleteMenstrualCycle(Action):
    def name(self) -> str:
        return "action_delete_menstrual_cycle"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        # Retrieve the slots with the start and end dates
        delete_start_date = tracker.get_slot("delete_start_dates")
        delete_end_date = tracker.get_slot("delete_end_date")
        user_id = tracker.sender_id  # Get the currently logged-in user's ID

        if not delete_start_date or not delete_end_date:
            dispatcher.utter_message(text="Please provide both the start date and the end date of the cycle you want to delete.")
            return []

        try:
            # Fetch the user's menstrual cycles from Firestore
            doc_ref = db.collection('menstrual_cycles').document(user_id)
            doc = doc_ref.get()

            if doc.exists:
                cycles = doc.to_dict().get('cycles', [])

                # Find and remove the cycle with the matching start and end dates
                updated_cycles = [cycle for cycle in cycles if not (cycle['start_date'] == delete_start_date and cycle['end_date'] == delete_end_date)]

                if len(updated_cycles) < len(cycles):
                    # Check if the deleted cycle was the only one
                    if len(cycles) == 1:
                        # Delete the only cycle and predictions
                        doc_ref.delete()
                        dispatcher.utter_message(text=f"The only cycle from {delete_start_date} to {delete_end_date} has been successfully deleted along with its predictions.")
                    else:
                        # Update Firestore with the remaining cycles
                        doc_ref.update({'cycles': updated_cycles})
                        dispatcher.utter_message(text=f"Cycle from {delete_start_date} to {delete_end_date} has been successfully deleted.")
                        
                        # Recalculate predictions based on remaining cycles
                        self.recalculate_predictions(doc_ref, updated_cycles)

                else:
                    dispatcher.utter_message(text="No cycle found with the provided start and end dates.")
            else:
                dispatcher.utter_message(text="You have not logged any menstrual cycles yet.")
        except Exception as e:
            dispatcher.utter_message(text="There was an error deleting your menstrual cycle. Please try again.")
            print(f"ERROR: {e}")

        # Reset the slots after deletion
        return [SlotSet("delete_start_dates", None), SlotSet("delete_end_date", None)]
    
    def recalculate_predictions(self, doc_ref, cycles):
        predictions = []
        current_start_date = None

        if cycles:
            last_cycle = cycles[-1]
            cycle_duration_days = last_cycle['cycle_duration']
            current_start_date = datetime.strptime(last_cycle['start_date'], "%d/%m/%Y") + timedelta(days=cycle_duration_days)

        for _ in range(4):  # Predict for the next four cycles
            cycle_end_date_dt = current_start_date + timedelta(days=last_cycle['period_duration'] - 1)
            cycle_end_date = cycle_end_date_dt.strftime("%d/%m/%Y")
            next_cycle_start_date_dt = current_start_date + timedelta(days=cycle_duration_days)
            next_cycle_start_date = next_cycle_start_date_dt.strftime("%d/%m/%Y")

            # Ovulation and fertile window calculations
            ovulation_date_dt = next_cycle_start_date_dt - timedelta(days=14)
            ovulation_date = ovulation_date_dt.strftime("%d/%m/%Y")
            fertile_window_start_dt = ovulation_date_dt - timedelta(days=2)
            fertile_window_end_dt = ovulation_date_dt + timedelta(days=2)
            fertile_window_start = fertile_window_start_dt.strftime("%d/%m/%Y")
            fertile_window_end = fertile_window_end_dt.strftime("%d/%m/%Y")

            predictions.append({
                'cycle_start_date': current_start_date.strftime("%d/%m/%Y"),
                'cycle_end_date': cycle_end_date,
                'fertile_window_start': fertile_window_start,
                'fertile_window_end': fertile_window_end,
                'ovulation_date': ovulation_date,
            })

            current_start_date = next_cycle_start_date_dt  # Move to the next cycle start date

        # Update Firestore with the recalculated predictions
        doc_ref.update({'predictions': predictions})

# Actions for handling update menstrual cycle
class ActionShowLoggedCyclesForUpdate(Action):
    def name(self) -> str:
        return "action_show_logged_cycles_for_update"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        user_id = tracker.sender_id

        try:
            # Fetch the user's menstrual cycles from Firestore
            doc_ref = db.collection('menstrual_cycles').document(user_id)
            doc = doc_ref.get()

            if doc.exists:
                cycles = doc.to_dict().get('cycles', [])
                if cycles:
                    # Create a message to display the cycles
                    cycles_message = "Here are your logged menstrual cycles:\n"
                    for cycle in cycles:
                        cycles_message += (f"Start Date: {cycle['start_date']}, "
                                           f"End Date: {cycle['end_date']}, "
                                           f"Cycle Duration: {cycle['cycle_duration']} days, "
                                           f"Period Duration: {cycle['period_duration']} days\n")
                    dispatcher.utter_message(text=cycles_message)
                else:
                    dispatcher.utter_message(text="You have not logged any menstrual cycles yet.")
            else:
                dispatcher.utter_message(text="You have not logged any menstrual cycles yet.")

        except Exception as e:
            dispatcher.utter_message(text="There was an error retrieving your menstrual cycles. Please try again.")
            print(f"ERROR: {e}")

        return []

class ActionCollectUpdateStartDate(Action):
    def name(self) -> str:
        return "action_collect_update_start_date"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        # Prompt user for the start date of the cycle they want to update
        dispatcher.utter_message(text="Please provide the start date of the cycle you'd like to update.\n\nExample:\nIt starts on DD/MM/YYYY")
        
        return []

class ActionFetchMatchingCycle(Action):
    def name(self) -> str:
        return "action_fetch_matching_cycle"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        user_id = tracker.sender_id
        update_start_date = tracker.get_slot('update_start_date')

        if not update_start_date:
            dispatcher.utter_message(text="I couldn't find the start date you provided. Please try again.")
            return []

        try:
            # Fetch the user's menstrual cycles from Firestore
            doc_ref = db.collection('menstrual_cycles').document(user_id)
            doc = doc_ref.get()

            if doc.exists:
                cycles = doc.to_dict().get('cycles', [])
                matching_cycle = None

                # Search for the cycle that matches the start date
                for cycle in cycles:
                    if cycle['start_date'] == update_start_date:
                        matching_cycle = cycle
                        break

                if matching_cycle:
                    # Show details of the matching cycle
                    dispatcher.utter_message(text=(f"Cycle found: Start Date: {matching_cycle['start_date']}, "
                                                   f"End Date: {matching_cycle['end_date']}, "
                                                   f"Cycle Duration: {matching_cycle['cycle_duration']} days, "
                                                   f"Period Duration: {matching_cycle['period_duration']} days."))
                else:
                    dispatcher.utter_message(text=f"No cycle found with start date {update_start_date}. Please check your entry.")
            else:
                dispatcher.utter_message(text="You have not logged any menstrual cycles yet.")

        except Exception as e:
            dispatcher.utter_message(text="There was an error retrieving the cycle. Please try again later.")
            print(f"ERROR: {e}")

        return []

class ActionAskUpdateField(Action):
    def name(self) -> str:
        return "action_ask_update_field"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        # Asking the user which part of the cycle they want to update
        dispatcher.utter_message(text="Which part of the cycle would you like to update? (start date, end date, cycle duration, or period duration)\n\nExample:\nChange the (start date)")
        return []

class ActionUpdateCycleInFirestore(Action):
    def name(self) -> str:
        return "action_update_cycle_in_firestore"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        user_id = tracker.sender_id
        update_start_date = tracker.get_slot('update_start_date')
        update_field = tracker.get_slot('update_field')
        new_value = tracker.get_slot('new_value')  # The updated value the user provided

        try:
            # Extract the actual value from the new_value slot
            if update_field in ["start date", "end date"]:
                # Extract the date from the user's input (e.g., "The new value is 10/10/2023")
                date_match = re.search(r'\d{2}/\d{2}/\d{4}', new_value)
                if date_match:
                    new_value = date_match.group(0)  # Extract the actual date
                else:
                    dispatcher.utter_message(text="I couldn't extract a valid date. Please provide the date in DD/MM/YYYY format.")
                    return []
            elif update_field in ["cycle duration", "period duration"]:
                # Extract the number from the user's input (e.g., "The duration is 30 days")
                duration_match = re.search(r'\d+', new_value)
                if duration_match:
                    new_value = int(duration_match.group(0))  # Extract the actual number and convert to integer
                else:
                    dispatcher.utter_message(text="I couldn't extract a valid number. Please provide the duration as a number.")
                    return []

            # Fetch the user's menstrual cycles from Firestore
            doc_ref = db.collection('menstrual_cycles').document(user_id)
            doc = doc_ref.get()

            if doc.exists:
                cycles = doc.to_dict().get('cycles', [])

                # Search for the cycle to update
                for cycle in cycles:
                    if cycle['start_date'] == update_start_date:
                        print(f"Updating cycle: {cycle}")  # Debug print to verify the cycle being updated

                        # Update the chosen field with the extracted new value
                        if update_field == "start date":
                            cycle['start_date'] = new_value  # Update the existing key for start date
                        elif update_field == "end date":
                            cycle['end_date'] = new_value  # Update the existing key for end date
                        elif update_field == "cycle duration":
                            cycle['cycle_duration'] = new_value  # Update cycle duration
                        elif update_field == "period duration":
                            cycle['period_duration'] = new_value  # Update period duration
                        else:
                            dispatcher.utter_message(text="Invalid field selected for update.")
                            return []

                        print(f"Cycle after update: {cycle}")  # Debug print to show the updated cycle
                        break

                # Update the document in Firestore
                doc_ref.update({'cycles': cycles})
                print(f"Updated cycles in Firestore: {cycles}")  # Debug print to verify what is being written

                # Recalculate predictions based on updated cycle information
                self.recalculate_predictions(doc_ref, cycles)

                dispatcher.utter_message(text=f"Your menstrual cycle's {update_field} has been updated successfully, and predictions have been recalculated.")

            else:
                dispatcher.utter_message(text="No cycles found to update.")

        except Exception as e:
            dispatcher.utter_message(text="There was an error updating your cycle. Please try again.")
            print(f"ERROR: {e}")  # Log the error for debugging

        return []

    def recalculate_predictions(self, doc_ref, cycles):
        predictions = []
        current_start_date = None

        if cycles:
            last_cycle = cycles[-1]  # Use the most recent cycle for prediction logic
            cycle_duration_days = last_cycle['cycle_duration']
            current_start_date = datetime.strptime(last_cycle['start_date'], "%d/%m/%Y") + timedelta(days=cycle_duration_days)

            for _ in range(4):  # Predict for the next four cycles
                cycle_end_date_dt = current_start_date + timedelta(days=last_cycle['period_duration'] - 1)
                cycle_end_date = cycle_end_date_dt.strftime("%d/%m/%Y")
                next_cycle_start_date_dt = current_start_date + timedelta(days=cycle_duration_days)
                next_cycle_start_date = next_cycle_start_date_dt.strftime("%d/%m/%Y")

                # Ovulation and fertile window calculations
                ovulation_date_dt = next_cycle_start_date_dt - timedelta(days=14)
                ovulation_date = ovulation_date_dt.strftime("%d/%m/%Y")
                fertile_window_start_dt = ovulation_date_dt - timedelta(days=2)
                fertile_window_end_dt = ovulation_date_dt + timedelta(days=2)
                fertile_window_start = fertile_window_start_dt.strftime("%d/%m/%Y")
                fertile_window_end = fertile_window_end_dt.strftime("%d/%m/%Y")

                # Strong flow calculations: 2nd and 3rd day of the period
                strong_flow_start_dt = current_start_date + timedelta(days=1)  # 2nd day
                strong_flow_end_dt = current_start_date + timedelta(days=2)  # 3rd day
                strong_flow_start = strong_flow_start_dt.strftime("%d/%m/%Y")
                strong_flow_end = strong_flow_end_dt.strftime("%d/%m/%Y")

                predictions.append({
                    'cycle_start_date': current_start_date.strftime("%d/%m/%Y"),
                    'cycle_end_date': cycle_end_date,
                    'fertile_window_start': fertile_window_start,
                    'fertile_window_end': fertile_window_end,
                    'ovulation_date': ovulation_date,
                    'strong_flow_start': strong_flow_start,
                    'strong_flow_end': strong_flow_end
                })

                current_start_date = next_cycle_start_date_dt  # Move to the next cycle start date

        # Update Firestore with the recalculated predictions
        doc_ref.update({'predictions': predictions})

class ActionCollectUpdatedValue(Action):
    def name(self) -> str:
        return "action_collect_updated_value"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        # Get the field the user wants to update
        update_field = tracker.get_slot('update_field')

        # Capture the user's input as the new value
        new_value = tracker.latest_message.get('text')  # Extract user input
        print(f"Captured new value: {new_value}")  # Debugging: Print the captured value to verify

        # Return SlotSet to update the new_value slot
        events = [SlotSet("new_value", new_value)]  # Set the new value in the slot

        # Provide feedback based on the field the user is updating
        if update_field == "start date":
            dispatcher.utter_message(text="Please enter the new value for the start date in DD/MM/YYYY format.\n\nExample:\nChange it to DD/MM/YYYY")
        elif update_field == "end date":
            dispatcher.utter_message(text="For end date, please enter in DD/MM/YYYY format.\n\nExample:\nChange it to DD/MM/YYYY")
        elif update_field == "cycle duration":
            dispatcher.utter_message(text="For cycle duration, please enter the number of days.\n\nExample:\nChange it to (29 days)")
        elif update_field == "period duration":
            dispatcher.utter_message(text="For period duration, please enter the number of days.\n\nExample:\nChange it to (4 days)")
        else:
            dispatcher.utter_message(text="I didn't recognize the field to update.")

        return events  # Return SlotSet event to ensure the new value is set
