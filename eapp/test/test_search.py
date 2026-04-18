import pytest
from eapp.test.test_base import test_client, test_app, sample_data, test_session


# --- NHÓM 1: KIỂM TRA TÌM KIẾM THEO TỪ KHÓA (KW) ---

def test_search_by_book_name(test_client, sample_data):
    """1. Kiểm tra tìm đúng tên sách (Ràng buộc: Tên sách)"""
    # Sử dụng tên sách từ sample_data (ví dụ: Sách Test 1)
    res = test_client.get('/?kw=Sách Test 1')
    data = res.get_data(as_text=True)

    assert res.status_code == 200
    assert 'Sách Test 1' in data
    # Đảm bảo có hiển thị danh sách (kiểm tra phần tử bao ngoài hoặc class cụ thể)
    assert 'book' in data.lower()


def test_search_by_author(test_client, sample_data, test_session):
    """2. Kiểm tra tìm theo tên tác giả (Ràng buộc Đề 5: Tên hoặc Tác giả)"""
    from eapp.models import Sach
    tl_id = sample_data['categories'][0].id

    # Thêm sách mẫu có tên tác giả cụ thể
    lh = Sach(ten_sach="Lao Hac", tac_gia="Nam Cao", so_luong_con=5,
              tong_so_luong=5, ma_the_loai=tl_id)
    test_session.add(lh)
    test_session.commit()

    res = test_client.get('/?kw=Nam Cao')
    data = res.get_data(as_text=True)

    assert res.status_code == 200
    assert "Nam Cao" in data
    assert "Lao Hac" in data


def test_search_no_result(test_client, sample_data):
    """3. Kiểm tra giao diện khi KHÔNG tìm thấy kết quả"""
    res = test_client.get('/?kw=SachVienTuong9999')
    data = res.get_data(as_text=True).lower() # Chuyển toàn bộ về chữ thường để so sánh

    # Sửa lại từ khóa khớp với template: "không tìm thấy tài liệu nào phù hợp"
    assert "không tìm thấy" in data or "rất tiếc" in data


# --- NHÓM 2: KIỂM TRA RÀNG BUỘC NGHIỆP VỤ (ĐỀ TÀI 5) ---

def test_search_min_length_validation(test_client, sample_data):
    """4. RÀNG BUỘC: Từ khóa < 2 ký tự phải báo lỗi/cảnh báo"""
    # follow_redirects=True để nhận được flash message sau khi redirect
    res = test_client.get('/?kw=S', follow_redirects=True)
    data = res.get_data(as_text=True)

    assert "2 ký tự" in data


def test_pagination_logic(test_client, test_app, sample_data):
    """5. RÀNG BUỘC: Hiển thị tối đa 50 cuốn/trang"""
    # Kiểm tra config khớp với yêu cầu đề bài
    assert test_app.config['PAGE_SIZE'] == 50

    # Trang 1: Kiểm tra xem có dữ liệu sách không
    res_p1 = test_client.get('/?page=1')
    data_p1 = res_p1.get_data(as_text=True)
    assert 'Sách Test' in data_p1

    # Trang 2: sample_data tạo 52 cuốn, trang 2 phải có nốt các cuốn còn lại
    res_p2 = test_client.get('/?page=2')
    data_p2 = res_p2.get_data(as_text=True)
    assert 'Sách Test 50' in data_p2 or 'Sách Test 51' in data_p2


def test_pagination_empty_page(test_client, sample_data):
    """6. KIỂM TRA RANH GIỚI: Trang không có dữ liệu"""
    res = test_client.get('/?page=99')
    data = res.get_data(as_text=True).lower()

    assert res.status_code == 200
    # Khớp với thông báo thực tế trong template của bạn
    assert "không tìm thấy" in data or "rất tiếc" in data


# --- NHÓM 3: KIỂM TRA LỌC (FILTER) ---

def test_filter_by_category(test_client, sample_data):
    """7. Kiểm tra lọc sách theo danh mục (Thể loại)"""
    cate_id = sample_data['categories'][0].id
    res = test_client.get(f'/?category_id={cate_id}')
    data = res.get_data(as_text=True)

    assert res.status_code == 200
    # Đảm bảo kết quả thuộc đúng thể loại (nếu giao diện có hiện tên thể loại)
    assert sample_data['categories'][0].ten_the_loai in data