import math
from datetime import datetime
from flask import render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import current_user, login_user, logout_user, login_required
from eapp import login, dao, utils
from eapp.models import PhieuMuon


def register_routes(app):
    @login.user_loader
    def load_user(user_id):
        return dao.get_user_by_id(user_id)

    @app.context_processor
    def common_data():
        cart = session.get('cart', {})
        stats = utils.stats_cart(cart)
        return {
            'categories': dao.load_categories(),
            'cart_stats': stats,
            'total_count': stats['total_quantity']
        }

    @app.route('/')
    def index():
        kw = request.args.get('kw', '').strip()
        category_id = request.args.get('category_id')
        page = request.args.get('page', 1, type=int)

        per_page = app.config.get('PAGE_SIZE', 50)

        # Ràng buộc: Từ khóa phải >= 2 ký tự
        if kw and len(kw) < 2:
            flash("Từ khóa tìm kiếm phải từ 2 ký tự trở lên!", "warning")
            kw = ""

        books = dao.load_books(category_id=category_id, kw=kw, page=page)
        total_books = dao.count_books_filtered(kw=kw, category_id=category_id)

        return render_template('index.html',
                               books=books,
                               pages=math.ceil(total_books / per_page),
                               page=page,
                               current_kw=kw)


    @app.route('/phieu-muon')
    @login_required
    def view_cart():
        cart = session.get('cart', {})
        stats = utils.stats_cart(cart)
        return render_template('phieu_muon.html', cart=cart, total_count=stats['total_quantity'])

    @app.route('/api/cart', methods=['post'])
    @login_required
    def add_to_cart():
        # Ràng buộc: Tài khoản không bị khóa
        if current_user.bi_khoa:
            return jsonify({'status': 403, 'err_msg': 'Tài khoản của bạn đang bị khóa!'}), 403

        data = request.json
        book_id = str(data.get('id'))
        cart = session.get('cart', {})

        if book_id in cart:
            return jsonify({'status': 400, 'err_msg': 'Cuốn sách này đã có trong danh sách chờ!'}), 400

        # Ràng buộc: Kiểm tra sách còn hay hết
        s = dao.get_book_by_id(int(book_id))
        if not s or s.so_luong_con <= 0:
            return jsonify({'status': 400, 'err_msg': 'Sách này hiện đã hết bản trong thư viện!'}), 400

        # Ràng buộc: Tối đa 5 cuốn (đang mượn + đang chọn)
        borrowed_count = dao.count_books_currently_borrowed(current_user.id)
        if borrowed_count + len(cart) >= 5:
            return jsonify({'status': 400, 'err_msg': 'Bạn chỉ được mượn tối đa 5 cuốn sách!'}), 400

        cart[book_id] = {
            'id': book_id,
            'name': data.get('name'),
            'image': s.hinh_anh,
            'quantity': 1
        }
        session['cart'] = cart
        return jsonify(utils.stats_cart(cart))

    @app.route('/api/cart/<book_id>', methods=['delete'])
    @login_required
    def remove_item(book_id):
        cart = session.get('cart', {})
        if book_id in cart:
            del cart[book_id]
            session['cart'] = cart
        return jsonify(utils.stats_cart(cart))

    @app.route('/api/pay', methods=['post'])
    @login_required
    def pay():
        if dao.check_overdue(current_user.id):
            return jsonify({'status': 400, 'err_msg': 'Bạn đang nợ sách quá hạn, vui lòng trả sách trước!'}), 400

        data = request.json
        cart = session.get('cart')
        if not cart:
            return jsonify({'status': 400, 'err_msg': 'Túi mượn đang trống!'}), 400

        try:
            dao.create_borrow_receipt(
                user_id=current_user.id,
                cart_items=cart.values(),
                phone=data.get('phone'),
                return_date=data.get('returnDate'),
                note=data.get('note')
            )
            session['cart'] = {}
            return jsonify({'status': 200})
        except Exception as e:
            return jsonify({'status': 500, 'err_msg': str(e)}), 500

    @app.route('/tra-sach/<int:phieu_id>', methods=['post'])
    @login_required
    def return_book_process(phieu_id):
        try:
            message, fee = dao.process_return_book(phieu_id, current_user.id)
            if fee > 0:
                flash(f"{message}. Phí phạt trễ hạn: {fee:,.0f} VNĐ", "warning")
            else:
                flash(message, "success")
        except Exception as e:
            flash(str(e), "danger")
        return redirect(url_for('lich_su_muon', tab='da-tra'))

    @app.route('/lich-su-muon')
    @login_required
    def lich_su_muon():
        tab = request.args.get('tab', 'dang-muon')
        page = request.args.get('page', 1, type=int)

        from eapp.models import PhieuMuon, TrangThaiMuon
        query = PhieuMuon.query.filter_by(ma_nguoi_dung=current_user.id)

        if tab == 'da-tra':
            query = query.filter_by(trang_thai=TrangThaiMuon.DA_TRA)
        else:
            query = query.filter(PhieuMuon.trang_thai != TrangThaiMuon.DA_TRA)

        pagination = query.order_by(PhieuMuon.ngay_muon.desc()).paginate(page=page, per_page=5)

        return render_template('lich_su_muon.html',
                               history=pagination.items,
                               pagination=pagination,
                               active_tab=tab)

    @app.route('/login', methods=['get', 'post'])
    def login_user_process():
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        if request.method == 'POST':
            user = dao.auth_user(request.form.get('username'), request.form.get('password'))
            if user:
                login_user(user)
                return redirect(request.args.get('next', url_for('index')))
            flash("Tên đăng nhập hoặc mật khẩu không đúng!", "danger")
        return render_template('login.html')

    @app.route('/register', methods=['get', 'post'])
    def register_process():
        err_msg = ""
        if request.method == 'POST':
            name = request.form.get('name')
            username = request.form.get('username')
            password = request.form.get('password')
            confirm = request.form.get('confirm')
            avatar = request.files.get('avatar')

            if password != confirm:
                err_msg = "Mật khẩu xác nhận không khớp!"
            elif dao.check_username(username):
                err_msg = "Tên tài khoản này đã được sử dụng!"
            else:
                try:
                    dao.add_user(name=name, username=username, password=password, avatar=avatar)
                    flash("Đăng ký thành công! Mời bạn đăng nhập.", "success")
                    return redirect(url_for('login_user_process'))
                except Exception as ex:
                    err_msg = "Lỗi hệ thống: " + str(ex)

        return render_template('register.html', err_msg=err_msg)

    @app.route('/logout')
    def logout_process():
        logout_user()
        return redirect(url_for('index'))


    # --- 7. CÁC ROUTE PHỤ ---
    @app.route('/sach/<int:sach_id>')
    def chi_tiet_sach(sach_id):
        sach = dao.get_book_by_id(sach_id)
        return render_template('chi_tiet.html', sach=sach)

    @app.route('/profile')
    @login_required
    def profile():
        return render_template('profile.html', user=current_user)


from eapp import app

register_routes(app)

@app.route('/api/tra-sach/<int:phieu_id>', methods=['POST'])
@login_required
def tra_sach(phieu_id):
    # Kiểm tra quyền: Chỉ người mượn mới được trả (Ràng buộc Mục 2)
    phieu = PhieuMuon.query.get(phieu_id)
    if not phieu or phieu.ma_nguoi_dung != current_user.id:
        return jsonify({'status': 'error', 'msg': 'Bạn không có quyền thực hiện thao tác này!'})

    try:
        if dao.return_borrow_receipt(phieu_id):
            return jsonify({'status': 'success', 'msg': 'Đã trả sách thành công!'})
    except Exception as e:
        return jsonify({'status': 'error', 'msg': str(e)})

    return jsonify({'status': 'error', 'msg': 'Phiếu không tồn tại hoặc đã trả rồi!'})

if __name__ == '__main__':
    from eapp import admin

    app.run(debug=True)