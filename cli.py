"""MedRule - terminal version (use this if Streamlit is blocked).   Run:  python cli.py"""
from engine import InferenceEngine, SymptomMatcher, label
from knowledge_base import DISEASES

engine, matcher = InferenceEngine(), SymptomMatcher()
print("MedRule - educational expert system. Not medical advice.")
print("Type your symptoms in plain English. Commands: why <number>, trace, new, quit\n")

result, ranked = None, []
while True:
    text = input("symptoms / command > ").strip()
    low = text.lower()
    if low in ("quit", "exit"):
        break
    if low == "trace" and result:
        print(result.trace_text()); continue
    if low.startswith("why") and result:
        try:
            print(result.explain(ranked[int(low.split()[1]) - 1][0]))
        except (IndexError, ValueError):
            print("Use: why 1")
        continue
    matches, negated = matcher.extract(text)
    if not matches:
        print("Could not recognise any symptom. Try different wording.\n"); continue
    print("\nUnderstood:")
    for m in matches:
        print(f"  '{m['heard']}' -> {label(m['symptom'])} (certainty {m['cf']}, {m['how']})")
    if negated:
        print("  Ignored negations:", "; ".join(negated))
    result = engine.run({m["symptom"]: m["cf"] for m in matches})
    level, tcf = result.triage()
    if level != "routine":
        print(f"\n*** {level.upper()} warning signs (certainty {tcf:.2f}). Seek medical help. ***")
    ranked = result.diagnoses()
    print("\nRanked diagnoses:")
    for i, (d, cf) in enumerate(ranked, 1):
        print(f"  {i}. {d:<28} {cf:5.0%}  {'#' * int(cf * 30)}")
    if ranked:
        print("\nAdvice:", DISEASES[ranked[0][0]]["advice"])
    print("\n(type 'why 1' for the explanation, 'trace' for all rules fired)\n")
