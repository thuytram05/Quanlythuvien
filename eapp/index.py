from flask import render_template
from eapp import app, login  # Thêm login từ thư mục eapp
from eapp.models import Sach, TheLoai, NguoiDung  # Thêm bảng NguoiDung


# --- THÊM HÀM NÀY ĐỂ FIX LỖI MISSING USER_LOADER ---
@login.user_loader
def load_user(user_id):
    return NguoiDung.query.get(user_id)


# ---------------------------------------------------

@app.route('/')
def index():
    # Lấy dữ liệu từ Database
    categories = TheLoai.query.all()
    books = Sach.query.all()

    # Dữ liệu giả cho Giỏ mượn để không bị lỗi giao diện
    cart_stats = {'total_quantity': 0}

    # Đổ ra giao diện
    return render_template('index.html',
                           books=books,
                           categories=categories,
                           cart_stats=cart_stats,
                           pages=1)


if __name__ == '__main__':
    app.run(debug=True)