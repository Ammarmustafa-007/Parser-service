import tempfile
import os
import camelot
from constants import DAYS, SLOT_TIMES, SECTION_PATTERN
from cell_parser import parse_cell

def parse(pdf_bytes):
    slots = []
    accuracy_scores = []
    
    # Camelot needs a file path, so we save bytes to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(pdf_bytes)
        temp_path = temp_pdf.name
        
    try:
        # Run camelot in lattice mode
        tables = camelot.read_pdf(temp_path, flavor='lattice', pages='all')
        
        for page_idx, table in enumerate(tables):
            # Capture accuracy
            accuracy_scores.append(table.accuracy)
            
            # Convert to list of lists (pandas dataframe to 2D list)
            grid = table.df.values.tolist()
            
            # Row 0 is day headers, Row 1 is slot headers
            dynamic_times = {}
            time_row_idx = None
            for r in range(1, min(4, len(grid))):
                time_matches = sum(1 for c in grid[r] if c and ":" in str(c))
                if time_matches >= 4:
                    time_row_idx = r
                    break
            
            if time_row_idx is not None:
                for c_idx in range(1, min(37, len(grid[time_row_idx]))):
                    cell_text = str(grid[time_row_idx][c_idx]).strip()
                    if ":" in cell_text:
                        day_idx = (c_idx - 1) // 6
                        slot_number = (c_idx - 1) % 6 + 1
                        lines = [line.strip() for line in cell_text.replace('\r', '\n').split('\n') if line.strip()]
                        if len(lines) >= 2:
                            dynamic_times[(day_idx, slot_number)] = {"start": lines[0], "end": lines[-1]}
                        else:
                            parts = cell_text.replace('-', ' ').split()
                            if len(parts) >= 2:
                                dynamic_times[(day_idx, slot_number)] = {"start": parts[0], "end": parts[-1]}

            for r_idx in range(2, len(grid)):
                if r_idx == time_row_idx:
                    continue
                    
                row = grid[r_idx]
                section_name = row[0]
                
                # Check if it's a valid section row
                if not section_name or not str(section_name).strip():
                    continue
                    
                section_name = str(section_name).strip()
                if not SECTION_PATTERN.match(section_name):
                    continue
                    
                # We have 36 columns (1 to 36)
                num_cols = min(36, len(row) - 1)
                
                for c_idx in range(1, num_cols + 1):
                    cell_text = row[c_idx]
                    
                    # Calculate day and slot number
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
                        
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    return slots, accuracy_scores
