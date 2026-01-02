import csv
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from ics import Calendar, Event

BASE = Path("C:/Dienstplan")

TIME_REGEX = re.compile(r"(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})")

MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12
}

def parse_date(text):
    parts = text.replace(",", "").split()
    day = int(parts[1].replace(".", ""))
    month = MONTHS[parts[2]]
    year = datetime.now().year
    return datetime(year, month, day)

def find_time(row):
    joined = " ".join(row)
    m = TIME_REGEX.search(joined)
    if not m:
        return None, None
    return m.group(1), m.group(2)

def build_calendar(person):
    folder = BASE / person
    cal = Calendar()

    current_date = None
    last_event = None
    last_begin = None
    last_end = None

    for csv_file in sorted(folder.glob("*.csv")):
        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # Header überspringen

            for row in reader:
                if not row:
                    continue

                if row[0].strip():
                    current_date = parse_date(row[0])

                if not current_date:
                    continue

                start, end = find_time(row)
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

                name = row[1].strip() if len(row) > 1 and row[1].strip() else "Dienst"
                location = row[3].strip() if len(row) > 3 else ""

                # 🔹 NUR KAI: zusammenhängende Dienste am selben Tag zusammenführen
                if (
                    person == "kai"
                    and last_event
                    and last_begin
                    and last_end
                    and begin.date() == last_begin.date()
                    and begin <= last_end
                    and finish > last_end
                ):
                    last_event.end = finish
                    last_end = finish
                    continue

                e = Event()
                e.name = name
                e.begin = begin
                e.end = finish
                e.location = location

                cal.events.add(e)

                last_event = e
                last_begin = begin
                last_end = finish

    ics_path = folder / "dienstplan.ics"
    ics_path.write_text(str(cal), encoding="utf-8")

    # 🔧 dæly-Fix: UTC-Z entfernen
    text = ics_path.read_text(encoding="utf-8")
    text = text.replace("Z", "")
    ics_path.write_text(text, encoding="utf-8")

def git_push():
    subprocess.run(["git", "add", "."], cwd=BASE, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Automatisches Dienstplan-Update"],
        cwd=BASE,
        check=False
    )
    subprocess.run(["git", "push"], cwd=BASE, check=True)

if __name__ == "__main__":
    build_calendar("kai")
    build_calendar("isa")
    git_push()
