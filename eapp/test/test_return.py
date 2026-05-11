import pytest
from datetime import datetime, timedelta
from eapp.test.test_base import test_client, test_session, sample_data, test_app
from eapp.models import PhieuMuon, ChiTietMuon, TrangThaiMuon, Sach

# --- NHÓM 1: CÁC KỊCH BẢN CƠ BẢN ---

def test_return_book_success(test_client, test_session, sample_data):
    """1. Test trả sách thành công đúng hạn, kiểm tra thay đổi trạng thái"""
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
    """2. Ràng buộc: Chỉ người mượn mới được trả sách của mình"""
    user_1 = sample_data['users'][0]
    user_2 = sample_data['users'][1]
    phieu = PhieuMuon(ma_nguoi_dung=user_1.id, han_tra=datetime.now() + timedelta(days=7))
    test_session.add(phieu)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user_2.id) # Kẻ gian đăng nhập

    res = test_client.post(f'/tra-sach/{phieu.id}', follow_redirects=True)
    assert "không tìm thấy phiếu mượn" in res.get_data(as_text=True).lower()

# --- NHÓM 2: RÀNG BUỘC PHÍ PHẠT & TÀI CHÍNH ---

def test_return_book_late_fee(test_client, test_session, sample_data):
    """3. Ràng buộc: Trả trễ hạn bị tính phí phạt 5k/ngày"""
    user = sample_data['users'][0]
    # Giả lập trễ 3 ngày
    han_tra = datetime.now() - timedelta(days=3)
    phieu = PhieuMuon(ma_nguoi_dung=user.id, han_tra=han_tra, trang_thai=TrangThaiMuon.QUA_HAN)
    test_session.add(phieu)
    test_session.commit()
    test_session.add(ChiTietMuon(ma_phieu=phieu.id, ma_sach=sample_data['books'][0].id))
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.post(f'/tra-sach/{phieu.id}', follow_redirects=True)
    # 3 ngày trễ x 5000 = 15,000
    assert "15,000" in res.get_data(as_text=True)

def test_return_database_verification(test_client, test_session, sample_data):
    """4. Kiểm tra ngày trả thực tế và tiền phạt được lưu đúng vào Database"""
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

# --- NHÓM 3: KIỂM THỬ BẢO MẬT & TỒN KHO ---

def test_return_unauthorized_blocking(test_client, sample_data):
    """5. Bảo mật: Chưa đăng nhập không thể gọi API trả sách"""
    res = test_client.post('/tra-sach/1', follow_redirects=True)
    assert "/login" in res.request.path or res.status_code == 401

def test_return_multiple_books_inventory_integrity(test_client, test_session, sample_data):
    """6. Đảm bảo trả phiếu nhiều sách phải tăng tồn kho của tất cả sách trong phiếu"""
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
    test_session.refresh(b1); test_session.refresh(b2)
    assert b1.so_luong_con == stock1 + 1
    assert b2.so_luong_con == stock2 + 1

def test_return_invalid_id(test_client, sample_data):
    """7. Chặn trả phiếu mượn với ID không tồn tại"""
    user = sample_data['users'][0]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.post('/tra-sach/9999', follow_redirects=True)
    assert "không tìm thấy" in res.get_data(as_text=True).lower()

def test_return_already_returned_blocking(test_client, test_session, sample_data):
    """Bổ sung: Chặn việc trả một phiếu mượn đã được trả trước đó"""
    user = sample_data['users'][0]
    # Tạo phiếu đã ở trạng thái DA_TRA
    phieu = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now(), trang_thai=TrangThaiMuon.DA_TRA)
    test_session.add(phieu)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.post(f'/tra-sach/{phieu.id}', follow_redirects=True)
    assert "đã được trả" in res.get_data(as_text=True).lower()