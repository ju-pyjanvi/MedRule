# MedRule ✚

**A symptom-based triage and differential diagnosis expert system.**

Type your symptoms in plain English, and MedRule ranks the likely conditions with a certainty score, flags dangerous symptom combinations, and shows exactly which rules produced every answer. It is modelled on **MYCIN**, the classic medical expert system, and built as an AI course project.

> **Disclaimer:** MedRule is an educational project. The rule values are hand-picked estimates, not clinically validated. It is not medical advice. See a doctor for real symptoms.

<!-- Add a screenshot or GIF here: ![MedRule demo](docs/demo.gif) -->

**Live demo:** _add your Render link here_

---

## What it does

- **Understands everyday language.** "high temperature, body pain and chills" becomes Fever, Body ache and Chills. It handles synonyms, spelling mistakes ("headdache") and negation ("no fever" is ignored).
- **Reasons under uncertainty.** Overlapping symptoms give a ranked list of conditions instead of a single yes or no.
- **Flags red flags.** Combinations like chest pain with shortness of breath trigger an emergency warning, separate from the diagnosis ranking.
- **Explains itself.** Click any diagnosis to see the exact rules that fired and the arithmetic behind the score.
- **Lets you watch the AI think.** The Inference Lab replays forward chaining one rule at a time while working memory updates live.

## How it works

MedRule follows the textbook expert system architecture:

| Component | Where it lives |
|---|---|
| Knowledge base (18 diseases, 42 symptoms, 118 IF-THEN rules) | `knowledge_base.py` / `kb.js` |
| Working memory (facts and their certainty factors) | `wm` in the inference engine |
| Inference engine (forward chaining) | `engine.py` / `engine.js` |
| Explanation module ("why this diagnosis?") | `Result.explain()` / `explain()` |
| Text preprocessor (synonyms, spelling repair, negation, TF-IDF) | `SymptomMatcher` in `engine.py`, `parse()` in `engine.js` |

The knowledge base holds all the medical facts and the engine holds none, so you can add a disease by editing data without touching the logic.

### Forward chaining

Each cycle the engine finds every rule whose premises are all in working memory, fires them, and adds the conclusions. New facts can enable more rules in the next cycle. It stops when nothing new can fire. For example, fever + chills + body ache first derives a *flu-like syndrome*, which then lets the Viral Flu rule fire in cycle 2.

### Certainty factors (MYCIN method)

```
contribution     = rule CF × min(CF of its premises)
combined CF      = old + contribution × (1 − old)
```

Worked example (fever, chills, body ache and dry cough, each at 0.8): Viral Flu reaches **0.88**.

Note that these scores are **certainty factors, not probabilities.** 88% means the entered evidence strongly supports the conclusion according to the rules, not that 88 in 100 people with these symptoms have flu.

## Syllabus mapping

| Topic | Where it shows up |
|---|---|
| Unit II: rule-based knowledge representation | 118 IF-THEN production rules stored as data |
| Unit II: text feature extraction, TF-IDF | Symptom matcher (TF-IDF fallback is in the Python version) |
| Unit III: handling uncertainty | MYCIN certainty factors |
| Unit IV: expert system architecture, MYCIN case study | Whole system, including the explanation module |
| Unit IV: applications in medical sciences, ethics in AI | Domain, red-flag triage, disclaimers |

## Pages

- **Consult:** describe symptoms in text or tap them by body region, set how sure you are, and run the diagnosis.
- **Knowledge base:** browse every rule by condition, with certainty bars and a symptom-overlap highlighter.
- **Inference lab:** step through forward chaining with live working memory.
- **How it works:** the architecture and the maths.

## Run it locally

Requires Python 3.9 or newer. There is nothing to install because MedRule uses only the standard library.

```bash
git clone https://github.com/ju-pyjanvi/MedRule.git
cd MedRule
python app.py
```

It opens `http://127.0.0.1:8000/index.html` in your browser.

**Terminal version** (no browser needed):

```bash
python cli.py
```

Try `high temperature, body pain and chills, dry cough`, then type `why 1` to see the explanation.

## Deploy on Render

1. Push this repo to GitHub with `requirements.txt` at the root.
2. Create a new **Web Service** on Render and connect the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `python app.py`

`app.py` reads Render's `PORT` variable automatically. Since the frontend runs fully in the browser, you can also deploy it as a free **Static Site** with no build command.

## Try these inputs

| Input | What it shows |
|---|---|
| `high temperature, body pain and chills, dry cough` | Synonym matching and two-cycle chaining. Viral Flu ranks first |
| `fever, pain behind eyes, joint pain, skin rash` | Compound rules. Dengue ranks first |
| `severe headdache and feel nauseus, sensitive to light, no fever` | Spelling repair and negation. Migraine ranks first |
| `cant breathe, pain in chest` | Red-flag triage. Emergency banner appears |

## Project structure

```
MedRule/
├── app.py              # Python web server (standard library only)
├── engine.py           # Inference engine, explanation, text preprocessor
├── knowledge_base.py   # Diseases, symptoms, synonyms, rules
├── cli.py              # Terminal version
├── requirements.txt
├── index.html          # Consult page
├── knowledge.html      # Knowledge base browser
├── lab.html            # Inference lab
├── about.html          # Architecture and syllabus
├── style.css
├── common.js           # Shared header, pulse line, footer
├── engine.js           # JavaScript port of the engine
└── kb.js               # JavaScript copy of the knowledge base
```

`engine.js` and `kb.js` mirror the Python files so the site works entirely in the browser. If you change `knowledge_base.py`, update `kb.js` too so both versions stay identical.

## Limitations

- Rule values are hand-written estimates, not clinically validated.
- Only positive evidence is modelled, so a missing symptom never lowers a score.
- Certainty factor combination assumes symptoms are independent, which is not always true.
- Covers 18 conditions and cannot learn from new cases.

## Future work

- Learn rule weights from a labelled dataset (decision tree or naive Bayes).
- Add negative evidence and MYCIN-style follow-up questions.
- Validate the rules with a medical professional.

## Credits

Inspired by the MYCIN expert system (Shortliffe and Buchanan, Stanford). Built by Janvi as an AI course project.
