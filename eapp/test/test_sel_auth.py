import pytest
import time
from eapp.test.pages.LoginPage import LoginPage
from eapp.test.pages.RegisterPage import RegisterPage

pytest_plugins = ["eapp.test.test_base"]

def test_sel_register_success(driver):
    register_page = RegisterPage(driver)
    register_page.open_page()

    unique_user = f"sel_u{int(time.time())}"
    register_page.register_new_user("Người Dùng Selenium", unique_user, "Password123")

    time.sleep(2)
    assert "/login" in driver.current_url

def test_sel_register_invalid_password(driver):
    register_page = RegisterPage(driver)
    register_page.open_page()

    register_page.register_new_user("Lỗi MK", "user_fail_pw", "onlyletters")

    assert "Mật khẩu yếu" in driver.page_source

def test_sel_register_duplicate_username(driver, sample_data):
    register_page = RegisterPage(driver)
    register_page.open_page()

    register_page.register_new_user("Trùng Tên", "user1", "Password123")

    time.sleep(1)
    assert "đã được sử dụng" in driver.page_source

def test_sel_login_success(driver):
    register_page = RegisterPage(driver)
    login_page = LoginPage(driver)

    unique_user = f"user{int(time.time())}"
    register_page.open_page()

    register_page.register_new_user("Người Dùng Test", unique_user, "Password123")

    time.sleep(2)
    login_page.login(unique_user, "Password123")

    time.sleep(3)

    source_lower = driver.page_source.lower()
    assert "thoát hệ thống" in source_lower
    assert "người dùng test" in source_lower

def test_sel_login_wrong_password(driver):
    login_page = LoginPage(driver)
    login_page.open_page()

    login_page.login("user1", "mat_khau_sai_123")

    assert "không đúng" in driver.page_source

def test_sel_login_blocked_user(driver, sample_data):
    login_page = LoginPage(driver)
    login_page.open_page()

    login_page.login("user2", "123")

    time.sleep(1)
    assert "không đúng" in driver.page_source or "bị khóa" in driver.page_source

def test_sel_logout(driver, sample_data):
    login_page = LoginPage(driver)
    login_page.open_page()
    login_page.login("user1", "123")

    driver.get("http://127.0.0.1:5000/logout")

    time.sleep(1)
    assert "ĐĂNG NHẬP" in driver.page_source