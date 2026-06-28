import json

with open('parsed_timetable.json', 'r') as f:
    response = json.load(f)

data = response.get('data', {})
silent_errors = []
total_slots = 0
checked_slots = 0

for sem in data.get('semesters', []):
    for sec, days in sem.get('timetable', {}).items():
        for day, slots in days.items():
            for slot in slots:
                total_slots += 1
                if slot.get('type') == 'free':
                    continue
                
                checked_slots += 1
                subj = slot.get('subject') or ""
                teacher = slot.get('teacher') or ""
                room = slot.get('room') or ""
                
                # Check for silent errors (where needs_review is False but something is likely wrong)
                if not slot.get('needs_review'):
                    issues = []
                    if "Dr." in subj or "Mr." in subj or "Ms." in subj:
                        issues.append("Teacher title found in Subject")
                    if "Lab" in teacher or "LAB" in teacher:
                        issues.append("Lab keyword found in Teacher")
                    if not teacher.strip() and not subj.strip():
                        issues.append("Both subject and teacher are empty")
                    if len(teacher) > 30:
                        issues.append("Teacher name extremely long")
                    if len(subj) > 35:
                        issues.append("Subject name extremely long")
                    if "\n" in teacher or "\n" in subj or "\n" in room:
                        issues.append("Newline character not stripped")
                    if not teacher.strip():
                        issues.append("Teacher name is empty")
                        
                    if issues:
                        silent_errors.append({
                            "section": sec,
                            "day": day,
                            "slot": slot.get('slot'),
                            "issues": issues,
                            "subject": subj,
                            "teacher": teacher,
                            "room": room,
                            "raw": slot.get('cell_text')
                        })

print(f"Total slots: {total_slots}")
print(f"Filled slots checked: {checked_slots}")
print(f"Potential Silent Errors found: {len(silent_errors)}")
for err in silent_errors[:15]:
    print(f"\n[{err['section']} {err['day']} Slot {err['slot']}] Issues: {err['issues']}")
    print(f"Subj: '{err['subject']}' | Teacher: '{err['teacher']}' | Room: '{err['room']}'")
    print(f"Raw: {repr(err['raw'])}")
