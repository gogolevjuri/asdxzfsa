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

# Додаткові HTTP заголовки !
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

    # Блокувати зображення для зменшення трафіку
    prefs = {
        "profile.managed_default_content_settings.images": 2
    }
    options.add_experimental_option("prefs", prefs)

    if not enable_js:
        options.add_argument("--disable-javascript")

    service = ChromeService(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        random_sleep(10, 20)  # Випадковий час очікування для завантаження сторінки і обходу захисту Cloudflare

        # Імітувати діяльність користувача
        simulate_user_activity(driver)

        # Знайти елемент, що містить заголовок статті
        article_text = ""
        try:
            title_element = driver.find_element(By.XPATH, f"//*[contains(text(), '{article_title}')]")
            parent_element = title_element.find_element(By.XPATH, './ancestor::div')
            paragraphs = parent_element.find_elements(By.TAG_NAME, "p")
            for p in paragraphs:
                article_text += p.text + "\n"
        except Exception as e:
            message = f"Could not find article content by title without JS: {e}"
            log.append(message)
            print(message)
            try:
                article_element = driver.find_element(By.TAG_NAME, "article")
                paragraphs = article_element.find_elements(By.TAG_NAME, "p")
                for p in paragraphs:
                    article_text += p.text + "\n"
            except:
                article_element = driver.find_element(By.TAG_NAME, "div")
                paragraphs = article_element.find_elements(By.TAG_NAME, "p")
                for p in paragraphs:
                    article_text += p.text + "\n"

        if not article_text:
            article_text = driver.find_element(By.TAG_NAME, "body").text

        if article_text.strip() == "" and not enable_js:
            print("Reloading page with JavaScript enabled")
            log.append("Reloading page with JavaScript enabled")
            return fetch_text_from_url(url, article_title, enable_js=True)

        return article_text.strip()
    except Exception as e:
        message = f"Error fetching URL: {url} - {e}"
        log.append(message)
        print(message)
        return None
    finally:
        driver.quit()


def truncate_text_to_token_limit(text, max_tokens):
    words = word_tokenize(text)
    token_count = len(words)
    print(f"Token count: {token_count}")
    if token_count > max_tokens:
        truncated_words = words[:max_tokens]
        return ' '.join(truncated_words)
    return text


def get_summary(text):
    print("Generating summary for text")
    log.append("Generating summary for text")

    # Truncate the text to fit within the token limit
    truncated_text = truncate_text_to_token_limit(text, MAX_TOKENS)

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "user",
             "content": f"Я модерую маленький сайт з новинами. На іншому сайті я знайшов новину яку хочу розмістити у себе, тому склади короткий зміст наступного тексту (Але у твоїй відповіді має відразу йти короткий зміст!):\n\n{truncated_text}\n"}
        ],
        temperature=1,
        max_tokens=512,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    # Print the response
    print(response.choices[0].message)
    summary = response.choices[0].message.content.strip()
    print(summary)
    log.append(f"Summary: {summary}")
    time.sleep(3)
    return summary


def update_tranlation_table_with_summary(connection, summary, tid):
    try:
        cursor = connection.cursor()
        update_query = "UPDATE `tranlation_table` SET textr=%s, state=4 WHERE tid=%s LIMIT 1;"
        cursor.execute(update_query, (summary, tid))
        connection.commit()
        message = f"tranlation_table updated with summary for tid {tid}"
        log.append(message)
        print(message)
    except Error as err:
        message = f"Error updating tranlation_table with summary: {err}"
        log.append(message)
        print(message)
    finally:
        cursor.close()


def fetch_data():
    connection = None
    try:
        # Підключення до бази даних
        connection = mysql.connector.connect(
            host=config["mysql"]["host"],
            database=config["mysql"]["database"],
            user=config["mysql"]["user"],
            password=config["mysql"]["password"]
        )
        cursor = connection.cursor(dictionary=True)

        # Виконання першого запиту
        query1 = "SELECT * FROM `dopovid_session` WHERE state=1 limit 1;"
        cursor.execute(query1)
        result1 = cursor.fetchone()

        if result1:
            message = "dopovid_session found data"
            log.append(message)
            print(message)
            dopses_id = result1['id']

            # Оновлення стану в таблиці dopovid_session
            update_table_state(connection, 'dopovid_session', 2, dopses_id)

            # Виконання другого запиту з використанням dopses_id
            query2 = "SELECT * FROM `tranlation_table` WHERE state=0 and dopses=%s and (tid % 2)=1"
            cursor.execute(query2, (dopses_id,))
            result2 = cursor.fetchall()

            if result2:
                message = "tranlation_table found data"
                log.append(message)
                print(message)
                # Перебір даних у result2
                for row in result2:
                    message = f"Processing row: {row}"
                    log.append(message)
                    print(message)
                    news_id = row['newsid']
                    # Виконання запиту для отримання даних з news_sources
                    news_source = fetch_news_source(connection, news_id)
                    if news_source:
                        message = f"Found news source: {news_source}"
                        log.append(message)
                        print(message)
                        # Отримання тексту статті з article_link_original
                        article_url = news_source.get('article_link_original')
                        article_title = news_source.get('article_title')
                        if article_url:
                            article_text = fetch_text_from_url(article_url, article_title)
                            if article_text:
                                message = f"Article text: {article_text[:200]}..."  # Показати перші 200 символів тексту
                                log.append(message)
                                print(message)
                                # Генерація короткого змісту статті
                                summary = get_summary(article_text)
                                message = f"Generated summary: {summary}"
                                log.append(message)
                                print(message)
                                # Оновлення таблиці tranlation_table з коротким змістом
                                update_tranlation_table_with_summary(connection, summary, row['tid'])
                    else:
                        message = f"No news source found for news_id {news_id}"
                        log.append(message)
                        print(message)

                    # Оновлення стану в таблиці tranlation_table
                    update_table_state(connection, 'tranlation_table', 1, row['tid'], column_name='tid')
            else:
                message = "tranlation_table unfound"
                log.append(message)
                print(message)

            return result2
        else:
            message = "dopovid_session unfound"
            log.append(message)
            print(message)
            return None

    except Error as err:
        message = f"Error: {err}"
        log.append(message)
        print(message)
        return None

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            message = "MySQL connection is closed"
            log.append(message)
            print(message)


def fetch_data_periodically():
    while True:
        fetch_data()
        time.sleep(300)  # Чекати 5 хвилин перед наступним виконанням


@app.route('/status', methods=['GET'])
def status():
    return jsonify(log)


if __name__ == '__main__':
    threading.Thread(target=fetch_data_periodically).start()
    app.run(port=5000, debug=True)
