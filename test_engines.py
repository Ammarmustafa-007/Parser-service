import json
from engines import pdfplumber_engine
from formatter import format_hierarchical

with open("../uol-timetable.pdf", "rb") as f:
    pdf_bytes = f.read()

print("Testing pdfplumber...")
p_slots = pdfplumber_engine.parse(pdf_bytes)
print(f"PDFPlumber slots: {len(p_slots)}")
print(f"Free slots: {sum(1 for s in p_slots if s['type'] == 'free')}")

print("\nTesting Formatter (with pdfplumber slots)...")
hierarchical = format_hierarchical(p_slots)
print("Keys in formatted JSON:", hierarchical.keys())
print("Total semesters:", len(hierarchical.get('semesters', [])))

with open("test_output.json", "w") as f:
    json.dump(hierarchical, f, indent=2)
print("Saved to test_output.json")
