import pytest
import hashlib
import os
import sys
from datetime import datetime, timedelta
from flask import Flask
from flask_login import current_user
from eapp import db, login
from eapp.admin import admin as admin_instance
from eapp.models import Sach, TheLoai, NguoiDung, VaiTro, TrangThaiMuon, PhieuMuon
from selenium import webdriver
from selenium.webdriver.chrome.service import Service


base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

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

@pytest.fixture
def sample_data(test_session):
    tl1 = TheLoai(ten_the_loai="Công nghệ")
    tl2 = TheLoai(ten_the_loai="Văn học")
    test_session.add_all([tl1, tl2])
    test_session.commit()
    books = []
    for i in range(52):
        books.append(Sach(
            ten_sach=f"Sách Test {i}",
            tac_gia="Tác giả Test",
            so_luong_con=10 if i > 0 else 0,
            tong_so_luong=10,
            ma_the_loai=tl1.id
        ))
    pass_hash = hashlib.md5('123'.encode('utf-8')).hexdigest()
    u1 = NguoiDung(ten="Độc giả 1", ten_dang_nhap="user1",
                   mat_khau=pass_hash, vai_tro=VaiTro.NGUOI_DUNG, bi_khoa=False)
    u2 = NguoiDung(ten="Độc giả bị khóa", ten_dang_nhap="user2",
                   mat_khau=pass_hash, vai_tro=VaiTro.NGUOI_DUNG, bi_khoa=True)

    test_session.add_all(books + [u1, u2])
    test_session.commit()

    return {
        'books': books,
        'users': [u1, u2],
        'categories': [tl1, tl2]
    }
@pytest.fixture
def overdue_user(test_session, sample_data):
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

    def fake_upload(file, **kwargs):
        return {'secure_url': 'https://fake-library-image.png'}

    monkeypatch.setattr('cloudinary.uploader.upload', fake_upload)


@pytest.fixture
def driver():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    driver_path = os.path.normpath(os.path.join(current_dir, '..', '..', '.venv', 'chromedriver.exe'))

    if not os.path.exists(driver_path):
        pytest.fail(f"LỖI: Không tìm thấy chromedriver tại {driver_path}")

    service = Service(executable_path=driver_path)
    options = webdriver.ChromeOptions()

    driver = webdriver.Chrome(service=service, options=options)
    yield driver
    driver.quit()