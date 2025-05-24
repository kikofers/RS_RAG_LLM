from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

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
    route_name = route_el.text.strip()
    route_el.click()

    wait.until(EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, "#schedule4 > div.container-fluid > div.row-fluid.row-directions > ul > li > a")
    ))
    time.sleep(0.5)

    directions = []
    direction_elements = driver.find_elements(By.CSS_SELECTOR, "#schedule4 > div.container-fluid > div.row-fluid.row-directions > ul > li > a")
    for j in range(len(direction_elements)):
        # re-fetch to avoid stale reference
        dir_el = driver.find_elements(By.CSS_SELECTOR, "#schedule4 > div.container-fluid > div.row-fluid.row-directions > ul > li > a")[j]
        directions.append({
            "name": dir_el.text.strip(),
            "url": dir_el.get_attribute("href")
        })

    routes.append({
        "route_name": route_name,
        "directions": directions
    })

    driver.back()
    wait.until(EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, "#schedule > div.container-fluid > div:nth-child(3) > ul > li > a")
    ))
    time.sleep(0.5)

driver.quit()

with open("data/routes_with_directions.json", "w", encoding="utf-8") as f:
    json.dump(routes, f, ensure_ascii=False, indent=2)
