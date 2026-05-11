from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 20)

    def open(self, url):
        self.driver.get(url)

    def find(self, by, value):
        """Đợi phần tử hiển thị trên màn hình"""
        return self.wait.until(EC.visibility_of_element_located((by, value)))

    def find_present(self, by, value):
        """Đợi phần tử hiện diện trong code (dùng cho phần tử bị ẩn CSS)"""
        return self.wait.until(EC.presence_of_element_located((by, value)))

    def click(self, by, value):
        element = self.wait.until(EC.element_to_be_clickable((by, value)))
        element.click()

    def js_click(self, by, value):
        """Ép click bằng JavaScript để vượt qua các lớp phủ UI"""
        element = self.find_present(by, value)
        self.driver.execute_script("arguments[0].click();", element)

    def typing(self, by, value, text):
        e = self.find(by, value)
        e.clear()
        e.send_keys(text)

