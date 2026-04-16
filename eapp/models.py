from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, Float, Enum, DateTime
from sqlalchemy.orm import relationship
from eapp import db, app
from flask_login import UserMixin
from enum import Enum as UserEnum
from datetime import datetime
import hashlib


# 1. Mô hình cơ bản dùng chung
class MoHinhCoBan(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    ngay_tao = Column(DateTime, default=datetime.now)
    hoat_dong = Column(Boolean, default=True)


class VaiTro(UserEnum):
    QUAN_TRI = 1
    NGUOI_DUNG = 2


class TrangThaiMuon(UserEnum):
    DANG_MUON = 1
    DA_TRA = 2
    QUA_HAN = 3


class NguoiDung(MoHinhCoBan, UserMixin):
    ten = Column(String(50), nullable=False)
    anh_dai_dien = Column(String(200), default='https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg')
    ten_dang_nhap = Column(String(50), nullable=False, unique=True)
    mat_khau = Column(String(100), nullable=False)
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
    hinh_anh = Column(String(500), default='https://via.placeholder.com/300x450?text=Pages+Book')
    tong_so_luong = Column(Integer, default=10)
    so_luong_con = Column(Integer, default=10)
    ma_the_loai = Column(Integer, ForeignKey(TheLoai.id), nullable=False)
    chi_tiet_muon = relationship('ChiTietMuon', backref='sach', lazy=True)

    def __str__(self):
        return self.ten_sach


class PhieuMuon(MoHinhCoBan):
    ma_nguoi_dung = Column(Integer, ForeignKey(NguoiDung.id), nullable=False)
    ngay_muon = Column(DateTime, default=datetime.now)
    han_tra = Column(DateTime, nullable=False)
    trang_thai = Column(Enum(TrangThaiMuon), default=TrangThaiMuon.DANG_MUON)
    so_dien_thoai = Column(String(15), nullable=True)
    dia_chi = Column(String(255), nullable=True)
    ghi_chu = Column(Text, nullable=True)
    chi_tiet = relationship('ChiTietMuon', backref='phieu_muon', lazy=True, cascade="all, delete-orphan")


class ChiTietMuon(db.Model):
    ma_phieu = Column(Integer, ForeignKey(PhieuMuon.id), primary_key=True)
    ma_sach = Column(Integer, ForeignKey(Sach.id), primary_key=True)
    ngay_tra_thuc_te = Column(DateTime, nullable=True)
    tien_phat = Column(Float, default=0.0)


# --- HÀM NẠP DỮ LIỆU TỰ ĐỘNG (Chỉnh sửa: Chỉ 6 quyển) ---
if __name__ == "__main__":
    with app.app_context():
        # db.drop_all() # Mở comment nếu muốn làm sạch DB cũ
        db.create_all()

        # 1. Tạo Admin mặc định
        if not NguoiDung.query.filter_by(ten_dang_nhap='admin').first():
            admin_user = NguoiDung(
                ten='Quản trị viên',
                ten_dang_nhap='admin',
                mat_khau=str(hashlib.md5('123456'.encode('utf-8')).hexdigest()),
                vai_tro=VaiTro.QUAN_TRI
            )
            db.session.add(admin_user)

        # 2. Tạo Thể loại và nạp đúng 6 cuốn sách
        if not TheLoai.query.first():
            tl1 = TheLoai(ten_the_loai="Công nghệ thông tin")
            tl2 = TheLoai(ten_the_loai="Kỹ năng sống")
            tl3 = TheLoai(ten_the_loai="Ngoại ngữ")
            db.session.add_all([tl1, tl2, tl3])
            db.session.commit()

            # Danh sách 6 cuốn sách độc bản
            danh_sach_sach = [
                # Nhóm CNTT
                Sach(ten_sach="Python Crash Course", tac_gia="Eric Matthes", ma_the_loai=tl1.id,
                     hinh_anh="https://bizweb.dktcdn.net/100/197/269/products/python-crash-course.jpg",
                     mo_ta="Cuốn sách bán chạy nhất thế giới về lập trình Python dành cho người mới bắt đầu."),
                Sach(ten_sach="Clean Code", tac_gia="Robert C. Martin", ma_the_loai=tl1.id,
                     hinh_anh="https://m.media-amazon.com/images/I/41xShlnTZTL.jpg",
                     mo_ta="Cẩm nang về tư duy viết mã sạch và bảo trì phần mềm chuyên nghiệp."),

                # Nhóm Kỹ năng
                Sach(ten_sach="Đắc Nhân Tâm", tac_gia="Dale Carnegie", ma_the_loai=tl2.id,
                     hinh_anh="https://salt.tikicdn.com/cache/w1200/ts/product/d1/20/d5/06fdc3004c7fd9d39999b1062991901a.jpg",
                     mo_ta="Tác phẩm kinh điển về nghệ thuật giao tiếp và thu phục lòng người."),
                Sach(ten_sach="Nhà Giả Kim", tac_gia="Paulo Coelho", ma_the_loai=tl2.id,
                     hinh_anh="https://salt.tikicdn.com/ts/product/45/3d/81/8f8b2d436a94ec0ade3764459f4215f1.jpg",
                     mo_ta="Hành trình theo đuổi vận mệnh và khám phá tâm hồn của chàng chăn cừu Santiago."),

                # Nhóm Ngoại ngữ
                Sach(ten_sach="English Grammar in Use", tac_gia="Raymond Murphy", ma_the_loai=tl3.id,
                     hinh_anh="https://salt.tikicdn.com/ts/product/f4/78/39/3a8d46101c57e841285499292b35d8fc.jpg",
                     mo_ta="Tài liệu tự học ngữ pháp tiếng Anh phổ biến nhất trên toàn thế giới."),
                Sach(ten_sach="Hacking Your English", tac_gia="Hoàng Ngọc Quỳnh", ma_the_loai=tl3.id,
                     hinh_anh="https://salt.tikicdn.com/ts/product/3e/26/51/9d53347c6e6443d07747e4b971a06901.jpg",
                     mo_ta="Phương pháp đột phá để nghe nói tiếng Anh trôi chảy dành cho người bận rộn.")
            ]

            db.session.add_all(danh_sach_sach)
            db.session.commit()
            print(">>> Đã nạp thành công 06 cuốn sách tinh hoa.")

        print(">>> Hệ thống database Pages+ đã sẵn sàng.")