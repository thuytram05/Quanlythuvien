import pytest
import hashlib
from eapp.models import NguoiDung, VaiTro, Sach, TheLoai,PhieuMuon,TrangThaiMuon
from eapp.test.test_base import test_client, test_app, test_session, sample_data
from datetime import datetime,timedelta


# --- NHÓM 1: BẢO MẬT & PHÂN QUYỀN ---

def test_admin_access_denied_for_normal_user(test_client, sample_data):
    """1. RÀNG BUỘC BẢO MẬT: Độc giả bình thường không được vào trang Admin"""
    user = sample_data['users'][0]

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.get('/admin/', follow_redirects=True)
    data = res.get_data(as_text=True).lower()
    # Kiểm tra không có chữ "quản trị" hoặc bị đẩy về login/trang chủ
    assert "quản trị" not in data or "/login" in res.request.path


def test_admin_access_granted_for_admin(test_client, test_session):
    """2. Kiểm tra Quản trị viên truy cập trang Admin thành công"""
    # FIX: Băm mật khẩu MD5 để đồng bộ với hệ thống
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
    """3. BỔ SUNG: Admin truy cập được trang Thống kê báo cáo"""
    pass_hash = hashlib.md5("123".encode('utf-8')).hexdigest()
    admin = NguoiDung(ten="Admin Stats", ten_dang_nhap="admin_stats",
                      mat_khau=pass_hash, vai_tro=VaiTro.QUAN_TRI)
    test_session.add(admin)
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(admin.id)

    # Truy cập trực tiếp vào route thống kê (StatsView)
    res = test_client.get('/admin/statsview/')
    assert res.status_code == 200


# --- NHÓM 2: QUẢN LÝ NGƯỜI DÙNG & DANH MỤC ---

def test_admin_block_user_logic(test_session, sample_data):
    """4. Kiểm tra tính năng khóa tài khoản độc giả"""
    user = sample_data['users'][0]
    user.bi_khoa = True
    test_session.commit()

    test_session.refresh(user)
    assert user.bi_khoa is True


def test_admin_add_category_success(test_session):
    """5. Kiểm tra Admin thêm thể loại sách mới"""
    new_cate = TheLoai(ten_the_loai="Kinh tế mới")
    test_session.add(new_cate)
    test_session.commit()

    check = test_session.query(TheLoai).filter_by(ten_the_loai="Kinh tế mới").first()
    assert check is not None


# --- NHÓM 3: QUẢN LÝ SÁCH (CRUD) ---

def test_admin_add_new_book(test_session, sample_data):
    """6. Admin thêm sách mới vào kho"""
    tl = sample_data['categories'][0]
    new_book = Sach(ten_sach="Sách Admin Mới", tac_gia="Tác giả A",
                    so_luong_con=10, tong_so_luong=10, ma_the_loai=tl.id)
    test_session.add(new_book)
    test_session.commit()
    assert test_session.query(Sach).filter_by(ten_sach="Sách Admin Mới").first() is not None


def test_admin_update_book_stock(test_session, sample_data):
    """7. Admin cập nhật số lượng sách trong kho"""
    book = sample_data['books'][1]
    book.so_luong_con = 99
    test_session.commit()
    test_session.refresh(book)
    assert book.so_luong_con == 99


def test_admin_delete_book_safe(test_session, sample_data):
    """8. Admin xóa sách khỏi hệ thống"""
    book = sample_data['books'][5]
    book_id = book.id
    test_session.delete(book)
    test_session.commit()
    assert test_session.get(Sach, book_id) is None


def test_admin_add_duplicate_category(test_session, sample_data):
    """Bổ sung: Chặn việc thêm Thể loại trùng tên"""
    # Lấy tên thể loại đã có trong sample_data
    existing_name = sample_data['categories'][0].ten_the_loai

    duplicate_cate = TheLoai(ten_the_loai=existing_name)
    test_session.add(duplicate_cate)

    with pytest.raises(Exception):  # Kỳ vọng DB sẽ báo lỗi IntegrityError
        test_session.commit()


def test_admin_delete_book_in_use_integrity(test_session, sample_data):
    """Bổ sung: Kiểm tra ràng buộc khi xóa sách đang được mượn"""
    from eapp.models import ChiTietMuon  # Đảm bảo đã import ChiTietMuon
    book = sample_data['books'][0]
    user = sample_data['users'][0]
    now = datetime.now()

    # 1. Tạo phiếu mượn với đầy đủ các trường bắt buộc (phải có han_tra)
    p = PhieuMuon(
        ma_nguoi_dung=user.id,
        ngay_muon=now,
        han_tra=now + timedelta(days=14),  # FIX: Thêm hạn trả 14 ngày
        trang_thai=TrangThaiMuon.DANG_MUON
    )
    test_session.add(p)
    test_session.commit()

    # 2. Tạo chi tiết mượn để liên kết cuốn sách này với phiếu mượn
    test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book.id))
    test_session.commit()

    # 3. Kiểm tra ràng buộc: Hệ thống phải CHẶN việc xóa sách khi sách đang nằm trong phiếu mượn
    # Lưu ý: Điều này đòi hỏi Database có Foreign Key constraint (ON DELETE RESTRICT/NO ACTION)
    with pytest.raises(Exception):  # Kỳ vọng sẽ ném ra lỗi vì vi phạm ràng buộc khóa ngoại
        test_session.delete(book)
        test_session.commit()

    # Rollback để không ảnh hưởng đến các bài test sau nếu có lỗi
    test_session.rollback()


def test_admin_delete_category_with_books_integrity(test_session, sample_data):
    """9. BỔ SUNG: Kiểm tra chặn xóa Thể loại khi vẫn còn sách bên trong"""
    tl = sample_data['categories'][0]

    # Đảm bảo thể loại này đang có sách (sample_data đã tạo sẵn sách cho tl1)

    with pytest.raises(Exception):  # Kỳ vọng ném lỗi vì vi phạm Foreign Key
        test_session.delete(tl)
        test_session.commit()

    test_session.rollback()