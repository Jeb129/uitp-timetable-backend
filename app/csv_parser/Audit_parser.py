import os
import time
import logging
import requests
import json
from icalendar import Calendar
from datetime import datetime
import pytz

# --- 1. Конфигурация ---
INPUT_FILE = "auth_id.txt"   # Файл с нужными ID аудиторий
ICAL_DIR = "../events/ical_files"      # Куда сохранять .ics файлы
JSON_DIR = "../events/lessons"
BASE_URL_ICAL = "https://eios.kosgos.ru/api/Rasp"
REQUEST_DELAY = 0.3
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/108.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
def ics_to_fullcalendar_json(eios_aud_id):
    with open(f'{ICAL_DIR}/{eios_aud_id}.ics', 'rb') as f:
        cal = Calendar.from_ical(f.read())

    events = []

    for component in cal.walk():
        if component.name == "VEVENT":
            summary = str(component.get('summary'))
            dtstart = component.get('dtstart').dt
            dtend = component.get('dtend').dt

            # Приведение типов к строке ISO формата, FullCalendar это любит
            if isinstance(dtstart, datetime):
                dtstart = dtstart.astimezone(pytz.UTC).isoformat()
            else:  # если это дата без времени
                dtstart = datetime(dtstart.year, dtstart.month, dtstart.day).isoformat()

            if isinstance(dtend, datetime):
                dtend = dtend.astimezone(pytz.UTC).isoformat()
            else:
                dtend = datetime(dtend.year, dtend.month, dtend.day).isoformat()

            events.append({
                "title": summary,
                "start": dtstart,
                "end": dtend
            })

    with open(f'{JSON_DIR}/{eios_aud_id}.json', 'w', encoding='utf-8') as jf:
        json.dump(events, jf, indent=4, ensure_ascii=False)

def get_aud_ics(eios_aud_id):
    response = requests.get(
                            f"{BASE_URL_ICAL}?idAudLine={eios_aud_id}&iCal=true",
                                headers=HEADERS, 
                                timeout=15
                                )
    response.raise_for_status()

    if not response.content:
        return False
    else:
        file_path = os.path.join(ICAL_DIR, f"{eios_aud_id}.ics")
        with open(file_path, 'wb') as f:
            f.write(response.content)
        return True

def download_from_file():
    """Скачивает .ics файлы только для ID, указанных в auth_id.txt."""
    logging.info(f"Загрузка списка ID из {INPUT_FILE}...")

    # Проверяем, что файл существует
    if not os.path.exists(INPUT_FILE):
        logging.error(f"Файл {INPUT_FILE} не найден!")
        return

    # Читаем ID из файла
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        ids = [line.strip() for line in f if line.strip().isdigit()]

    if not ids:
        logging.warning("Файл auth_id.txt пуст или не содержит корректных ID.")
        return

    # Создаём директорию для сохранения, если нужно
    if not os.path.exists(ICAL_DIR):
        os.makedirs(ICAL_DIR)
    if not os.path.exists(JSON_DIR):
        os.makedirs(JSON_DIR)

    logging.info(f"Найдено {len(ids)} ID для скачивания.")
    success_count = 0
    fail_count = 0

    # Основной цикл
    for audit_id in ids:
        try:
            if get_aud_ics(audit_id):
                logging.info(f"Успешно скачан файл для ID {audit_id}")
                ics_to_fullcalendar_json(audit_id)
                logging.info(f'Расписание для аудитории {audit_id} сохранено в json')
            else:
                logging.warning(f"Пустой ответ для ID: {audit_id}")
                fail_count += 1            

        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при скачивании ID {audit_id}: {e}")
            fail_count += 1
        finally:
            time.sleep(REQUEST_DELAY)

    logging.info(f"--- Скачивание завершено ---")
    logging.info(f"Успешно: {success_count}, Ошибок: {fail_count}")

download_from_file()