from eapp.test.pages.BasePage import BasePage
from selenium.webdriver.common.by import By

class ProfilePage(BasePage):
    URL =  'http://127.0.0.1:5000/profile/'

    USER_NAME_TEXT = (By.CSS_SELECTOR, '.glass-main-card h2')
    USER_ID_TEXT = (By.CSS_SELECTOR, '.glass-main-card .text-gold.font-monospace')

    STATUS_BADGE = (By.CSS_SELECTOR, '.badge-active-premium, .badge-locked-premium')

    COUNT_BORROWING = (By.XPATH, "//div[contains(text(), 'ĐANG MƯỢN')]/preceding-sibling::div")  #
    COUNT_TOTAL = (By.XPATH, "//div[contains(text(), 'LƯỢT MƯỢN')]/preceding-sibling::div")  #

    BTN_HISTORY = (By.CSS_SELECTOR, '.btn-warning-premium')
    BTN_ADMIN = (By.CSS_SELECTOR, '.btn-outline-gold')

    def open_page(self):
        self.open(self.URL)

    def get_displayed_name(self):
        return self.find(*self.USER_NAME_TEXT).text

    def get_user_status(self):
        return self.find(*self.STATUS_BADGE).text

    def get_borrow_stats(self):
        return {
            'borrowing': self.find(*self.COUNT_BORROWING).text,
            'total': self.find(*self.COUNT_TOTAL).text
        }

    def click_view_history(self):
        self.js_click(*self.BTN_HISTORY)

    def is_admin_button_visible(self):
        try:
            return self.find(*self.BTN_ADMIN).is_displayed()
        except:
            return False


