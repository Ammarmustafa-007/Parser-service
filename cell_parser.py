import re
from constants import ROOM_PATTERN, FALLBACK_ROOM_PATTERN

def join_broken_lines(lines):
    if not lines:
        return []
    
    joined = [lines[0].strip()]
    for i in range(1, len(lines)):
        line = lines[i].strip()
        if not line:
            continue
            
        prev = joined[-1]
        
        # Conditions to join:
        # 1. Starts with a lowercase letter (e.g. "b" for "Tayyab")
        # 2. Starts with "(" (e.g. "(LAB)" for "Phy (LAB)")
        # 3. Is a single character (e.g. "1")
        if (line and line[0].islower()) or line.startswith('(') or len(line) == 1:
            joined[-1] = f"{prev}{line}"
        else:
            joined.append(line)
            
    return joined

def parse_cell(cell_text):
    if not cell_text or not str(cell_text).strip():
        return None
        
    raw_lines = str(cell_text).split('\n')
    lines = join_broken_lines(raw_lines)
    
    room = None
    subject = None
    teacher = None
    needs_review = False
    
    # 1. Detect Room
    room_idx = -1
    for i, line in enumerate(lines):
        if ROOM_PATTERN.match(line) or FALLBACK_ROOM_PATTERN.match(line):
            room = line
            room_idx = i
            
            # Combine multi-line room names only for "Electrical\nMachine Lab\nEE1 (104)"
            if i >= 1 and "Machine Lab" in lines[i-1]:
                room = lines[i-1] + " " + room
                lines[i] = room
                lines.pop(i-1)
                room_idx = i - 1
                if room_idx >= 1 and "Electrical" in lines[room_idx-1]:
                    room = lines[room_idx-1] + " " + room
                    lines[room_idx] = room
                    lines.pop(room_idx-1)
                    room_idx = room_idx - 1
            break
            
    # If no room found, try looser search
    if room_idx == -1:
        for i, line in enumerate(lines):
            if "LAB" in line or "CS-" in line or "EE" in line or "FIT-" in line or "LB" in line:
                room = line
                room_idx = i
                break
                
    if room_idx == -1:
        needs_review = True
    
    # 2. Split Subject and Teacher
    remaining_lines = [l for i, l in enumerate(lines) if i != room_idx]
    
    if len(remaining_lines) == 2:
        if room_idx == 0:
            # Format A: Room, Subject, Teacher
            subject = remaining_lines[0]
            teacher = remaining_lines[1]
        elif room_idx == len(lines) - 1:
            # Format B: Teacher, Subject, Room
            teacher = remaining_lines[0]
            subject = remaining_lines[1]
        else:
            # Room in middle? Ambiguous
            subject = remaining_lines[0]
            teacher = remaining_lines[1]
            needs_review = True
            
    elif len(remaining_lines) > 2:
        if room_idx == 0:
            # Format A: Room, Subject, Teacher (Teacher split)
            subject = remaining_lines[0]
            teacher = " ".join(remaining_lines[1:])
        elif room_idx == len(lines) - 1:
            # Format B: Teacher, Subject, Room (Teacher split)
            subject = remaining_lines[-1]
            teacher = " ".join(remaining_lines[:-1])
        else:
            subject = remaining_lines[0]
            teacher = " ".join(remaining_lines[1:])
            needs_review = True
            
    elif len(remaining_lines) == 1:
        subject = remaining_lines[0]
        teacher = ""
        needs_review = True
    else:
        subject = ""
        teacher = ""
        needs_review = True
        
    # Col_span detection is done by the engine by checking the adjacent cell,
    # but we can detect type here
    slot_type = "lecture"
    if subject and ("Lab" in subject or "LAB" in subject or "lab" in subject):
        slot_type = "lab"
    elif subject and "2hr" in subject:
        slot_type = "extended"
        
    return {
        "room": room,
        "subject": subject,
        "teacher": teacher,
        "type": slot_type,
        "needs_review": needs_review,
        "cell_text": str(cell_text)
    }
