"""
MedRule - Pure Python Web Server (Standard Library Only)
Serves the HTML/CSS/JS frontend and runs the Python InferenceEngine & SymptomMatcher.
Run with:  python app.py
"""
import json
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from engine import InferenceEngine, SymptomMatcher, label
from knowledge_base import DISEASES

PORT = 8000
engine = InferenceEngine()
matcher = SymptomMatcher()


class MedRuleHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/api/diagnose":
            self.send_error(404, "Not found")
            return

        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        text = payload.get("text", "")
        picked = payload.get("picked", {})  # {symptom_id: cf}

        matches, negated = matcher.extract(text) if text.strip() else ([], [])
        symptoms = {m["symptom"]: m["cf"] for m in matches}
        for sym_id, cf in picked.items():
            symptoms[sym_id] = max(float(cf), symptoms.get(sym_id, 0.0))

        result = engine.run(symptoms)
        level, tcf = result.triage()
        ranked = result.diagnoses()

        response = {
            "matches": [
                {**m, "label": label(m["symptom"])} for m in matches
            ],
            "negated": negated,
            "triage": {"level": level, "cf": tcf},
            "cycles": result.cycles,
            "rules_fired": len(result.trace),
            "diagnoses": [
                {
                    "disease": d,
                    "cf": cf,
                    "advice": DISEASES[d]["advice"],
                    "explanation": result.explain(d),
                }
                for d, cf in ranked
            ],
            "trace_text": result.trace_text(),
        }

        body = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Clean terminal output during viva demo
        print(f"[MedRule] {args[0]}")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), MedRuleHandler)
    url = f"http://127.0.0.1:{PORT}/index.html"
    print(f"MedRule running at {url}  (Press Ctrl+C to stop)")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")