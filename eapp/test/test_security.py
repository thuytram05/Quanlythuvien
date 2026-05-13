import pytest
from eapp.test.test_base import test_client, test_app, sample_data, test_session
from eapp.models import VaiTro, NguoiDung, PhieuMuon, TrangThaiMuon, ChiTietMuon
from datetime import datetime, timedelta
from eapp.dao import create_borrow_receipt

def test_admin_access_unauthenticated_redirect(test_client):
    res = test_client.get('/admin/', follow_redirects=True)
    assert "/login" in res.request.path

    res_sach = test_client.get('/admin/sach/', follow_redirects=True)
    assert "/login" in res_sach.request.path


def test_admin_access_denied_for_regular_user(test_client, sample_data):
    user = sample_data['users'][0]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    admin_routes = ['/admin/', '/admin/theloai/', '/admin/sach/', '/admin/stats/']

    for route in admin_routes:
        res = test_client.get(route, follow_redirects=True)

        assert "HỆ THỐNG THƯ VIỆN" not in res.get_data(as_text=True)

        if res.request.path == '/':
            assert res.status_code == 200
        else:
            assert "Danh Mục Sách" not in res.get_data(as_text=True)
            assert "Thống Kê" not in res.get_data(as_text=True)

def test_admin_access_granted_for_admin_user(test_client, sample_data, test_session):
    admin_user = NguoiDung(
        ten='Admin Test',
        ten_dang_nhap='admin_secure',
        mat_khau='hash_here',
        vai_tro=VaiTro.QUAN_TRI
    )
    test_session.add(admin_user)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(admin_user.id)

    res = test_client.get('/admin/')
    assert res.status_code == 200
    assert "HỆ THỐNG THƯ VIỆN" in res.get_data(as_text=True)


def test_admin_logout_view_security(test_client, sample_data):
    user = sample_data['users'][0]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.get('/admin/logoutview/', follow_redirects=True)

    assert res.status_code == 200
    with test_client.session_transaction() as sess:
        assert '_user_id' not in sess

def test_admin_api_stats_forbidden_for_user(test_client, sample_data):
    user = sample_data['users'][0]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.get('/api/stats')
    assert res.status_code == 403
    assert "Không có quyền" in res.get_json()['err_msg']

def test_security_overdue_auto_update_and_block(test_client, test_session, sample_data):
    user = sample_data['users'][0]

    yesterday = datetime.now() - timedelta(days=1)
    pm = PhieuMuon(ma_nguoi_dung=user.id,
                   han_tra=yesterday,
                   trang_thai=TrangThaiMuon.DANG_MUON)
    test_session.add(pm)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {'1': {'id': '1'}}

    res = test_client.post('/api/pay', json={'phone': '0123456789'})

    assert res.status_code == 400
    assert "nợ sách quá hạn" in res.get_json()['err_msg']

    test_session.refresh(pm)
    assert pm.trang_thai == TrangThaiMuon.QUA_HAN

def test_security_borrow_limit_exact_5(test_client, test_session, sample_data):
    user = sample_data['users'][0]

    for i in range(5):
        pm = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now() + timedelta(days=7))
        test_session.add(pm)
        test_session.flush()  # Để có ID phiếu mượn
        ct = ChiTietMuon(ma_phieu=pm.id, ma_sach=sample_data['books'][i].id)
        test_session.add(ct)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.post('/api/cart', json={'id': sample_data['books'][5].id})

    assert res.status_code == 400
    assert "tối đa 5 cuốn" in res.get_json()['err_msg']

def test_security_borrow_limit_with_cart_items(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    books = sample_data['books']

    for i in range(3):
        pm = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now() + timedelta(days=7))
        test_session.add(pm)
        test_session.flush()
        ct = ChiTietMuon(ma_phieu=pm.id, ma_sach=books[i].id)
        test_session.add(ct)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {
            str(books[3].id): {'id': books[3].id},
            str(books[4].id): {'id': books[4].id}
        }

    res = test_client.post('/api/cart', json={
        'id': books[5].id,
        'name': books[5].ten_sach
    })

    assert res.status_code == 400
    assert "tối đa 5 cuốn" in res.get_json()['err_msg']

def test_security_return_book_clears_limit(test_client, test_session, sample_data):
    user = sample_data['users'][0]

    pm = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now() + timedelta(days=7))
    test_session.add(pm)
    test_session.flush()
    for i in range(5):
        ct = ChiTietMuon(ma_phieu=pm.id, ma_sach=sample_data['books'][i].id)
        test_session.add(ct)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    test_client.post(f'/tra-sach/{pm.id}', follow_redirects=True)

    res = test_client.post('/api/cart', json={'id': sample_data['books'][0].id})
    assert res.status_code == 200

def test_security_blocked_user_cannot_add_to_cart(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    user.bi_khoa = True
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.post('/api/cart', json={
        'id': sample_data['books'][0].id,
        'name': sample_data['books'][0].ten_sach
    })

    assert res.status_code == 403
    assert "đang bị khóa" in res.get_json()['err_msg']

def test_security_blocked_user_cannot_pay(test_client, test_session, sample_data):
    user = sample_data['users'][1]
    user.bi_khoa = True
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {'1': {'id': '1', 'name': 'Sách Có Sẵn'}}

    res = test_client.post('/api/pay', json={
        'phone': '0987654321',
        'returnDate': '2026-12-31'
    })

    assert res.status_code == 403
    assert "đã bị khóa" in res.get_json()['err_msg']

def test_security_dao_create_receipt_blocked_user_exception(test_session, sample_data):
    user = sample_data['users'][0]
    user.bi_khoa = True
    test_session.commit()

    with pytest.raises(Exception) as excinfo:
        create_borrow_receipt(
            user_id=user.id,
            cart_items=[{'id': sample_data['books'][0].id}],
            phone='0123456789'
        )

    assert "Tài khoản đang bị khóa" in str(excinfo.value)

def test_security_sql_injection_search(test_client):
    payloads = [
        "' OR 1=1 --",
        "'; DROP TABLE NguoiDung; --",
        "\" OR \"a\"=\"a"
    ]

    for payload in payloads:
        res = test_client.get(f'/?kw={payload}')
        assert res.status_code == 200
        data = res.get_data(as_text=True)
        assert "Sách Tự Động" not in data

def test_security_sql_injection_login(test_client):
    res = test_client.post('/login', data={
        'username': "' OR '1'='1",
        'password': "any_password"
    }, follow_redirects=True)

    assert "Tên đăng nhập hoặc mật khẩu không đúng" in res.get_data(as_text=True)
    assert res.request.path == '/login'

def test_security_unauthorized_return_book(test_client, test_session, sample_data):
    user_a = sample_data['users'][0]
    user_b = sample_data['users'][1]

    pm_b = PhieuMuon(ma_nguoi_dung=user_b.id, han_tra=datetime.now())
    test_session.add(pm_b)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user_a.id)

    res = test_client.post(f'/tra-sach/{pm_b.id}', follow_redirects=True)

    data = res.get_data(as_text=True)
    assert "Không tìm thấy phiếu mượn của bạn" in data

    test_session.refresh(pm_b)
    assert pm_b.trang_thai == TrangThaiMuon.DANG_MUON

def test_security_xss_protection_in_search(test_client):
    payload = "<script>alert('xss')</script>"
    res = test_client.get(f'/?kw={payload}')

    assert payload not in res.get_data(as_text=True)

def test_security_pay_invalid_return_date(test_client, sample_data):
    user = sample_data['users'][0]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {'1': {'id': '1'}}

    past_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    res_past = test_client.post('/api/pay', json={'phone': '0123456789', 'returnDate': past_date})
    assert "nhỏ hơn ngày hiện tại" in res_past.get_json()['err_msg']

    future_date = (datetime.now() + timedelta(days=16)).strftime('%Y-%m-%d')
    res_future = test_client.post('/api/pay', json={'phone': '0123456789', 'returnDate': future_date})
    assert "quá 14 ngày" in res_future.get_json()['err_msg']

def test_security_pay_invalid_phone_format(test_client, sample_data):
    user = sample_data['users'][0]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {'1': {'id': '1'}}

    res = test_client.post('/api/pay', json={'phone': '090-ABC-123'})
    assert res.status_code == 400
    assert "định dạng" in res.get_json()['err_msg'].lower()

def test_security_pay_note_length_limit(test_client, sample_data):
    user = sample_data['users'][0]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['cart'] = {'1': {'id': '1'}}

    long_note = "A" * 256
    res = test_client.post('/api/pay', json={'phone': '0123456789', 'note': long_note})
    assert res.status_code == 400
    assert "255 ký tự" in res.get_json()['err_msg']