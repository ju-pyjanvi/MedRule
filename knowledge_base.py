"""
MedRule - KNOWLEDGE BASE  (Unit II: Knowledge Representation / Rule-Based Systems)

Everything the system "knows" lives in this file as plain data. The inference
engine (engine.py) contains NO medical knowledge. Change a rule here and the
behaviour changes without touching any logic. That separation is the defining
feature of an expert system (Unit IV, MYCIN architecture).

Rule format (production rule):   IF <premises joined by AND> THEN <conclusion>  [CF]
CF = certainty factor of the rule, between 0 and 1 (MYCIN style).
"""

# ---------------------------------------------------------------------------
# 1. SYMPTOM VOCABULARY  (canonical symptom -> label + synonyms)
#    The synonyms are used by the text preprocessor to map everyday phrases
#    ("high temperature") to canonical symptoms ("fever").
# ---------------------------------------------------------------------------
SYMPTOMS = {
    "fever": {"label": "Fever", "synonyms": ["high temperature", "high fever", "feverish", "running a temperature", "temperature", "temp", "hot body"]},
    "chills": {"label": "Chills", "synonyms": ["shivering", "shivers", "rigors", "feeling cold"]},
    "headache": {"label": "Headache", "synonyms": ["head ache", "head pain", "head hurts", "head is hurting"]},
    "one_sided_headache": {"label": "One-sided throbbing headache", "synonyms": ["one sided headache", "throbbing headache", "pain on one side of head", "half headache"]},
    "body_ache": {"label": "Body ache", "synonyms": ["body pain", "muscle pain", "muscle ache", "aching body", "myalgia"]},
    "joint_pain": {"label": "Joint pain", "synonyms": ["joints hurt", "arthralgia", "painful joints", "joint ache"]},
    "fatigue": {"label": "Fatigue", "synonyms": ["tired", "tiredness", "weakness", "exhausted", "lethargy", "feeling weak"]},
    "cough": {"label": "Cough", "synonyms": ["coughing"]},
    "dry_cough": {"label": "Dry cough", "synonyms": ["dry coughing"]},
    "productive_cough": {"label": "Cough with phlegm", "synonyms": ["phlegm", "mucus cough", "productive cough", "wet cough"]},
    "sore_throat": {"label": "Sore throat", "synonyms": ["throat pain", "scratchy throat", "painful swallowing", "throat hurts"]},
    "runny_nose": {"label": "Runny nose", "synonyms": ["nasal discharge", "running nose"]},
    "blocked_nose": {"label": "Blocked nose", "synonyms": ["stuffy nose", "nasal congestion", "congestion"]},
    "sneezing": {"label": "Sneezing", "synonyms": ["sneezes", "sneeze"]},
    "nausea": {"label": "Nausea", "synonyms": ["nauseous", "feel like vomiting", "queasy", "feeling sick"]},
    "vomiting": {"label": "Vomiting", "synonyms": ["throwing up", "puking", "vomit", "vomits"]},
    "diarrhea": {"label": "Diarrhea", "synonyms": ["diarrhoea", "loose motions", "loose stools", "watery stools", "loose motion"]},
    "abdominal_pain": {"label": "Abdominal pain", "synonyms": ["stomach ache", "stomach pain", "belly pain", "tummy ache", "cramps", "stomach cramps"]},
    "lower_abdominal_pain": {"label": "Lower abdominal pain", "synonyms": ["pain in lower stomach", "pelvic pain", "lower belly pain"]},
    "loss_of_appetite": {"label": "Loss of appetite", "synonyms": ["not hungry", "no appetite"]},
    "heartburn": {"label": "Heartburn", "synonyms": ["acidity", "acid reflux", "sour taste", "acid in throat"]},
    "chest_burning": {"label": "Burning in chest", "synonyms": ["chest burning", "burning chest"]},
    "bloating": {"label": "Bloating", "synonyms": ["bloated", "gas", "gassy"]},
    "rash": {"label": "Skin rash", "synonyms": ["skin rash", "red spots", "spots on skin", "rashes"]},
    "eye_pain": {"label": "Pain behind the eyes", "synonyms": ["pain behind eyes", "retro orbital pain", "eye pain", "eyes hurt"]},
    "light_sensitivity": {"label": "Sensitivity to light", "synonyms": ["sensitive to light", "photophobia", "light hurts eyes"]},
    "red_eyes": {"label": "Red eyes", "synonyms": ["pink eye", "bloodshot eyes", "red eye"]},
    "itchy_eyes": {"label": "Itchy / watery eyes", "synonyms": ["watery eyes", "eye itching", "teary eyes", "itchy eye"]},
    "eye_discharge": {"label": "Eye discharge", "synonyms": ["sticky eyes", "pus in eyes", "eyes sticking"]},
    "shortness_of_breath": {"label": "Shortness of breath", "synonyms": ["breathlessness", "difficulty breathing", "cannot breathe", "cant breathe", "can't breathe", "breathless", "trouble breathing"]},
    "chest_pain": {"label": "Chest pain", "synonyms": ["pain in chest", "pain in my chest"]},
    "chest_tightness": {"label": "Chest tightness", "synonyms": ["tight chest", "tightness in chest"]},
    "wheezing": {"label": "Wheezing", "synonyms": ["whistling sound in chest", "wheeze", "wheezy"]},
    "loss_of_smell_taste": {"label": "Loss of smell or taste", "synonyms": ["cannot smell", "loss of smell", "loss of taste", "no taste", "cant smell", "cannot taste"]},
    "burning_urination": {"label": "Burning urination", "synonyms": ["burning while urinating", "painful urination", "burning while peeing", "burning when i pee"]},
    "frequent_urination": {"label": "Frequent urination", "synonyms": ["urinating often", "frequent peeing", "peeing a lot", "pee often", "peeing often"]},
    "dark_urine": {"label": "Dark urine", "synonyms": ["tea coloured urine", "tea colored urine", "dark pee"]},
    "yellow_skin": {"label": "Yellow skin / eyes", "synonyms": ["yellow eyes", "jaundice", "yellowing", "yellow skin"]},
    "stiff_neck": {"label": "Stiff neck", "synonyms": ["neck stiffness", "neck is stiff", "neck pain"]},
    "sweating": {"label": "Heavy sweating", "synonyms": ["night sweats", "sweats", "sweating a lot"]},
    "dizziness": {"label": "Dizziness", "synonyms": ["dizzy", "giddy", "lightheaded"]},
    "stress": {"label": "Stress / anxiety", "synonyms": ["stressed", "anxiety", "tense", "anxious", "overwork"]},
}

# ---------------------------------------------------------------------------
# 2. DISEASES  (disease -> symptom evidence with CF, advice, urgency)
#    Each (symptom, cf) pair becomes one rule:  IF symptom THEN disease (CF)
# ---------------------------------------------------------------------------
DISEASES = {
    "Viral Flu": {
        "symptoms": {"fever": 0.50, "chills": 0.40, "body_ache": 0.50, "fatigue": 0.40, "headache": 0.30, "dry_cough": 0.40, "sore_throat": 0.20, "runny_nose": 0.15},
        "advice": "Rest, fluids, and paracetamol for fever. See a doctor if it lasts beyond 3 to 4 days.",
    },
    "Common Cold": {
        "symptoms": {"runny_nose": 0.50, "sneezing": 0.50, "blocked_nose": 0.40, "sore_throat": 0.35, "cough": 0.30},
        "advice": "Rest, warm fluids, steam inhalation. Usually settles in about a week.",
    },
    "Dengue": {
        "symptoms": {"fever": 0.40, "eye_pain": 0.50, "joint_pain": 0.40, "rash": 0.40, "body_ache": 0.35, "headache": 0.30, "nausea": 0.20, "fatigue": 0.20},
        "advice": "See a doctor soon for a blood test (NS1 / platelet count). Avoid NSAIDs like ibuprofen or aspirin.",
    },
    "Malaria": {
        "symptoms": {"fever": 0.35, "chills": 0.50, "sweating": 0.40, "headache": 0.25, "nausea": 0.20, "vomiting": 0.20, "body_ache": 0.20},
        "advice": "Needs a blood smear or rapid test. See a doctor the same day.",
    },
    "Typhoid": {
        "symptoms": {"fever": 0.40, "abdominal_pain": 0.35, "loss_of_appetite": 0.30, "headache": 0.25, "fatigue": 0.25, "diarrhea": 0.15, "nausea": 0.15},
        "advice": "Needs a blood culture or Widal test. See a doctor; do not self-medicate with antibiotics.",
    },
    "COVID-19": {
        "symptoms": {"fever": 0.30, "dry_cough": 0.40, "loss_of_smell_taste": 0.70, "fatigue": 0.30, "sore_throat": 0.20, "body_ache": 0.25, "shortness_of_breath": 0.30, "headache": 0.20},
        "advice": "Isolate, take a test, and monitor breathing. Seek care if breathing becomes difficult.",
    },
    "Migraine": {
        "symptoms": {"one_sided_headache": 0.60, "light_sensitivity": 0.50, "nausea": 0.40, "headache": 0.30, "vomiting": 0.20, "dizziness": 0.15},
        "advice": "Rest in a dark, quiet room and stay hydrated. Recurrent migraines need a doctor's review.",
    },
    "Tension Headache": {
        "symptoms": {"headache": 0.40, "stress": 0.50, "stiff_neck": 0.35, "fatigue": 0.15},
        "advice": "Rest, hydration, posture breaks, and stress reduction. See a doctor if it becomes frequent.",
    },
    "Food Poisoning": {
        "symptoms": {"vomiting": 0.50, "diarrhea": 0.50, "nausea": 0.40, "abdominal_pain": 0.40, "fever": 0.10},
        "advice": "Drink ORS and fluids. See a doctor if it lasts over 2 days or you cannot keep fluids down.",
    },
    "Viral Gastroenteritis": {
        "symptoms": {"diarrhea": 0.50, "vomiting": 0.40, "abdominal_pain": 0.30, "fever": 0.30, "nausea": 0.30, "body_ache": 0.15},
        "advice": "Stay hydrated with ORS and eat light food. It usually resolves in a few days.",
    },
    "Acid Reflux (GERD)": {
        "symptoms": {"heartburn": 0.60, "chest_burning": 0.50, "bloating": 0.30, "nausea": 0.20},
        "advice": "Avoid spicy or oily food and late meals; do not lie down right after eating.",
    },
    "Allergic Rhinitis": {
        "symptoms": {"sneezing": 0.50, "itchy_eyes": 0.50, "runny_nose": 0.40, "blocked_nose": 0.30},
        "advice": "Avoid triggers like dust and pollen. An antihistamine may help; ask a pharmacist.",
    },
    "Asthma": {
        "symptoms": {"wheezing": 0.60, "shortness_of_breath": 0.50, "chest_tightness": 0.50, "cough": 0.30},
        "advice": "Use your prescribed inhaler if you have one. Get checked by a doctor if you do not have a diagnosis.",
    },
    "Urinary Tract Infection": {
        "symptoms": {"burning_urination": 0.65, "frequent_urination": 0.50, "lower_abdominal_pain": 0.40, "fever": 0.15},
        "advice": "Drink plenty of water and see a doctor for a urine test; antibiotics need a prescription.",
    },
    "Strep Throat / Tonsillitis": {
        "symptoms": {"sore_throat": 0.60, "fever": 0.35, "headache": 0.15, "body_ache": 0.15},
        "advice": "See a doctor for a throat swab. Warm saltwater gargles help meanwhile.",
    },
    "Acute Bronchitis": {
        "symptoms": {"productive_cough": 0.60, "cough": 0.30, "fatigue": 0.20, "shortness_of_breath": 0.15, "fever": 0.15},
        "advice": "Rest and fluids. See a doctor if the cough lasts more than 3 weeks or you have breathing trouble.",
    },
    "Hepatitis A (Jaundice)": {
        "symptoms": {"yellow_skin": 0.65, "dark_urine": 0.50, "fatigue": 0.30, "loss_of_appetite": 0.30, "nausea": 0.30, "abdominal_pain": 0.20, "fever": 0.15},
        "advice": "See a doctor for liver function tests. Avoid alcohol and oily food.",
    },
    "Conjunctivitis": {
        "symptoms": {"red_eyes": 0.60, "eye_discharge": 0.50, "itchy_eyes": 0.30},
        "advice": "Do not touch or rub your eyes, wash hands often, and see a doctor if vision is affected.",
    },
}

# ---------------------------------------------------------------------------
# 3. COMPOUND RULES  (multi-premise rules; some create intermediate facts so
#    the engine has to CHAIN: symptoms -> syndrome -> disease)
#    Format: (list_of_premises, conclusion, cf)
# ---------------------------------------------------------------------------
INTERMEDIATE_LABELS = {
    "syndrome:flu_like": "Flu-like syndrome",
    "syndrome:gastro": "Gastrointestinal syndrome",
}

COMPOUND_RULES = [
    # Step 1: symptoms -> intermediate syndromes
    (["fever", "chills", "body_ache"], "syndrome:flu_like", 0.70),
    (["vomiting", "diarrhea", "abdominal_pain"], "syndrome:gastro", 0.70),
    # Step 2: syndromes (+ symptoms) -> diseases  (second round of forward chaining)
    (["syndrome:flu_like", "dry_cough"], "dx:Viral Flu", 0.50),
    (["syndrome:gastro"], "dx:Food Poisoning", 0.40),
    (["syndrome:gastro", "fever"], "dx:Viral Gastroenteritis", 0.40),
    # Direct combinations of symptoms that are stronger together than apart
    (["fever", "rash", "joint_pain"], "dx:Dengue", 0.50),
    (["fever", "eye_pain"], "dx:Dengue", 0.40),
    (["fever", "chills", "sweating"], "dx:Malaria", 0.50),
    (["fever", "loss_of_smell_taste"], "dx:COVID-19", 0.50),
    (["heartburn", "chest_burning"], "dx:Acid Reflux (GERD)", 0.50),
    (["wheezing", "shortness_of_breath"], "dx:Asthma", 0.50),
    (["burning_urination", "frequent_urination"], "dx:Urinary Tract Infection", 0.50),
    (["yellow_skin", "dark_urine"], "dx:Hepatitis A (Jaundice)", 0.50),
]

# ---------------------------------------------------------------------------
# 4. TRIAGE (red-flag) RULES  -> how urgent is this?
# ---------------------------------------------------------------------------
TRIAGE_RULES = [
    (["chest_pain", "shortness_of_breath"], "triage:emergency", 0.90),
    (["fever", "stiff_neck", "light_sensitivity"], "triage:emergency", 0.85),
    (["chest_pain"], "triage:urgent", 0.60),
    (["wheezing", "shortness_of_breath"], "triage:urgent", 0.70),
    (["vomiting", "diarrhea", "dizziness"], "triage:urgent", 0.60),
    (["fever", "rash", "eye_pain"], "triage:urgent", 0.60),
]
