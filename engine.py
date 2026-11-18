"""
MedRule - INFERENCE ENGINE, WORKING MEMORY, EXPLANATION MODULE, TEXT PREPROCESSOR
Pure Python (standard library only).

Expert-system components (Unit IV, MYCIN architecture):
  * Knowledge Base      -> knowledge_base.py
  * Working Memory      -> the `wm` dict: fact -> certainty factor
  * Inference Engine    -> InferenceEngine.run()  (forward chaining)
  * Explanation Module  -> Result.explain() / Result.trace_text()
  * Uncertainty (Unit III) -> MYCIN certainty factors (combine())
  * Text pre-processing (Unit II) -> SymptomMatcher (synonyms + TF-IDF + spell fix)
"""
import difflib
import math
import re
from dataclasses import dataclass

from knowledge_base import (COMPOUND_RULES, DISEASES, INTERMEDIATE_LABELS,
                            SYMPTOMS, TRIAGE_RULES)

CERTAINTY_LEVELS = {"Slightly": 0.4, "Probably": 0.7, "Definitely": 1.0}
THRESHOLD = 0.20   # diagnoses below this certainty are not shown
TRIAGE_CUTOFF = 0.50


def label(fact):
    """Human readable name of any fact."""
    if fact.startswith("dx:"):
        return fact[3:]
    if fact.startswith("triage:"):
        return "TRIAGE = " + fact[7:].upper()
    if fact in SYMPTOMS:
        return SYMPTOMS[fact]["label"]
    return INTERMEDIATE_LABELS.get(fact, fact)


# ===========================================================================
# RULES
# ===========================================================================
@dataclass
class Rule:
    id: str
    premises: list
    conclusion: str
    cf: float

    def text(self):
        lhs = " AND ".join(label(p) for p in self.premises)
        return f"IF {lhs} THEN {label(self.conclusion)}  [rule CF = {self.cf:.2f}]"


def build_rules():
    """Turn the knowledge base data into a flat list of production rules."""
    rules = []
    for disease, info in DISEASES.items():
        for symptom, cf in info["symptoms"].items():
            rules.append(Rule(f"R{len(rules) + 1}", [symptom], f"dx:{disease}", cf))
    for premises, conclusion, cf in COMPOUND_RULES + TRIAGE_RULES:
        rules.append(Rule(f"R{len(rules) + 1}", premises, conclusion, cf))
    return rules


# ===========================================================================
# UNCERTAINTY  (Unit III) - MYCIN certainty factors
# ===========================================================================
def combine(cf_old, cf_new):
    """Combine two positive CFs that support the same conclusion.
    CF = old + new * (1 - old).  Result always stays below 1 and never decreases."""
    return cf_old + cf_new * (1 - cf_old)


@dataclass
class TraceStep:
    cycle: int
    rule: Rule
    premise_cfs: dict
    contribution: float   # rule CF x min(premise CFs)
    before: float         # CF of the conclusion before this rule (None if new)
    after: float          # CF of the conclusion after combining


class Result:
    def __init__(self, wm, trace, cycles, rules):
        self.wm = wm
        self.trace = trace
        self.cycles = cycles
        self.rules = rules

    def diagnoses(self):
        """Ranked list of (disease, certainty) at or above THRESHOLD."""
        found = [(f[3:], cf) for f, cf in self.wm.items() if f.startswith("dx:") and cf >= THRESHOLD]
        return sorted(found, key=lambda x: -x[1])

    def triage(self):
        """Return ('emergency' | 'urgent' | 'routine', cf)."""
        for level in ("emergency", "urgent"):
            cf = self.wm.get(f"triage:{level}", 0)
            if cf >= TRIAGE_CUTOFF:
                return level, cf
        return "routine", 0.0

    def explain(self, disease):
        """EXPLANATION MODULE: the exact rules that fired for one diagnosis."""
        steps = [s for s in self.trace if s.rule.conclusion == f"dx:{disease}"]
        if not steps:
            return f"No rule fired for {disease}."
        lines = [f"WHY {disease.upper()}?  (final certainty {self.wm[f'dx:{disease}']:.2f})", ""]
        for i, s in enumerate(steps, 1):
            prem = ", ".join(f"{label(p)} ({cf:.2f})" for p, cf in s.premise_cfs.items())
            lines.append(f"{i}. {s.rule.id}: {s.rule.text()}")
            lines.append(f"     evidence: {prem}")
            lines.append(f"     contribution = {s.rule.cf:.2f} x {min(s.premise_cfs.values()):.2f} = {s.contribution:.3f}")
            if s.before is None:
                lines.append(f"     running certainty: {s.after:.3f}")
            else:
                lines.append(f"     combine: {s.before:.3f} + {s.contribution:.3f} x (1 - {s.before:.3f}) = {s.after:.3f}")
        return "\n".join(lines)

    def trace_text(self):
        """Full inference trace, cycle by cycle."""
        if not self.trace:
            return "No rules fired."
        lines, current = [], 0
        for s in self.trace:
            if s.cycle != current:
                current = s.cycle
                lines.append(f"--- Forward-chaining cycle {current} ---")
            lines.append(f"{s.rule.id} fired: {s.rule.text()}")
            lines.append(f"     {label(s.rule.conclusion)}: {0 if s.before is None else s.before:.3f} -> {s.after:.3f}")
        return "\n".join(lines)


# ===========================================================================
# INFERENCE ENGINE  (forward chaining)
# ===========================================================================
class InferenceEngine:
    def __init__(self):
        self.rules = build_rules()

    def run(self, symptoms):
        """symptoms: {symptom_id: certainty 0..1}  ->  Result.

        Forward chaining (match -> fire -> repeat): in each cycle, find all rules
        whose premises are ALL present in working memory, fire them, and add their
        conclusions to working memory. New facts may enable more rules in the next
        cycle. Stop when no new rule can fire. Each rule fires at most once.
        """
        wm = dict(symptoms)           # WORKING MEMORY
        fired, trace, cycle = set(), [], 0
        while True:
            cycle += 1
            # MATCH: find every unfired rule whose premises are all in working memory
            snapshot = dict(wm)
            conflict_set = [r for r in self.rules
                            if r.id not in fired and all(p in snapshot for p in r.premises)]
            if not conflict_set:
                break
            # FIRE: execute them all, update working memory
            for rule in conflict_set:
                fired.add(rule.id)
                premise_cfs = {p: snapshot[p] for p in rule.premises}
                # MYCIN: a rule is only as certain as its weakest premise
                contribution = rule.cf * min(premise_cfs.values())
                before = wm.get(rule.conclusion)
                after = contribution if before is None else combine(before, contribution)
                wm[rule.conclusion] = after
                trace.append(TraceStep(cycle, rule, premise_cfs, contribution, before, after))
        return Result(wm, trace, cycle - 1, self.rules)


# ===========================================================================
# TEXT PRE-PROCESSOR  (Unit II: TF-IDF / text feature extraction)
#   1. exact phrase / synonym match (longest phrase first)
#   2. spell correction of unknown words (difflib)
#   3. TF-IDF cosine similarity as fallback for unfamiliar wording
# ===========================================================================
STOPWORDS = {"i", "a", "an", "the", "my", "is", "am", "are", "have", "has", "had", "feel", "feeling",
             "in", "on", "of", "to", "and", "with", "very", "since", "from", "also", "got", "been",
             "me", "it", "its", "for", "at", "when", "while", "be", "having", "getting", "bit"}
NEGATIONS = {"no", "not", "without", "never", "dont", "don't", "denies", "nothing"}
INTENSIFIERS = {"severe", "very", "extreme", "terrible", "intense", "high", "bad", "worst", "definitely"}
HEDGES = {"slight", "slightly", "mild", "little", "maybe", "minor", "occasional", "bit", "possibly"}


def _tokens(text):
    return [t for t in re.findall(r"[a-z']+", text.lower()) if t not in STOPWORDS]


class SymptomMatcher:
    def __init__(self):
        self.phrases = []                      # (phrase, symptom_id)
        self.docs = {}                         # symptom_id -> token list
        for sid, info in SYMPTOMS.items():
            names = [info["label"].lower()] + info["synonyms"]
            for p in names:
                self.phrases.append((p, sid))
            self.docs[sid] = [t for p in names for t in _tokens(p)]
        self.phrases.sort(key=lambda x: -len(x[0]))        # longest first
        self.vocab = sorted({t for doc in self.docs.values() for t in doc})
        n = len(self.docs)
        df = {}
        for doc in self.docs.values():
            for t in set(doc):
                df[t] = df.get(t, 0) + 1
        self.idf = {t: math.log((n + 1) / (df[t] + 1)) + 1 for t in df}
        self.doc_vecs = {sid: self._vec(doc) for sid, doc in self.docs.items()}

    def _vec(self, tokens):
        tf = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        return {t: c * self.idf.get(t, 1.0) for t, c in tf.items()}

    @staticmethod
    def _cosine(a, b):
        dot = sum(v * b.get(t, 0) for t, v in a.items())
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        return dot / (na * nb) if na and nb else 0.0

    def _spell_fix(self, chunk):
        words, fixed = chunk.split(), []
        for w in words:
            bare = re.sub(r"[^a-z']", "", w)
            if len(bare) > 3 and bare not in self.vocab and bare not in STOPWORDS \
                    and bare not in INTENSIFIERS and bare not in HEDGES and bare not in NEGATIONS:
                m = difflib.get_close_matches(bare, self.vocab, n=1, cutoff=0.8)
                fixed.append(m[0] if m else w)
            else:
                fixed.append(w)
        return " ".join(fixed)

    def _phrase_match(self, chunk):
        found = []
        for phrase, sid in self.phrases:
            pat = r"\b" + re.escape(phrase) + r"\b"
            if re.search(pat, chunk):
                found.append((sid, phrase))
                chunk = re.sub(pat, " ", chunk)      # consume so shorter phrases cannot re-match
        return found

    def extract(self, text):
        """Return (matches, negated).
        matches: list of dicts {symptom, cf, how, heard}
        negated: list of chunks skipped because the patient said they do NOT have it."""
        matches, negated = [], []
        for chunk in re.split(r"[,.;\n]| and | but | also ", text.lower()):
            chunk = chunk.strip()
            if not chunk:
                continue
            words = set(re.findall(r"[a-z']+", chunk))
            if words & NEGATIONS:
                negated.append(chunk)
                continue
            cf = 1.0 if words & INTENSIFIERS else 0.5 if words & HEDGES else 0.8

            found = self._phrase_match(chunk)
            how = "synonym match"
            if not found:
                fixed = self._spell_fix(chunk)
                found = self._phrase_match(fixed)
                how = "spelling corrected"
                if not found:
                    qv = self._vec(_tokens(fixed))
                    scores = sorted(((self._cosine(qv, dv), sid) for sid, dv in self.doc_vecs.items()), reverse=True)
                    if scores and scores[0][0] >= 0.45 and (len(scores) < 2 or scores[0][0] > 1.2 * scores[1][0]):
                        found = [(scores[0][1], chunk)]
                        how = f"TF-IDF similarity {scores[0][0]:.2f}"
            for sid, _ in found:
                matches.append({"symptom": sid, "cf": cf, "how": how, "heard": chunk})
        # keep the highest certainty if a symptom is heard twice
        best = {}
        for m in matches:
            if m["symptom"] not in best or m["cf"] > best[m["symptom"]]["cf"]:
                best[m["symptom"]] = m
        return list(best.values()), negated
