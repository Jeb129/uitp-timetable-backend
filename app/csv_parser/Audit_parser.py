import os
import time
import logging
import requests

# --- 1. Конфигурация ---
INPUT_FILE = "auth_id.txt"   # Файл с нужными ID аудиторий
ICAL_DIR = "ical_files"      # Куда сохранять .ics файлы
BASE_URL_ICAL = "https://eios.kosgos.ru/api/Rasp"
REQUEST_DELAY = 0.3

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/108.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


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

    logging.info(f"Найдено {len(ids)} ID для скачивания.")
    success_count = 0
    fail_count = 0

    # Основной цикл
    for audit_id in ids:
        url = f"{BASE_URL_ICAL}?idAudLine={audit_id}&iCal=true"
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()

            if not response.content:
                logging.warning(f"Пустой ответ для ID: {audit_id}")
                fail_count += 1
                continue

            # Сохраняем файл
            file_path = os.path.join(ICAL_DIR, f"calendar_{audit_id}.ics")
            with open(file_path, 'wb') as f:
                f.write(response.content)

            success_count += 1
            logging.info(f"Успешно скачан файл для ID {audit_id}")

        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при скачивании ID {audit_id}: {e}")
            fail_count += 1
        finally:
            time.sleep(REQUEST_DELAY)

    logging.info(f"--- Скачивание завершено ---")
    logging.info(f"Успешно: {success_count}, Ошибок: {fail_count}")


# --- Точка входа ---
if __name__ == '__main__':
    download_from_file()
