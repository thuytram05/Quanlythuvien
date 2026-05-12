import pytest
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from eapp.models import NguoiDung, TheLoai, Sach, PhieuMuon, ChiTietMuon, VaiTro, TrangThaiMuon
from eapp.test.test_base import test_session, sample_data, test_app
from sqlalchemy import text


def test_model_user_unique_username(test_session):
    u1 = NguoiDung(ten="User 1", ten_dang_nhap="username_unique", mat_khau="123")
    test_session.add(u1)
    test_session.commit()

    u2 = NguoiDung(ten="User 2", ten_dang_nhap="username_unique", mat_khau="456")
    test_session.add(u2)
    with pytest.raises(IntegrityError):
        test_session.commit()
    test_session.rollback()


def test_model_user_non_nullable_fields(test_session):
    u = NguoiDung(ten="No Username", mat_khau="123")
    test_session.add(u)
    with pytest.raises(IntegrityError):
        test_session.commit()
    test_session.rollback()


def test_model_category_unique_name(test_session):
    c1 = TheLoai(ten_the_loai="Kinh tế")
    test_session.add(c1)
    test_session.commit()

    c2 = TheLoai(ten_the_loai="Kinh tế")
    test_session.add(c2)
    with pytest.raises(IntegrityError):
        test_session.commit()
    test_session.rollback()


def test_model_book_foreign_key_constraint(test_session):
    test_session.execute(text("PRAGMA foreign_keys=ON"))
    s = Sach(ten_sach="Sách lỗi", tac_gia="A", ma_the_loai=999)
    test_session.add(s)

    with pytest.raises(IntegrityError):
        test_session.commit()
    test_session.rollback()

def test_model_receipt_cascade_delete(test_session, sample_data):
    user = sample_data['users'][0]
    book = sample_data['books'][0]
    p = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now() + timedelta(days=7))
    test_session.add(p)
    test_session.commit()
    ct = ChiTietMuon(ma_phieu=p.id, ma_sach=book.id)
    test_session.add(ct)
    test_session.commit()
    test_session.delete(p)
    test_session.commit()

    check_ct = test_session.query(ChiTietMuon).filter_by(ma_phieu=p.id).first()
    assert check_ct is None


def test_model_receipt_non_nullable_return_date(test_session, sample_data):
    user = sample_data['users'][0]
    p = PhieuMuon(ma_nguoi_dung=user.id)
    test_session.add(p)
    with pytest.raises(IntegrityError):
        test_session.commit()
    test_session.rollback()

def test_model_default_values(test_session, sample_data):
    tl = sample_data['categories'][0]
    s = Sach(ten_sach="Sách Default", tac_gia="A", ma_the_loai=tl.id)
    test_session.add(s)
    test_session.commit()
    assert s.so_luong_con == 10
    assert s.tong_so_luong == 10
    assert s.hoat_dong is True


def test_model_enum_constraints(test_session, sample_data):
    user = sample_data['users'][0]
    p = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now())
    test_session.add(p)
    test_session.flush()
    assert p.trang_thai == TrangThaiMuon.DANG_MUON
    p.trang_thai = TrangThaiMuon.QUA_HAN
    test_session.commit()
    test_session.refresh(p)
    assert p.trang_thai == TrangThaiMuon.QUA_HAN


def test_model_chitietmuon_composite_pk(test_session, sample_data):
    user = sample_data['users'][0]
    book = sample_data['books'][0]

    p = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now() + timedelta(days=7))
    test_session.add(p)
    test_session.commit()
    ct1 = ChiTietMuon(ma_phieu=p.id, ma_sach=book.id)
    test_session.add(ct1)
    test_session.commit()
    ct2 = ChiTietMuon(ma_phieu=p.id, ma_sach=book.id)
    test_session.add(ct2)
    with pytest.raises(IntegrityError):
        test_session.commit()
    test_session.rollback()


def test_model_sach_soft_delete_logic(test_session, sample_data):
    book = sample_data['books'][0]
    book_id = book.id
    book.hoat_dong = False
    test_session.commit()
    check_book = test_session.get(Sach, book_id)
    assert check_book is not None
    assert check_book.hoat_dong is False


def test_model_user_default_avatar(test_session):
    new_user = NguoiDung(ten="No Avatar", ten_dang_nhap="no_avatar_user", mat_khau="123")
    test_session.add(new_user)
    test_session.commit()
    assert "cloudinary" in new_user.anh_dai_dien
    assert "sample.jpg" in new_user.anh_dai_dien