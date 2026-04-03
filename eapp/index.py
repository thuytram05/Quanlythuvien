import math
from datetime import datetime
from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user, login_required
from eapp import app, login, dao, utils
from eapp.models import PhieuMuon, Sach


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


@app.context_processor
def common_data():
    cart_items = dao.get_cart_all(current_user.id) if current_user.is_authenticated else []
    return {
        'categories': dao.load_categories(),
        'cart_stats': utils.stats_cart(cart_items)
    }


@app.route('/')
def index():
    kw = request.args.get('kw', '').strip()
    category_id = request.args.get('category_id')
    page = request.args.get('page', 1, type=int)

    query = Sach.query
    if kw:
        query = query.filter(Sach.ten_sach.contains(kw) | Sach.tac_gia.contains(kw))
    if category_id:
        query = query.filter(Sach.ma_the_loai == category_id)

    pagination = query.order_by(Sach.id.desc()).paginate(page=page, per_page=app.config['PAGE_SIZE'], error_out=False)

    return render_template('index.html',
                           books=pagination.items,
                           pagination=pagination,
                           page=page,
                           current_kw=kw)


@app.route('/phieu-muon')
@login_required
def phieu_muon():
    cart_items = dao.get_cart_all(current_user.id)
    return render_template('phieu_muon.html', cart_items=cart_items, total_count=len(cart_items))


@app.route('/api/muon-sach', methods=['POST'])
@login_required
def add_to_borrow_cart():
    book_id = request.json.get('id')
    sach_dang_giu = dao.count_books_currently_borrowed(current_user.id)
    sach_trong_tui = dao.count_cart_items(current_user.id)

    if not utils.can_borrow(sach_dang_giu, sach_trong_tui):
        return jsonify({'status': 'error', 'msg': f'Giới hạn 5 cuốn! (Bạn đang giữ {sach_dang_giu} cuốn)'})

    if dao.check_book_in_cart(current_user.id, book_id):
        return jsonify({'status': 'error', 'msg': 'Sách này đã có trong túi mượn!'})

    sach = dao.get_book_by_id(book_id)
    if not sach or sach.so_luong_con < 1:
        return jsonify({'status': 'error', 'msg': 'Sách này hiện đã hết bản!'})

    try:
        dao.add_to_cart(current_user.id, book_id)
        return jsonify({'status': 'success', 'msg': 'Đã thêm vào túi mượn!', 'total_quantity': sach_trong_tui + 1})
    except:
        return jsonify({'status': 'error', 'msg': 'Lỗi hệ thống!'})


@app.route('/api/xac-nhan-muon', methods=['POST'])
@login_required
def confirm_borrow():
    if getattr(current_user, 'bi_khoa', False):
        return jsonify({'status': 'error', 'msg': 'Tài khoản của bạn đang bị khóa!'})

    if dao.check_overdue(current_user.id):
        return jsonify({'status': 'error', 'msg': 'Bạn đang nợ sách quá hạn, vui lòng trả trước!'})

    cart_items = dao.get_cart_all(current_user.id)
    if not cart_items:
        return jsonify({'status': 'error', 'msg': 'Danh sách mượn trống!'})

    sach_dang_giu = dao.count_books_currently_borrowed(current_user.id)
    if utils.is_over_limit(sach_dang_giu, len(cart_items)):
        return jsonify({'status': 'error', 'msg': 'Tổng số sách mượn vượt quá 5 cuốn!'})

    try:
        dao.create_borrow_receipt(current_user.id, cart_items)
        return jsonify({'status': 'success', 'msg': 'Lập phiếu mượn thành công!'})
    except Exception as e:
        return jsonify({'status': 'error', 'msg': str(e)})


@app.route('/api/borrow-cart/clear', methods=['POST'])
@login_required
def clear_cart():
    try:
        dao.clear_user_cart(current_user.id)
        return jsonify({'status': 'success', 'msg': 'Đã xóa toàn bộ túi mượn!'})
    except Exception as e:
        return jsonify({'status': 'error', 'msg': str(e)})


@app.route('/api/borrow-cart/<int:book_id>', methods=['DELETE'])
@login_required
def delete_item(book_id):
    dao.remove_cart_item(current_user.id, book_id)
    return jsonify({'status': 'success'})


@app.route('/login', methods=['GET', 'POST'])
def login_user_process():
    if request.method == 'POST':
        user = dao.auth_user(request.form.get('username'), request.form.get('password'))
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
        if data.get('password') != data.get('confirm'):
            err_msg = 'Mật khẩu không khớp!'
        else:
            try:
                dao.add_user(name=data.get('name'), username=data.get('username'),
                             password=data.get('password'), avatar=request.files.get('avatar'))
                return redirect(url_for('login_user_process'))
            except Exception as ex:
                err_msg = str(ex)
    return render_template('register.html', err_msg=err_msg)


@app.route('/logout')
def logout_process():
    logout_user()
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    phieu_muon_list = dao.get_borrow_history(current_user.id)
    return render_template('profile.html', phieu_muon_list=phieu_muon_list)


@app.route('/lich-su-muon')
@login_required
def lich_su_muon():
    page = request.args.get('page', 1, type=int)
    pagination = PhieuMuon.query.filter_by(ma_nguoi_dung=current_user.id) \
        .order_by(PhieuMuon.ngay_muon.desc()) \
        .paginate(page=page, per_page=app.config['PAGE_SIZE'], error_out=False)

    return render_template('lich_su_muon.html',
                           phieu_muon_list=pagination.items,
                           pagination=pagination,
                           now=datetime.now())


@app.route('/sach/<int:sach_id>')
def chi_tiet_sach(sach_id):
    sach = dao.get_book_by_id(sach_id)
    if not sach: return "Không tìm thấy", 404
    return render_template('chi_tiet.html', sach=sach)


if __name__ == '__main__':
    from eapp import admin

    app.run(debug=True)