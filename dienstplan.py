import csv
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from ics import Calendar, Event

PERSON = sys.argv[1].lower()

BASE = Path("C:/Dienstplan") / PERSON
CSV_FILE = BASE / "dienstplan.csv"
ICS_FILE = BASE / "dienstplan.ics"

YEAR = 2026

MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12
}

TIME_REGEX = re.compile(r"(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})")

def parse_date(text):
    parts = text.replace(",", "").split()
    day = int(parts[1].replace(".", ""))
    month = MONTHS[parts[2]]
    return datetime(YEAR, month, day)

def find_time_in_row(row):
    joined = " ".join(row)
    m = TIME_REGEX.search(joined)
    if not m:
        return None, None
    return m.group(1), m.group(2)

cal = Calendar()

current_date = None
last_event = None
last_end = None

with open(CSV_FILE, newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader, None)

    for row in reader:
        if not row:
            continue

        if row[0].strip():
            current_date = parse_date(row[0])

        if not current_date:
            continue

        start, end = find_time_in_row(row)
        if not start or not end:
            continue

        begin = datetime.combine(
            current_date.date(),
            datetime.strptime(start, "%H:%M").time()
        )

        finish = datetime.combine(
            current_date.date(),
            datetime.strptime(end, "%H:%M").time()
        )

        if finish <= begin:
            finish += timedelta(days=1)

        dienst = row[1].strip() if len(row) > 1 and row[1].strip() else "Dienst"
        ort = row[3].strip() if len(row) > 3 else ""

        if PERSON == "kai" and last_event and last_end:
            if begin <= last_end and finish > last_end:
                last_event.end = finish
                last_end = finish
                continue

        e = Event()
        e.name = dienst
        e.begin = begin
        e.end = finish
        e.location = ort

        cal.events.add(e)
        last_event = e
        last_end = finish

# --- Schreiben ---
with open(ICS_FILE, "w", encoding="utf-8") as f:
    f.writelines(cal)

# --- POST-FIX: UTC -> lokale Zeit erzwingen ---
text = ICS_FILE.read_text(encoding="utf-8")
text = text.replace("DTSTART:", "DTSTART:")
text = text.replace("DTEND:", "DTEND:")
text = text.replace("Z", "")
ICS_FILE.write_text(text, encoding="utf-8")
