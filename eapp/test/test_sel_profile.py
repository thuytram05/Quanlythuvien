import pytest
import time
from selenium.webdriver.common.by import By
from eapp.test.pages.LoginPage import LoginPage
from eapp.test.pages.RegisterPage import RegisterPage

pytest_plugins = ["eapp.test.test_base"]


def test_sel_profile_unauthenticated_access(driver):
    driver.get("http://127.0.0.1:5000/profile")
    time.sleep(2)

    source = driver.page_source
    assert "Unauthorized" in source or "/login" in driver.current_url or "401" in source


def test_sel_profile_normal_user_display(driver):
    register_page = RegisterPage(driver)
    login_page = LoginPage(driver)

    display_name = "Thám Tử Conan"
    unique_user = f"detective_{int(time.time())}"

    register_page.open_page()
    register_page.register_new_user(display_name, unique_user, "Password123")
    time.sleep(2)

    login_page.open_page()
    login_page.login(unique_user, "Password123")
    time.sleep(2)

    driver.get("http://127.0.0.1:5000/profile")
    time.sleep(2)

    source = driver.page_source
    assert display_name in source
    assert unique_user in source

    admin_buttons = driver.find_elements(By.CSS_SELECTOR, "a[href='/admin']")
    assert len(admin_buttons) == 0


def test_sel_profile_admin_user_display(driver):
    register_page = RegisterPage(driver)
    login_page = LoginPage(driver)

    display_name = "Quản Trị Mạng"
    unique_user = f"admin_pro_{int(time.time())}"

    register_page.open_page()
    register_page.register_new_user(display_name, unique_user, "Password123")
    time.sleep(2)

    from eapp import app, db
    from eapp.models import NguoiDung, VaiTro
    with app.app_context():
        u = NguoiDung.query.filter_by(ten_dang_nhap=unique_user).first()
        if u:
            u.vai_tro = VaiTro.QUAN_TRI
            db.session.commit()

    login_page.open_page()
    login_page.login(unique_user, "Password123")
    time.sleep(2)

    driver.get("http://127.0.0.1:5000/profile")
    time.sleep(2)

    source = driver.page_source
    assert display_name in source
    assert unique_user in source

    admin_buttons = driver.find_elements(By.CSS_SELECTOR, "a[href='/admin']")
    assert len(admin_buttons) > 0

def test_sel_profile_navigate_to_history(driver):
    register_page = RegisterPage(driver)
    login_page = LoginPage(driver)

    unique_user = f"history_nav_{int(time.time())}"

    register_page.open_page()
    register_page.register_new_user("Người Xem Lịch Sử", unique_user, "Password123")
    time.sleep(2)

    login_page.open_page()
    login_page.login(unique_user, "Password123")
    time.sleep(2)

    driver.get("http://127.0.0.1:5000/profile")
    time.sleep(2)

    history_btn = driver.find_elements(By.CSS_SELECTOR, "a[href='/lich-su-muon']")
    if history_btn:
        driver.execute_script("arguments[0].click();", history_btn[0])
        time.sleep(2)

    assert "/lich-su-muon" in driver.current_url