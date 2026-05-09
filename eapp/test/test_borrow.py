import pytest
from eapp.test.test_base import test_client, test_app, sample_data, test_session, overdue_user
from eapp.models import Sach, PhieuMuon, ChiTietMuon


# --- NHÓM 1: KIỂM THỬ THÊM VÀO TÚI MƯỢN (CART) ---

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


def test_add_to_cart_unauthorized(test_client, sample_data):
    """2. RÀNG BUỘC: Chưa đăng nhập không được phép mượn sách"""
    book = sample_data['books'][1]
    # Không set _user_id vào session
    res = test_client.post('/api/cart', json={'id': book.id, 'name': book.ten_sach})

    # Flask-Login sẽ trả về 401 hoặc redirect về trang login
    assert res.status_code in [401, 302]


def test_add_to_cart_duplicate(test_client, sample_data):
    """3. RÀNG BUỘC: Không cho phép thêm trùng 1 cuốn sách vào túi"""
    user = sample_data['users'][0]
    book_id = str(sample_data['books'][1].id)

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        # Giả lập túi đã có sách này
        sess['cart'] = {book_id: {'id': book_id, 'name': 'Sách đã có'}}

    res = test_client.post('/api/cart', json={'id': book_id, 'name': 'Sách thêm trùng'})

    assert res.status_code == 400
    assert "đã có trong danh sách chờ" in res.get_json().get('err_msg', '').lower()


def test_add_to_cart_blocked_user(test_client, sample_data):
    """4. RÀNG BUỘC: Tài khoản bị khóa không được phép mượn sách"""
    blocked_user = sample_data['users'][1]

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(blocked_user.id)

    res = test_client.post('/api/cart', json={'id': 1, 'name': 'Test'})
    assert res.status_code == 403


def test_add_to_cart_over_limit_5_books(test_client, sample_data):
    """5. RÀNG BUỘC: Không cho mượn quá 5 cuốn (Tổng đang mượn + trong túi)"""
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
    """6. RÀNG BUỘC: Không cho mượn nếu sách đã hết bản"""
    user = sample_data['users'][0]
    out_of_stock_book = sample_data['books'][0]  # Cuốn có so_luong_con=0

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.post('/api/cart', json={'id': out_of_stock_book.id, 'name': 'Hết sách'})

    assert res.status_code == 400
    assert "hết bản" in res.get_json().get('err_msg', '').lower()


# --- NHÓM 2: KIỂM THỬ XÁC NHẬN MƯỢN (PAY/RECEIPT) ---

def test_pay_overdue_blocking(test_client, overdue_user):
    """7. RÀNG BUỘC: Chặn lập phiếu mượn nếu đang có nợ quá hạn"""
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(overdue_user.id)
        sess['cart'] = {"1": {"id": 1, "name": "Sách test"}}

    res = test_client.post('/api/pay', json={})  # Bổ sung json rỗng để tránh lỗi 415

    assert res.status_code == 400
    assert "quá hạn" in res.get_json().get('err_msg', '').lower()


def test_pay_success_logic(test_client, sample_data, test_session):
    """8. QUY TRÌNH CHÍNH: Tạo phiếu mượn, trừ tồn kho và xóa túi mượn"""
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

    # Kiểm tra tồn kho giảm
    updated_book = test_session.get(Sach, book_id)
    assert updated_book.so_luong_con == 9

    # Kiểm tra phiếu mượn được tạo trong DB
    receipt = test_session.query(PhieuMuon).filter_by(ma_nguoi_dung=user.id).first()
    assert receipt is not None

    # Kiểm tra túi mượn đã được làm rỗng
    with test_client.session_transaction() as sess:
        assert len(sess.get('cart', {})) == 0


def test_pay_exception_with_mock(test_client, mocker, sample_data):
    """9. KỸ THUẬT MOCKING: Giả lập lỗi server khi lập phiếu (Giống saleapp)"""
    user = sample_data['users'][0]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {"1": {"id": 1, "name": "Lỗi"}}

    # Giả lập hàm create_borrow_receipt trong dao.py ném ra lỗi
    mock_dao = mocker.patch('eapp.dao.create_borrow_receipt', side_effect=Exception("DB Error"))

    res = test_client.post('/api/pay', json={'phone': '0123'})

    assert res.status_code == 500
    assert "db error" in res.get_json().get('err_msg', '').lower()
    mock_dao.assert_called_once()


def test_api_remove_cart_item(test_client, sample_data):
    """10. Kiểm tra API xóa sách khỏi túi mượn (Đã sửa lỗi Login)"""
    user = sample_data['users'][0]  # Lấy user mẫu để đăng nhập
    book_id = str(sample_data['books'][1].id)

    with test_client.session_transaction() as sess:
        # ĐĂNG NHẬP: Gán ID người dùng vào session
        sess['_user_id'] = str(user.id)
        # Giả lập túi mượn đang có sách
        sess['cart'] = {book_id: {'id': book_id, 'name': 'Xóa tôi'}}

    # Bây giờ gọi API DELETE sẽ thành công
    res = test_client.delete(f'/api/cart/{book_id}')

    assert res.status_code == 200

    with test_client.session_transaction() as sess:
        assert book_id not in sess.get('cart', {})


def test_add_to_cart_limit_mix_db_and_session(test_client, test_session, sample_data):
    """
    RÀNG BUỘC: Tổng 5 cuốn bao gồm sách đang mượn (DB) và sách trong giỏ (Session).
    Kịch bản: Đang mượn 3 cuốn + Giỏ có 2 cuốn -> Thêm cuốn thứ 3 vào giỏ (tổng 6) phải bị chặn.
    """
    user = sample_data['users'][0]
    books = sample_data['books']

    # 1. SETUP: Giả lập User đang mượn thực tế 3 cuốn trong Database
    from eapp.models import PhieuMuon, ChiTietMuon, TrangThaiMuon
    from datetime import datetime, timedelta

    phieu = PhieuMuon(ma_nguoi_dung=user.id,
                      han_tra=datetime.now() + timedelta(days=14),
                      trang_thai=TrangThaiMuon.DANG_MUON)
    test_session.add(phieu)
    test_session.commit()

    # Thêm 3 cuốn vào phiếu mượn này
    for i in range(10, 13):
        test_session.add(ChiTietMuon(ma_phieu=phieu.id, ma_sach=books[i].id))
    test_session.commit()

    # 2. SESSION: Giả lập giỏ hàng đang có 2 cuốn khác
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {
            str(books[20].id): {'id': books[20].id, 'name': 'Sách giỏ 1'},
            str(books[21].id): {'id': books[21].id, 'name': 'Sách giỏ 2'}
        }

    # 3. ACTION: Thêm cuốn tiếp theo (Cuốn thứ 6 tính tổng cộng)
    res = test_client.post('/api/cart', json={
        'id': books[22].id,
        'name': books[22].ten_sach
    })

    # 4. ASSERT: Phải bị chặn với lỗi tối đa 5 cuốn
    assert res.status_code == 400
    assert "tối đa 5 cuốn" in res.get_json().get('err_msg', '').lower()