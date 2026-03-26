from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Float, Enum, DateTime
from sqlalchemy.orm import relationship
from eapp import db, app
from flask_login import UserMixin
from enum import Enum as UserEnum
from datetime import datetime
import hashlib


# ==========================================
# 1. ĐỊNH NGHĨA CÁC BẢNG (MODELS)
# ==========================================
class MoHinhCoBan(db.Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    ngay_tao = Column(DateTime, default=datetime.now)
    hoat_dong = Column(Boolean, default=True)


class VaiTro(UserEnum):
    NGUOI_DUNG = 1
    QUAN_TRI = 2


class TrangThaiMuon(UserEnum):
    DANG_MUON = 1
    DA_TRA = 2
    QUA_HAN = 3


class NguoiDung(MoHinhCoBan, UserMixin):
    ten = Column(String(50), nullable=False)
    anh_dai_dien = Column(String(100),
                          default='https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg')
    ten_dang_nhap = Column(String(50), nullable=False, unique=True)
    mat_khau = Column(String(50), nullable=False)
    vai_tro = Column(Enum(VaiTro), default=VaiTro.NGUOI_DUNG)
    bi_khoa = Column(Boolean, default=False)

    phieu_muon_sach = relationship('PhieuMuon', backref='nguoi_dung', lazy=True)

    def __str__(self):
        return self.ten


class TheLoai(MoHinhCoBan):
    ten_the_loai = Column(String(50), unique=True, nullable=False)
    cac_sach = relationship('Sach', backref='the_loai', lazy=True)

    def __str__(self):
        return self.ten_the_loai


class Sach(MoHinhCoBan):
    ten_sach = Column(String(255), nullable=False)
    tac_gia = Column(String(100), nullable=False)
    mo_ta = Column(Text, nullable=True)
    hinh_anh = Column(String(100),
                      default='https://res.cloudinary.com/dxxwcby8l/image/upload/v1647248722/r8sjly3st7estapvj19u.jpg')

    tong_so_luong = Column(Integer, default=1)
    so_luong_con = Column(Integer, default=1)

    ma_the_loai = Column(Integer, ForeignKey(TheLoai.id), nullable=False)
    chi_tiet_muon = relationship('ChiTietMuon', backref='sach', lazy=True)

    def __str__(self):
        return self.ten_sach


class PhieuMuon(MoHinhCoBan):
    ma_nguoi_dung = Column(Integer, ForeignKey(NguoiDung.id), nullable=False)
    ngay_muon = Column(DateTime, default=datetime.now)
    han_tra = Column(DateTime, nullable=False)
    trang_thai = Column(Enum(TrangThaiMuon),
                        default=TrangThaiMuon.DANG_MUON)

    chi_tiet = relationship('ChiTietMuon', backref='phieu_muon', lazy=True)


class ChiTietMuon(db.Model):
    ma_phieu = Column(Integer, ForeignKey(PhieuMuon.id), primary_key=True)
    ma_sach = Column(Integer, ForeignKey(Sach.id), primary_key=True)

    ngay_tra_thuc_te = Column(DateTime, nullable=True)
    tien_phat = Column(Float, default=0.0)


# ==========================================
# 2. HÀM TẠO DỮ LIỆU MẪU
# ==========================================
def add_data():
    # 1. Thêm Admin (Bắt buộc vì db.drop_all đã xóa hết)
    admin_user = NguoiDung(
        ten='Quản trị viên',
        ten_dang_nhap='admin',
        mat_khau=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()),
        vai_tro=VaiTro.QUAN_TRI
    )
    db.session.add(admin_user)
    print("✅ Đã tạo tài khoản Admin (admin/123456)!")

    # 2. Thêm Thể Loại
    tl1 = TheLoai(ten_the_loai="Công nghệ thông tin")
    tl2 = TheLoai(ten_the_loai="Kỹ năng sống")
    tl3 = TheLoai(ten_the_loai="Ngoại ngữ")

    db.session.add_all([tl1, tl2, tl3])
    db.session.commit()  # Lưu xuống database trước để lấy ID
    print("✅ Đã thêm các thể loại sách!")

    # 3. Thêm Sách (Dùng ID từ thể loại vừa tạo ở trên)
    s1 = Sach(
        ten_sach="Công nghệ phần mềm",
        tac_gia="Nguyễn Văn A",
        so_luong_con=10,
        tong_so_luong=10,
        hinh_anh="https://thuquan.ou.edu.vn/cover//2024/03/08/I23-Congnghephanmem-01.jpg",
        ma_the_loai=tl1.id  # Trỏ vào "Công nghệ thông tin"
    )

    s2 = Sach(
        ten_sach="Đắc Nhân Tâm",
        tac_gia="Dale Carnegie",
        so_luong_con=5,
        tong_so_luong=5,
        hinh_anh="https://tiki.vn/blog/wp-content/uploads/2023/08/noi-dung-chinh-dac-nhan-tam-1024x682.jpg",
        ma_the_loai=tl2.id  # Trỏ vào "Kỹ năng sống"
    )

    db.session.add_all([s1, s2])
    db.session.commit()
    print("✅ Đã thêm dữ liệu sách mẫu thành công!")


# ==========================================
# 3. KÍCH HOẠT CHẠY
# ==========================================
if __name__ == "__main__":
    with app.app_context():
        print("🗑️  Đang dọn dẹp database cũ...")
        db.drop_all()

        print("🛠️  Đang tạo lại các bảng...")
        db.create_all()

        print("📦 Đang nạp dữ liệu mới...")
        add_data()

        print("🎉 XONG! Cơ sở dữ liệu đã sẵn sàng.")