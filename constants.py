import re

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

SLOT_TIMES = {
    1: {"start": "08:00 AM", "end": "09:15 AM"},
    2: {"start": "09:30 AM", "end": "10:45 AM"},
    3: {"start": "11:00 AM", "end": "12:15 PM"},
    4: {"start": "12:30 PM", "end": "01:45 PM"},
    5: {"start": "02:00 PM", "end": "03:15 PM"},
    6: {"start": "03:30 PM", "end": "04:45 PM"},
}

SECTION_PATTERN = re.compile(r'^[A-Z]{2,4}-\d+[A-Z]?$')

# Matches: CS-204, LAB-CS-304, EE1 (104), DLD-LAB-(CS&IT), LB3-107, FIT-307
ROOM_PATTERN = re.compile(r'^(?:LAB-|DLD-LAB-)?(?:[A-Z]{2,3}\d?|EE\d|FIT)(?:\s?\(\d{3}\)|[-]\d{3}|-\(CS&IT\))$')

# A fallback room pattern that is a bit more forgiving for anything that looks like a room code.
# Usually 2-3 letters, maybe a number, a dash or space, and 3 digits.
FALLBACK_ROOM_PATTERN = re.compile(r'^([A-Z]{2,4}\d?[- ]\d{3}|LAB-[A-Z]{2,3}-\d{3}|EE\d \(\d{3}\)|DLD-LAB-\(CS&IT\))$', re.IGNORECASE)
