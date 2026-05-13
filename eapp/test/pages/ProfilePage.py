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


