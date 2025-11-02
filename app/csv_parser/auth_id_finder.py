import os
import time
import logging
import requests

# --- 1. Конфигурация ---
OUTPUT_FILE = "auth_id.txt"  # Файл для записи ID аудиторий с "Б"
BASE_URL_ICAL = "https://eios.kosgos.ru/api/Rasp"
START_ID = 3115136
END_ID = 3130000
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


def download_schedule_ids():
    """
    Проверяет расписания по ID и записывает в файл только те ID,
    где есть аудитория с 'Б', но нет 'Б1' в LOCATION.
    """
    logging.info("Начинается поиск аудиторий с 'Б' (без 'Б1') в названии...")

    success_count = 0
    skipped_count = 0

    for audit_id in range(START_ID, END_ID + 1):
        url = f"{BASE_URL_ICAL}?idAudLine={audit_id}&iCal=true"
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()

            if not response.content:
                logging.warning(f"Пустой ответ для ID: {audit_id}")
                continue

            text_content = response.content.decode('utf-8', errors='ignore')

            if "LOCATION:Б1" in text_content:
                skipped_count += 1
                logging.info(f"Пропущен ID {audit_id} — содержит 'Б1' в LOCATION")
                continue

            # Фильтр: должно быть "LOCATION:Б", но не "LOCATION:Б1"
            if "LOCATION:Б" not in text_content:
                skipped_count += 1
                logging.info(f"Пропущен ID {audit_id} — нет 'Б' в LOCATION")
                continue


            # Записываем ID в файл
            with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{audit_id}\n")

            success_count += 1
            logging.info(f"Добавлен ID {audit_id} — найдено 'Б', без 'Б1'")

        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при запросе ID {audit_id}: {e}")
            continue
        finally:
            time.sleep(REQUEST_DELAY)

    logging.info(f"--- Проверка завершена ---")
    logging.info(f"Найдено {success_count} аудиторий с 'Б' (без 'Б1'). Пропущено {skipped_count}.")
    logging.info(f"Результаты сохранены в: {OUTPUT_FILE}")


# --- Точка входа ---
if __name__ == '__main__':
    download_schedule_ids()
