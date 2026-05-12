import pytest
from datetime import datetime, timedelta
from eapp.test.test_base import test_client, test_app, sample_data, test_session, overdue_user
from eapp.models import Sach, PhieuMuon, ChiTietMuon, TrangThaiMuon

def test_add_to_cart_success(test_client, sample_data):
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
    book = sample_data['books'][1]
    res = test_client.post('/api/cart', json={'id': book.id, 'name': book.ten_sach})
    assert res.status_code in [401, 302]

def test_add_to_cart_duplicate(test_client, sample_data):
    user = sample_data['users'][0]
    book_id = str(sample_data['books'][1].id)
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {book_id: {'id': book_id, 'name': 'Sách đã có'}}
    res = test_client.post('/api/cart', json={'id': book_id, 'name': 'Sách thêm trùng'})
    assert res.status_code == 400
    assert "đã có trong danh sách chờ" in res.get_json().get('err_msg', '').lower()

def test_add_to_cart_blocked_user(test_client, sample_data):
    blocked_user = sample_data['users'][1]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(blocked_user.id)
    res = test_client.post('/api/cart', json={'id': 1, 'name': 'Test'})
    assert res.status_code == 403

def test_add_to_cart_over_limit_5_books(test_client, sample_data):
    user = sample_data['users'][0]
    valid_book_id = sample_data['books'][1].id
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {str(i): {'id': i, 'name': 'Sách cũ'} for i in range(100, 105)}
    res = test_client.post('/api/cart', json={'id': valid_book_id, 'name': 'Cuốn thứ 6'})
    assert res.status_code == 400
    assert "tối đa 5 cuốn" in res.get_json().get('err_msg', '').lower()

def test_add_to_cart_out_of_stock(test_client, sample_data):
    user = sample_data['users'][0]
    out_of_stock_book = sample_data['books'][0]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
    res = test_client.post('/api/cart', json={'id': out_of_stock_book.id, 'name': 'Hết sách'})
    assert res.status_code == 400
    assert "hết bản" in res.get_json().get('err_msg', '').lower()

def test_pay_overdue_blocking(test_client, overdue_user):
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(overdue_user.id)
        sess['cart'] = {"1": {"id": 1, "name": "Sách test"}}
    res = test_client.post('/api/pay', json={})
    assert res.status_code == 400
    assert "quá hạn" in res.get_json().get('err_msg', '').lower()

def test_pay_success_logic(test_client, sample_data, test_session):
    user = sample_data['users'][0]
    book = sample_data['books'][1]
    book_id = book.id
    valid_return_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {str(book_id): {"id": book_id, "name": "Sách Test"}}
    res = test_client.post('/api/pay', json={
        'phone': '0987654321',
        'returnDate': valid_return_date
    })
    assert res.status_code == 200
    updated_book = test_session.get(Sach, book_id)
    assert updated_book.so_luong_con == 9
    receipt = test_session.query(PhieuMuon).filter_by(ma_nguoi_dung=user.id).first()
    assert receipt is not None
    with test_client.session_transaction() as sess:
        assert len(sess.get('cart', {})) == 0

def test_pay_exception_with_mock(test_client, mocker, sample_data):
    user = sample_data['users'][0]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {"1": {"id": 1, "name": "Lỗi"}}
    mock_dao = mocker.patch('eapp.dao.create_borrow_receipt', side_effect=Exception("DB Error"))
    res = test_client.post('/api/pay', json={'phone': '0123'})
    assert res.status_code == 500
    assert "db error" in res.get_json().get('err_msg', '').lower()
    mock_dao.assert_called_once()

def test_api_remove_cart_item(test_client, sample_data):
    user = sample_data['users'][0]
    book_id = str(sample_data['books'][1].id)
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {book_id: {'id': book_id, 'name': 'Xóa tôi'}}
    res = test_client.delete(f'/api/cart/{book_id}')
    assert res.status_code == 200
    with test_client.session_transaction() as sess:
        assert book_id not in sess.get('cart', {})

def test_add_to_cart_limit_mix_db_and_session(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    books = sample_data['books']
    phieu = PhieuMuon(ma_nguoi_dung=user.id,
                      han_tra=datetime.now() + timedelta(days=14),
                      trang_thai=TrangThaiMuon.DANG_MUON)
    test_session.add(phieu)
    test_session.commit()
    for i in range(10, 13):
        test_session.add(ChiTietMuon(ma_phieu=phieu.id, ma_sach=books[i].id))
    test_session.commit()
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {
            str(books[20].id): {'id': books[20].id, 'name': 'Sách giỏ 1'},
            str(books[21].id): {'id': books[21].id, 'name': 'Sách giỏ 2'}
        }
    res = test_client.post('/api/cart', json={
        'id': books[22].id,
        'name': books[22].ten_sach
    })
    assert res.status_code == 400
    assert "tối đa 5 cuốn" in res.get_json().get('err_msg', '').lower()

def test_pay_rollback_on_error(test_client, test_session, sample_data, mocker):
    user = sample_data['users'][0]
    book = sample_data['books'][1]
    book_id = book.id
    initial_stock = book.so_luong_con
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {str(book_id): {"id": book_id, "name": "Sách Test", "price": 0}}
    mocker.patch('eapp.dao.create_borrow_receipt', side_effect=Exception("Lỗi hệ thống bất ngờ"))
    res = test_client.post('/api/pay', json={'phone': '0123'})
    assert res.status_code == 500
    test_session.refresh(book)
    assert book.so_luong_con == initial_stock

def test_add_to_cart_overdue_blocking(test_client, overdue_user):
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(overdue_user.id)
    res = test_client.post('/api/cart', json={'id': 2, 'name': 'Sách mới'})
    assert res.status_code == 400
    assert "nợ sách quá hạn" in res.get_json().get('err_msg', '').lower()

def test_pay_empty_cart_blocking(test_client, sample_data):
    user = sample_data['users'][0]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {}
    res = test_client.post('/api/pay', json={'phone': '0123'})
    assert res.status_code == 400
    assert "túi mượn đang trống" in res.get_json().get('err_msg', '').lower()

def test_pay_multiple_books_integrity(test_client, sample_data, test_session):
    user = sample_data['users'][0]
    b1 = sample_data['books'][1]
    b2 = sample_data['books'][2]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {
            str(b1.id): {"id": b1.id, "name": b1.ten_sach},
            str(b2.id): {"id": b2.id, "name": b2.ten_sach}
        }
    res = test_client.post('/api/pay', json={'phone': '0987654321'})
    assert res.status_code == 200
    test_session.refresh(b1)
    test_session.refresh(b2)
    assert b1.so_luong_con == 9
    assert b2.so_luong_con == 9

def test_add_to_cart_already_holding_in_db(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    book = sample_data['books'][5]
    now = datetime.now()
    phieu = PhieuMuon(
        ma_nguoi_dung=user.id,
        trang_thai=TrangThaiMuon.DANG_MUON,
        ngay_muon=now,
        han_tra=now + timedelta(days=14)
    )
    test_session.add(phieu)
    test_session.commit()
    test_session.add(ChiTietMuon(ma_phieu=phieu.id, ma_sach=book.id))
    test_session.commit()
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
    res = test_client.post('/api/cart', json={'id': book.id, 'name': book.ten_sach})
    assert res.status_code == 200

def test_pay_invalid_return_date(test_client, sample_data, mocker):
    user = sample_data['users'][0]
    valid_future_date = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {"1": {"id": 1, "name": "Sách Test"}}
    mocker.patch('eapp.dao.create_borrow_receipt', side_effect=Exception("Lỗi hệ thống bất ngờ"))
    res = test_client.post('/api/pay', json={
        'phone': '0123456789',
        'returnDate': valid_future_date
    })
    assert res.status_code == 500

def test_pay_date_in_past(test_client, sample_data):
    user = sample_data['users'][0]
    past_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {"1": {"id": 1, "name": "Sách Test"}}
    res = test_client.post('/api/pay', json={
        'phone': '0987654321',
        'returnDate': past_date
    })
    assert res.status_code == 400
    assert "nhỏ hơn ngày hiện tại" in res.get_json().get('err_msg', '').lower()

def test_pay_date_exceed_14_days(test_client, sample_data):
    user = sample_data['users'][0]
    future_date = (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d')
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {"1": {"id": 1, "name": "Sách Test"}}
    res = test_client.post('/api/pay', json={
        'phone': '0987654321',
        'returnDate': future_date
    })
    assert res.status_code == 400
    assert "14 ngày" in res.get_json().get('err_msg', '').lower()

def test_pay_date_exactly_14_days(test_client, sample_data):
    user = sample_data['users'][0]
    book = sample_data['books'][1]
    edge_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {str(book.id): {"id": book.id, "name": book.ten_sach}}
    res = test_client.post('/api/pay', json={
        'phone': '0987654321',
        'returnDate': edge_date
    })
    assert res.status_code == 200

def test_pay_invalid_date_format_string(test_client, sample_data):
    user = sample_data['users'][0]
    invalid_date = "abc-xyz-2026"
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {"1": {"id": 1, "name": "Sách Test"}}
    res = test_client.post('/api/pay', json={
        'phone': '0987654321',
        'returnDate': invalid_date
    })
    assert res.status_code == 400
    assert "định dạng" in res.get_json().get('err_msg', '').lower()

def test_pay_phone_required(test_client, sample_data):
    user = sample_data['users'][0]
    future_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {"1": {"id": 1, "name": "Sách Test"}}
    res = test_client.post('/api/pay', json={
        'phone': '',
        'returnDate': future_date
    })
    assert res.status_code == 400
    assert "số điện thoại" in res.get_json().get('err_msg', '').lower()

def test_pay_invalid_phone_format(test_client, sample_data):
    user = sample_data['users'][0]
    future_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {"1": {"id": 1, "name": "Sách Test"}}
    res = test_client.post('/api/pay', json={
        'phone': '0987abc123',
        'returnDate': future_date
    })
    assert res.status_code == 400
    assert "định dạng" in res.get_json().get('err_msg', '').lower()

def test_pay_note_too_long(test_client, sample_data):
    user = sample_data['users'][0]
    future_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    long_note = "x" * 300
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {"1": {"id": 1, "name": "Sách Test"}}
    res = test_client.post('/api/pay', json={
        'phone': '0987654321',
        'returnDate': future_date,
        'note': long_note
    })
    assert res.status_code == 400
    assert "ghi chú" in res.get_json().get('err_msg', '').lower()

def test_pay_blocked_user_last_minute(test_client, sample_data, test_session):
    user = sample_data['users'][0]
    user.bi_khoa = True
    test_session.add(user)
    test_session.commit()
    future_date = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {"1": {"id": 1, "name": "Sách Test"}}
    res = test_client.post('/api/pay', json={
        'phone': '0987654321',
        'returnDate': future_date
    })
    assert res.status_code == 403
    assert "bị khóa" in res.get_json().get('err_msg', '').lower()

def test_pay_unauthorized_access(test_client):
    res = test_client.post('/api/pay', json={
        'phone': '0987654321',
        'returnDate': '2026-05-20'
    })
    assert res.status_code in [401, 302]

def test_pay_book_deleted_last_minute(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    book = sample_data['books'][1]
    book_id = book.id
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {str(book_id): {"id": book_id, "name": book.ten_sach}}
    book_to_delete = test_session.get(Sach, book_id)
    test_session.delete(book_to_delete)
    test_session.commit()
    res = test_client.post('/api/pay', json={'phone': '0987654321'})
    assert res.status_code == 500
    err_msg = res.get_json().get('err_msg', '').lower()
    assert "hết bản" in err_msg
    assert f"id:{book_id}" in err_msg

def test_pay_out_of_stock_last_minute(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    book = sample_data['books'][2]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {str(book.id): {"id": book.id, "name": book.ten_sach}}
    book.so_luong_con = 0
    test_session.add(book)
    test_session.commit()
    res = test_client.post('/api/pay', json={'phone': '0987654321'})
    assert res.status_code == 500
    assert "hết bản" in res.get_json().get('err_msg', '').lower()

def test_remove_non_existent_book_from_cart(test_client, sample_data):
    user = sample_data['users'][0]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {"1": {"id": 1, "name": "Sách thực tế"}}
    res = test_client.delete('/api/cart/9999')
    assert res.status_code in [200, 404]
    with test_client.session_transaction() as sess:
        assert "1" in sess.get('cart', {})

def test_clear_all_cart_success(test_client, sample_data):
    user = sample_data['users'][0]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {
            "1": {"id": 1, "name": "Sách 1"},
            "2": {"id": 2, "name": "Sách 2"}
        }
    res = test_client.delete('/api/cart')
    assert res.status_code == 200
    with test_client.session_transaction() as sess:
        assert len(sess.get('cart', {})) == 0

def test_pay_invalid_date_format_slash(test_client, sample_data):
    user = sample_data['users'][0]
    invalid_date = "20/05/2026"
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {"1": {"id": 1, "name": "Sách Test"}}
    res = test_client.post('/api/pay', json={
        'phone': '0987654321',
        'returnDate': invalid_date
    })
    assert res.status_code == 400
    assert "định dạng" in res.get_json().get('err_msg', '').lower()

def test_add_to_cart_invalid_id(test_client, sample_data):
    user = sample_data['users'][0]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
    res = test_client.post('/api/cart', json={
        'id': 999999,
        'name': 'Sách ma'
    })
    assert res.status_code == 400
    assert "hết bản" in res.get_json().get('err_msg', '').lower()

def test_cart_retention_on_payment_failure(test_client, sample_data):
    user = sample_data['users'][0]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {"1": {"id": 1, "name": "Sách giữ lại"}}
    test_client.post('/api/pay', json={'phone': 'abc', 'returnDate': '2026-05-20'})
    with test_client.session_transaction() as sess:
        assert "1" in sess.get('cart', {})