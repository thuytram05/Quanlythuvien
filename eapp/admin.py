from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user
from flask import redirect
from sqlalchemy import func
from eapp.models import Sach, TheLoai, NguoiDung, VaiTro
from eapp import db, app

app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

class AdminBaseView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.vai_tro == VaiTro.QUAN_TRI

class SachView(AdminBaseView):
    column_list = ['id', 'ten_sach', 'tac_gia', 'so_luong_con', 'tong_so_luong', 'the_loai']
    column_labels = {
        'ten_sach': 'Tên sách',
        'tac_gia': 'Tác giả',
        'so_luong_con': 'Còn lại',
        'tong_so_luong': 'Tổng số',
        'the_loai': 'Thể loại'
    }
    column_searchable_list = ['ten_sach', 'tac_gia']
    column_filters = ['ten_sach', 'tac_gia', 'so_luong_con']
    can_export = True
    edit_modal = True
    column_editable_list = ['ten_sach', 'so_luong_con', 'tong_so_luong']
    page_size = 10 # Trong Admin để 10 cho dễ quản lý

class NguoiDungView(AdminBaseView):
    column_list = ['id', 'ten', 'ten_dang_nhap', 'vai_tro', 'bi_khoa']
    column_labels = {
        'ten': 'Họ tên',
        'ten_dang_nhap': 'Username',
        'vai_tro': 'Vai trò',
        'bi_khoa': 'Trạng thái khóa'
    }
    column_searchable_list = ['ten', 'ten_dang_nhap']
    column_editable_list = ['bi_khoa']

    form_excluded_columns = ['phieu_muon_sach', 'items_trong_gio', 'mat_khau']

class TheLoaiView(AdminBaseView):
    column_list = ['id', 'ten_the_loai']
    column_labels = {'ten_the_loai': 'Tên thể loại'}
    column_searchable_list = ['ten_the_loai']

class StatsView(BaseView):
    @expose('/')
    def index(self):
        # Thống kê số lượng sách theo thể loại
        stats = db.session.query(TheLoai.ten_the_loai, func.count(Sach.id))\
            .join(Sach, Sach.ma_the_loai == TheLoai.id, isouter=True)\
            .group_by(TheLoai.id).all()
        return self.render('admin/stats.html', stats=stats)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.vai_tro == VaiTro.QUAN_TRI

class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/')

    def is_accessible(self):
        return current_user.is_authenticated

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')

admin = Admin(app=app, name="HỆ THỐNG THƯ VIỆN", index_view=MyAdminIndexView())

admin.add_view(TheLoaiView(TheLoai, db.session, name='Thể Loại'))
admin.add_view(SachView(Sach, db.session, name='Sách'))
admin.add_view(NguoiDungView(NguoiDung, db.session, name='Độc Giả'))
admin.add_view(StatsView(name='Thống Kê'))
admin.add_view(LogoutView(name='Đăng Xuất'))