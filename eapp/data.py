from eapp import app, db
from eapp.models import TheLoai, Sach


def add_data():
    with app.app_context():
        # 1. Thêm Thể Loại
        tl1 = TheLoai(ten_the_loai="Công nghệ thông tin")
        tl2 = TheLoai(ten_the_loai="Kỹ năng sống")
        tl3 = TheLoai(ten_the_loai="Ngoại ngữ")

        db.session.add_all([tl1, tl2, tl3])
        db.session.commit()  # Lưu thể loại trước để lấy ID

        # 2. Thêm Sách (ma_the_loai phải khớp với ID vừa tạo)
        s1 = Sach(ten_sach="Công nghệ phần mềm",
                  tac_gia="Nguyễn Văn A",
                  so_luong_con=10,
                  tong_so_luong=10,
                  hinh_anh="https://thuquan.ou.edu.vn/cover//2024/03/08/I23-Congnghephanmem-01.jpg",
                  ma_the_loai=tl1.id)

        s2 = Sach(ten_sach="Đắc Nhân Tâm",
                  tac_gia="Dale Carnegie",
                  so_luong_con=5,
                  tong_so_luong=5,
                  hinh_anh="https://tiki.vn/blog/wp-content/uploads/2023/08/noi-dung-chinh-dac-nhan-tam-1024x682.jpg",
                  ma_the_loai=tl2.id)

        db.session.add_all([s1, s2])
        db.session.commit()
        print("Đã thêm dữ liệu mẫu thành công!")


if __name__ == "__main__":
    with app.app_context():
        db.drop_all()
        db.create_all()
        add_data()