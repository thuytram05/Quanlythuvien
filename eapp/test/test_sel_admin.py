import pytest
import time
from selenium.webdriver.common.by import By
from eapp.test.pages.LoginPage import LoginPage
from eapp.test.pages.RegisterPage import RegisterPage
from eapp.test.pages.AdminPage import AdminPage

pytest_plugins = ["eapp.test.test_base"]


def test_sel_admin_access_denied_for_normal_user(driver):
    register_page = RegisterPage(driver)
    login_page = LoginPage(driver)
    admin_page = AdminPage(driver)

    unique_user = f"normal_{int(time.time())}"

    register_page.open_page()
    register_page.register_new_user("Thường Dân", unique_user, "Password123")
    time.sleep(2)

    login_page.open_page()
    login_page.login(unique_user, "Password123")
    time.sleep(2)

    admin_page.open_page()
    time.sleep(1)

    source = driver.page_source
    assert "libraryOverviewChart" not in source
    assert "Báo Cáo Thống Kê" not in source


def test_sel_admin_full_e2e_flow(driver):
    register_page = RegisterPage(driver)
    login_page = LoginPage(driver)
    admin_page = AdminPage(driver)

    unique_user = f"boss_{int(time.time())}"
    register_page.open_page()
    register_page.register_new_user("Sếp Sòng", unique_user, "Password123")
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

    admin_page.open_page()
    time.sleep(2)
    assert "Quản trị" in driver.page_source
    assert len(driver.find_elements(By.ID, "libraryOverviewChart")) > 0

    driver.get("http://127.0.0.1:5000/admin/sach/")
    time.sleep(2)

    add_btn = driver.find_elements(By.CSS_SELECTOR, '.btn-primary[href*="/new/"]')
    if add_btn:
        driver.execute_script("arguments[0].click();", add_btn[0])
        time.sleep(1.5)

        admin_page.typing(*AdminPage.INPUT_TEN_SACH, "Selenium Admin Pro")
        admin_page.typing(*AdminPage.INPUT_TAC_GIA, "Auto QA Bot")

        save_btn = driver.find_elements(By.CSS_SELECTOR, 'button[type="submit"]')
        if save_btn:
            driver.execute_script("arguments[0].click();", save_btn[0])
            time.sleep(2)

        assert "Selenium Admin Pro" in driver.page_source

    driver.get("http://127.0.0.1:5000/admin/statsview/?month=5&year=2026")
    time.sleep(2)

    assert "Báo Cáo" in driver.page_source or "Thống Kê" in driver.page_source

    driver.get("http://127.0.0.1:5000/admin/logoutview/")
    time.sleep(2)

    assert "libraryOverviewChart" not in driver.page_source