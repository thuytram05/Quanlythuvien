import pytest
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Import các Page Objects
from eapp.test.pages.RegisterPage import RegisterPage
from eapp.test.pages.LoginPage import LoginPage
from eapp.test.pages.HomePage import HomePage
from eapp.test.pages.CartPage import CartPage
from eapp.test.pages.HistoryPage import HistoryPage


@pytest.fixture
def driver():
    """Khởi tạo trình duyệt Chrome cho mỗi bài kiểm tra"""
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Bật nếu muốn chạy ngầm
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    driver.implicitly_wait(10)
    yield driver
    driver.quit()


class TestLibrarySystem:

    def test_user_registration(self, driver):
        """Kịch bản: Đăng ký hội viên mới (Xử lý hiệu ứng Artsy overlay)"""
        reg_page = RegisterPage(driver)
        reg_page.open_page()
        unique_username = f"user_{int(time.time())}"
        reg_page.register_new_user(name="Độc Giả Thử Nghiệm", user=unique_username, pwd="Password123")

        time.sleep(3)
        # Kiểm tra chuyển hướng về trang login
        assert "/login" in driver.current_url

    def test_login_success(self, driver):
        """Kịch bản: Đăng nhập thành công với tài khoản admin"""
        login_page = LoginPage(driver)
        login_page.open_page()
        login_page.login("admin", "123456")

        time.sleep(3)
        assert driver.current_url == "http://127.0.0.1:5000/"
        # Kiểm tra tên admin xuất hiện trên navbar (Class 'user-name-text' trong header.html)
        nav_user = driver.find_element(By.CLASS_NAME, "user-name-text")
        assert "quản trị" in nav_user.text.lower()

    def test_search_too_short_keyword(self, driver):
        """Kiểm tra ràng buộc: Từ khóa < 2 ký tự phải báo lỗi từ Server (Bypass HTML5)"""
        home_page = HomePage(driver)
        home_page.open_page()
        # Dùng JS xóa minlength để test logic Backend
        driver.execute_script("document.getElementsByName('kw')[0].removeAttribute('minlength');")
        home_page.search_book("P")

        # Đợi thông báo Flash (Class 'alert-premium' trong header.html)
        wait = WebDriverWait(driver, 10)
        error_element = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "alert-premium")))
        assert "2 ký tự" in error_element.text

    def test_search_valid_keyword(self, driver):
        """Kịch bản: Tìm kiếm sách thành công (Class 'book-title-classic')"""
        home_page = HomePage(driver)
        home_page.open_page()
        home_page.search_book("Python")

        wait = WebDriverWait(driver, 10)
        # Class chính xác trong index.html của bạn là 'book-title-classic'
        titles = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "book-title-classic")))
        assert len(titles) > 0
        assert "python" in titles[0].text.lower()

    def test_full_borrow_process(self, driver):
        """Kịch bản chính: Đăng nhập -> Tìm sách -> Thêm vào túi -> Xác nhận qua SweetAlert2"""
        login_page = LoginPage(driver)
        login_page.open_page()
        login_page.login("admin", "123456")

        home_page = HomePage(driver)
        home_page.open_page()
        home_page.search_book("Python")
        home_page.add_to_cart()  # Nút '+' màu vàng

        # Thêm thời gian chờ ngắn để Session/Badge cập nhật
        time.sleep(1)

        cart_page = CartPage(driver)
        cart_page.open_page()

        # Bước này sẽ gọi js_click đã sửa ở trên
        cart_page.confirm_borrow(phone="0912345678")

        # 4. Kiểm tra popup thành công
        wait = WebDriverWait(driver, 15)

        # SỬA TẠI ĐÂY: Sử dụng text_to_be_present_in_element để đợi nội dung cụ thể
        # Thay vì chỉ đợi element hiển thị (vì element "Đang xử lý" đã hiển thị trước đó)
        success_loaded = wait.until(
            EC.text_to_be_present_in_element((By.CLASS_NAME, "swal2-title"), "THÀNH CÔNG")
        )

        # Sau khi xác nhận văn bản đã đổi thành công, lấy lại element để assert
        final_msg = driver.find_element(By.CLASS_NAME, "swal2-title")
        assert "thành công" in final_msg.text.lower()

    def test_return_book_from_history(self, driver):
        """Kịch bản: Hội viên thực hiện trả sách đang mượn"""
        login_page = LoginPage(driver)
        login_page.open_page()
        login_page.login("admin", "123456")

        history_page = HistoryPage(driver)
        history_page.open_page()

        if not history_page.is_history_empty():
            # Sửa tên hàm cho khớp với HistoryPage.py
            history_page.click_return_book()
            time.sleep(3)
            assert "lich-su-muon" in driver.current_url
        else:
            pytest.skip("Bỏ qua: Không có phiếu mượn để trả.")