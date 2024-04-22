import csv
import os
import time

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth

URL = "https://www.nseindia.com/"


def parse_table(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    """
    Парсит таблицу и выводит данные в csv файл

    :param driver: драйвер для имитации поведения пользователя в браузере Chrome
    :param wait: экземпляр класса WebDriverWait для ожидания загрузки элементов
    :return: None
    """
    action = ActionChains(driver)

    driver.get(URL)

    # Локатор дропдаун меню для наведения
    MARKET_DATA_LOCATOR = ("css selector", "#link_2")
    # Элемент для перехода к таблице
    PRE_OPEN_MARKET_LOCATOR = ("css selector", "div.d-none.d-sm-block"
                                               " a[href='/market-data/pre-open-market-cm-and-emerge-market']")
    # Локатор столбца таблицы с именем (SYMBOL)
    SYMBOLS_LOCATOR = ("css selector", "a.symbol-word-break")
    # Локатор столбца с ценой (FINAL)
    FINAL_PRICES_LOCATOR = ("css selector", "tr td.bold")

    market_data = driver.find_element(*MARKET_DATA_LOCATOR)
    pre_open_market = driver.find_element(*PRE_OPEN_MARKET_LOCATOR)

    action.move_to_element(market_data). \
        click(pre_open_market). \
        perform()

    # Ждём пока таблица не подгрузится
    wait.until(EC.presence_of_element_located(SYMBOLS_LOCATOR))

    symbols = driver.find_elements(*SYMBOLS_LOCATOR)
    final_prices = driver.find_elements(*FINAL_PRICES_LOCATOR)
    # Собираем данные в массив кортежей
    data = list(map(lambda x: (x[0].text, x[1].text.replace(",", "")), zip(symbols, final_prices)))

    # Записываем в csv файл
    with open(os.getcwd() + "\data.csv", "w+") as file:
        writer = csv.writer(file, delimiter=';', lineterminator='\n')
        writer.writerow(["SYMBOL", "FINAL"])
        writer.writerows(data)


def imitate_human(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    """
    Имитация поведения пользователя в браузере

    :param driver: драйвер для имитации поведения пользователя в браузере Chrome
    :param wait: экземпляр класса WebDriverWait для ожидания загрузки элементов
    :return: None
    """
    driver.get(URL)

    # Локатор элемента, при клике на который открывается нужный график
    # NIFTY_BANK_P_LOCATOR = ("xpath", "//p[@id='NIFTY BANK']")
    NIFTY_BANK_P_LOCATOR = ("css selector", "#NIFTY\ BANK")
    # Локатор ссылки для перехода к таблице. День ото дня меняется ссылка, поэтому 2 локатора
    NIFTY_BANK_VIEWALL_LOCATOR = ("css selector", "#tab4_gainers_loosers > div.link-wrap > a")
    # Локатор нужного нам элемента в селекторе
    OPTION_LOCATOR = ("css selector", "#equitieStockSelect > optgroup:nth-child(4) > option:nth-child(7)")
    # Локатор, детектящий загрузку таблицы
    FREEZED_ROW_LOCATOR = ("css selector", "#equityStockTable > tbody > tr.freezed-row")
    # Локатор всей таблицы, для получения размера, нужного для прокрутки вниз
    TABLE_LOCATOR = ("css selector", "#equityStockTable")

    nifty_bank_p = driver.find_element(*NIFTY_BANK_P_LOCATOR)
    nifty_bank_p.click()

    wait.until(EC.visibility_of_element_located(NIFTY_BANK_VIEWALL_LOCATOR))
    nifty_bank_viewall = driver.find_element(*NIFTY_BANK_VIEWALL_LOCATOR)

    webdriver.ActionChains(driver) \
        .scroll_to_element(nifty_bank_viewall). \
        perform()

    # Промотка страницы чтобы можно было кликнуть на ссылку
    driver.execute_script("""
                window.scrollTo({
                    top: window.scrollY + 100,
                    });
                """)
    nifty_bank_viewall.click()

    wait.until(EC.presence_of_element_located(OPTION_LOCATOR))
    driver.find_element(*OPTION_LOCATOR).click()

    wait.until(EC.presence_of_element_located(FREEZED_ROW_LOCATOR))
    height = driver.find_element(*TABLE_LOCATOR).size["height"]
    # Проматываем до конца таблицы
    driver.execute_script("window.scrollTo({top: window.scrollY + " + str(height) + ",});")

    time.sleep(5)


def main():
    # Автоматическая установка драйвера для хрома
    service = Service(executable_path=ChromeDriverManager().install())

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 5, 1)

    # Защита от детекта бота, без этого сайт мог не открываться
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)

    try:
        parse_table(driver, wait)
        time.sleep(2)
        imitate_human(driver, wait)
    except Exception as exception:
        print(exception)


if __name__ == "__main__":
    main()
