from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()
driver.get("https://saraksti.rigassatiksme.lv/index.html#tram/1/a-b")

WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "spanDir1"))).click()

WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#ulDirections a"))
)

print("Dropdown loaded.")
driver.quit()