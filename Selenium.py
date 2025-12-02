import time

from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Edge()
driver.get("https://www.saucedemo.com/")
driver.maximize_window()

time.sleep(2)
login_field = driver.find_element(By.XPATH, '//*[@id="user-name"]')
login_field.send_keys("standard_user")
password_field = driver.find_element(By.XPATH, "//*[@id='password']")
password_field.send_keys("secret_sauce")
time.sleep(3)
button = driver.find_element(By.XPATH, "//*[@id='login-button']")
button.click()
time.sleep(3)
check_element = driver.find_element(By.XPATH, '//*[@id="header_container"]/div[2]/span')
if check_element.text == "Products":
    print("Авторизация выполнена")
else:
    print("Что-то не так")

driver.quit()