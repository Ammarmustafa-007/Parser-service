import json

with open('parsed_timetable.json', 'r') as f:
    data = json.load(f)

rooms = set()
for sem in data.get('data', {}).get('semesters', []):
    for sec, days in sem.get('timetable', {}).items():
        for day, slots in days.items():
            for slot in slots:
                if slot.get('room'):
                    rooms.add(slot.get('room'))
for r in sorted(list(rooms)):
    print(r)
