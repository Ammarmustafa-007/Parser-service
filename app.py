from flask import Flask, request, jsonify
from flask_cors import CORS
from engines import pdfplumber_engine, camelot_engine
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
        if 'pdf' not in request.files:
            return jsonify({"error": "No pdf file provided"}), 400
            
        pdf_bytes = request.files['pdf'].read()
        
        flat_slots = pdfplumber_engine.parse(pdf_bytes)
        summary = summarize_slots(flat_slots)
        hierarchical_data = format_hierarchical(flat_slots)
        
        return jsonify({
            "engine": "pdfplumber",
            "summary": summary,
            "data": hierarchical_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/parse/camelot', methods=['POST'])
def parse_camelot():
    try:
        if 'pdf' not in request.files:
            return jsonify({"error": "No pdf file provided"}), 400
            
        pdf_bytes = request.files['pdf'].read()
        
        flat_slots, accuracy_scores = camelot_engine.parse(pdf_bytes)
        summary = summarize_slots(flat_slots)
        hierarchical_data = format_hierarchical(flat_slots)
        
        return jsonify({
            "engine": "camelot",
            "accuracy_scores": accuracy_scores,
            "average_accuracy": sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0,
            "summary": summary,
            "data": hierarchical_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/parse/compare', methods=['POST'])
def parse_compare():
    try:
        if 'pdf' not in request.files:
            return jsonify({"error": "No pdf file provided"}), 400
            
        pdf_bytes = request.files['pdf'].read()
        
        # Run pdfplumber
        plumber_flat = pdfplumber_engine.parse(pdf_bytes)
        plumber_summary = summarize_slots(plumber_flat)
        
        # Run camelot
        camelot_flat, accuracy = camelot_engine.parse(pdf_bytes)
        camelot_summary = summarize_slots(camelot_flat)
        
        # Simple diffing
        mismatched = []
        # Create dictionaries mapped by section-day-slot
        plumber_dict = {f"{s['section']}-{s['day']}-{s['slot']}": s for s in plumber_flat}
        camelot_dict = {f"{s['section']}-{s['day']}-{s['slot']}": s for s in camelot_flat}
        
        all_keys = set(plumber_dict.keys()).union(set(camelot_dict.keys()))
        
        for key in all_keys:
            p_slot = plumber_dict.get(key)
            c_slot = camelot_dict.get(key)
            
            if not p_slot or not c_slot:
                mismatched.append({"key": key, "issue": "Missing in one engine", "pdfplumber": p_slot, "camelot": c_slot})
                continue
                
            # Compare cell text
            if p_slot.get("cell_text") != c_slot.get("cell_text"):
                mismatched.append({
                    "key": key, 
                    "issue": "Cell text mismatch", 
                    "pdfplumber": p_slot.get("cell_text"), 
                    "camelot": c_slot.get("cell_text")
                })
        
        return jsonify({
            "pdfplumber": {
                "summary": plumber_summary,
            },
            "camelot": {
                "summary": camelot_summary,
                "average_accuracy": sum(accuracy) / len(accuracy) if accuracy else 0
            },
            "diff": {
                "total_slots_match": plumber_summary["total_slots"] == camelot_summary["total_slots"],
                "mismatched_cells": len(mismatched),
                "mismatched_details": mismatched[:50] # Limit to 50
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "parser", "engines": ["pdfplumber", "camelot"]})

if __name__ == '__main__':
    app.run(port=5000, debug=True)
