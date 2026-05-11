from eapp.test.pages.BasePage import BasePage
from selenium.webdriver.common.by import By


# eapp/test/pages/CartPage.py

class CartPage(BasePage):
    URL = 'http://127.0.0.1:5000/phieu-muon'
    CONFIRM_PROCESS_BTN = (By.CSS_SELECTOR, '.btn-confirm-mega')
    # Locators bên trong popup SweetAlert2
    SWAL_PHONE = (By.ID, 'sw-phone')
    SWAL_CONFIRM_BTN = (By.CSS_SELECTOR, '.swal2-confirm')

    def open_page(self):
        self.open(self.URL)

    def confirm_borrow(self, phone):
        # SỬA TẠI ĐÂY: Thay self.click bằng self.js_click để tránh bị chặn
        self.js_click(*self.CONFIRM_PROCESS_BTN)

        # Đợi popup SweetAlert2 hiện ra và nhập liệu
        self.typing(*self.SWAL_PHONE, phone)

        # Nút xác nhận trên popup thường không bị chặn, có thể dùng click()
        # nhưng dùng js_click() sẽ luôn an toàn hơn
        self.js_click(*self.SWAL_CONFIRM_BTN)