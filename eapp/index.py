import math, hashlib
from flask import render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user, login_required
from eapp import app, login, db
from eapp.models import Sach, TheLoai, NguoiDung, PhieuMuon, ChiTietMuon, TrangThaiMuon
from datetime import datetime, timedelta


# 1. Hàm tải người dùng cho Flask-Login
@login.user_loader
def load_user(user_id):
    return NguoiDung.query.get(user_id)


# 2. HÀM TỰ ĐỘNG GỬI DỮ LIỆU SANG TẤT CẢ CÁC TRANG HTML
@app.context_processor
def common_data():
    categories = TheLoai.query.all()
    cart = session.get('borrow_cart', {})
    total_quantity = sum(item['quantity'] for item in cart.values())

    return {
        'categories': categories,
        'cart_stats': {
            'total_quantity': total_quantity
        }
    }


# 3. Route Trang chủ (Hỗ trợ Tìm kiếm & Phân trang)
@app.route('/')
def index():
    kw = request.args.get('kw')
    category_id = request.args.get('category_id')
    page = request.args.get('page', 1, type=int)

    query = Sach.query

    # Ràng buộc: Tìm theo tên sách hoặc tác giả (Từ khóa >= 2 ký tự)
    if kw and len(kw.strip()) >= 2:
        kw_format = f"%{kw.strip()}%"
        query = query.filter(Sach.ten_sach.ilike(kw_format) | Sach.tac_gia.ilike(kw_format))

    if category_id:
        query = query.filter(Sach.ma_the_loai == category_id)

    # Ràng buộc: Tối đa 50 bản ghi/trang
    page_size = app.config.get("PAGE_SIZE", 50)
    total = query.count()
    pages = math.ceil(total / page_size)

    books = query.slice((page - 1) * page_size, page * page_size).all()

    return render_template('index.html', books=books, pages=pages)


# 4. Route Trang danh sách sách chờ mượn
@app.route('/phieu-muon')
def phieu_muon():
    return render_template('phieu_muon.html')


# 5. API: Thêm sách vào giỏ mượn tạm
@app.route('/api/muon-sach', methods=['POST'])
def add_to_borrow_cart():
    if not current_user.is_authenticated:
        return jsonify({'status': 'error', 'msg': 'Bạn cần đăng nhập để mượn sách!'})

    data = request.json
    book_id = str(data.get('id'))
    book_name = data.get('ten_sach')

    cart = session.get('borrow_cart', {})

    if len(cart) >= 5 and book_id not in cart:
        return jsonify({'status': 'error', 'msg': 'Bạn chỉ được mượn tối đa 5 cuốn sách!'})

    if book_id not in cart:
        cart[book_id] = {
            'id': book_id,
            'ten_sach': book_name,
            'quantity': 1
        }

    session['borrow_cart'] = cart
    return jsonify({
        'status': 'success',
        'msg': 'Đã thêm vào danh sách chờ mượn!',
        'total_quantity': len(cart)
    })


# 6. API: Xác nhận lập phiếu mượn (Ghi vào Database)
@app.route('/api/xac-nhan-muon', methods=['POST'])
@login_required
def confirm_borrow():
    # Ràng buộc: Tài khoản không bị khóa
    if current_user.bi_khoa:
        return jsonify({'status': 'error', 'msg': 'Tài khoản của bạn đang bị khóa!'})

    # MỚI: Ràng buộc không nợ sách quá hạn
    no_qua_han = PhieuMuon.query.filter(PhieuMuon.ma_nguoi_dung == current_user.id,
                                        PhieuMuon.trang_thai == TrangThaiMuon.QUA_HAN).first()
    if no_qua_han:
        return jsonify({'status': 'error', 'msg': 'Bạn đang có sách mượn quá hạn chưa trả!'})

    cart = session.get('borrow_cart')
    if not cart:
        return jsonify({'status': 'error', 'msg': 'Danh sách mượn đang trống.'})

    # Tạo Phiếu Mượn chính thức
    phieu = PhieuMuon(
        ma_nguoi_dung=current_user.id,
        han_tra=datetime.now() + timedelta(days=14)
    )
    db.session.add(phieu)

    for book_id, item in cart.items():
        sach = Sach.query.get(book_id)
        if not sach or sach.so_luong_con < 1:
            return jsonify({'status': 'error', 'msg': f'Sách "{item["ten_sach"]}" hiện đã hết bản.'})

        sach.so_luong_con -= 1
        chi_tiet = ChiTietMuon(ma_phieu=phieu.id, ma_sach=book_id)
        db.session.add(chi_tiet)

    try:
        db.session.commit()
        session.pop('borrow_cart', None)
        return jsonify({'status': 'success', 'msg': 'Lập phiếu mượn thành công!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'msg': 'Lỗi hệ thống: ' + str(e)})


# 7. Xử lý Đăng nhập
@app.route('/login', methods=['get', 'post'])
def login_user_process():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        password_hashed = str(hashlib.md5(password.encode('utf-8')).hexdigest())
        user = NguoiDung.query.filter(NguoiDung.ten_dang_nhap == username,
                                      NguoiDung.mat_khau == password_hashed).first()

        if user:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Sai tên đăng nhập hoặc mật khẩu!", "danger")
            return redirect(url_for('login_user_process'))

    return render_template('login.html')


# 8. Xử lý Đăng ký
@app.route('/register', methods=['get', 'post'])
def register_process():
    err_msg = ''
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if password == confirm:
            user_exists = NguoiDung.query.filter(NguoiDung.ten_dang_nhap == username).first()
            if user_exists:
                err_msg = 'Tên đăng nhập đã tồn tại!'
            else:
                password_hashed = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
                new_user = NguoiDung(ten=name,
                                     ten_dang_nhap=username,
                                     mat_khau=password_hashed)
                try:
                    db.session.add(new_user)
                    db.session.commit()
                    return redirect(url_for('login_user_process'))
                except Exception as e:
                    err_msg = 'Lỗi hệ thống: ' + str(e)
        else:
            err_msg = 'Mật khẩu xác nhận không khớp!'

    return render_template('register.html', err_msg=err_msg)


# 9. Xử lý Đăng xuất
@app.route('/logout')
def logout_process():
    logout_user()
    return redirect(url_for('index'))


@app.route('/api/borrow-cart/<book_id>', methods=['delete'])
def delete_cart_item(book_id):
    cart = session.get('borrow_cart')
    if cart and book_id in cart:
        del cart[book_id]
        session['borrow_cart'] = cart

    return jsonify({
        'status': 'success',
        'total_quantity': sum(item['quantity'] for item in cart.values())
    })

if __name__ == '__main__':
    app.run(debug=True)