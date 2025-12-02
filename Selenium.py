import time
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Edge()
driver.maximize_window()
driver.get("https://35finance.mskobr.ru/")
time.sleep(2)

h1_element = driver.find_element(By.TAG_NAME, "h1")
print(f"Заголовок страницы: {h1_element.text}")
driver.save_screenshot("example.png")
print("Скриншот сохранен как example.png")

driver.quit()