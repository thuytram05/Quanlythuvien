import hashlib
import cloudinary.uploader
import re
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from datetime import datetime, timedelta
from eapp import db
from eapp.models import Sach, TheLoai, NguoiDung, PhieuMuon, ChiTietMuon, TrangThaiMuon
from flask import current_app


# --- 1. QUẢN LÝ NGƯỜI DÙNG ---

def get_user_by_id(user_id):
    return NguoiDung.query.get(user_id)


def auth_user(username, password):
    if not username or not password:
        return None
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    return NguoiDung.query.filter(NguoiDung.ten_dang_nhap == username.strip(),
                                  NguoiDung.mat_khau == password).first()


def add_user(name, username, password, avatar):
    # Áp dụng ràng buộc bảo mật từ saleappv1
    if len(username) < 5:
        raise ValueError('Tên đăng nhập phải ít nhất 5 ký tự!')
    if len(password) < 6:
        raise ValueError('Mật khẩu phải ít nhất 6 ký tự!')
    if not re.search(r'[0-9]', password) or not re.search(r'[a-zA-Z]', password):
        raise ValueError('Mật khẩu phải chứa cả chữ và số!')

    if NguoiDung.query.filter_by(ten_dang_nhap=username).first():
        raise ValueError(f'Tên đăng nhập {username} đã tồn tại!')

    password_hashed = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    u = NguoiDung(ten=name.strip(), ten_dang_nhap=username.strip(), mat_khau=password_hashed)

    if avatar:
        res = cloudinary.uploader.upload(avatar)
        u.anh_dai_dien = res.get("secure_url")

    db.session.add(u)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise Exception('Lỗi hệ thống: Tên đăng nhập đã tồn tại!')


# --- 2. QUẢN LÝ SÁCH ---

def load_categories():
    return TheLoai.query.all()


def load_books(category_id=None, kw=None, page=None):
    # Join với TheLoai để tìm kiếm theo tên thể loại (Yêu cầu đề bài)
    query = db.session.query(Sach).join(TheLoai, Sach.ma_the_loai == TheLoai.id)

    if kw and len(kw.strip()) >= 2:
        query = query.filter(Sach.ten_sach.contains(kw) |
                             Sach.tac_gia.contains(kw) |
                             TheLoai.ten_the_loai.contains(kw))

    if category_id:
        query = query.filter(Sach.ma_the_loai == category_id)

    if page:
        page_size = current_app.config.get('PAGE_SIZE', 50)
        start = (page - 1) * page_size
        query = query.offset(start).limit(page_size)

    return query.all()


def count_books_filtered(kw=None, category_id=None):
    query = db.session.query(func.count(Sach.id)).join(TheLoai, Sach.ma_the_loai == TheLoai.id)
    if kw and len(kw.strip()) >= 2:
        query = query.filter(Sach.ten_sach.contains(kw) |
                             Sach.tac_gia.contains(kw) |
                             TheLoai.ten_the_loai.contains(kw))
    if category_id:
        query = query.filter(Sach.ma_the_loai == category_id)
    return query.scalar()


def get_book_by_id(book_id):
    return Sach.query.get(book_id)


# --- 3. NGHIỆP VỤ MƯỢN TRẢ ---

def count_books_currently_borrowed(user_id):
    """Đếm tổng số sách đang chiếm dụng (DANG_MUON hoặc QUA_HAN)"""
    return db.session.query(func.count(ChiTietMuon.ma_sach)) \
        .join(PhieuMuon) \
        .filter(PhieuMuon.ma_nguoi_dung == user_id,
                PhieuMuon.trang_thai != TrangThaiMuon.DA_TRA).scalar() or 0


def check_overdue(user_id):
    """Cập nhật và kiểm tra sách quá hạn (Ràng buộc đề bài)"""
    # Tự động cập nhật các phiếu DANG_MUON nhưng đã quá han_tra sang QUA_HAN
    PhieuMuon.query.filter(PhieuMuon.ma_nguoi_dung == user_id,
                           PhieuMuon.trang_thai == TrangThaiMuon.DANG_MUON,
                           PhieuMuon.han_tra < datetime.now()) \
        .update({PhieuMuon.trang_thai: TrangThaiMuon.QUA_HAN})
    db.session.commit()

    return PhieuMuon.query.filter_by(ma_nguoi_dung=user_id,
                                     trang_thai=TrangThaiMuon.QUA_HAN).first() is not None


def create_borrow_receipt(user_id, cart_items, phone=None, return_date=None, note=None):
    user = NguoiDung.query.get(user_id)
    if not user or user.bi_khoa:
        raise Exception("Tài khoản đang bị khóa hoặc không tồn tại!")
    if check_overdue(user_id):
        raise Exception("Bạn đang nợ sách quá hạn, vui lòng trả trước khi mượn mới!")

    # Ràng buộc tối đa 5 cuốn
    current_total = count_books_currently_borrowed(user_id)
    if current_total + len(cart_items) > 5:
        raise Exception(f"Bạn đang mượn {current_total} cuốn. Chỉ được mượn thêm {5 - current_total} cuốn!")

    dt_return = datetime.strptime(return_date, '%Y-%m-%d') if return_date else (datetime.now() + timedelta(days=14))

    try:
        phieu = PhieuMuon(ma_nguoi_dung=user_id, han_tra=dt_return, so_dien_thoai=phone, ghi_chu=note)
        db.session.add(phieu)

        for item in cart_items:
            sach = Sach.query.get(int(item.get('id')))
            if not sach or sach.so_luong_con < 1:
                raise Exception(f"Sách '{sach.ten_sach if sach else 'ID:' + str(item.get('id'))}' đã hết bản!")

            sach.so_luong_con -= 1
            ct = ChiTietMuon(phieu_muon=phieu, sach=sach)
            db.session.add(ct)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


def process_return_book(phieu_id, user_id):
    phieu = PhieuMuon.query.filter_by(id=phieu_id, ma_nguoi_dung=user_id).first()
    if not phieu: raise Exception("Không tìm thấy phiếu mượn của bạn!")
    if phieu.trang_thai == TrangThaiMuon.DA_TRA: raise Exception("Sách thuộc phiếu này đã được trả!")

    phi_phat = 0
    now = datetime.now()

    if now > phieu.han_tra:
        days_late = (now - phieu.han_tra).days
        phi_phat = days_late * 5000  # 5k/ngày trễ

    try:
        phieu.trang_thai = TrangThaiMuon.DA_TRA
        for ct in phieu.chi_tiet:
            ct.sach.so_luong_con += 1
            ct.ngay_tra_thuc_te = now
            ct.tien_phat = phi_phat
        db.session.commit()
        return "Trả sách thành công!", phi_phat
    except Exception as e:
        db.session.rollback()
        raise e

def check_username(username):
    return NguoiDung.query.filter(NguoiDung.ten_dang_nhap == username.strip()).first() is not None

# --- 4. THỐNG KÊ ---

# --- 4. THỐNG KÊ ---

def count_sach_by_theloai():
    """Thống kê số lượng sách theo từng thể loại"""
    return db.session.query(TheLoai.id, TheLoai.ten_the_loai, func.count(Sach.id)) \
        .join(Sach, Sach.ma_the_loai == TheLoai.id, isouter=True) \
        .group_by(TheLoai.id).all()

def thong_ke_muon_tra(month=None, year=None):
    """
    Thống kê tần suất mượn sách theo thể loại trong tháng/năm cụ thể.
    Trả về: Tên thể loại, Số lượt mượn, Tỉ lệ.
    """
    if not month:
        month = datetime.now().month
    if not year:
        year = datetime.now().year

    query = db.session.query(
        TheLoai.ten_the_loai,
        func.count(ChiTietMuon.ma_sach)
    ).join(Sach, Sach.ma_the_loai == TheLoai.id, isouter=True) \
     .join(ChiTietMuon, ChiTietMuon.ma_sach == Sach.id, isouter=True) \
     .join(PhieuMuon, ChiTietMuon.ma_phieu == PhieuMuon.id, isouter=True)

    query = query.filter(func.extract('month', PhieuMuon.ngay_muon) == month,
                         func.extract('year', PhieuMuon.ngay_muon) == year)

    return query.group_by(TheLoai.id).all()