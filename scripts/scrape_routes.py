from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)

base_url = "https://saraksti.rigassatiksme.lv/index.html"
driver.get(base_url)

WebDriverWait(driver, 30).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table#tblRoutes a"))
)

routes_elements = driver.find_elements(By.CSS_SELECTOR, "table#tblRoutes td:nth-child(2) a")
routes = []

for route_el in routes_elements:
    route_name = route_el.text.strip()
    href = route_el.get_attribute("href")
    if not href:
        continue

    route_el.click()
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#spanDir1"))
    )

    time.sleep(1)
    dir1_span = driver.find_element(By.CSS_SELECTOR, "#spanDir1")
    dir1_text = dir1_span.text.strip()
    dir1_href = driver.current_url

    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#ulDirections a"))
    )

    directions = driver.find_elements(By.CSS_SELECTOR, "#ulDirections a")
    direction_data = []
    for dir_el in directions:
        direction_data.append({
            "name": dir_el.text.strip(),
            "url": dir_el.get_attribute("href")
        })

    routes.append({
        "route_name": route_name,
        "main_url": dir1_href,
        "directions": direction_data
    })

    driver.back()
    WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table#tblRoutes a"))
    )
    routes_elements = driver.find_elements(By.CSS_SELECTOR, "table#tblRoutes td:nth-child(2) a")

driver.quit()

with open("routes_with_directions.json", "w", encoding="utf-8") as f:
    json.dump(routes, f, ensure_ascii=False, indent=2)
