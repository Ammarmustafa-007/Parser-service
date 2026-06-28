import io
import pdfplumber
from constants import DAYS, SLOT_TIMES, SECTION_PATTERN
from cell_parser import parse_cell

def parse(pdf_bytes):
    slots = []
    
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            if not tables:
                continue
                
            table = tables[0]
            
            # Row 0 is day headers, Row 1 is slot headers
            # Data starts from row 2
            for r_idx in range(2, len(table)):
                row = table[r_idx]
                section_name = row[0]
                
                # Check if it's a valid section row
                if not section_name or not str(section_name).strip():
                    continue
                    
                section_name = str(section_name).strip()
                if not SECTION_PATTERN.match(section_name):
                    continue
                
                # We have 36 columns (1 to 36)
                # Ensure row has enough columns
                num_cols = min(36, len(row) - 1)
                
                for c_idx in range(1, num_cols + 1):
                    cell_text = row[c_idx]
                    
                    # Calculate day and slot number
                    # col 1 -> day 0 (Monday), slot 1
                    # col 2 -> day 0 (Monday), slot 2
                    day_idx = (c_idx - 1) // 6
                    slot_number = (c_idx - 1) % 6 + 1
                    
                    if day_idx >= len(DAYS):
                        continue
                        
                    day_name = DAYS[day_idx]
                    
                    # Parse cell text
                    cell_data = parse_cell(cell_text)
                    
                    if not cell_data:
                        # Empty cell
                        slots.append({
                            "section": section_name,
                            "day": day_name,
                            "slot": slot_number,
                            "start_time": SLOT_TIMES[slot_number]["start"],
                            "end_time": SLOT_TIMES[slot_number]["end"],
                            "subject": None,
                            "teacher": None,
                            "room": None,
                            "type": "free",
                            "col_span": 1,
                            "needs_review": False,
                            "cell_text": None
                        })
                    else:
                        # Detect col_span for labs
                        # If the current slot is a lab/extended, and the next cell is empty
                        col_span = 1
                        if cell_data["type"] in ["lab", "extended"]:
                            # Look ahead to next cell in the SAME DAY
                            if slot_number < 6 and c_idx + 1 < len(row):
                                next_cell = row[c_idx + 1]
                                if not next_cell or not str(next_cell).strip():
                                    col_span = 2
                        
                        slots.append({
                            "section": section_name,
                            "day": day_name,
                            "slot": slot_number,
                            "start_time": SLOT_TIMES[slot_number]["start"],
                            "end_time": SLOT_TIMES[slot_number + col_span - 1]["end"] if slot_number + col_span - 1 <= 6 else SLOT_TIMES[6]["end"],
                            "subject": cell_data["subject"],
                            "teacher": cell_data["teacher"],
                            "room": cell_data["room"],
                            "type": cell_data["type"],
                            "col_span": col_span,
                            "needs_review": cell_data["needs_review"],
                            "cell_text": cell_data["cell_text"]
                        })
                        
    return slots
