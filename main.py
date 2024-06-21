import openai
import time
import json
import threading
import mysql.connector
from mysql.connector import Error
from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import nltk
from nltk.tokenize import word_tokenize
import random

app = Flask(__name__)
log = []

# Завантаження конфігураційного файлу
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

# Встановлення API ключа OpenAI
openai.api_key = config["openai_api_key"]

# Максимальна кількість токенів для повідомлення
MAX_TOKENS = 2048  # Ви можете встановити цей ліміт за потреби

nltk.download('punkt')

# Список проксі
proxies = [
    "",
    ""
]

# Пул User-Agent та відповідних розмірів вікон
user_agents_and_sizes = [
    (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A372 Safari/604.1",
    "375,667"),
    (
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
    "412,915"),
    (
    "Mozilla/5.0 (Linux; Android 9; SM-G960F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
    "360,740"),
    (
    "Mozilla/5.0 (Linux; Android 8.0.0; Pixel 2 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
    "411,823"),
    (
    "Mozilla/5.0 (Linux; Android 7.1.1; Nexus 6P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
    "411,731"),
    (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0 Mobile/15E148 Safari/604.1",
    "375,667"),
    (
    "Mozilla/5.0 (Linux; Android 10; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
    "360,740"),
    (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Mobile/16A366 Safari/604.1",
    "375,667"),
    (
    "Mozilla/5.0 (Linux; Android 9; SAMSUNG SM-J530F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
    "360,640"),
    (
    "Mozilla/5.0 (Linux; Android 10; SAMSUNG SM-N960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
    "360,740")
]

# Додаткові HTTP заголовки
additional_headers = [
    {"accept-language": "en-US,en;q=0.9", "upgrade-insecure-requests": "1", "accept-encoding": "gzip, deflate, br",
     "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
     "cache-control": "max-age=0"},
    {"accept-language": "en-US,en;q=0.8", "upgrade-insecure-requests": "1", "accept-encoding": "gzip, deflate, br",
     "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.7",
     "cache-control": "no-cache"},
    {"accept-language": "en-GB,en;q=0.9", "upgrade-insecure-requests": "1", "accept-encoding": "gzip, deflate, br",
     "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.6",
     "cache-control": "max-age=0"},
    # Додайте більше варіантів заголовків тут
]

def get_random_user_agent_and_size():
    return random.choice(user_agents_and_sizes)

def get_random_headers():
    return random.choice(additional_headers)

def random_sleep(min_seconds, max_seconds):
    time.sleep(random.uniform(min_seconds, max_seconds))

def simulate_user_activity(driver):
    action = ActionChains(driver)
    for _ in range(random.randint(2, 5)):
        action.move_by_offset(random.randint(1, 100), random.randint(1, 100)).perform()
        random_sleep(0.5, 2)
    for _ in range(random.randint(2, 5)):
        action.send_keys(Keys.PAGE_DOWN).perform()
        random_sleep(1, 3)
    for _ in range(random.randint(2, 5)):
        action.send_keys(Keys.PAGE_UP).perform()
        random_sleep(1, 3)
    for _ in range(random.randint(2, 5)):
        action.send_keys(Keys.ARROW_LEFT).perform()
        random_sleep(0.5, 2)
    for _ in range(random.randint(2, 5)):
        action.send_keys(Keys.ARROW_RIGHT).perform()
        random_sleep(0.5, 2)

def update_table_state(connection, table_name, new_state, record_id, column_name='id'):
    try:
        cursor = connection.cursor()
        update_query = f"UPDATE `{table_name}` SET state=%s WHERE {column_name}=%s LIMIT 1;"
        cursor.execute(update_query, (new_state, record_id))
        connection.commit()
        message = f"{table_name} updated successfully"
        log.append(message)
        print(message)
    except Error as err:
        message = f"Error updating {table_name}: {err}"
        log.append(message)
        print(message)
    finally:
        cursor.close()

def fetch_news_source(connection, news_id):
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM `news_sources` WHERE news_id=%s ORDER BY `news_sources`.`article_created_at` DESC LIMIT 1;"
        cursor.execute(query, (news_id,))
        news_source = cursor.fetchone()
        return news_source
    except Error as err:
        message = f"Error fetching news source: {err}"
        log.append(message)
        print(message)
        return None
    finally:
        cursor.close()

def fetch_text_from_url(url, article_title, enable_js=False):
    options = Options()
    options.headless = False  # Використовуйте безголовий режим для автоматизації без відображення браузера
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Отримати випадковий User-Agent і розмір вікна
    user_agent, window_size = get_random_user_agent_and_size()
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument(f"--window-size={window_size}")  # Встановити розмір вікна відповідно до User-Agent

    # Додати додаткові заголовки
    headers = get_random_headers()
    for key, value in headers.items():
        options.add_argument(f"--header={key}: {value}")

    # Встановлення проксі в залежності від User-Agent
    user_agent_index = user_agents_and_sizes.index((user_agent, window_size))
    proxy = proxies[0] if user_agent_index < 5 else proxies[1]
    proxy_host, proxy_port, proxy_user, proxy_pass = proxy.split(':')
    options.add_argument(f"--proxy-server=socks5://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}")

    # Блокувати зображення для зменшення трафіку
    prefs = {
        "profile.managed_default_content_settings.images": 2
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.get(url)

    # Симуляція активності користувача
    simulate_user_activity(driver)

    content = driver.page_source
    driver.quit()
    return content

# Функція для обробки тексту за допомогою ChatGPT
def process_text_with_chatgpt(prompt):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=MAX_TOKENS
        )
        return response.choices[0].text.strip()
    except Exception as e:
        log.append(f"Error with OpenAI API: {e}")
        return None

# Основна функція для обробки новин
def process_news_record(record):
    try:
        connection = mysql.connector.connect(
            host=config["mysql_host"],
            user=config["mysql_user"],
            password=config["mysql_password"],
            database=config["mysql_database"]
        )

        news_id = record['id']
        news_source = fetch_news_source(connection, news_id)
        if news_source:
            article_url = news_source['article_url']
            article_title = news_source['article_title']
            article_content = fetch_text_from_url(article_url, article_title)

            if article_content:
                prompt = f"Title: {article_title}\n\nArticle: {article_content}\n\nSummary:"
                summary = process_text_with_chatgpt(prompt)
                if summary:
                    cursor = connection.cursor()
                    insert_query = """
                    INSERT INTO `news_summaries` (news_id, summary, created_at)
                    VALUES (%s, %s, NOW());
                    """
                    cursor.execute(insert_query, (news_id, summary))
                    connection.commit()
                    update_table_state(connection, 'news', 'processed', news_id)
                    message = f"News ID {news_id} processed successfully"
                    log.append(message)
                    print(message)
                else:
                    update_table_state(connection, 'news', 'error', news_id)
            else:
                update_table_state(connection, 'news', 'error', news_id)
        else:
            update_table_state(connection, 'news', 'error', news_id)
    except Error as err:
        message = f"Error processing news record: {err}"
        log.append(message)
        print(message)
    finally:
        if connection.is_connected():
            connection.close()

# Функція для періодичної перевірки новин у базі даних
def check_news():
    while True:
        try:
            connection = mysql.connector.connect(
                host=config["mysql_host"],
                user=config["mysql_user"],
                password=config["mysql_password"],
                database=config["mysql_database"]
            )
            cursor = connection.cursor(dictionary=True)
            query = "SELECT * FROM `news` WHERE `state`='new';"
            cursor.execute(query)
            records = cursor.fetchall()
            for record in records:
                process_news_record(record)
            cursor.close()
        except Error as err:
            log.append(f"Error connecting to MySQL: {err}")
        finally:
            if connection.is_connected():
                connection.close()
        time.sleep(300)  # Перевірка кожні 5 хвилин

# Запуск Flask-сервера для відображення статусу та журналу
@app.route('/status', methods=['GET'])
def get_status():
    return jsonify(log)

if __name__ == '__main__':
    threading.Thread(target=check_news).start()
    app.run(host='0.0.0.0', port=5000)
