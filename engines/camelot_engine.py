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
            for r_idx in range(2, len(grid)):
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
                        
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    return slots, accuracy_scores
