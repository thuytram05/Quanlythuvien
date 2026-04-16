import pytest
from eapp.test.test_base import test_client, test_app, sample_data, test_session, overdue_user
from eapp.models import Sach, PhieuMuon, ChiTietMuon

def test_add_to_cart_success(test_client, sample_data):
    """1. Kiểm tra thêm sách vào túi thành công (Đã đăng nhập)"""
    user = sample_data['users'][0]
    book = sample_data['books'][1]

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.post('/api/cart', json={
        'id': book.id,
        'name': book.ten_sach
    })

    assert res.status_code == 200
    with test_client.session_transaction() as sess:
        assert str(book.id) in sess.get('cart', {})


def test_add_to_cart_blocked_user(test_client, sample_data):
    """2. RÀNG BUỘC: Tài khoản bị khóa không được phép mượn sách"""
    blocked_user = sample_data['users'][1]

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(blocked_user.id)

    res = test_client.post('/api/cart', json={'id': 1, 'name': 'Test'})
    # Phải trả về lỗi 403 Forbidden (Logic trong index.py của bạn)
    assert res.status_code == 403


def test_add_to_cart_over_limit_5_books(test_client, sample_data):
    """3. RÀNG BUỘC: Không cho mượn quá 5 cuốn trong túi"""
    user = sample_data['users'][0]
    valid_book_id = sample_data['books'][1].id

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        # Giả lập đã có 5 cuốn trong túi mượn
        sess['cart'] = {str(i): {'id': i, 'name': 'Sách cũ'} for i in range(100, 105)}

    res = test_client.post('/api/cart', json={'id': valid_book_id, 'name': 'Cuốn thứ 6'})

    assert res.status_code == 400
    assert "tối đa 5 cuốn" in res.get_json().get('err_msg', '').lower()


def test_add_to_cart_out_of_stock(test_client, sample_data):
    """4. RÀNG BUỘC: Không cho mượn nếu sách đã hết bản (so_luong_con=0)"""
    user = sample_data['users'][0]
    out_of_stock_book = sample_data['books'][0] # Cuốn này có so_luong_con=0 từ sample_data

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.post('/api/cart', json={'id': out_of_stock_book.id, 'name': 'Hết sách'})

    assert res.status_code == 400
    assert "hết bản" in res.get_json().get('err_msg', '').lower()


def test_pay_overdue_blocking(test_client, overdue_user):
    """5. RÀNG BUỘC: Chặn lập phiếu mượn nếu đang có nợ quá hạn"""
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(overdue_user.id)
        sess['cart'] = {"1": {"id": 1, "name": "Sách test"}}

    res = test_client.post('/api/pay')

    assert res.status_code == 400
    assert "quá hạn" in res.get_json().get('err_msg', '').lower()


def test_pay_success_logic(test_client, sample_data, test_session):
    """6. QUY TRÌNH CHÍNH: Tạo phiếu mượn thực tế và trừ tồn kho"""
    user = sample_data['users'][0]
    book = sample_data['books'][1]
    book_id = book.id

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {str(book_id): {"id": book_id, "name": "Sách Test"}}

    res = test_client.post('/api/pay', json={
        'phone': '0987654321',
        'returnDate': '2026-05-01'
    })

    assert res.status_code == 200

    # Kiểm tra database: Tồn kho phải giảm
    updated_book = test_session.get(Sach, book_id)
    assert updated_book.so_luong_con == 9

    # Kiểm tra phiếu mượn đã được tạo
    receipt = test_session.query(PhieuMuon).filter_by(ma_nguoi_dung=user.id).first()
    assert receipt is not None

    # SỬA LỖI 1: Kiểm tra cart rỗng thay vì "not in"
    with test_client.session_transaction() as sess:
        # Nếu code của bạn xóa cart bằng sess.pop('cart'), dùng: assert 'cart' not in sess
        # Nếu code của bạn gán sess['cart'] = {}, dùng dòng dưới đây:
        assert len(sess.get('cart', {})) == 0


def test_pay_empty_cart(test_client, sample_data):
    """7. Kiểm tra lỗi khi xác nhận mượn với túi mượn rỗng"""
    user = sample_data['users'][0]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        # Giả lập túi mượn rỗng
        sess['cart'] = {}

    # SỬA LỖI 2: Gửi kèm json={} để tránh lỗi 415
    res = test_client.post('/api/pay', json={})

    assert res.status_code == 400
    assert "trống" in res.get_json().get('err_msg', '').lower()