import pytest
import time
from selenium.webdriver.common.by import By
from eapp.test.pages.LoginPage import LoginPage
from eapp.test.pages.RegisterPage import RegisterPage
from eapp.test.pages.HomePage import HomePage
from eapp.test.pages.CartPage import CartPage

pytest_plugins = ["eapp.test.test_base"]

def test_sel_return_book_success(driver):
    register_page = RegisterPage(driver)
    login_page = LoginPage(driver)
    home_page = HomePage(driver)
    cart_page = CartPage(driver)

    unique_user = f"rt_ok_{int(time.time())}"
    register_page.open_page()
    register_page.register_new_user("Người Trả Sách", unique_user, "Password123")
    time.sleep(2)

    login_page.open_page()
    login_page.login(unique_user, "Password123")
    time.sleep(2)

    home_page.open_page()
    home_page.add_to_cart()
    time.sleep(1.5)

    cart_page.open_page()
    cart_page.confirm_borrow("0999888777")
    time.sleep(3)

    driver.get("http://127.0.0.1:5000/lich-su-muon")
    time.sleep(2)

    return_btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'TRẢ SÁCH')]")
    if return_btns:
        driver.execute_script("arguments[0].click();", return_btns[0])
        time.sleep(1.5)

        confirm_btn = driver.find_elements(By.CSS_SELECTOR, ".swal2-confirm")
        if confirm_btn:
            driver.execute_script("arguments[0].click();", confirm_btn[0])
        time.sleep(2)  # Chờ load lại trang sau khi trả xong

    source_lower = driver.page_source.lower()
    # Kiểm tra có dòng thông báo "trả sách thành công" ở góc màn hình không
    assert "thành công" in source_lower or "hoàn tất" in source_lower


def test_sel_return_book_late_fine(driver):
    register_page = RegisterPage(driver)
    login_page = LoginPage(driver)
    home_page = HomePage(driver)
    cart_page = CartPage(driver)

    unique_user = f"rt_late_{int(time.time())}"
    register_page.open_page()
    register_page.register_new_user("Kẻ Trả Trễ", unique_user, "Password123")
    time.sleep(2)

    login_page.open_page()
    login_page.login(unique_user, "Password123")
    time.sleep(2)

    home_page.open_page()
    home_page.add_to_cart()
    time.sleep(1.5)

    cart_page.open_page()
    cart_page.confirm_borrow("0911222333")
    time.sleep(3)

    from eapp import app, db
    from eapp.models import NguoiDung, PhieuMuon, TrangThaiMuon
    from datetime import datetime, timedelta

    with app.app_context():
        u = NguoiDung.query.filter_by(ten_dang_nhap=unique_user).first()
        if u:
            p = PhieuMuon.query.filter_by(ma_nguoi_dung=u.id).order_by(PhieuMuon.id.desc()).first()
            if p:
                p.han_tra = datetime.now() - timedelta(days=5)  # Lùi 5 ngày
                p.trang_thai = TrangThaiMuon.QUA_HAN
                db.session.commit()

    driver.get("http://127.0.0.1:5000/lich-su-muon")
    time.sleep(2)

    return_btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'TRẢ SÁCH')]")
    if return_btns:
        driver.execute_script("arguments[0].click();", return_btns[0])
        time.sleep(1.5)

        confirm_btn = driver.find_elements(By.CSS_SELECTOR, ".swal2-confirm")
        if confirm_btn:
            driver.execute_script("arguments[0].click();", confirm_btn[0])
        time.sleep(2)

    source_lower = driver.page_source.lower()
    assert "phí phạt" in source_lower
    assert "25,000" in source_lower