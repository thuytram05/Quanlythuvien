import pytest
import hashlib
import os
from datetime import datetime, timedelta
from flask import Flask
from flask_login import current_user
from eapp import db,login
from eapp.models import Sach, TheLoai, NguoiDung, VaiTro, TrangThaiMuon, PhieuMuon


def create_app():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    app = Flask(__name__,
                template_folder=os.path.join(base_dir, 'templates'),
                static_folder=os.path.join(base_dir, 'static'))

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["PAGE_SIZE"] = 50
    app.config["TESTING"] = True
    app.secret_key = 'library_test_secret_key_123'

    # Khởi tạo db và login cho app test
    db.init_app(app)
    login.init_app(app)  # QUAN TRỌNG: Phải init login ở đây

    # Đăng ký current_user vào context của template để tránh lỗi Undefined
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
        db.create_all()  # Khởi tạo bảng
        yield app
        db.drop_all()  # Xóa bảng sau khi test xong


@pytest.fixture
def test_client(test_app):
    return test_app.test_client()


@pytest.fixture
def test_session(test_app):
    yield db.session
    db.session.rollback()


# --- 3. DỮ LIỆU MẪU BAO PHỦ RÀNG BUỘC ĐỀ TÀI 5 ---
@pytest.fixture
def sample_data(test_session):
    """Nạp dữ liệu mẫu để test tìm kiếm, phân trang và mượn sách"""
    # Tạo Thể loại
    tl1 = TheLoai(ten_the_loai="Công nghệ")
    tl2 = TheLoai(ten_the_loai="Văn học")
    test_session.add_all([tl1, tl2])
    test_session.commit()

    # Tạo Sách (Test phân trang: Tạo 52 cuốn để trang 2 có 2 cuốn)
    books = []
    for i in range(52):
        books.append(Sach(
            ten_sach=f"Sách Test {i}",
            tac_gia="Tác giả Test",
            # Cuốn đầu tiên (i=0) cho hết sách để test ràng buộc hết bản
            so_luong_con=10 if i > 0 else 0,
            tong_so_luong=10,
            ma_the_loai=tl1.id
        ))

    # Tạo Người dùng (Băm mật khẩu MD5 chuẩn)
    pass_hash = str(hashlib.md5('123'.encode('utf-8')).hexdigest())

    # User 1: Bình thường
    u1 = NguoiDung(ten="Độc giả 1", ten_dang_nhap="user1",
                   mat_khau=pass_hash, vai_tro=VaiTro.NGUOI_DUNG, bi_khoa=False)
    # User 2: Bị khóa (Test ràng buộc tài khoản bị khóa)
    u2 = NguoiDung(ten="Độc giả bị khóa", ten_dang_nhap="user2",
                   mat_khau=pass_hash, vai_tro=VaiTro.NGUOI_DUNG, bi_khoa=True)

    test_session.add_all(books + [u1, u2])
    test_session.commit()

    return {
        'books': books,
        'users': [u1, u2],
        'categories': [tl1, tl2]
    }


# --- 4. CÁC FIXTURE HỖ TRỢ TEST RÀNG BUỘC ĐẶC THÙ ---
@pytest.fixture
def overdue_user(test_session, sample_data):
    """Giả lập user có sách nợ quá hạn (Test chặn mượn mới)"""
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
    """Giả lập upload ảnh lên Cloudinary để test đăng ký"""

    def fake_upload(file, **kwargs):
        return {'secure_url': 'https://fake-library-image.png'}

    monkeypatch.setattr('cloudinary.uploader.upload', fake_upload)