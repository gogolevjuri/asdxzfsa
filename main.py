import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

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
        action.move_by_offset(random.randint(-100, 100), random.randint(-100, 100)).perform()
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
