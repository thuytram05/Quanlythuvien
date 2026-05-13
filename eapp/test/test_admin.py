import pytest
import hashlib

from flask_login import current_user

from eapp.models import NguoiDung, VaiTro, Sach, TheLoai,PhieuMuon,TrangThaiMuon, ChiTietMuon
from eapp.test.test_base import test_client, test_app, test_session, sample_data
from eapp.dao import count_sach_by_theloai
from datetime import datetime,timedelta



def test_admin_access_denied_for_normal_user(test_client, sample_data):
    user = sample_data['users'][0]

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.get('/admin/', follow_redirects=True)
    data = res.get_data(as_text=True).lower()
    assert "quản trị" not in data or "/login" in res.request.path


def test_admin_access_granted_for_admin(test_client, test_session):
    pass_hash = hashlib.md5("123".encode('utf-8')).hexdigest()

    admin = NguoiDung(ten="Admin Test", ten_dang_nhap="admin_test",
                      mat_khau=pass_hash, vai_tro=VaiTro.QUAN_TRI)
    test_session.add(admin)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(admin.id)

    res = test_client.get('/admin/')
    assert res.status_code == 200
    assert "quản trị" in res.get_data(as_text=True).lower()


def test_admin_access_stats_view(test_client, test_session):
    pass_hash = hashlib.md5("123".encode('utf-8')).hexdigest()
    admin = NguoiDung(ten="Admin Stats", ten_dang_nhap="admin_stats",
                      mat_khau=pass_hash, vai_tro=VaiTro.QUAN_TRI)
    test_session.add(admin)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(admin.id)

    res = test_client.get('/admin/statsview/')
    assert res.status_code == 200

def test_admin_block_user_logic(test_session, sample_data):
    user = sample_data['users'][0]
    user.bi_khoa = True
    test_session.commit()

    test_session.refresh(user)
    assert user.bi_khoa is True


def test_admin_add_category_success(test_session):
    new_cate = TheLoai(ten_the_loai="Kinh tế mới")
    test_session.add(new_cate)
    test_session.commit()

    check = test_session.query(TheLoai).filter_by(ten_the_loai="Kinh tế mới").first()
    assert check is not None

def test_admin_add_new_book(test_session, sample_data):
    tl = sample_data['categories'][0]
    new_book = Sach(ten_sach="Sách Admin Mới", tac_gia="Tác giả A",
                    so_luong_con=10, tong_so_luong=10, ma_the_loai=tl.id)
    test_session.add(new_book)
    test_session.commit()
    assert test_session.query(Sach).filter_by(ten_sach="Sách Admin Mới").first() is not None


def test_admin_update_book_stock(test_session, sample_data):
    book = sample_data['books'][1]
    book.so_luong_con = 99
    test_session.commit()
    test_session.refresh(book)
    assert book.so_luong_con == 99


def test_admin_delete_book_safe(test_session, sample_data):
    book = sample_data['books'][5]
    book_id = book.id
    test_session.delete(book)
    test_session.commit()
    assert test_session.get(Sach, book_id) is None


def test_admin_add_duplicate_category(test_session, sample_data):
    existing_name = sample_data['categories'][0].ten_the_loai

    duplicate_cate = TheLoai(ten_the_loai=existing_name)
    test_session.add(duplicate_cate)

    with pytest.raises(Exception):
        test_session.commit()


def test_admin_delete_book_in_use_integrity(test_session, sample_data):
    book = sample_data['books'][0]
    user = sample_data['users'][0]
    now = datetime.now()

    p = PhieuMuon(
        ma_nguoi_dung=user.id,
        ngay_muon=now,
        han_tra=now + timedelta(days=14),
        trang_thai=TrangThaiMuon.DANG_MUON
    )
    test_session.add(p)
    test_session.commit()

    test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book.id))
    test_session.commit()

    with pytest.raises(Exception):
        test_session.delete(book)
        test_session.commit()

    test_session.rollback()


def test_admin_delete_category_with_books_integrity(test_session, sample_data):
    tl = sample_data['categories'][0]

    with pytest.raises(Exception):
        test_session.delete(tl)
        test_session.commit()

    test_session.rollback()

def test_admin_stats_data_accuracy(test_session, sample_data):
    stats = count_sach_by_theloai()

    assert len(stats) > 0

    assert stats[0][1] == sample_data['categories'][0].ten_the_loai

def test_admin_unblock_user_logic(test_session, sample_data):
    user = sample_data['users'][1]
    user.bi_khoa = False
    test_session.commit()

    test_session.refresh(user)
    assert user.bi_khoa is False

def test_admin_delete_book_transaction_rollback(test_session, sample_data):
    book = sample_data['books'][0]
    book_id = book.id

    try:
        test_session.delete(book)
        test_session.commit()
    except:
        test_session.rollback()

    check_book = test_session.get(Sach, book_id)
    assert check_book is None

def test_admin_export_books_csv(test_client, test_session):
    pass_hash = hashlib.md5("123".encode('utf-8')).hexdigest()
    admin = NguoiDung(ten="Admin Export", ten_dang_nhap="admin_export",
                      mat_khau=pass_hash, vai_tro=VaiTro.QUAN_TRI)
    test_session.add(admin); test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(admin.id)

    res = test_client.get('/admin/sach/export/csv/')
    assert res.status_code == 200
    assert "text/csv" in res.content_type

def test_admin_stats_with_params(test_client, test_session):
    pass_hash = hashlib.md5("123".encode('utf-8')).hexdigest()
    admin = NguoiDung(ten="Admin Stats Param", ten_dang_nhap="admin_p",
                      mat_khau=pass_hash, vai_tro=VaiTro.QUAN_TRI)
    test_session.add(admin); test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(admin.id)

    res = test_client.get('/admin/statsview/?month=5&year=2026')
    assert res.status_code == 200

def test_admin_user_form_excludes_password(test_client, test_session):
    pass_hash = hashlib.md5("123".encode('utf-8')).hexdigest()
    admin = NguoiDung(ten="Admin Sec", ten_dang_nhap="admin_sec",
                      mat_khau=pass_hash, vai_tro=VaiTro.QUAN_TRI)
    test_session.add(admin); test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(admin.id)

    res = test_client.get('/admin/nguoidung/new/')
    assert 'name="mat_khau"' not in res.get_data(as_text=True)

def test_admin_logout_view(test_client, test_session):
    pass_hash = hashlib.md5("123".encode('utf-8')).hexdigest()
    admin = NguoiDung(ten="Admin Out", ten_dang_nhap="admin_out",
                      mat_khau=pass_hash, vai_tro=VaiTro.QUAN_TRI)
    test_session.add(admin); test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(admin.id)

    res = test_client.get('/admin/logoutview/', follow_redirects=True)
    assert res.status_code == 200

    with test_client.session_transaction() as sess:
        assert '_user_id' not in sess

    data = res.get_data(as_text=True)
    assert "ĐĂNG NHẬP" in data