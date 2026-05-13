from eapp.test.pages.BasePage import BasePage
from selenium.webdriver.common.by import By
import time

class AdminPage(BasePage):
    URL = 'http://127.0.0.1:5000/admin'
    START_CHART=(By.ID,'libraryOverviewChart')

    NAV_SACH=(By.LINK_TEXT,'Sách')
    NAV_DOC_GIA=(By.LINK_TEXT,'Độc Giả')
    NAV_THONG_KE=(By.LINK_TEXT,'Thống kê')
    NAV_DANG_XUAT=(By.LINK_TEXT,'Đăng xuất')

    BIN_ADD_NEW=(By.CSS_SELECTOR,'.btn-primary[href*="/new/"]')
    INPUT_TEN_SACH=(By.ID,'ten_sach')
    INPUT_TAC_GIA=(By.ID,'tac_gia')
    BTN_SAVE= (By.CSS_SELECTOR, 'button[type=\"submit\"]')

    FILTER_MONTH = (By.NAME, 'month')
    FILTER_YEAR = (By.NAME, 'year')
    BTN_FILTER_SUBMIT = (By.CSS_SELECTOR, 'button[type=\"submit\"]')

    def open_page(self):
        self.open(self.URL)

    def go_to_book_management(self):
        self.js_click(*self.NAV_SACH)

    def add_new_book(self,title,author):
        self.click(*self.BIN_ADD_NEW)
        self.click(*self.INPUT_TEN_SACH,title)
        self.click(*self.INPUT_TAC_GIA,author)
        self.click(*self.BTN_SAVE)

    def filter_stats(self,month,year):
        self.click(*self.NAV_THONG_KE)
        self.click(*self.FILTER_MONTH,month)
        self.click(*self.FILTER_YEAR,year)
        self.click(*self.BTN_FILTER_SUBMIT)
        time.sleep(1)

    def logout_admin(self):
        self.click(*self.NAV_DANG_XUAT)

    def is_dashboard_visible(self):
        try:
            return self.find(*self.STATS_CHART).is_displayed()
        except:
            return False

