from eapp.test.pages.BasePage import BasePage
from selenium.webdriver.common.by import By
import time

class HomePage(BasePage):
    URL = 'http://127.0.0.1:5000/'
    SEARCH_BAR = (By.NAME, 'kw')
    SEARCH_BTN = (By.CSS_SELECTOR, '.search-box button')
    FIRST_BORROW_BTN = (By.CSS_SELECTOR, '.btn-circle-pages.gold')

    def open_page(self):
        self.open(self.URL)

    def search_book(self, keyword):
        self.typing(*self.SEARCH_BAR, keyword)
        self.js_click(*self.SEARCH_BTN)
        time.sleep(2)

    def add_to_cart(self):
        self.js_click(*self.FIRST_BORROW_BTN)
        time.sleep(1.5)

