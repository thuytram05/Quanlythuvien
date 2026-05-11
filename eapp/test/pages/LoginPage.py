from eapp.test.pages.BasePage import BasePage
from selenium.webdriver.common.by import By

class LoginPage(BasePage):
    URL = 'http://127.0.0.1:5000/login'
    USER_FIELD = (By.NAME, 'username')
    PASS_FIELD = (By.NAME, 'password')
    SUBMIT_BTN = (By.CSS_SELECTOR, '.btn-dark-premium')

    def open_page(self): self.open(self.URL)

    def login(self, username, password):
        self.typing(*self.USER_FIELD, username)
        self.typing(*self.PASS_FIELD, password)
        self.js_click(*self.SUBMIT_BTN)