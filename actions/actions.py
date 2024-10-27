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
openai.api_key = 

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
        
        # Construct the prompt for GPT
        prompt = f"User asked: {user_query}\nAnswer them as a helpful assistant."

        try:
            # Call the OpenAI API with GPT-3.5 or GPT-4
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=70
            )

            # Extract the GPT response
            result = response['choices'][0]['message']['content'].strip()

            # Send the result back to the user
            dispatcher.utter_message(text=result)

        except Exception as e:
            # Handle potential errors and provide fallback response
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
                
# Action for Head Symptoms along with types
class ActionHeadSymptom(Action):
    def name(self) -> Text:
        return "action_head_symptom"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_head_symptom")

        return []

class ActionHeadWhole(Action):
    def name(self) -> Text:
        return "action_head_whole"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_head_whole_response")

        return []

class ActionHeadSides(Action):
    def name(self) -> Text:
        return "action_head_sides"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_head_sides_response")

        return []

class ActionHeadCrown(Action):
    def name(self) -> Text:
        return "action_head_crown"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_head_crown_response")

        return []

class ActionHeadEyes(Action):
    def name(self) -> Text:
        return "action_head_eyes"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_head_eyes_response")

        return []

# Action for Flu
class ActionFluSymptom(Action):
    def name(self) -> Text:
        return "action_flu_symptom"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_flu_response")

        return []

# Action for Vision
class ActionVisionSymptom(Action):
    def name(self) -> Text:
        return "action_vision_symptom"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_vision_types")

        return []

# Action for Stomach
class ActionStomachSymptom(Action):
    def name(self) -> Text:
        return "action_stomach_symptom"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_stomach_types")

        return []
    
# Actions for handling lifestyle of men
class ActionLifestyleMen(Action):
    def name(self) -> Text:
        return "action_lifestyle_men"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_nine_life_style_men")

        return []
    
# Actions for handling itchy testicles
class ActionItchyTesticles(Action):
    def name(self) -> Text:
        return "action_itchy_testicles"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_men_itchy_testicles")

        return []
    
# Actions for handling common causes of testicular pain
class ActionCommonCauses(Action):
    def name(self) -> Text:
        return "action_common_causes"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_men_common_causes")

        return []
    
# Actions for handling sperm health
class ActionSpermHealth(Action):
    def name(self) -> Text:
        return "action_sperm_health"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_men_sperm_health")

        return []
    
# Actions for handling good signs of healthy eggs
class ActionEggsHealthy(Action):
    def name(self) -> Text:
        return "action_eggs_healthy"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_good_quality_eggs")

        return []
    
# Actions for handling signs of a poor egg quality
class ActionEggsPoorQuality(Action):
    def name(self) -> Text:
        return "action_eggs_poor_quality"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_poor_quality_eggs")

        return []

# Actions for handling enhance quality of eggs
class ActionEggsEnhanceQuality(Action):
    def name(self) -> Text:
        return "action_eggs_enhance_quality"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_enhanced_quality_eggs")

        return []
    
# Actions for handling 10 foods for healthy eggs
class ActionEggsHealthyFoods(Action):
    def name(self) -> Text:
        return "action_eggs_healthy_foods"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_healthy_eggs_foods")

        return []
    
# Actions for handling why beans is healthy for eggs
class ActionEggsBeansHealthy(Action):
    def name(self) -> Text:
        return "action_eggs_beans_healthy"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_beans_healthy_eggs")

        return []
    
# Actions for handling why seeds is healthy for eggs
class ActionEggsSeedsHealthy(Action):
    def name(self) -> Text:
        return "action_eggs_seeds_healthy"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_seeds_healthy_eggs")

        return []
    
# Actions for handling why nuts and dry fruits is healthy for eggs
class ActionEggsNutsHealthy(Action):
    def name(self) -> Text:
        return "action_eggs_nuts_healthy"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_nuts_healthy_eggs")

        return []
    
# Actions for handling why avocados is healthy for eggs
class ActionEggsAvocadosHealthy(Action):
    def name(self) -> Text:
        return "action_eggs_avocados_healthy"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_avocados_healthy_eggs")

        return []

# Actions for handling why berries is healthy for eggs
class ActionEggsBerriesHealthy(Action):
    def name(self) -> Text:
        return "action_eggs_berries_healthy"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_berries_healthy_eggs")

        return []

# Actions for handling why cinnamon is healthy for eggs
class ActionEggsCinnamonHealthy(Action):
    def name(self) -> Text:
        return "action_eggs_cinnamon_healthy"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_cinnamon_healthy_eggs")

        return []

# Actions for handling why ginger is healthy for eggs
class ActionEggsGingerHealthy(Action):
    def name(self) -> Text:
        return "action_eggs_ginger_healthy"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_ginger_healthy_eggs")

        return []

# Actions for handling why green leafy vegetables is healthy for eggs
class ActionEggsGreenLeafyHealthy(Action):
    def name(self) -> Text:
        return "action_eggs_green_leafy_healthy"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_green_leafy_healthy_eggs")

        return []

# Actions for handling why whole grains is healthy for eggs
class ActionEggsWholeGrainsHealthy(Action):
    def name(self) -> Text:
        return "action_eggs_whole_grains_healthy"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_whole_grains_healthy_eggs")

        return []

# Actions for handling why dairy is healthy for eggs
class ActionEggsDairyHealthy(Action):
    def name(self) -> Text:
        return "action_eggs_dairy_healthy"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_dairy_healthy_eggs")

        return []
    
# Actions for handling dietary changes to affect egg quality
class ActionDietaryChangesAffectHealthyEggs(Action):
    def name(self) -> Text:
        return "action_dietary_changes_affect_healthy_egg"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_dietary_changes_affect_healthy_eggs")

        return []

# Actions for handling foods to avoid improve egg quality
class ActionFoodAvoidImproveEggsQuality(Action):
    def name(self) -> Text:
        return "action_food_avoid_improve_eggs_quality"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_foods_to_avoid_improve_healthy_eggs")

        return []

# Action for handling organic and non-organic food
class ActionOrganicNonOrganicFoods(Action):
    def name(self) -> Text:
        return "action_organic_non_organic_foods_eggs"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_organic_and_non_organic_foods_eggs")

        return []

# Action for handling why egg quality is important
class ActionEggQualityImportant(Action):
    def name(self) -> Text:
        return "action_egg_quality_important"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_egg_quality_important")

        return []

# Action for handling top ten diet rules
class ActionTopTenDietRules(Action):
    def name(self) -> Text:
        return "action_top_ten_diet_rules"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_top_ten_diet_rules")

        return []

# Action for handling food increase sperm count
class ActionFoodIncreaseSpermCount(Action):
    def name(self) -> Text:
        return "action_food_increase_sperm_count"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_food_increased_sperm_count")

        return []

# Action for handling ways to increase sperm count
class ActionIncreaseSpermCountWays(Action):
    def name(self) -> Text:
        return "action_increase_sperm_count_ways"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_ways_to_increase_sperm_count")

        return []

# Action for handling what is d-aspartic acid supplements
class ActionDAsparticAcidSupplements(Action):
    def name(self) -> Text:
        return "action_d_aspartic_acid_supplements"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_d_aspartic_acid_supplements")

        return []

# Action for handling what is tribulus terrestris
class ActionTribulusTerrestris(Action):
    def name(self) -> Text:
        return "action_tribulus_terrestris"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_tribulus_terrestris")

        return []
    
# Action for handling what is fenugreek supplements
class ActionFenugreekSupplements(Action):
    def name(self) -> Text:
        return "action_fenugreek_supplements"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_fenugreek_supplements")

        return []
    
# Action for handling what is ashwagandha
class ActionAshwagandha(Action):
    def name(self) -> Text:
        return "action_ashwagandha"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_ashwagandha")

        return []

# Action for handling what is maca root
class ActionMacaRoot(Action):
    def name(self) -> Text:
        return "action_maca_root"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_maca_root")

        return []

# Action for handling how can you find out your baby's sex
class ActionFindBabySex(Action):
    def name(self) -> Text:
        return "action_find_baby_sex"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_how_to_find_baby_sex")

        return []

# Action for handling how accurate is IVF with sex selection
class ActionIVFSexSelectionAccuracy(Action):
    def name(self) -> Text:
        return "action_ivf_sex_selection_accuracy"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_accuracy_of_ivf_with_sex_selection")

        return []

# Action for handling what is NIPT and how does it work
class ActionNIPTAndWork(Action):
    def name(self) -> Text:
        return "action_nipt_and_work"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_nipt_and_how_it_works")

        return []

# Action for handling what are the benefits of nipt
class ActionBenefitsOfNIPT(Action):
    def name(self) -> Text:
        return "action_benefits_of_nipt"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_benefits_of_nipt")

        return []

# Action for handling what is cvs and when is it performed
class ActionCVSAndWhen(Action):
    def name(self) -> Text:
        return "action_cvs_and_when"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_cvs_and_how_it_works")

        return []

# Action for handling what is amniocentesis and what does it reveal?
class ActionAmniocentesisAndReveal(Action):
    def name(self) -> Text:
        return "action_amniocentesis_and_reveal"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_amniocentesis_and_how_it_works")

        return []

# Action for handling when can you find out the baby's sex with an ultrasound
class ActionUltrasoundSexFind(Action):
    def name(self) -> Text:
        return "action_ultrasound_sex_find"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_when_to_find_baby_sex_with_ultrasound")

        return []

# Action for handling do gender predictor tests work?
class ActionGenderPredictorTestsWork(Action):
    def name(self) -> Text:
        return "action_gender_predictor_tests_work"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_gender_predictor_tests_work")

        return []

# Action for handling what is the gender identity pregnancy test
class ActionGenderIdentityPregnancyTest(Action):
    def name(self) -> Text:
        return "action_gender_identity_pregnancy_test"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_gender_identity_pregnancy_test")

        return []

# Action for handling can antibiotics cause your period to be late?
class ActionAntibioticsPeriodLate(Action):
    def name(self) -> Text:
        return "action_antibiotics_period_late"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_antibiotics_cause_period_to_be_late")

        return []

# Action for handling does taking antibiotics affect your period at all
class ActionAntibioticsPeriodImpact(Action):
    def name(self) -> Text:
        return "action_antibiotics_period_impact"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_taking_antibiotics_affects_period")

        return []

# Action for handling can stress from illness affect your period
class ActionStressIllnessPeriod(Action):
    def name(self) -> Text:
        return "action_stress_illness_period"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_stress_from_illness_affects_period")

        return []

# Action for handling what are the most common reasons your period may be late
class ActionCommonPeriodLateReasons(Action):
    def name(self) -> Text:
        return "action_common_period_late_reasons"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_most_common_reasons_for_period_late")

        return []

# Action for handling is there anything i can do about late periods
class ActionLatePeriodHelp(Action):
    def name(self) -> Text:
        return "action_late_period_help"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_anything_i_can_do_about_late_periods")

        return []

# Action for handling when should you consult a doctor about missed periods
class ActionConsultDoctorPeriodMissed(Action):
    def name(self) -> Text:
        return "action_consult_doctor_period_missed"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_when_to_consult_doctor_about_missed_periods")

        return []

# Action for handling what is ivf
class ActionIVF(Action):
    def name(self) -> Text:
        return "action_ivf"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_ivf")

        return []

# Action for handling what is icsi
class ActionICSI(Action):
    def name(self) -> Text:
        return "action_icsi"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_icsi")

        return []

# Action for handling what is the procedure of IVF
class ActionIVFProcedure(Action):
    def name(self) -> Text:
        return "action_ivf_procedure"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_procedure_of_ivf")

        return []

# Action for handling drinks and foods that harm male fertility
class ActionDrinksAndFoods(Action):
    def name(self) -> Text:
        return "action_drinks_and_foods_that_harm_male_fertility"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_drinks_and_foods_that_harm_male_fertility")

        return []

# Action for handling things that could be messing with your guys sperm
class ActionThingsMessingWithSperm(Action):
    def name(self) -> Text:
        return "action_things_messing_with_sperm"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_things_that_could_be_messing_with_guys_sperm")

        return []

# Action for handling what physical changes happen after childbirth
class ActionPhysicalChangesAfterBirth(Action):
    def name(self) -> Text:
        return "action_physical_changes_after_birth"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_physical_changes_after_childbirth")

        return []

# Action for handling what is a c-section
class ActionCSection(Action):
    def name(self) -> Text:
        return "action_c_section"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_c_section")

        return []

# Action for handling why c sections is done
class ActionWhyCSection(Action):
    def name(self) -> Text:
        return "action_why_c_section"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_why_c_section")

        return []

# Action for handling what happens after c section
class ActionAfterCSection(Action):
    def name(self) -> Text:
        return "action_after_c_section"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_after_c_section")

        return []

# Action for handling how long to wait before cleaning up after sex
class ActionCleaningUpAfterSex(Action):
    def name(self) -> Text:
        return "action_cleaning_up_after_sex"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_how_long_to_wait_before_cleaning_up_after_sex")

        return []

# Action for handling vagina care
class ActionVaginaCare(Action):
    def name(self) -> Text:
        return "action_vagina_care"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_vagina_care")

        return []

# Action for handling penis care
class ActionPenisCare(Action):
    def name(self) -> Text:
        return "action_penis_care"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_penis_care")

        return []

# Action for handling anal sex hygiene
class ActionAnalSexHygiene(Action):
    def name(self) -> Text:
        return "action_anal_sex_hygiene"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_anal_sex_hygiene")

        return []

# Action for handling oral sex hygiene 
class ActionOralSexHygiene(Action):
    def name(self) -> Text:
        return "action_oral_sex_hygiene"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_oral_sex_hygiene")

        return []
    
# Actions for handling cleaning sex toys
class ActionCleaningSexToys(Action):
    def name(self) -> Text:
        return "action_cleaning_sex_toys"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_cleaning_sex_toys")

        return []

# Actions for handling cleaning bed
class ActionCleaningBed(Action):
    def name(self) -> Text:
        return "action_cleaning_bed"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_cleaning_bed")

        return []

# Actions for handling trying to conceived
class ActionTryingToConceive(Action):
    def name(self) -> Text:
        return "action_trying_to_conceive"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_trying_to_conceive")

        return []

# Actions for handling cleaning vagina prevent sex
class ActionCleaningVaginaPreventSex(Action):
    def name(self) -> Text:
        return "action_cleaning_vagina_prevent_sex"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_cleaning_vagina_prevent_sex")

        return []

# Actions for handling prevent infection after sex
class ActionPreventInfectionAfterSex(Action):
    def name(self) -> Text:
        return "action_prevent_infection_after_sex"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_prevent_infection_after_sex")

        return []

# Actions for handling best time to get pregnant
class ActionBestTimeToGetPregnant(Action):
    def name(self) -> Text:
        return "action_best_time_to_get_pregnant"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_best_time_to_get_pregnant")

        return []

# Actions for handling miscarriage
class ActionMiscarriage(Action):
    def name(self) -> Text:
        return "action_miscarriage"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_miscarriage")

        return []

# Actions for handling types of miscarriage
class ActionTypesOfMiscarriage(Action):
    def name(self) -> Text:
        return "action_types_of_miscarriage"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_types_of_miscarriage")

        return []

# Actions for handling missed miscarriage
class ActionMissedMiscarriage(Action):
    def name(self) -> Text:
        return "action_missed_miscarriage"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_missed_miscarriage")

        return []

# Actions for handling complete miscarriage
class ActionCompleteMiscarriage(Action):
    def name(self) -> Text:
        return "action_complete_miscarriage"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_complete_miscarriage")

        return []

# Actions for handling recurrent miscarriage
class ActionRecurrentMiscarriage(Action):
    def name(self) -> Text:
        return "action_recurrent_miscarriage"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_recurrent_miscarriage")

        return []

# Actions for handling threatened miscarriage
class ActionThreatenedMiscarriage(Action):
    def name(self) -> Text:
        return "action_threatened_miscarriage"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_threatened_miscarriage")

        return []

# Actions for handling inevitable miscarriage
class ActionInevitableMiscarriage(Action):
    def name(self) -> Text:
        return "action_inevitable_miscarriage"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_inevitable_miscarriage")

        return []

# Actions for handling having miscarriage
class ActionHavingMiscarriage(Action):
    def name(self) -> Text:
        return "action_having_miscarriage"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_having_miscarriage")

        return []

# Actions for handling cause miscarriage
class ActionCauseMiscarriage(Action):
    def name(self) -> Text:
        return "action_cause_miscarriage"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_cause_miscarriage")

        return []

# Actions for handling painful miscarriage
class ActionPainfulMiscarriage(Action):
    def name(self) -> Text:
        return "action_painful_miscarriage"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_painful_miscarriage")

        return []

# Actions for handling safe sex
class ActionSafeSex(Action):
    def name(self) -> Text:
        return "action_safe_sex"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_safe_sex")

        return []

# Actions for handling importance safe sex
class ActionImportanceSafeSex(Action):
    def name(self) -> Text:
        return "action_importance_safe_sex"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response="utter_importance_safe_sex")

        return []

# Actions for handling sti
class ActionSti(Action):
    def name(self) -> Text:
        return "action_sti"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(response="utter_sti")

        return []

# Actions for handling std
class ActionStd(Action):
    def name(self) -> Text:
        return "action_std"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(response="utter_std")

        return []

# Actions for handling difference std sti
class ActionDifferenceStdSti(Action):
    def name(self) -> Text:
        return "action_difference_std_sti"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(response="utter_difference_std_sti")

        return []

# Actions for handling type sti
class ActionTypeSti(Action):
    def name(self) -> Text:
        return "action_types_sti"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(response="utter_types_sti")

        return []

# Actions for handling how common sti
class ActionHowCommonSti(Action):
    def name(self) -> Text:
        return "action_how_common_sti"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(response="utter_how_common_sti")

        return []

# Actions for handling symptoms sti
class ActionSymptomsSti(Action):
    def name(self) -> Text:
        return "action_symptoms_sti"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(response="utter_symptoms_sti")

        return []

# Actions for handling causes sti
class ActionCausesSti(Action):
    def name(self) -> Text:
        return "action_causes_sti"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(response="utter_causes_sti")

        return []

# Actions for handling sti contagious
class ActionStiContagious(Action):
    def name(self) -> Text:
        return "action_sti_contagious"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(response="utter_sti_contagious")

        return []

# Actions for handling sti diagnosed
class ActionStiDiagnosed(Action):
    def name(self) -> Text:
        return "action_sti_diagnosed"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(response="utter_sti_diagnosed")

        return []

# Actions for handling sti testing
class ActionStiTesting(Action):
    def name(self) -> Text:
        return "action_sti_testing"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(response="utter_sti_testing")

        return []

# Actions for handling sexual health
class ActionSexualHealth(Action):
    def name(self) -> Text:
        return "action_sexual_health"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(response="utter_sexual_health")

        return []

# Actions for handling importance sexual health
class ActionImportanceSexualHealth(Action):
    def name(self) -> Text:
        return "action_importance_sexual_health"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(response="utter_importance_sexual_health")

        return []

# Actions for handling hiv
class ActionHiv(Action):
    def name(self) -> Text:
        return "action_hiv"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(response="utter_hiv")

        return []

# Actions for handling hiv treatment
class ActionHivTreatment(Action):
    def name(self) -> Text:
        return "action_hiv_treatment"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(response="utter_hiv_treatment")

        return []

# Actions for handling medication during pregnancy
class ActionMedicationPregnancy(Action):
    def name(self) -> Text:
        return "action_medication_during_pregnancy"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(response="utter_medication_during_pregnancy")

        return []
    
# Actions for handling best time safe sex
class ActionBestTimeSafeSex(Action):
    def name(self) -> Text:
        return "action_best_time_safe_sex"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(response="utter_best_time_safe_sex")

        return []
    
# Actions for handling create symptoms
class ActionCollectStartDates(Action):
    def name(self) -> str:
        return "action_collect_start_dates"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        start_date_input = tracker.latest_message.get('text')
        
        date_match = re.search(r'\d{2}/\d{2}/\d{4}', start_date_input)
        
        if date_match:
            start_date_str = date_match.group()
            try:
                start_date = datetime.strptime(start_date_str, '%d/%m/%Y')
                current_date = datetime.now()
                
                if start_date > current_date:
                    dispatcher.utter_message(text=f"The start date cannot be after today ({current_date.strftime('%d/%m/%Y')}). Please provide a valid start date.")
                    return []
                else:
                    dispatcher.utter_message(text=f"Start Date recorded: {start_date_str}. Please provide the end date (in dd/mm/yyyy).")
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
        end_date_input = tracker.latest_message.get('text')
        
        date_match = re.search(r'\d{2}/\d{2}/\d{4}', end_date_input)
        
        if date_match:
            end_date_str = date_match.group()
            try:
                end_date = datetime.strptime(end_date_str, '%d/%m/%Y')
                current_date = datetime.now()
                
                if end_date > current_date:
                    dispatcher.utter_message(text=f"The end date cannot be after today ({current_date.strftime('%d/%m/%Y')}). Please provide a valid end date.")
                    return []
                else:
                    dispatcher.utter_message(text=f"End Date recorded: {end_date_str}. Now, please describe your symptoms.")
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

            historical_logs = doc.to_dict().get('logs', []) if doc.exists else []

            # Append new log entry
            historical_logs.append({
                'start_dates': start_dates,
                'end_dates': end_dates,
                'symptoms': symptoms
            })

            # Update Firestore with the new log
            doc_ref.set({'logs': historical_logs}, merge=True)
            dispatcher.utter_message(text="Your symptoms have been logged successfully.")

        except Exception as e:
            dispatcher.utter_message(text="There was an error logging your symptoms.")
            print(f"ERROR: {e}")

        return []
    

class ActionEvaluateSymptoms(Action):
    def name(self) -> str:
        return "action_evaluate_symptoms"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]):
        # Retrieve the symptoms from the slot
        symptoms = tracker.get_slot("symptoms")
        user_id = tracker.sender_id

        if not symptoms:
            dispatcher.utter_message(text="I don't have any symptoms to evaluate.")
            return []

        # Ensure symptoms are in a readable format if multiple symptoms are provided
        if isinstance(symptoms, list):
            symptoms_text = ", ".join(symptoms)  # Join multiple symptoms with commas
        else:
            symptoms_text = symptoms  # Handle single symptom as a string

        try:
            # Construct the chat message for OpenAI
            messages = [
                {"role": "system", "content": "You are an AI health assistant."},
                {"role": "user", "content": f"I am experiencing the following symptoms: {symptoms_text}. What could be the possible condition?"}
            ]

            # Call OpenAI Chat Completion API asynchronously
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",  # or "gpt-4" if available on your plan
                messages=messages,
                max_tokens=150,
                n=1,
                stop=None,
                temperature=0.7,
            )

            evaluation = response['choices'][0]['message']['content'].strip()

            # Provide the user with the AI evaluation
            dispatcher.utter_message(text=f"Based on your symptoms, here is a possible evaluation:\n{evaluation}")

            # Log the evaluation for future reference if needed
            doc_ref = db.collection('symptom_logs').document(user_id)
            doc = doc_ref.get()

            if doc.exists:
                historical_logs = doc.to_dict().get('logs', [])
            else:
                historical_logs = []

            # Add the evaluation to the latest log
            if historical_logs:
                historical_logs[-1]['evaluation'] = evaluation
            else:
                historical_logs.append({'symptoms': symptoms_text, 'evaluation': evaluation})

            # Update Firestore with the evaluation
            doc_ref.set({'logs': historical_logs}, merge=True)

        except Exception as e:
            dispatcher.utter_message(text="There was an error evaluating your symptoms.")
            print(f"ERROR: {e}")  # Debugging the error

        return []

    
# Actions for handling delete symptoms
    
# Actions for handling update symptoms

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
                else:
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

                # Check if the end date is after today
                if end_date > current_date:
                    dispatcher.utter_message(text=f"The end date cannot be after today ({current_date.strftime('%d/%m/%Y')}). Please provide a valid end date.")
                    return []
                else:
                    dispatcher.utter_message(text=f"End Date recorded: {end_date_input}. How long was your entire cycle (in days)\n\nThe cycle duration typically refers to the length of time between the first day of one menstrual cycle and the first day of the next.\n\nExamples: 23 days")
                    return [SlotSet("end_date", end_date_input)]

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
        dispatcher.utter_message(text="Please provide the start date of the cycle you'd like to update.\n\nExample:\nIt Starts on: DD/MM/YYYY")
        
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
        dispatcher.utter_message(text="Which part of the cycle would you like to update? (start date, end date, cycle duration, or period duration)\n\nExample:\nChange the start date:")
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
            dispatcher.utter_message(text="Please enter the new value for the start date in DD/MM/YYYY format.\n\nExample:\nChange it to: DD/MM/YYYY")
        elif update_field == "end date":
            dispatcher.utter_message(text="For end date, please enter in DD/MM/YYYY format.\n\nExample:\nChange it to: DD/MM/YYYY")
        elif update_field == "cycle duration":
            dispatcher.utter_message(text="For cycle duration, please enter the number of days.\n\nExample:\nChange it to: 29 days")
        elif update_field == "period duration":
            dispatcher.utter_message(text="For period duration, please enter the number of days.\n\nExample:\nChange it to: 4 days")
        else:
            dispatcher.utter_message(text="I didn't recognize the field to update.")

        return events  # Return SlotSet event to ensure the new value is set