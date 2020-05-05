import argparse
import locale
import random
import sys
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from esportsbattle.config import DOMAIN_NAME, SEARCH_STRING
from esportsbattle.src.parser import save_to_file


locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

MAIN_PAGE_RESULTS_CLASS_NAME = "item-label__text"


def load_data(date_start, date_end):
    # create webdriver
    driver = webdriver.Firefox()
    wait = WebDriverWait(driver, 30)

    driver.get(DOMAIN_NAME)
    wait.until(EC.visibility_of_element_located((By.ID, 'search_words_field')))
    time.sleep(random.uniform(1, 4))

    # fill search params and get results
    search_input_field = driver.find_element_by_id('search_words_field')
    search_input_field.send_keys(SEARCH_STRING)
    time.sleep(random.uniform(1, 4))

    date_type_range = driver.find_element_by_id('date_type_RANGE')
    date_type_range.click()
    time.sleep(random.uniform(1, 2))
    wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, 'input-field-component date-field-component')))

    date_range_from = driver.find_element_by_id('date_range_from')
    date_range_to = driver.find_element_by_id('date_range_to')

    date_range_from.send_keys(Keys.COMMAND + 'A')
    time.sleep(random.uniform(0.2, 3))
    date_range_from.send_keys(Keys.BACKSPACE)
    time.sleep(random.uniform(0.3, 2))
    date_range_from.send_keys(date_start)
    time.sleep(random.uniform(0.5, 2))

    date_range_to.send_keys(Keys.COMMAND + 'A')
    time.sleep(random.uniform(1, 3))
    date_range_to.send_keys(Keys.BACKSPACE)
    time.sleep(random.uniform(0.3, 2))
    date_range_to.send_keys(date_end)
    time.sleep(random.uniform(0.6, 3))

    button_submit = driver.find_element_by_name('submit')
    try:
        button_submit.click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'result-sport')))
        div_results = driver.find_element_by_class_name('result-sport-list')
        div_results_text = div_results.text
    except TimeoutException:
        print(f'No data for requested date interval {date_start}-{date_end} :(')
        sys.exit(1)
    finally:
        driver.close()

    save_to_file(div_results_text, date_start, date_end)


if __name__ == '__main__':
    # parse arguments
    p = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--date-start', type=str, required=True, help='date games result')
    p.add_argument('--date-end', type=str, required=True, help='date games result')
    args = p.parse_args()
    date_start = args.date_start
    date_end = args.date_end

    print('Searching dates: ', date_start, '-', date_end)

    load_data(date_start, date_end)
