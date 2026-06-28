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
            dynamic_times = {}
            time_row_idx = None
            for r in range(1, min(4, len(table))):
                time_matches = sum(1 for c in table[r] if c and ":" in str(c))
                if time_matches >= 4:
                    time_row_idx = r
                    break
            
            if time_row_idx is not None:
                for c_idx in range(1, min(37, len(table[time_row_idx]))):
                    cell_text = str(table[time_row_idx][c_idx]).strip()
                    if ":" in cell_text:
                        day_idx = (c_idx - 1) // 6
                        slot_number = (c_idx - 1) % 6 + 1
                        lines = [line.strip() for line in cell_text.replace('\r', '\n').split('\n') if line.strip()]
                        time_lines = [line for line in lines if ":" in line]
                        if len(time_lines) >= 2:
                            dynamic_times[(day_idx, slot_number)] = {"start": time_lines[0], "end": time_lines[-1]}
                        elif len(time_lines) == 1:
                            parts = time_lines[0].replace('-', ' ').split()
                            if len(parts) >= 2:
                                dynamic_times[(day_idx, slot_number)] = {"start": parts[0], "end": parts[-1]}
            for r_idx in range(2, len(table)):
                if r_idx == time_row_idx:
                    continue
                    
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
                        start_time = SLOT_TIMES[slot_number]["start"]
                        end_time = SLOT_TIMES[slot_number]["end"]
                        if (day_idx, slot_number) in dynamic_times:
                            start_time = dynamic_times[(day_idx, slot_number)]["start"]
                            end_time = dynamic_times[(day_idx, slot_number)]["end"]
                            
                        # Empty cell
                        slots.append({
                            "section": section_name,
                            "day": day_name,
                            "slot": slot_number,
                            "start_time": start_time,
                            "end_time": end_time,
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
                        
                        start_time = SLOT_TIMES[slot_number]["start"]
                        if (day_idx, slot_number) in dynamic_times:
                            start_time = dynamic_times[(day_idx, slot_number)]["start"]
                            
                        end_slot = slot_number + col_span - 1
                        if end_slot > 6:
                            end_slot = 6
                            
                        end_time = SLOT_TIMES[end_slot]["end"]
                        if (day_idx, end_slot) in dynamic_times:
                            end_time = dynamic_times[(day_idx, end_slot)]["end"]
                        
                        slots.append({
                            "section": section_name,
                            "day": day_name,
                            "slot": slot_number,
                            "start_time": start_time,
                            "end_time": end_time,
                            "subject": cell_data["subject"],
                            "teacher": cell_data["teacher"],
                            "room": cell_data["room"],
                            "type": cell_data["type"],
                            "col_span": col_span,
                            "needs_review": cell_data["needs_review"],
                            "cell_text": cell_data["cell_text"]
                        })
                        
    return slots
