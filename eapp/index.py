import math
import hashlib
import os
from datetime import datetime, timedelta
from flask import render_template, request, jsonify, session, redirect, url_for, flash, abort
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.utils import secure_filename

from eapp import app, login, db
from eapp.models import Sach, TheLoai, NguoiDung, PhieuMuon, ChiTietMuon, TrangThaiMuon, UserCart


@login.user_loader
def load_user(user_id):
    return NguoiDung.query.get(user_id)


@app.context_processor
def common_data():
    total_quantity = 0
    if current_user.is_authenticated:
        total_quantity = UserCart.query.filter_by(user_id=current_user.id).count()

    return {
        'categories': TheLoai.query.all(),
        'cart_stats': {
            'total_quantity': total_quantity
        }
    }


@app.route('/')
def index():
    kw = request.args.get('kw', '').strip()
    category_id = request.args.get('category_id')
    page = request.args.get('page', 1, type=int)
    page_size = 4

    query = Sach.query

    # RÀNG BUỘC: Tìm kiếm theo tên hoặc tác giả (Từ khóa phải >= 2 ký tự)
    if kw and len(kw) >= 2:
        query = query.filter(Sach.ten_sach.ilike(f"%{kw}%") | Sach.tac_gia.ilike(f"%{kw}%"))

    if category_id:
        query = query.filter(Sach.ma_the_loai == category_id)

    total = query.count()
    pages = math.ceil(total / page_size)
    books = query.offset((page - 1) * page_size).limit(page_size).all()

    return render_template('index.html', books=books, pages=pages, page=page, current_kw=kw)


@app.route('/phieu-muon')
@login_required
def phieu_muon():
    page = request.args.get('page', 1, type=int)
    pagination = UserCart.query.filter_by(user_id=current_user.id) \
        .paginate(page=page, per_page=4, error_out=False)
    cart_items = pagination.items
    total_count = UserCart.query.filter_by(user_id=current_user.id).count()
    return render_template('phieu_muon.html',cart_items=cart_items, pagination=pagination,total_count=total_count)

@app.route('/api/muon-sach', methods=['POST'])
@login_required
def add_to_borrow_cart():
    # RÀNG BUỘC: Người dùng phải đăng nhập (Xử lý tự động bởi @login_required)
    data = request.json
    book_id = data.get('id')

    # RÀNG BUỘC: Một người chỉ được mượn tối đa 5 sách (Kiểm tra số lượng trong túi của User)
    current_cart_count = UserCart.query.filter_by(user_id=current_user.id).count()
    if current_cart_count >= 5:
        return jsonify({'status': 'error', 'msg': 'Túi mượn đã đầy (tối đa 5 cuốn)!'})

    exists = UserCart.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if exists:
        return jsonify({'status': 'error', 'msg': 'Sách này đã có trong túi mượn của bạn!'})

    # RÀNG BUỘC: Không được mượn nếu sách đã hết bản (Kiểm tra tồn kho khi thêm vào giỏ)
    sach = Sach.query.get(book_id)
    if not sach or sach.so_luong_con < 1:
        return jsonify({'status': 'error', 'msg': 'Sách này hiện đã hết bản!'})

    try:
        new_item = UserCart(user_id=current_user.id, book_id=book_id)
        db.session.add(new_item)
        db.session.commit()

        total_in_cart = UserCart.query.filter_by(user_id=current_user.id).count()
        return jsonify({'status': 'success', 'msg': 'Đã thêm vào túi mượn!', 'total_quantity': total_in_cart})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'msg': 'Lỗi hệ thống!'})


@app.route('/api/xac-nhan-muon', methods=['POST'])
@login_required
def confirm_borrow():
    # RÀNG BUỘC: Không được mượn nếu tài khoản bị khóa
    if hasattr(current_user, 'bi_khoa') and current_user.bi_khoa:
        return jsonify({'status': 'error', 'msg': 'Tài khoản của bạn đang bị khóa!'})

    # RÀNG BUỘC: Không được mượn nếu người dùng đang nợ sách quá hạn
    no_qua_han = PhieuMuon.query.filter_by(ma_nguoi_dung=current_user.id,
                                           trang_thai=TrangThaiMuon.QUA_HAN).first()
    if no_qua_han:
        return jsonify({'status': 'error', 'msg': 'Bạn đang nợ sách quá hạn, vui lòng trả trước khi mượn mới!'})

    cart_items = UserCart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        return jsonify({'status': 'error', 'msg': 'Danh sách mượn trống!'})

    try:
        phieu = PhieuMuon(
            ma_nguoi_dung=current_user.id,
            han_tra=datetime.now() + timedelta(days=14)
        )
        db.session.add(phieu)
        db.session.flush()

        for item in cart_items:
            sach = Sach.query.get(item.book_id)
            # RÀNG BUỘC: Kiểm tra lại tồn kho thực tế trước khi chính thức lập phiếu
            if not sach or sach.so_luong_con < 1:
                db.session.rollback()
                return jsonify({'status': 'error', 'msg': f'Sách "{sach.ten_sach}" đã hết bản!'})

            sach.so_luong_con -= 1
            chi_tiet = ChiTietMuon(ma_phieu=phieu.id, ma_sach=sach.id)
            db.session.add(chi_tiet)

        UserCart.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({'status': 'success', 'msg': 'Lập phiếu mượn thành công!'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'msg': 'Lỗi hệ thống!'})


@app.route('/login', methods=['GET', 'POST'])
def login_user_process():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        pwd_hashed = hashlib.md5(password.encode('utf-8')).hexdigest()

        user = NguoiDung.query.filter_by(ten_dang_nhap=username, mat_khau=pwd_hashed).first()
        if user:
            login_user(user)
            return redirect(url_for('index'))

        flash("Sai tên đăng nhập hoặc mật khẩu!", "danger")
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register_process():
    err_msg = ''
    if request.method == 'POST':
        data = request.form
        password = data.get('password')
        confirm = data.get('confirm')
        username = data.get('username').strip()

        if password != confirm:
            err_msg = 'Mật khẩu không khớp!'
        elif NguoiDung.query.filter_by(ten_dang_nhap=username).first():
            err_msg = 'Tên đăng nhập đã tồn tại!'
        else:
            avatar = request.files.get('avatar')
            avatar_path = "/static/images/default-avatar.png"

            if avatar:
                user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
                if not os.path.exists(user_folder):
                    os.makedirs(user_folder)

                fname = secure_filename(avatar.filename)
                avatar.save(os.path.join(user_folder, fname))
                avatar_path = f"/{app.config['UPLOAD_FOLDER']}/{username}/{fname}"

            new_user = NguoiDung(
                ten=data.get('name'),
                ten_dang_nhap=username,
                mat_khau=hashlib.md5(password.encode('utf-8')).hexdigest(),
                anh_dai_dien=avatar_path
            )
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login_user_process'))

    return render_template('register.html', err_msg=err_msg)


@app.route('/logout')
def logout_process():
    logout_user()
    return redirect(url_for('index'))


@app.route('/api/borrow-cart/<int:book_id>', methods=['DELETE'])
@login_required
def delete_item(book_id):
    item = UserCart.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if item:
        db.session.delete(item)
        db.session.commit()
    return jsonify({'status': 'success'})


@app.route('/api/borrow-cart/clear', methods=['POST'])
@login_required
def clear_cart():
    UserCart.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'status': 'success'})


@app.route('/profile')
@login_required
def profile():
    phieu_muon_list = PhieuMuon.query.filter_by(ma_nguoi_dung=current_user.id).all()
    return render_template('profile.html', phieu_muon_list=phieu_muon_list)


@app.route('/lich-su-muon')
@login_required
def lich_su_muon():
    page = request.args.get('page', 1, type=int)
    pagination = PhieuMuon.query.filter_by(ma_nguoi_dung=current_user.id) \
        .order_by(PhieuMuon.ngay_muon.desc()) \
        .paginate(page=page, per_page=3, error_out=False)
    phieu_muon_list = pagination.items
    return render_template('lich_su_muon.html',
                           phieu_muon_list=phieu_muon_list,
                           pagination=pagination,
                           now=datetime.now())

@app.route('/sach/<int:sach_id>')
def chi_tiet_sach(sach_id):
    sach = Sach.query.get_or_404(sach_id)
    return render_template('chi_tiet.html', sach=sach)


if __name__ == '__main__':
    app.run(debug=True)