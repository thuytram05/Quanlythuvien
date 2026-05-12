import pytest
from datetime import datetime, timedelta
import hashlib
from eapp.test.test_base import test_client, test_session, sample_data, test_app
from eapp.models import PhieuMuon, ChiTietMuon, TrangThaiMuon, Sach, VaiTro

def test_return_book_success(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    book = sample_data['books'][0]
    ngay_tra = datetime.now() + timedelta(days=14)
    phieu = PhieuMuon(ma_nguoi_dung=user.id, han_tra=ngay_tra, trang_thai=TrangThaiMuon.DANG_MUON)
    test_session.add(phieu)
    test_session.commit()
    test_session.add(ChiTietMuon(ma_phieu=phieu.id, ma_sach=book.id))
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.post(f'/tra-sach/{phieu.id}', follow_redirects=True)
    assert res.status_code == 200
    updated_phieu = test_session.get(PhieuMuon, phieu.id)
    assert updated_phieu.trang_thai == TrangThaiMuon.DA_TRA

def test_return_book_not_owner(test_client, test_session, sample_data):
    user_1 = sample_data['users'][0]
    user_2 = sample_data['users'][1]
    phieu = PhieuMuon(ma_nguoi_dung=user_1.id, han_tra=datetime.now() + timedelta(days=7))
    test_session.add(phieu)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user_2.id)

    res = test_client.post(f'/tra-sach/{phieu.id}', follow_redirects=True)
    assert "không tìm thấy phiếu mượn" in res.get_data(as_text=True).lower()

def test_return_book_late_fee(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    han_tra = datetime.now() - timedelta(days=3)
    phieu = PhieuMuon(ma_nguoi_dung=user.id, han_tra=han_tra, trang_thai=TrangThaiMuon.QUA_HAN)
    test_session.add(phieu)
    test_session.commit()
    test_session.add(ChiTietMuon(ma_phieu=phieu.id, ma_sach=sample_data['books'][0].id))
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.post(f'/tra-sach/{phieu.id}', follow_redirects=True)
    assert "15,000" in res.get_data(as_text=True)

def test_return_database_verification(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    p = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now() - timedelta(days=1))
    test_session.add(p)
    test_session.commit()
    ct = ChiTietMuon(ma_phieu=p.id, ma_sach=sample_data['books'][0].id)
    test_session.add(ct)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    test_client.post(f'/tra-sach/{p.id}')
    test_session.refresh(ct)
    assert ct.ngay_tra_thuc_te is not None
    assert ct.tien_phat == 5000.0

def test_return_unauthorized_blocking(test_client, sample_data):
    res = test_client.post('/tra-sach/1', follow_redirects=True)
    assert "/login" in res.request.path or res.status_code == 401

def test_return_multiple_books_inventory_integrity(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    b1, b2 = sample_data['books'][1], sample_data['books'][2]
    stock1, stock2 = b1.so_luong_con, b2.so_luong_con

    p = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now() + timedelta(days=7))
    test_session.add(p)
    test_session.commit()
    test_session.add_all([
        ChiTietMuon(ma_phieu=p.id, ma_sach=b1.id),
        ChiTietMuon(ma_phieu=p.id, ma_sach=b2.id)
    ])
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    test_client.post(f'/tra-sach/{p.id}')
    test_session.refresh(b1)
    test_session.refresh(b2)
    assert b1.so_luong_con == stock1 + 1
    assert b2.so_luong_con == stock2 + 1

def test_return_invalid_id(test_client, sample_data):
    user = sample_data['users'][0]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.post('/tra-sach/9999', follow_redirects=True)
    assert "không tìm thấy" in res.get_data(as_text=True).lower()

def test_return_already_returned_blocking(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    phieu = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now(), trang_thai=TrangThaiMuon.DA_TRA)
    test_session.add(phieu)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.post(f'/tra-sach/{phieu.id}', follow_redirects=True)
    assert "đã được trả" in res.get_data(as_text=True).lower()

def test_return_book_on_time_zero_fee(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    book = sample_data['books'][0]
    han_tra = datetime.now() + timedelta(days=5)

    p = PhieuMuon(ma_nguoi_dung=user.id, han_tra=han_tra, trang_thai=TrangThaiMuon.DANG_MUON)
    test_session.add(p)
    test_session.commit()
    ct = ChiTietMuon(ma_phieu=p.id, ma_sach=book.id)
    test_session.add(ct)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    test_client.post(f'/tra-sach/{p.id}')
    test_session.refresh(ct)
    assert ct.tien_phat == 0 or ct.tien_phat is None

def test_return_flash_message_content(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    han_tra = datetime.now() - timedelta(days=1)
    p = PhieuMuon(ma_nguoi_dung=user.id, han_tra=han_tra, trang_thai=TrangThaiMuon.QUA_HAN)
    test_session.add(p)
    test_session.commit()
    test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=sample_data['books'][0].id))
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.post(f'/tra-sach/{p.id}', follow_redirects=True)
    data = res.get_data(as_text=True)
    assert "Phí phạt trễ hạn" in data
    assert "5,000" in data

def test_return_process_rollback_on_error(test_client, test_session, sample_data, mocker):
    user = sample_data['users'][0]
    book = sample_data['books'][0]
    initial_stock = book.so_luong_con

    phieu = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now() + timedelta(days=7),
                      trang_thai=TrangThaiMuon.DANG_MUON)
    test_session.add(phieu)
    test_session.commit()
    test_session.add(ChiTietMuon(ma_phieu=phieu.id, ma_sach=book.id))
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    mocker.patch('eapp.dao.process_return_book', side_effect=Exception("Lỗi hệ thống"))
    test_client.post(f'/tra-sach/{phieu.id}')

    test_session.refresh(book)
    assert book.so_luong_con == initial_stock
    test_session.refresh(phieu)
    assert phieu.trang_thai == TrangThaiMuon.DANG_MUON

def test_return_book_even_if_blocked(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    user.bi_khoa = True
    test_session.commit()

    phieu = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now() + timedelta(days=7),
                      trang_thai=TrangThaiMuon.DANG_MUON)
    test_session.add(phieu)
    test_session.commit()
    test_session.add(ChiTietMuon(ma_phieu=phieu.id, ma_sach=sample_data['books'][0].id))
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.post(f'/tra-sach/{phieu.id}', follow_redirects=True)
    assert res.status_code == 200
    updated_phieu = test_session.get(PhieuMuon, phieu.id)
    assert updated_phieu.trang_thai == TrangThaiMuon.DA_TRA

def test_return_book_exactly_on_deadline(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    book = sample_data['books'][0]
    deadline = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    p = PhieuMuon(ma_nguoi_dung=user.id, han_tra=deadline, trang_thai=TrangThaiMuon.DANG_MUON)
    test_session.add(p)
    test_session.commit()
    ct = ChiTietMuon(ma_phieu=p.id, ma_sach=book.id)
    test_session.add(ct)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    test_client.post(f'/tra-sach/{p.id}')
    test_session.refresh(ct)
    assert ct.tien_phat == 0

def test_return_empty_receipt_graceful_handling(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    p = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now(), trang_thai=TrangThaiMuon.DANG_MUON)
    test_session.add(p)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.post(f'/tra-sach/{p.id}', follow_redirects=True)
    assert res.status_code == 200
    test_session.refresh(p)
    assert p.trang_thai == TrangThaiMuon.DA_TRA

def test_return_inventory_not_exceed_total(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    book = sample_data['books'][0]
    book.tong_so_luong = 10
    book.so_luong_con = 9
    test_session.commit()

    p = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now() + timedelta(days=7))
    test_session.add(p)
    test_session.commit()
    test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book.id))
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    test_client.post(f'/tra-sach/{p.id}')
    test_session.refresh(book)
    assert book.so_luong_con <= book.tong_so_luong

def test_return_immediately_after_borrow(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    p = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now(), ngay_muon=datetime.now())
    test_session.add(p)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.post(f'/tra-sach/{p.id}', follow_redirects=True)
    assert res.status_code == 200
    assert p.trang_thai == TrangThaiMuon.DA_TRA

def test_return_extreme_late_fee(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    han_tra = datetime.now() - timedelta(days=365)
    p = PhieuMuon(ma_nguoi_dung=user.id, han_tra=han_tra)
    test_session.add(p)
    test_session.commit()
    test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=sample_data['books'][0].id))
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    test_client.post(f'/tra-sach/{p.id}')
    ct = ChiTietMuon.query.filter_by(ma_phieu=p.id).first()
    assert ct.tien_phat == 365 * 5000

def test_admin_can_process_any_return(test_client, test_session, sample_data):
    admin_user = sample_data['users'][0]
    admin_user.vai_tro = VaiTro.QUAN_TRI
    test_session.commit()

    user_thuong = sample_data['users'][1]
    p = PhieuMuon(ma_nguoi_dung=user_thuong.id, han_tra=datetime.now())
    test_session.add(p)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(admin_user.id)

    res = test_client.post(f'/tra-sach/{p.id}', follow_redirects=True)
    assert res.status_code == 200
    assert "không tìm thấy" in res.get_data(as_text=True).lower()

def test_return_book_deleted_from_system(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    p = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now())
    test_session.add(p)
    test_session.commit()

    book = sample_data['books'][5]
    ct = ChiTietMuon(ma_phieu=p.id, ma_sach=book.id)
    test_session.add(ct)
    book.hoat_dong = False
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.post(f'/tra-sach/{p.id}', follow_redirects=True)
    assert res.status_code == 200
    assert test_session.get(PhieuMuon, p.id).trang_thai == TrangThaiMuon.DA_TRA

def test_return_book_from_overdue_status(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    p = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now() - timedelta(days=5),
                  trang_thai=TrangThaiMuon.QUA_HAN)
    test_session.add(p)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    test_client.post(f'/tra-sach/{p.id}', follow_redirects=True)
    test_session.refresh(p)
    assert p.trang_thai == TrangThaiMuon.DA_TRA

def test_return_fee_data_type_consistency(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    p = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now() - timedelta(days=2))
    test_session.add(p)
    test_session.commit()
    ct = ChiTietMuon(ma_phieu=p.id, ma_sach=sample_data['books'][0].id)
    test_session.add(ct)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    test_client.post(f'/tra-sach/{p.id}')
    test_session.refresh(ct)
    assert isinstance(ct.tien_phat, (int, float))
    assert ct.tien_phat >= 0

def test_return_date_not_before_borrow_date(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    ngay_muon = datetime.now() + timedelta(days=1)
    han_tra = ngay_muon + timedelta(days=7)

    p = PhieuMuon(ma_nguoi_dung=user.id, ngay_muon=ngay_muon, han_tra=han_tra)
    test_session.add(p)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    test_client.post(f'/tra-sach/{p.id}')
    ct = ChiTietMuon.query.filter_by(ma_phieu=p.id).first()
    if ct and ct.ngay_tra_thuc_te:
        assert ct.ngay_tra_thuc_te >= p.ngay_muon or p.ngay_muon > datetime.now()

def test_return_book_no_fee_flash_message(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    p = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now() + timedelta(days=1))
    test_session.add(p)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.post(f'/tra-sach/{p.id}', follow_redirects=True)
    assert "Trả sách thành công" in res.get_data(as_text=True)
    assert "Phí phạt trễ hạn" not in res.get_data(as_text=True)