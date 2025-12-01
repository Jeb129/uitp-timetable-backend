import os
import time
import logging
import requests
import json
from icalendar import Calendar
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import threading

# --- 1. Конфигурация ---
INPUT_FILE = "events/auth_id.txt"   # Файл с нужными ID аудиторий
UPDATE_DELAY = 0.05 # интервал обновления в часах

STATUS_FILE = "events/update_status.json"
ICAL_DIR = "events/ical_files"      # Куда сохранять .ics файлы
JSON_DIR = "events/lessons"
BASE_URL_ICAL = "https://eios.kosgos.ru/api/Rasp"
REQUEST_DELAY = 0.3
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/108.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}
LOCAL_TIMEZONE = 'Europe/Moscow'
WEEKDAYS_RU = {
    0: "Понедельник", 1: "Вторник", 2: "Среда", 3: "Четверг",
    4: "Пятница", 5: "Суббота", 6: "Воскресенье"
}


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Потокобезопасная блокировка для предотвращения одновременного запуска обновлений
update_lock = threading.Lock()
check_lock = threading.Lock()

# Загрузка расписания
def ics_to_fullcalendar_json(eios_aud_id):
    '''Преобразует ics файл выбранной аудитории в json для отображения в fullcalendar'''
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
    '''Запрашивает ics файл для выбранной аудитории'''
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

def update_audit_rasp(eios_aud_id):
    '''Скачивает расписание занятий выбранной аудитории из eios и сохраняет в json'''
    # Создаём директории для сохранения, если нужно
    if not os.path.exists(ICAL_DIR):
        os.makedirs(ICAL_DIR)
    if not os.path.exists(JSON_DIR):
        os.makedirs(JSON_DIR)

    try:
        if get_aud_ics(eios_aud_id):
            #logging.info(f"Успешно скачан ics файл для ID {eios_aud_id}")
            ics_to_fullcalendar_json(eios_aud_id)
            #logging.info(f'{eios_aud_id}.ics сохранено в json')
            return True
        else:
            logging.warning(f"Пустой ответ для ID: {eios_aud_id}")
            return False         

    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при скачивании ID {eios_aud_id}: {e}")
        return False

# Функции-помощники для управления состоянием 
def read_status():
    """Читает статус последнего обновления из JSON-файла."""
    if not os.path.exists(STATUS_FILE):
        return {}
    try:
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def write_status(data):
    """Записывает новый статус обновления в JSON-файл."""
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def read_aud_ids():
    '''Читаем список id аудиторий'''
     # Проверяем, что файл существует
    if not os.path.exists(INPUT_FILE):
        return

    # Читаем ID из файла
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        ids = [line.strip() for line in f if line.strip().isdigit()]
    return ids if ids else []

# Автообновление
def get_website_update_date(eios_aud_id):
    """Получает дату последнего обновления расписания с сайта через API."""
    try:
        response = requests.get(f"{BASE_URL_ICAL}?idAudLine={eios_aud_id}", headers=HEADERS, timeout=20)
        response.raise_for_status()
        data = response.json()
        update_date_str = data.get("data", {}).get("info", {}).get("dateUploadingRasp")
        if update_date_str:
            return update_date_str
        else:
            return None
    except Exception as e:
        return None

def check_updates(audit_ids):
    '''Проверка обновлений'''
    now = datetime.now()
    update_status = read_status()
    updates = []

    for id in audit_ids:
        logging.info(f"Проверяем id {id}...")
        local_request_str = update_status.get(id)
        if not local_request_str:
            updates.append(id)
            logging.info(f"Нет локальных данных.")
            continue # Если локальной информации нет - запрашиваем из eios

        try:
            local_request_dt = datetime.fromisoformat(local_request_str)
            if now - local_request_dt < timedelta(hours=UPDATE_DELAY):
                # logging.info(f"Информация обновлялась {local_request_str}. Запрос к eios не требуется")
                continue

            logging.info(f"Проверка даты обновления через API...")
            remote_update_str = get_website_update_date(id)

            # if remote_update_str:
            #     logging.info(f"Найдена дата в API: {remote_update_str}")
            # else:
            #     logging.error(f"Ошибка при получении даты с сайта:")

            if isinstance(remote_update_str, datetime):
                remote_update_str = remote_update_str.isoformat()
            remote_update_dt = datetime.fromisoformat(remote_update_str)

            if remote_update_dt < local_request_dt:
                # logging.info(f"Расписание не обновилось на портале. Обновление не требуется")
                continue
            # else:
            #     logging.info(f"Расписание обновилось на портале. Требуется обновление")
            updates.append(id)
        except ValueError:
            #logging.info(f"Ошибка при сравнении дат. Требуется обновление")
            updates.append(id)
            continue # В случае ошибки чтения обновляем информацию
    return updates if len(updates) > 0 else None
       
def maina():
    # Проверяем не запущенно ли обновление?
    if update_lock.locked():
        logging.info("Обновление уже запущено")
        return
    
    logging.info(f"Загрузка списка ID из {INPUT_FILE}...")

    ids = read_aud_ids()
    if not ids:
        logging.warning("Файл auth_id.txt не найден")
        return
    elif len(ids) == 0:
        logging.warning("Файл auth_id.txt пуст или не содержит корректных ID.")
        return
    
    logging.info(f"Поиск обновлений...")
    updatable_ids = check_updates(ids)

    if not updatable_ids:
        logging.info(f"Обновление не требуется")
        return
    
    logging.info(f"Требуется обновить {len(updatable_ids)} аудиторий")
    with update_lock:
        logging.info("НАЧАЛО ОБНОВЛЕНИЯ РАСПИСАНИЯ ")
        update_status = read_status()
        success_count = 0
        fail_count = 0

        # Основной цикл
        for audit_id in ids:
            if update_audit_rasp(audit_id):
                update_status[audit_id] = datetime.now().isoformat()
                write_status(update_status)
                success_count += 1
            else:
                fail_count += 1
            time.sleep(REQUEST_DELAY)
        logging.info("ОБНОВЛЕНИЕ РАСПИСАНИЯ ЗАВЕРШЕНО ")
        logging.info(f"Успешно: {success_count}, Ошибок: {fail_count}")

def task():
    logging.info("Запуск в режиме автоматической проверки обновлений...")
    scheduler = BackgroundScheduler(timezone=LOCAL_TIMEZONE)
    scheduler.add_job(maina, 'interval', hours=UPDATE_DELAY, misfire_grace_time=600)
    scheduler.start()
    logging.info(f"Планировщик запущен. Проверка будет выполняться каждые {UPDATE_DELAY} часа.")
    print("Скрипт работает в фоновом режиме. Нажмите Ctrl+C для выхода.")
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logging.info("Планировщик остановлен. Программа завершена.")

# Вот эту функцию нужно повесить в фон запускать.
# Пока не очень понятно будем мы это контролировать через flask сервер или запускать отдельно, поэтому оставил так
maina()
# Запуск в фоне (не через сервер)
task()

    
