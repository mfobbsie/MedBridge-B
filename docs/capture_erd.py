from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time, os

html_path = os.path.abspath(r"docs\sprint1_deliverables.html")
url = f"file:///{html_path}"

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.set_window_size(1400, 900)
driver.get(url)
time.sleep(2)

erd_tab = driver.find_element(By.XPATH, "//div[contains(@class,'nav-tab') and text()='ERD']")
erd_tab.click()
time.sleep(1)

# Get full page height, not just the div
height = driver.execute_script("return document.body.scrollHeight")
print(f"Page height: {height}")
driver.set_window_size(1400, height + 200)
time.sleep(1)

driver.save_screenshot("docs/ERD.png")
driver.quit()
print("Saved docs/ERD.png")
