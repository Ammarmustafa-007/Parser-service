import time

from flask import Flask, request, jsonify
from flask_cors import CORS
from engines import pdfplumber_engine
from formatter import format_hierarchical

app = Flask(__name__)
app.json.sort_keys = False
CORS(app, origins=["http://localhost:3001", "http://localhost:3000", "http://localhost:3002"])

def summarize_slots(flat_slots):
    return {
        "total_slots": len(flat_slots),
        "filled_slots": sum(1 for s in flat_slots if not s.get("type") == "free"),
        "free_slots": sum(1 for s in flat_slots if s.get("type") == "free"),
        "lab_slots": sum(1 for s in flat_slots if s.get("type") == "lab"),
        "lecture_slots": sum(1 for s in flat_slots if s.get("type") == "lecture"),
        "extended_slots": sum(1 for s in flat_slots if s.get("type") == "extended"),
        "needs_review_count": sum(1 for s in flat_slots if s.get("needs_review")),
        "sections_found": sorted(list(set(s.get("section") for s in flat_slots if s.get("section"))))
    }

@app.route('/parse/pdfplumber', methods=['POST'])
def parse_pdfplumber():
    try:
        started_at = time.perf_counter()
        if 'pdf' not in request.files:
            return jsonify({"error": "No pdf file provided"}), 400
            
        read_started_at = time.perf_counter()
        pdf_bytes = request.files['pdf'].read()
        read_seconds = time.perf_counter() - read_started_at

        parse_started_at = time.perf_counter()
        flat_slots = pdfplumber_engine.parse(pdf_bytes)
        parse_seconds = time.perf_counter() - parse_started_at

        format_started_at = time.perf_counter()
        summary = summarize_slots(flat_slots)
        hierarchical_data = format_hierarchical(flat_slots)
        format_seconds = time.perf_counter() - format_started_at
        total_seconds = time.perf_counter() - started_at
        
        return jsonify({
            "engine": "pdfplumber",
            "summary": summary,
            "data": hierarchical_data,
            "timings": {
                "read_seconds": round(read_seconds, 3),
                "parse_seconds": round(parse_seconds, 3),
                "format_seconds": round(format_seconds, 3),
                "total_seconds": round(total_seconds, 3)
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "parser", "engines": ["pdfplumber"]})

if __name__ == '__main__':
    app.run(port=5000, debug=True)
