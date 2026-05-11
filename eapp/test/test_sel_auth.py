import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from eapp.test.pages.LoginPage import LoginPage
from eapp.test.pages.RegisterPage import RegisterPage

class TestAuthentication:
    def test_register_success(self, driver):
        """Đăng ký hội viên mới thành công"""
        reg = RegisterPage(driver); reg.open_page()
        unique_user = f"user_{int(time.time())}"
        reg.register_new_user("Người Dùng Mẫu", unique_user, "Pass123")
        time.sleep(2)
        assert "/login" in driver.current_url

    def test_login_success(self, driver):
        """Đăng nhập thành công với tài khoản chuẩn"""
        login = LoginPage(driver); login.open_page()
        login.login("admin", "123456")
        time.sleep(2)
        assert driver.current_url == "http://127.0.0.1:5000/"
        # Kiểm tra tên người dùng hiển thị trên navbar
        assert "quản trị" in driver.find_element(By.CLASS_NAME, "user-name-text").text.lower()

    def test_login_failure_wrong_password(self, driver):
        """Ràng buộc: Nhập sai mật khẩu phải báo lỗi"""
        login = LoginPage(driver); login.open_page()
        login.login("admin", "sai_mat_khau_123")
        wait = WebDriverWait(driver, 10)
        # Class 'alert-premium' hiển thị flash message lỗi
        error = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "alert-premium")))
        assert "không đúng" in error.text.lower()