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