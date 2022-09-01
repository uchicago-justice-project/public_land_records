from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver.v2 as uc
import pandas as pd

import time


def get_text(driver):
    text_array = []
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "row"))
    )
    elements = driver.find_elements(By.CSS_SELECTOR, "div.col-sm-9.col-md-10")
    return [el.text for el in elements]

def cycle_through_page(driver, starting_name = None):
    page_data = []
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "tr"))
    )
    links = driver.find_elements(By.CSS_SELECTOR, "td a")

    i = 0

    if starting_name:
        while i < len(links):
            if links[i].text == starting_name:
                break
            i += 1

    while i < len(links):
        links[i].click()
        try:
            page_data.append(get_text(driver))
        except:
            return page_data
        driver.back()
        links = driver.find_elements(By.CSS_SELECTOR, "td a")
        time.sleep(1)
        i += 1

    return page_data



def scrape_tract_data():
    cols = ['Purchaser', 'Residence', 'Social Status', 'Aliquot Parts or Lot', 'Section Number','Township', 'Range', 'Meridian', 'County of Purchase', 'Acres', 'Price per Acre', 'Total Price', 'Type of Sale', 'Date of Purchase', 'Volume', 'Page']
    try:
        df = pd.read_csv("cook_county.csv")
    except:
        df = pd.DataFrame()

    starting_name = None
    if len(df) > 0:
        starting_name = df.iloc[-1, 0]

    options = uc.ChromeOptions()
    options.headless=True
    options.add_argument('--headless')

    driver = uc.Chrome(options=options)

    driver.get("https://apps.ilsos.gov/isa/pubdomsrch.jsp")
    county_select = Select(driver.find_element(By.ID, 'county'))
    county_select.select_by_value("COOK")
    driver.find_element(By.NAME, "submit").click()
    all_data = []
    try:
        pages = 0
        while True:
            pages = pages + 1
            new_data = cycle_through_page(driver, starting_name)
            if len(new_data) > 0:
                all_data.extend(new_data)
                starting_name = None
                print("starting name reset")
            try:
                time.sleep(1)
                button = driver.find_element(By.CSS_SELECTOR, "input[type=submit]").click()
            except:
                break
    finally:
        driver.quit()

    new_df = pd.DataFrame(all_data, columns=cols)
    print(len(new_df))
    df = pd.concat([df, new_df], ignore_index=True)
    print("writing out new csv")
    df.to_csv("cook_county.csv", index=False)


def count_total_rows():
    options = uc.ChromeOptions()
    options.headless=True
    options.add_argument('--headless')
    driver = uc.Chrome(options=options)


    driver.get("https://apps.ilsos.gov/isa/pubdomsrch.jsp")
    county_select = Select(driver.find_element(By.ID, 'county'))
    county_select.select_by_value("COOK")
    driver.find_element(By.NAME, "submit").click()
    count = 0
    try:
        while True:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "tr"))
            )
            count = count + len(driver.find_elements(By.CSS_SELECTOR, "td a"))
            try:
                time.sleep(5)
                button = driver.find_element(By.CSS_SELECTOR, "input[type=submit]").click()
            except:
                break
    finally:
        print(count)
        driver.quit()

if __name__ == "__main__":
    count_total_rows()
    # for _ in range(3):
    #     scrape_tract_data()
    #     print('pausing')
    #     time.sleep(30)
