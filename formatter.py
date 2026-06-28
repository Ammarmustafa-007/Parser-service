import re
from constants import SLOT_TIMES, DAYS

def parse_section_info(section_name):
    """Extracts program, semester, and section letter from a string like BSCS-1A"""
    # Default values
    program = "Unknown"
    semester = 0
    section_letter = ""
    
    # Try to match patterns like BSCS-1A, BSIT-2B
    match = re.match(r'^([A-Z]{2,4})-(\d+)([A-Z]?)$', section_name)
    if match:
        program = match.group(1)
        semester = int(match.group(2))
        section_letter = match.group(3)
    else:
        # Fallback if pattern is weird but has a dash
        parts = section_name.split('-')
        if len(parts) >= 2:
            program = parts[0]
            # Try to get number and letter from second part
            sub_match = re.match(r'^(\d+)([A-Z]?)$', parts[1])
            if sub_match:
                semester = int(sub_match.group(1))
                section_letter = sub_match.group(2)
            else:
                section_letter = parts[1]
                
    return program, semester, section_letter

def format_hierarchical(flat_slots):
    """
    Groups flat slots into:
    program -> semesters -> sections -> day -> [6 slots]
    """
    programs_map = {}
    
    # 1. Group by program, semester, section, day
    for slot in flat_slots:
        section_name = slot.get('section', 'Unknown')
        day = slot.get('day')
        slot_number = slot.get('slot')
        
        program, semester, section_letter = parse_section_info(section_name)
        
        if program not in programs_map:
            programs_map[program] = {}
            
        if semester not in programs_map[program]:
            programs_map[program][semester] = {}
            
        if section_name not in programs_map[program][semester]:
            programs_map[program][semester][section_name] = {d: [None]*6 for d in DAYS}
            
        # Insert slot into the array (0-indexed)
        if day in programs_map[program][semester][section_name] and 1 <= slot_number <= 6:
            programs_map[program][semester][section_name][day][slot_number - 1] = slot

    # 2. Build the final JSON structure
    # We will assume one main program for the root level, or just return an array of programs if multiple.
    # The user's requested JSON starts with "program": "BSCS", so we'll structure it like that.
    
    # Let's find the primary program (the one with the most slots)
    if not programs_map:
        return {}
        
    primary_program = max(programs_map.keys(), key=lambda p: sum(len(s) for s in programs_map[p].values()))
    
    result = {
        "program": primary_program,
        "university": "University of Lahore",
        "slot_times": SLOT_TIMES,
        "semesters": []
    }
    
    for semester_num, sections_dict in sorted(programs_map[primary_program].items()):
        semester_obj = {
            "semester_number": semester_num,
            "sections": sorted(list(sections_dict.keys())),
            "timetable": {}
        }
        
        for section_name, days_dict in sorted(sections_dict.items()):
            semester_obj["timetable"][section_name] = {}
            for day in DAYS:
                day_slots = days_dict[day]
                # Ensure no None values in the array, replace with free slots if missing
                cleaned_slots = []
                for i in range(6):
                    if day_slots[i] is None:
                        # Create an empty free slot
                        cleaned_slots.append({
                            "slot": i + 1,
                            "start_time": SLOT_TIMES[i+1]["start"],
                            "end_time": SLOT_TIMES[i+1]["end"],
                            "subject": None,
                            "teacher": None,
                            "room": None,
                            "type": "free",
                            "col_span": 1,
                            "needs_review": False,
                            "cell_text": None
                        })
                    else:
                        cleaned_slots.append(day_slots[i])
                        
                semester_obj["timetable"][section_name][day] = cleaned_slots
                
        result["semesters"].append(semester_obj)
        
    return result
