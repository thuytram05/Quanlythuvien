from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from flask import redirect, request, url_for
from eapp.models import Sach, TheLoai, NguoiDung, VaiTro
from eapp import db, app
import dao
from datetime import datetime

# Cấu hình giao diện Admin (Giao diện chuyên nghiệp cho quản lý)
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
app.config['FLASK_ADMIN_TEMPLATE_MODE'] = 'bootstrap4'


# --- 1. LỚP BASE KIỂM TRA QUYỀN (RÀNG BUỘC QUAN TRỌNG) ---
class AdminBaseView(ModelView):
    def is_accessible(self):
        # Chỉ Admin (QUAN_TRI) mới được vào các trang quản lý
        return current_user.is_authenticated and current_user.vai_tro == VaiTro.QUAN_TRI

    def inaccessible_callback(self, name, **kwargs):
        # Nếu không có quyền, tự động đẩy về trang đăng nhập
        return redirect(url_for('login_user_process'))


# --- 2. CÁC VIEW QUẢN LÝ DỮ LIỆU ---

class TheLoaiView(AdminBaseView):
    column_list = ['id', 'ten_the_loai', 'cac_sach']
    column_labels = {
        'ten_the_loai': 'Tên Thể Loại',
        'cac_sach': 'Danh Mục Sách'
    }


class SachView(AdminBaseView):
    # Hiển thị các cột theo đúng nghiệp vụ Thư viện (Đề tài 5)
    column_list = ['id', 'ten_sach', 'tac_gia', 'so_luong_con', 'tong_so_luong', 'the_loai']
    column_labels = {
        'ten_sach': 'Tên Sách',
        'tac_gia': 'Tác Giả',
        'so_luong_con': 'Còn Lại',
        'tong_so_luong': 'Tổng Số',
        'the_loai': 'Thể Loại'
    }
    # Tìm kiếm theo Tên sách và Tác giả như yêu cầu đề bài
    column_searchable_list = ['ten_sach', 'tac_gia']
    column_filters = ['ten_sach', 'tac_gia', 'so_luong_con', 'the_loai.ten_the_loai']

    can_export = True  # Cho phép xuất báo cáo sách
    edit_modal = True  # Sửa thông tin qua popup
    column_editable_list = ['ten_sach', 'so_luong_con', 'tong_so_luong']
    page_size = 20


class NguoiDungView(AdminBaseView):
    # Admin có thể khóa tài khoản độc giả (bi_khoa)
    column_list = ['id', 'ten', 'ten_dang_nhap', 'vai_tro', 'bi_khoa']
    column_labels = {
        'ten': 'Họ Tên',
        'ten_dang_nhap': 'Tên Đăng Nhập',
        'vai_tro': 'Vai Trò',
        'bi_khoa': 'Khóa Tài Khoản'
    }
    column_editable_list = ['bi_khoa', 'vai_tro']
    # Ẩn mật khẩu và các cột hệ thống để bảo mật
    form_excluded_columns = ['phieu_muon_sach', 'mat_khau', 'ngay_tao', 'hoat_dong']


# --- 3. VIEW TÙY CHỈNH (THỐNG KÊ & ĐĂNG XUẤT) ---

class StatsView(BaseView):
    @expose('/')
    def index(self): # Thêm 'self' vào đây
        # Lấy thời gian từ request
        thang = request.args.get('month', datetime.now().month, type=int)
        nam = request.args.get('year', datetime.now().year, type=int)

        return self.render('admin/stats.html',
                           stats=dao.count_sach_by_theloai(),
                           borrow_stats=dao.thong_ke_muon_tra(month=thang, year=nam))

    def is_accessible(self):
        return current_user.is_authenticated and current_user.vai_tro == VaiTro.QUAN_TRI


class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/')

    def is_accessible(self):
        return current_user.is_authenticated


# --- 4. TRANG CHỦ ADMIN (Bảo vệ nghiêm ngặt) ---
class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html', stats=dao.count_sach_by_theloai())

    # Chặn quyền truy cập Dashboard chính đối với người dùng thường
    def is_accessible(self):
        return current_user.is_authenticated and current_user.vai_tro == VaiTro.QUAN_TRI

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login_user_process'))


# --- 5. KHỞI TẠO HỆ THỐNG ADMIN ---
admin = Admin(app=app, name="HỆ THỐNG THƯ VIỆN", index_view=MyAdminIndexView())

admin.add_view(TheLoaiView(TheLoai, db.session, name='Thể Loại'))
admin.add_view(SachView(Sach, db.session, name='Sách'))
admin.add_view(NguoiDungView(NguoiDung, db.session, name='Độc Giả'))
admin.add_view(StatsView(name='Thống Kê'))
admin.add_view(LogoutView(name='Đăng Xuất'))