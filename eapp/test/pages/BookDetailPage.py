from eapp.test.pages.BasePage import BasePage
from selenium.webdriver.common.by import By

class BookDetailPage(BasePage):
    # Nút 'MƯỢN NGAY' trong chi_tiet.html
    BORROW_ULTRA_BTN = (By.CSS_SELECTOR, '.btn-borrow-ultra')

    def click_borrow_now(self):
        self.js_click(*self.BORROW_ULTRA_BTN)