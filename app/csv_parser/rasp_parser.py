import os
import time
import logging
import requests

# --- 1. Конфигурация ---
# Директория для сохранения скачанных .ics файлов
ICAL_DIR = "ical_files"
# Базовый URL для запроса расписания
BASE_URL_ICAL = "https://eios.kosgos.ru/api/Rasp"
# Диапазон ID групп для скачивания
START_ID = 8149
END_ID = 8515
# Задержка между запросами в секундах, чтобы не перегружать сервер
REQUEST_DELAY = 0.5
# Заголовки для HTTP-запроса
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

# Настройка логирования для вывода информации о процессе в консоль
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def download_schedule_files():
    """
    Скачивает файлы расписания в формате .ics для заданного диапазона ID групп.
    Перед началом нового скачивания очищает папку назначения.
    """
    logging.info("Начинается скачивание .ics файлов расписания...")

    # Создаем директорию, если она не существует
    if not os.path.exists(ICAL_DIR):
        os.makedirs(ICAL_DIR)
        logging.info(f"Создана директория: {ICAL_DIR}")

    # Очищаем директорию от старых файлов
    logging.info(f"Очистка директории {ICAL_DIR}...")
    for f in os.listdir(ICAL_DIR):
        os.remove(os.path.join(ICAL_DIR, f))

    success_count = 0
    # Проходим по всем ID групп в указанном диапазоне
    for group_id in range(START_ID, END_ID + 1):
        url = f"{BASE_URL_ICAL}?idGroup={group_id}&iCal=true"
        try:
            # Выполняем GET-запрос
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()  # Проверяем, успешен ли запрос

            # Пропускаем, если ответ пустой
            if not response.content:
                logging.warning(f"Получен пустой ответ для ID группы: {group_id}")
                continue

            # Сохраняем содержимое в файл
            file_path = os.path.join(ICAL_DIR, f"calendar_{group_id}.ics")
            with open(file_path, 'wb') as f:
                f.write(response.content)

            success_count += 1
            logging.info(f"Успешно скачан файл для ID группы: {group_id}")

        except requests.exceptions.RequestException as e:
            # Логируем ошибку, если запрос не удался
            logging.error(f"Ошибка при скачивании для ID группы {group_id}: {e}")
            continue
        finally:
            # Делаем паузу между запросами
            time.sleep(REQUEST_DELAY)

    logging.info(f"--- Скачивание завершено ---")
    logging.info(f"Всего загружено {success_count} файлов.")


# --- Точка входа в скрипт ---
if __name__ == '__main__':
    # При запуске скрипта сразу вызывается функция скачивания
    download_schedule_files()