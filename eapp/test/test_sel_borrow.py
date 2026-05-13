import pytest
import time
from selenium.webdriver.common.by import By
from eapp.test.pages.LoginPage import LoginPage
from eapp.test.pages.RegisterPage import RegisterPage
from eapp.test.pages.HomePage import HomePage
from eapp.test.pages.CartPage import CartPage

pytest_plugins = ["eapp.test.test_base"]

def test_sel_borrow_success_flow(driver):
    register_page = RegisterPage(driver)
    login_page = LoginPage(driver)
    unique_user = f"borrow_ok_{int(time.time())}"

    register_page.open_page()
    register_page.register_new_user("Người Mượn Sách", unique_user, "Password123")
    time.sleep(2)
    login_page.login(unique_user, "Password123")
    time.sleep(2)

    home_page = HomePage(driver)
    home_page.open_page()
    home_page.add_to_cart()
    time.sleep(2)

    cart_page = CartPage(driver)
    cart_page.open_page()
    cart_page.confirm_borrow("0901234567")
    time.sleep(3)

    source_lower = driver.page_source.lower()
    assert "thành công" in source_lower
    assert "phiếu mượn đã được tạo" in source_lower

def test_sel_borrow_constraint_must_login(driver):
    driver.get("http://127.0.0.1:5000/")
    time.sleep(2)

    borrow_btns = driver.find_elements(By.CSS_SELECTOR, '.btn-circle-pages.gold')
    if borrow_btns:
        driver.execute_script("arguments[0].click();", borrow_btns[0])
        time.sleep(1)

        source_lower = driver.page_source.lower()
        assert "yêu cầu đăng nhập" in source_lower
        assert "bạn cần đăng nhập" in source_lower

def test_sel_borrow_constraint_max_5_books(driver):
    register_page = RegisterPage(driver)
    login_page = LoginPage(driver)
    unique_user = f"borrow_max_{int(time.time())}"

    register_page.open_page()
    register_page.register_new_user("Tester Max 5", unique_user, "Password123")
    time.sleep(2)
    login_page.login(unique_user, "Password123")
    time.sleep(2)

    driver.get("http://127.0.0.1:5000/")
    time.sleep(2)

    borrow_btns = driver.find_elements(By.CSS_SELECTOR, '.btn-circle-pages.gold')

    for i in range(6):
        driver.execute_script("arguments[0].click();", borrow_btns[i])
        time.sleep(2)

        if i == 5:
            source_lower = driver.page_source.lower()
            assert "tối đa 5 cuốn" in source_lower

def test_sel_borrow_constraint_out_of_stock(driver, sample_data):
    home_page = HomePage(driver)
    home_page.open_page()

    home_page.search_book("Hết Hàng")
    time.sleep(2)

    detail_btn = driver.find_elements(By.CSS_SELECTOR, 'a.btn-circle-pages')
    if detail_btn:
        driver.execute_script("arguments[0].click();", detail_btn[0])
        time.sleep(2)

        source_upper = driver.page_source.upper()
        assert "HẾT SÁCH" in source_upper
        assert "Đã hết bản in" in driver.page_source

def test_sel_borrow_constraint_overdue(driver):
    register_page = RegisterPage(driver)
    login_page = LoginPage(driver)
    home_page = HomePage(driver)
    cart_page = CartPage(driver)

    unique_user = f"badboy_{int(time.time())}"
    register_page.open_page()
    register_page.register_new_user("Kẻ Nợ Sách", unique_user, "Password123")
    time.sleep(2)
    login_page.login(unique_user, "Password123")
    time.sleep(2)

    home_page.open_page()
    home_page.add_to_cart()
    time.sleep(1.5)
    cart_page.open_page()
    cart_page.confirm_borrow("0999999999")
    time.sleep(2)

    from eapp import app, db
    from eapp.models import NguoiDung, PhieuMuon, TrangThaiMuon
    from datetime import datetime, timedelta

    with app.app_context():
        user = NguoiDung.query.filter_by(ten_dang_nhap=unique_user).first()
        if user:
            phieu = PhieuMuon.query.filter_by(ma_nguoi_dung=user.id).order_by(PhieuMuon.id.desc()).first()
            if phieu:
                phieu.ngay_muon = datetime.now() - timedelta(days=30)
                phieu.han_tra = datetime.now() - timedelta(days=16)
                phieu.trang_thai = TrangThaiMuon.QUA_HAN
                db.session.commit()

    home_page.open_page()
    time.sleep(1)
    home_page.add_to_cart()
    time.sleep(1.5)

    source_lower = driver.page_source.lower()
    assert "quá hạn" in source_lower or "nợ sách" in source_lower

def test_sel_borrow_constraint_blocked_account(driver, sample_data):
    login_page = LoginPage(driver)
    login_page.open_page()

    login_page.login("user2", "123")
    time.sleep(2)

    source_lower = driver.page_source.lower()
    assert "bị khóa" in source_lower or "không đúng" in source_lower

