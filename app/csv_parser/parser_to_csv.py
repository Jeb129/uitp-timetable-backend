import os
import csv
from datetime import datetime
import re

# --- Конфигурация ---
ICAL_DIR = "ical_files"       # папка, где лежат .ics файлы
OUTPUT_CSV = "university_schedule.csv"


def parse_event(lines):
    """Парсит одно событие между BEGIN:VEVENT и END:VEVENT."""
    event = {}
    for line in lines:
        line = line.strip()

        if line.startswith("SUMMARY:"):
            event["summary"] = line.replace("SUMMARY:", "").strip()

        elif line.startswith("DTSTART:"):
            event["start"] = line.split(":")[1].strip()

        elif line.startswith("DTEND:"):
            event["end"] = line.split(":")[1].strip()

        elif line.startswith("LOCATION:"):
            event["location"] = line.replace("LOCATION:", "").strip()

        elif line.startswith("DESCRIPTION:"):
            event["description"] = line.replace("DESCRIPTION:", "").strip()

    return event


def parse_ics_file(file_path):
    """Извлекает все события из .ics файла."""
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    events = []
    inside_event = False
    buffer = []

    for line in lines:
        line = line.strip()
        if line == "BEGIN:VEVENT":
            inside_event = True
            buffer = []
        elif line == "END:VEVENT":
            inside_event = False
            event = parse_event(buffer)
            if event:
                events.append(event)
        elif inside_event:
            buffer.append(line)

    return events


def format_datetime(dt_str):
    """
    Преобразует строки вида 20251020T071000Z в дату и время.
    Возвращает (дата, время).
    """
    try:
        dt = datetime.strptime(dt_str, "%Y%m%dT%H%M%SZ")
        date = dt.strftime("%Y-%m-%d")
        time = dt.strftime("%H:%M")
        return date, time
    except Exception:
        return None, None


def extract_details(summary, description):
    """
    Извлекает из SUMMARY и DESCRIPTION предмет, тип занятия, преподавателя и группу.
    Пример SUMMARY: "лаб Живопись"
    Пример DESCRIPTION: "Преподаватель Еремин В.Е., группа: 21-ДИбо-5"
    """
    # Тип и предмет
    if summary:
        parts = summary.split(" ", 1)
        if len(parts) == 2:
            lesson_type, subject = parts
        else:
            lesson_type, subject = "", summary
    else:
        lesson_type, subject = "", ""

    # Преподаватель и группа
    teacher, group = "", ""
    if description:
        teacher_match = re.search(r"Преподаватель\s([^,]+)", description)
        group_match = re.search(r"группа:\s*([\w\-А-Яа-я]+)", description)
        if teacher_match:
            teacher = teacher_match.group(1).strip()
        if group_match:
            group = group_match.group(1).strip()

    return lesson_type, subject, teacher, group


def main():
    all_events = []

    for filename in os.listdir(ICAL_DIR):
        if filename.endswith(".ics"):
            file_path = os.path.join(ICAL_DIR, filename)
            events = parse_ics_file(file_path)
            all_events.extend(events)

    # --- Создаем CSV ---
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "date", "day", "start_time", "end_time",
            "type", "subject", "teacher", "location", "group"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for e in all_events:
            start_date, start_time = format_datetime(e.get("start", ""))
            _, end_time = format_datetime(e.get("end", ""))
            lesson_type, subject, teacher, group = extract_details(
                e.get("summary", ""), e.get("description", "")
            )

            # Определяем день недели (понедельник, вторник и т.д.)
            day_name = ""
            if start_date:
                day_name = datetime.strptime(start_date, "%Y-%m-%d").strftime("%A")
                days_ru = {
                    "Monday": "Понедельник",
                    "Tuesday": "Вторник",
                    "Wednesday": "Среда",
                    "Thursday": "Четверг",
                    "Friday": "Пятница",
                    "Saturday": "Суббота",
                    "Sunday": "Воскресенье"
                }
                day_name = days_ru.get(day_name, day_name)

            writer.writerow({
                "date": start_date or "",
                "day": day_name,
                "start_time": start_time or "",
                "end_time": end_time or "",
                "type": lesson_type,
                "subject": subject,
                "teacher": teacher,
                "location": e.get("location", ""),
                "group": group
            })

    print(f"✅ Готово! Сохранено {len(all_events)} записей в {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
