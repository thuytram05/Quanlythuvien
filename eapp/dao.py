import hashlib
import cloudinary.uploader
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from datetime import datetime, timedelta
from eapp import app, db
from eapp.models import Sach, TheLoai, NguoiDung, PhieuMuon, ChiTietMuon, TrangThaiMuon, UserCart


def load_categories():
    return TheLoai.query.all()


def load_books(category_id=None, kw=None, page=1):
    query = Sach.query
    if kw:
        query = query.filter(Sach.ten_sach.contains(kw) | Sach.tac_gia.contains(kw))
    if category_id:
        query = query.filter(Sach.ma_the_loai.__eq__(category_id))

    if page:
        page_size = app.config.get('PAGE_SIZE', 4)
        start = (page - 1) * page_size
        query = query.slice(start, start + page_size)

    return query.all()


def count_books():
    return Sach.query.count()


def get_book_by_id(book_id):
    return Sach.query.get(book_id)


def get_user_by_id(user_id):
    return NguoiDung.query.get(user_id)


def auth_user(username, password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    return NguoiDung.query.filter(NguoiDung.ten_dang_nhap == username,
                                  NguoiDung.mat_khau == password).first()


def add_user(name, username, password, avatar):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    u = NguoiDung(ten=name.strip(), ten_dang_nhap=username.strip(), mat_khau=password)

    if avatar:
        res = cloudinary.uploader.upload(avatar)
        u.anh_dai_dien = res.get("secure_url")

    db.session.add(u)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise Exception('Tên đăng nhập đã tồn tại trong hệ thống!')


def count_cart_items(user_id):
    return UserCart.query.filter_by(user_id=user_id).count()


def get_cart_all(user_id):
    return UserCart.query.filter_by(user_id=user_id).all()


def check_book_in_cart(user_id, book_id):
    return UserCart.query.filter_by(user_id=user_id, book_id=book_id).first() is not None


def add_to_cart(user_id, book_id):
    new_item = UserCart(user_id=user_id, book_id=book_id)
    db.session.add(new_item)
    db.session.commit()


def remove_cart_item(user_id, book_id):
    item = UserCart.query.filter_by(user_id=user_id, book_id=book_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()


def clear_user_cart(user_id):
    UserCart.query.filter_by(user_id=user_id).delete()
    db.session.commit()


def count_books_currently_borrowed(user_id):
    return db.session.query(func.count(ChiTietMuon.ma_sach)).join(PhieuMuon).filter(
        PhieuMuon.ma_nguoi_dung == user_id,
        PhieuMuon.trang_thai == TrangThaiMuon.DANG_MUON
    ).scalar() or 0


def check_overdue(user_id):
    return PhieuMuon.query.filter_by(ma_nguoi_dung=user_id, trang_thai=TrangThaiMuon.QUA_HAN).first() is not None

# --- ĐÃ SỬA LẠI HÀM NÀY ĐỂ KHÔNG BỊ LẶP PHIẾU ---
def create_borrow_receipt(user_id, cart_items, info=None):
    if not cart_items:
        return

    try:
        # BƯỚC 1: Tạo đối tượng phiếu mượn duy nhất
        phieu = PhieuMuon(
            ma_nguoi_dung=user_id,
            han_tra=datetime.now() + timedelta(days=14)
        )

        # Lưu thông tin từ Popup (Tên, SĐT, Email) vào ghi chú của phiếu
        if info:
            phieu.ghi_chu = f"Người mượn: {info.get('name')} - SĐT: {info.get('phone')} - Email: {info.get('email')}"

        db.session.add(phieu)
        db.session.flush()  # Đẩy lên DB tạm thời để lấy phieu.id

        # BƯỚC 2: Duyệt danh sách sách trong túi để trừ kho và tạo chi tiết
        for item in cart_items:
            sach = Sach.query.get(item.book_id)

            # RÀNG BUỘC: Kiểm tra tồn kho lần cuối
            if not sach or sach.so_luong_con < 1:
                db.session.rollback()
                raise Exception(f'Sách "{sach.ten_sach if sach else "Không xác định"}" đã hết bản trong kho!')

            # Trừ số lượng tồn
            sach.so_luong_con -= 1

            # Tạo chi tiết mượn
            chi_tiet = ChiTietMuon(ma_phieu=phieu.id, ma_sach=sach.id)
            db.session.add(chi_tiet)

        # BƯỚC 3: Xóa giỏ hàng tạm sau khi mượn thành công
        UserCart.query.filter_by(user_id=user_id).delete()

        # BƯỚC 4: Chốt dữ liệu
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        raise e


def get_borrow_history(user_id):
    return PhieuMuon.query.filter_by(ma_nguoi_dung=user_id).order_by(PhieuMuon.ngay_muon.desc()).all()