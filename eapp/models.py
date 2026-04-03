from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Float, Enum, DateTime
from sqlalchemy.orm import relationship
from eapp import db, app
from flask_login import UserMixin
from enum import Enum as UserEnum
from datetime import datetime
import hashlib

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
    anh_dai_dien = Column(String(200), default='https://i1.sndcdn.com/artworks-POzt1px8desduZHi-SGxkaw-t500x500.jpg')
    ten_dang_nhap = Column(String(50), nullable=False, unique=True)
    mat_khau = Column(String(50), nullable=False)
    vai_tro = Column(Enum(VaiTro), default=VaiTro.NGUOI_DUNG)
    bi_khoa = Column(Boolean, default=False)

    phieu_muon_sach = relationship('PhieuMuon', backref='nguoi_dung', lazy=True)
    items_trong_gio = relationship('UserCart', backref='nguoi_dung', lazy=True)

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
    hinh_anh = Column(String(500), default='https://tse4.mm.bing.net/th/id/OIP.kSEAVEjy8eu6LrNQDycYhwHaHa?rs=1&pid=ImgDetMain')
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
    trang_thai = Column(Enum(TrangThaiMuon), default=TrangThaiMuon.DANG_MUON)

    chi_tiet = relationship('ChiTietMuon', backref='phieu_muon', lazy=True)

class ChiTietMuon(db.Model):
    ma_phieu = Column(Integer, ForeignKey(PhieuMuon.id), primary_key=True)
    ma_sach = Column(Integer, ForeignKey(Sach.id), primary_key=True)
    ngay_tra_thuc_te = Column(DateTime, nullable=True)
    tien_phat = Column(Float, default=0.0)

class UserCart(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey(NguoiDung.id), nullable=False)
    book_id = Column(Integer, ForeignKey(Sach.id), nullable=False)
    created_date = Column(DateTime, default=datetime.now)

    sach = relationship('Sach', backref='cart_items')

def add_data():
    admin_user = NguoiDung(
        ten='Quản trị viên',
        ten_dang_nhap='admin',
        mat_khau=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()),
        vai_tro=VaiTro.QUAN_TRI
    )
    db.session.add(admin_user)

    tl1 = TheLoai(ten_the_loai="Công nghệ thông tin")
    tl2 = TheLoai(ten_the_loai="Kỹ năng sống")
    tl3 = TheLoai(ten_the_loai="Ngoại ngữ")
    db.session.add_all([tl1, tl2, tl3])
    db.session.commit()

    sach_list = [
        Sach(ten_sach="Công nghệ phần mềm", tac_gia="Nguyễn Văn A", so_luong_con=10, tong_so_luong=10, hinh_anh="https://thuquan.ou.edu.vn/cover//2024/03/08/I23-Congnghephanmem-01.jpg", ma_the_loai=tl1.id),
        Sach(ten_sach="Cấu Trúc Dữ Liệu Và Giải Thuật", tac_gia="Nguyễn Đức Nghĩa", so_luong_con=15, tong_so_luong=15, hinh_anh="https://hvpnvn.edu.vn/wp-content/uploads/sites/63/2024/02/Giao-trinh-cau-truc-du-lieu-va-giai-thuat.jpg", ma_the_loai=tl1.id),
        Sach(ten_sach="Lập Trình Python Cơ Bản", tac_gia="Nhiều Tác Giả", so_luong_con=8, tong_so_luong=10, hinh_anh="https://down-vn.img.susercontent.com/file/vn-11134201-7r98o-lu54jam92n4c98", ma_the_loai=tl1.id),
        Sach(ten_sach="Đắc Nhân Tâm", tac_gia="Dale Carnegie", so_luong_con=5, tong_so_luong=5, hinh_anh="https://tiki.vn/blog/wp-content/uploads/2023/08/noi-dung-chinh-dac-nhan-tam-1024x682.jpg", ma_the_loai=tl2.id),
        Sach(ten_sach="Nhà Giả Kim", tac_gia="Paulo Coelho", so_luong_con=20, tong_so_luong=20, hinh_anh="https://salt.tikicdn.com/cache/750x750/ts/product/45/3b/fc/aa81d0a534b45706ae1eee1e344e80d9.jpg", ma_the_loai=tl2.id),
        Sach(ten_sach="Tuổi Trẻ Đáng Giá Bao Nhiêu", tac_gia="Rosie Nguyễn", so_luong_con=12, tong_so_luong=15, hinh_anh="https://www.vietbookalley.com.au/cdn/shop/products/tuoi-tre-dang-gia-bao-nhieu_1100x.webp?v=1665371089", ma_the_loai=tl2.id),
        Sach(ten_sach="English Grammar in Use", tac_gia="Raymond Murphy", so_luong_con=25, tong_so_luong=30, hinh_anh="https://cf.shopee.vn/file/d2c41d6e53b7e420ef3129d705be78b7", ma_the_loai=tl3.id),
        Sach(ten_sach="Hack Não 1500 Từ Tiếng Anh", tac_gia="Nguyễn Văn Hiệp", so_luong_con=5, tong_so_luong=5, hinh_anh="https://th.bing.com/th/id/R.c58c3fa1ef48e42bdafec69757cace96?rik=E99vzYUwKphjbQ&pid=ImgRaw&r=0", ma_the_loai=tl3.id)
    ]
    db.session.add_all(sach_list)

    for i in range(1, 53):
        fake_book = Sach(
            ten_sach=f"Sách mẫu số {i}",
            tac_gia=f"Tác giả mẫu {i}",
            mo_ta=f"Đây là mô tả cho cuốn sách mẫu số {i}",
            hinh_anh=f"https://via.placeholder.com/300x450?text=Book+Model+{i}",
            tong_so_luong=10,
            so_luong_con=10,
            ma_the_loai=(tl1.id if i % 2 == 0 else tl2.id)  # Xen kẽ thể loại 1 và 2
        )
        db.session.add(fake_book)
    db.session.commit()
    print("Đã khởi tạo thành công 60 cuốn sách!")

if __name__ == "__main__":
    with app.app_context():
        db.drop_all()
        db.create_all()
        add_data()