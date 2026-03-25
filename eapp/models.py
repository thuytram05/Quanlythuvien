from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Float, Enum, DateTime
from sqlalchemy.orm import relationship
from eapp import db, app
from flask_login import UserMixin
from enum import Enum as UserEnum
from datetime import datetime, timedelta


class MoHinhCoBan(db.Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    ngay_tao = Column(DateTime, default=datetime.now())
    hoat_dong = Column(Boolean, default=True)  # Có thể dùng để khóa sách hoặc khóa danh mục


class VaiTro(UserEnum):
    NGUOI_DUNG = 1
    QUAN_TRI = 2


class TrangThaiMuon(UserEnum):
    DANG_MUON = 1  # Đang mượn
    DA_TRA = 2  # Đã trả
    QUA_HAN = 3  # Quá hạn


class NguoiDung(MoHinhCoBan, UserMixin):
    ten = Column(String(50), nullable=False)
    anh_dai_dien = Column(String(100),
                          default='https://res.cloudinary.com/dxxwcby8l/image/upload/v1647056401/ipmsmnxjydrhpo21xrd8.jpg')
    ten_dang_nhap = Column(String(50), nullable=False, unique=True)
    mat_khau = Column(String(50), nullable=False)
    vai_tro = Column(Enum(VaiTro), default=VaiTro.NGUOI_DUNG)
    bi_khoa = Column(Boolean, default=False)  # Ràng buộc: "Không được mượn nếu tài khoản bị khóa"

    phieu_muon_sach = relationship('PhieuMuon', backref='nguoi_dung', lazy=True)

    def __str__(self):
        return self.ten


class TheLoai(MoHinhCoBan):
    ten_the_loai = Column(String(50), unique=True, nullable=False)
    cac_sach = relationship('Sach', backref='the_loai', lazy=True)

    def __str__(self):
        return self.ten_the_loai


class Sach(MoHinhCoBan):
    ten_sach = Column(String(255), nullable=False)  # Tìm kiếm theo tên sách
    tac_gia = Column(String(100), nullable=False)  # Tìm kiếm theo tác giả
    mo_ta = Column(Text, nullable=True)
    hinh_anh = Column(String(100),
                      default='https://res.cloudinary.com/dxxwcby8l/image/upload/v1647248722/r8sjly3st7estapvj19u.jpg')

    tong_so_luong = Column(Integer, default=1)  # Tổng số bản sách có trong thư viện
    so_luong_con = Column(Integer, default=1)  # Số bản sách còn sẵn. Ràng buộc: "Không mượn nếu sách hết bản"

    ma_the_loai = Column(Integer, ForeignKey(TheLoai.id), nullable=False)  # Tìm kiếm theo thể loại
    chi_tiet_muon = relationship('ChiTietMuon', backref='sach', lazy=True)

    def __str__(self):
        return self.ten_sach


class PhieuMuon(MoHinhCoBan):
    ma_nguoi_dung = Column(Integer, ForeignKey(NguoiDung.id), nullable=False)
    ngay_muon = Column(DateTime, default=datetime.now())
    han_tra = Column(DateTime, nullable=False)  # Ngày phải trả
    trang_thai = Column(Enum(TrangThaiMuon),
                        default=TrangThaiMuon.DANG_MUON)  # Ràng buộc: "Cập nhật trạng thái overdue"

    chi_tiet = relationship('ChiTietMuon', backref='phieu_muon', lazy=True)


class ChiTietMuon(db.Model):  # Chi tiết mỗi cuốn sách trong 1 lần mượn
    ma_phieu = Column(Integer, ForeignKey(PhieuMuon.id), primary_key=True)
    ma_sach = Column(Integer, ForeignKey(Sach.id), primary_key=True)

    ngay_tra_thuc_te = Column(DateTime, nullable=True)  # Ngày trả thực tế
    tien_phat = Column(Float, default=0.0)  # Ràng buộc: "Nếu trả trễ tính phí phạt"


if __name__ == '__main__':
    with app.app_context():
        # db.drop_all()
        db.create_all()

        import hashlib

        u = NguoiDung(ten='Quản trị viên', ten_dang_nhap='admin',
                      mat_khau=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()),
                      vai_tro=VaiTro.QUAN_TRI)
        db.session.add(u)

        c1 = TheLoai(ten_the_loai='Công nghệ thông tin')
        c2 = TheLoai(ten_the_loai='Văn học')
        db.session.add_all([c1, c2])
        db.session.commit()

        # Thêm 1 cuốn sách mẫu
        s1 = Sach(ten_sach="Clean Code", tac_gia="Robert C. Martin",
                  tong_so_luong=5, so_luong_con=5, ma_the_loai=1)
        db.session.add(s1)
        db.session.commit()

        print("Tạo cơ sở dữ liệu tiếng Việt thành công!")