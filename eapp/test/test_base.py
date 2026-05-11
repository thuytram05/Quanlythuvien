import pytest
import hashlib
import os
import sys  # 1. Thêm import sys
from datetime import datetime, timedelta
from flask import Flask
from flask_login import current_user

# 2. MẸO QUAN TRỌNG: Thêm thư mục 'eapp' vào đường dẫn hệ thống trước khi import admin
# Việc này giúp lệnh 'import dao' bên trong admin.py hoạt động được mà không cần sửa file đó.
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from eapp import db, login
# 3. Import chính xác ĐỐI TƯỢNG admin (biến admin) từ MODULE admin (file admin.py)
from eapp.admin import admin as admin_instance

from eapp.models import Sach, TheLoai, NguoiDung, VaiTro, TrangThaiMuon, PhieuMuon
from selenium import webdriver
from selenium.webdriver.chrome.service import Service


# --- 1. KHỞI TẠO APP TEST ---
def create_app():
    app = Flask(__name__,
                template_folder=os.path.join(base_dir, 'templates'),
                static_folder=os.path.join(base_dir, 'static'))

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["PAGE_SIZE"] = 50
    app.config["TESTING"] = True
    app.secret_key = 'library_test_secret_key_123'

    db.init_app(app)
    login.init_app(app)

    # 4. GẮN ĐỐI TƯỢNG ADMIN VÀO APP TEST
    # Vì admin_instance là đối tượng được tạo từ Admin(), nó sẽ có hàm init_app
    admin_instance.init_app(app)

    login.login_view = 'login_user_process'

    @app.context_processor
    def inject_user():
        return dict(current_user=current_user)

    from eapp.index import register_routes
    register_routes(app)

    return app

@pytest.fixture
def test_app():
    app = create_app()
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def test_client(test_app):
    return test_app.test_client()


@pytest.fixture
def test_session(test_app):
    yield db.session
    db.session.rollback()


# --- 3. DỮ LIỆU MẪU (BAO PHỦ 100% ĐỀ TÀI 5) ---
@pytest.fixture
def sample_data(test_session):
    """Nạp dữ liệu mẫu để test: tìm kiếm, phân trang, hết bản, khóa tài khoản"""
    # Tạo Thể loại
    tl1 = TheLoai(ten_the_loai="Công nghệ")
    tl2 = TheLoai(ten_the_loai="Văn học")
    test_session.add_all([tl1, tl2])
    test_session.commit()

    # Tạo 52 cuốn sách để test phân trang (Trang 1: 50, Trang 2: 2)
    books = []
    for i in range(52):
        books.append(Sach(
            ten_sach=f"Sách Test {i}",
            tac_gia="Tác giả Test",
            # Cuốn đầu tiên (ID:1) set số lượng = 0 để test ràng buộc HẾT BẢN
            so_luong_con=10 if i > 0 else 0,
            tong_so_luong=10,
            ma_the_loai=tl1.id
        ))

    # Băm mật khẩu MD5 đồng bộ với dao.py
    pass_hash = hashlib.md5('123'.encode('utf-8')).hexdigest()

    # User 1: Bình thường để test mượn sách thành công
    u1 = NguoiDung(ten="Độc giả 1", ten_dang_nhap="user1",
                   mat_khau=pass_hash, vai_tro=VaiTro.NGUOI_DUNG, bi_khoa=False)

    # User 2: Bị khóa để test ràng buộc TÀI KHOẢN BỊ KHÓA
    u2 = NguoiDung(ten="Độc giả bị khóa", ten_dang_nhap="user2",
                   mat_khau=pass_hash, vai_tro=VaiTro.NGUOI_DUNG, bi_khoa=True)

    test_session.add_all(books + [u1, u2])
    test_session.commit()

    return {
        'books': books,
        'users': [u1, u2],
        'categories': [tl1, tl2]
    }


# --- 4. FIXTURE NÂNG CAO (RÀNG BUỘC ĐẶC THÙ) ---
@pytest.fixture
def overdue_user(test_session, sample_data):
    """Giả lập user có sách nợ quá hạn để test CHẶN MƯỢN MỚI"""
    user = sample_data['users'][0]
    p = PhieuMuon(ma_nguoi_dung=user.id,
                  ngay_muon=datetime.now() - timedelta(days=30),
                  han_tra=datetime.now() - timedelta(days=10),
                  trang_thai=TrangThaiMuon.QUA_HAN)
    test_session.add(p)
    test_session.commit()
    return user


@pytest.fixture
def mock_cloudinary(monkeypatch):
    """Giả lập Cloudinary để test đăng ký không cần internet"""

    def fake_upload(file, **kwargs):
        return {'secure_url': 'https://fake-library-image.png'}

    monkeypatch.setattr('cloudinary.uploader.upload', fake_upload)


@pytest.fixture
def driver():
    """Trình duyệt Chrome ảo cho Selenium (UI Test)"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Tìm chromedriver.exe trong thư mục .venv của project
    driver_path = os.path.normpath(os.path.join(current_dir, '..', '..', '.venv', 'chromedriver.exe'))

    if not os.path.exists(driver_path):
        pytest.fail(f"LỖI: Không tìm thấy chromedriver tại {driver_path}")

    service = Service(executable_path=driver_path)
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # Bật nếu muốn chạy ngầm

    driver = webdriver.Chrome(service=service, options=options)
    yield driver
    driver.quit()