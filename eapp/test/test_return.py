import pytest
from datetime import datetime, timedelta
from eapp.test.test_base import test_client, test_session, sample_data, test_app
from eapp.models import PhieuMuon, ChiTietMuon, TrangThaiMuon


def test_return_book_success(test_client, test_session, sample_data):
    """1. Test trả sách thành công đúng hạn, kiểm tra thay đổi trạng thái"""
    user = sample_data['users'][0]
    book = sample_data['books'][0]

    # --- SETUP: TẠO PHIẾU MƯỢN ---
    # Hẹn trả vào 14 ngày tới (Đúng hạn)
    ngay_tra = datetime.now() + timedelta(days=14)
    phieu = PhieuMuon(ma_nguoi_dung=user.id, han_tra=ngay_tra, trang_thai=TrangThaiMuon.DANG_MUON)
    test_session.add(phieu)
    test_session.commit()

    chitiet = ChiTietMuon(ma_phieu=phieu.id, ma_sach=book.id)
    test_session.add(chitiet)
    test_session.commit()
    # ------------------------------------------------

    phieu_id = phieu.id

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    # Gọi route trả sách (dùng POST)
    res = test_client.post(f'/tra-sach/{phieu_id}', follow_redirects=True)

    assert res.status_code == 200

    # Kiểm tra DB xem phiếu đã chuyển trạng thái sang DA_TRA chưa
    updated_phieu = test_session.get(PhieuMuon, phieu_id)
    assert updated_phieu.trang_thai == TrangThaiMuon.DA_TRA


def test_return_book_not_owner(test_client, test_session, sample_data):
    """2. Ràng buộc: Chỉ người mượn mới được trả sách của mình"""
    user_1 = sample_data['users'][0]
    user_2 = sample_data['users'][1]  # Đăng nhập bằng user 2 (Kẻ gian)
    book = sample_data['books'][0]

    # --- SETUP: TẠO PHIẾU MƯỢN CHO USER 1 ---
    ngay_tra = datetime.now() + timedelta(days=14)
    phieu_cua_user_1 = PhieuMuon(ma_nguoi_dung=user_1.id, han_tra=ngay_tra, trang_thai=TrangThaiMuon.DANG_MUON)
    test_session.add(phieu_cua_user_1)
    test_session.commit()

    ct = ChiTietMuon(ma_phieu=phieu_cua_user_1.id, ma_sach=book.id)
    test_session.add(ct)
    test_session.commit()
    # ---------------------------------------

    with test_client.session_transaction() as sess:
        # Giả lập phiên đăng nhập là User 2
        sess['_user_id'] = str(user_2.id)

    # User 2 cố tình gửi request trả phiếu mượn của User 1
    res = test_client.post(f'/tra-sach/{phieu_cua_user_1.id}', follow_redirects=True)
    data = res.get_data(as_text=True).lower()

    # 1. Kì vọng bị chặn bằng flash message từ hàm process_return_book trong dao.py
    assert "không tìm thấy phiếu mượn" in data

    # 2. Đảm bảo trạng thái phiếu trong Database vẫn không bị thay đổi (Vẫn là DANG_MUON)
    phieu_trong_db = test_session.get(PhieuMuon, phieu_cua_user_1.id)
    assert phieu_trong_db.trang_thai == TrangThaiMuon.DANG_MUON


def test_return_book_late_fee(test_client, test_session, sample_data):
    """3. Ràng buộc Đề tài 5: Trả trễ hạn bị tính phí phạt 5k/ngày"""
    user = sample_data['users'][0]
    book = sample_data['books'][0]

    # --- SETUP: TẠO PHIẾU MƯỢN BỊ TRỄ HẠN ---
    # Cố tình set hạn trả là 3 ngày TRƯỚC (Để bị tính trễ 3 ngày)
    ngay_tra_qua_khu = datetime.now() - timedelta(days=3)
    phieu = PhieuMuon(ma_nguoi_dung=user.id, han_tra=ngay_tra_qua_khu, trang_thai=TrangThaiMuon.QUA_HAN)
    test_session.add(phieu)
    test_session.commit()

    ct = ChiTietMuon(ma_phieu=phieu.id, ma_sach=book.id)
    test_session.add(ct)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    # Gửi request trả sách
    res = test_client.post(f'/tra-sach/{phieu.id}', follow_redirects=True)
    data = res.get_data(as_text=True).lower()

    assert res.status_code == 200

    # Logic trong dao.py tính: 3 ngày trễ x 5000 = 15000 VNĐ.
    # Kiểm tra xem flash message in ra có nhắc đến phí phạt không.
    assert "15,000" in data or "phí phạt" in data