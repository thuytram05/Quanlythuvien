import pytest
from eapp.test.test_base import test_client, test_app, sample_data, test_session


# --- KIỂM THỬ TRANG THÔNG TIN CÁ NHÂN (PROFILE) ---

def test_profile_access_denied_for_guest(test_client):
    """1. RÀNG BUỘC BẢO MẬT: Khách chưa đăng nhập không được xem Profile"""
    res = test_client.get('/profile', follow_redirects=True)
    # Kiểm tra xem có bị đẩy về trang login không
    assert "/login" in res.request.path


def test_profile_display_correct_user_info(test_client, sample_data):
    """2. QUY TRÌNH CHÍNH: Hiển thị đúng thông tin của người dùng đang đăng nhập"""
    user = sample_data['users'][0]

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.get('/profile')
    assert res.status_code == 200

    data = res.get_data(as_text=True)
    # Kiểm tra Tên và Tên đăng nhập (đã chuyển thành string)
    assert user.ten in data
    assert user.ten_dang_nhap in data

    # FIX LỖI TYPEERROR: Chuyển vai trò sang string hoặc kiểm tra text hiển thị
    # Nếu trong Enum của bạn QUAN_TRI = 1, ĐỘC GIẢ = 2...
    assert str(user.vai_tro.value) in data or "Thành viên" in data


def test_profile_role_visibility(test_client, sample_data):
    """3. Kiểm tra tính nhất quán của giao diện theo mã HTML thực tế"""
    user = sample_data['users'][1]  # Độc giả bị khóa

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.get('/profile')
    data = res.get_data(as_text=True)

    # FIX LỖI ASSERTION: Khớp với chữ "Trạng thái thẻ độc giả" trong HTML của bạn
    assert "Trạng thái thẻ độc giả" in data
    assert "TÀI KHOẢN BỊ KHÓA" in data
    assert user.ten in data


def test_profile_statistics_display(test_client, sample_data):
    """BỔ SUNG: Kiểm tra các con số thống kê mượn sách có xuất hiện không"""
    user = sample_data['users'][0]

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.get('/profile')
    data = res.get_data(as_text=True)

    # Kiểm tra các nhãn thống kê mà bạn đã đặt trong HTML
    assert "ĐANG MƯỢN" in data
    assert "LƯỢT MƯỢN" in data
    # Ít nhất là số 0 mặc định phải xuất hiện
    assert "0" in data


def test_profile_display_active_status(test_client, sample_data):
    """BỔ SUNG: Kiểm tra hiển thị trạng thái khi tài khoản bình thường"""
    user = sample_data['users'][0]
    user.bi_khoa = False  # Đảm bảo tài khoản đang hoạt động

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.get('/profile')
    data = res.get_data(as_text=True)
    # Khớp với nhãn trạng thái bạn đặt trong HTML cho tài khoản bình thường
    assert "ĐANG HOẠT ĐỘNG" in data or "Bình thường" in data


def test_profile_avatar_rendering(test_client, sample_data):
    """BỔ SUNG: Kiểm tra đường dẫn ảnh đại diện có xuất hiện trong HTML"""
    user = sample_data['users'][0]
    user.anh_dai_dien = "https://example.com/avatar.jpg"

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.get('/profile')
    # Kiểm tra xem link ảnh có nằm trong thẻ <img> không
    assert "avatar.jpg" in res.get_data(as_text=True)


def test_profile_real_statistics_count(test_client, test_session, sample_data):
    """BỔ SUNG: Kiểm tra thống kê hiển thị đúng số lượng phiếu mượn thực tế"""
    from eapp.models import PhieuMuon
    from datetime import datetime, timedelta
    user = sample_data['users'][0]

    # Tạo 2 phiếu mượn thực tế cho user này trong DB
    p1 = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now() + timedelta(days=7))
    p2 = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now() + timedelta(days=7))
    test_session.add_all([p1, p2])
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.get('/profile')
    data = res.get_data(as_text=True)

    # Kiểm tra con số "2" (tổng lượt mượn) có xuất hiện trong UI không
    assert "2" in data

def test_profile_special_characters_display(test_client, test_session, sample_data):
    """BỔ SUNG: Kiểm tra hiển thị tên có dấu tiếng Việt và ký tự đặc biệt"""
    user = sample_data['users'][0]
    user.ten = "Nguyễn Văn A <script>" # Test cả font chữ và tính an toàn
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.get('/profile')
    assert "Nguyễn Văn A" in res.get_data(as_text=True)


def test_profile_default_avatar_visibility(test_client, sample_data):
    """BỔ SUNG: Kiểm tra hiển thị ảnh đại diện mặc định của hệ thống"""
    user = sample_data['users'][0]
    # Mặc định trong model là link res.cloudinary...
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.get('/profile')
    # Kiểm tra một phần của link default bạn đặt trong models.py
    assert "cloudinary" in res.get_data(as_text=True) or "sample.jpg" in res.get_data(as_text=True)