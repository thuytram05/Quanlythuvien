from eapp.test.pages.BasePage import BasePage
from selenium.webdriver.common.by import By


class CartPage(BasePage):
    URL = 'http://127.0.0.1:5000/phieu-muon'
    CONFIRM_PROCESS_BTN = (By.CSS_SELECTOR, '.btn-confirm-mega')
    SWAL_PHONE = (By.ID, 'sw-phone')
    SWAL_CONFIRM_BTN = (By.CSS_SELECTOR, '.swal2-confirm')

    def open_page(self):
        self.open(self.URL)

    def confirm_borrow(self, phone):
        self.js_click(*self.CONFIRM_PROCESS_BTN)

        self.typing(*self.SWAL_PHONE, phone)

        self.js_click(*self.SWAL_CONFIRM_BTN)