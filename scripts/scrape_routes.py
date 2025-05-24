# Unnecessary script, because we already have GTFS data.

"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import os

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

driver.get("https://saraksti.lv/#lv")

wait = WebDriverWait(driver, 30)
wait.until(EC.presence_of_all_elements_located(
    (By.CSS_SELECTOR, "#schedule > div.container-fluid > div:nth-child(3) > ul > li > a")
))

routes = []
route_links = driver.find_elements(By.CSS_SELECTOR, "#schedule > div.container-fluid > div:nth-child(3) > ul > li > a")
route_count = len(route_links)

for i in range(route_count):
    route_links = driver.find_elements(By.CSS_SELECTOR, "#schedule > div.container-fluid > div:nth-child(3) > ul > li > a")
    route_el = route_links[i]
    route_text = route_el.text.strip()
    route_number = ''.join(filter(str.isdigit, route_text))
    route_el.click()

    wait.until(EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, "#schedule4 > div.container-fluid > div.row-fluid.row-directions > ul > li > a")
    ))
    time.sleep(0.2)

    directions = []
    direction_elements = driver.find_elements(By.CSS_SELECTOR, "#schedule4 > div.container-fluid > div.row-fluid.row-directions > ul > li > a")
    for j in range(len(direction_elements)):
        dir_el = driver.find_elements(By.CSS_SELECTOR, "#schedule4 > div.container-fluid > div.row-fluid.row-directions > ul > li > a")[j]
        directions.append({
            "name": dir_el.get_attribute("textContent").strip(),
            "url": dir_el.get_attribute("href")
        })

    routes.append({
        "route_name": route_number,
        "directions": directions
    })

    driver.back()
    wait.until(EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, "#schedule > div.container-fluid > div:nth-child(3) > ul > li > a")
    ))
    time.sleep(0.2)

driver.quit()

os.makedirs("data", exist_ok=True)
with open("data/routes.json", "w", encoding="utf-8") as f:
    json.dump(routes, f, ensure_ascii=False, indent=2)
"""