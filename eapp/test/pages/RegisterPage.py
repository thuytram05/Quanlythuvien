from eapp.test.pages.BasePage import BasePage
from selenium.webdriver.common.by import By

class RegisterPage(BasePage):
    URL = 'http://127.0.0.1:5000/register'
    NAME_FIELD = (By.NAME, 'name')
    USER_FIELD = (By.NAME, 'username')
    PASS_FIELD = (By.ID, 'password')
    CONFIRM_FIELD = (By.ID, 'confirm')
    SUBMIT_BTN = (By.CSS_SELECTOR, '.btn-dark-premium')

    def open_page(self): self.open(self.URL)

    def register_new_user(self, name, user, pwd):
        self.typing(*self.NAME_FIELD, name)
        self.typing(*self.USER_FIELD, user)
        self.typing(*self.PASS_FIELD, pwd)
        self.typing(*self.CONFIRM_FIELD, pwd)
        self.js_click(*self.SUBMIT_BTN)