from eapp.test.pages.BasePage import BasePage
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

class HistoryPage(BasePage):
    URL = 'http://127.0.0.1:5000/lich-su-muon?tab=dang-muon'
    RETURN_BTN = (By.CSS_SELECTOR, 'button[onclick*="confirmReturn"]')
    EMPTY_MSG = (By.CSS_SELECTOR, '.text-center h4')

    def open_page(self):
        self.open(self.URL)

    def click_return_book(self):
        self.click(*self.RETURN_BTN)
        ok_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.swal2-confirm')))
        ok_btn.click()

    def is_history_empty(self):
        try:
            msg = self.find(*self.EMPTY_MSG)
            return "trống" in msg.text.lower()
        except:
            return False