import pytest
from datetime import datetime, timedelta
from eapp.dao import count_sach_by_theloai, thong_ke_muon_tra
from eapp.models import PhieuMuon, ChiTietMuon, TrangThaiMuon, Sach, VaiTro
from eapp.test.test_base import test_session, test_app, sample_data, test_client

def test_count_sach_by_theloai(test_session, sample_data):
    stats = count_sach_by_theloai()
    assert len(stats) >= 1
    assert any("Công nghệ" in str(s) for s in stats)

def test_count_sach_by_theloai_exact_math(test_session, sample_data):
    tl = sample_data['categories'][0]
    test_session.query(Sach).filter_by(ma_the_loai=tl.id).delete()
    for i in range(7):
        test_session.add(Sach(ten_sach=f"Sách Test {i}", tac_gia="TG", ma_the_loai=tl.id))
    test_session.commit()
    stats = count_sach_by_theloai()
    target_row = next(s for s in stats if s[1] == tl.ten_the_loai)
    assert target_row[2] == 7

def test_thong_ke_muon_tra_logic_sum(test_session, sample_data):
    user = sample_data['users'][0]
    book = sample_data['books'][1]
    test_month, test_year = 8, 2026
    test_date = datetime(test_year, test_month, 20)
    han_tra = test_date + timedelta(days=14)
    for _ in range(2):
        p = PhieuMuon(ma_nguoi_dung=user.id, ngay_muon=test_date,
                      han_tra=han_tra, trang_thai=TrangThaiMuon.DA_TRA)
        test_session.add(p)
        test_session.commit()
        test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book.id))
        test_session.commit()
    report = thong_ke_muon_tra(month=test_month, year=test_year)
    count_val = next((row[1] for row in report if book.the_loai.ten_the_loai in row[0]), 0)
    assert count_val == 2

def test_thong_ke_muon_tra_isolation(test_session, sample_data):
    user = sample_data['users'][0]
    book = sample_data['books'][2]
    test_session.query(ChiTietMuon).delete()
    test_session.query(PhieuMuon).delete()
    test_session.commit()
    dates = [(datetime(2026, 5, 1), 1), (datetime(2026, 8, 1), 2)]
    for date_val, count in dates:
        han_tra = date_val + timedelta(days=14)
        for _ in range(count):
            p = PhieuMuon(ma_nguoi_dung=user.id, ngay_muon=date_val,
                          han_tra=han_tra, trang_thai=TrangThaiMuon.DA_TRA)
            test_session.add(p)
            test_session.commit()
            test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book.id))
            test_session.commit()
    report_aug = thong_ke_muon_tra(month=8, year=2026)
    count_aug = report_aug[0][1] if report_aug else 0
    assert count_aug == 2

def test_thong_ke_muon_tra_year_isolation(test_session, sample_data):
    user = sample_data['users'][0]
    book = sample_data['books'][0]
    years = [(2025, 1), (2026, 3)]
    for year, count in years:
        dt = datetime(year, 5, 10)
        han_tra = dt + timedelta(days=14)
        for _ in range(count):
            p = PhieuMuon(ma_nguoi_dung=user.id, ngay_muon=dt,
                          han_tra=han_tra, trang_thai=TrangThaiMuon.DA_TRA)
            test_session.add(p)
            test_session.commit()
            test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book.id))
            test_session.commit()
    report = thong_ke_muon_tra(month=5, year=2026)
    count_2026 = report[0][1] if report else 0
    assert count_2026 == 3

def test_thong_ke_muon_tra_percentage(test_session, sample_data):
    user = sample_data['users'][0]
    tl1, tl2 = sample_data['categories'][0], sample_data['categories'][1]
    dt = datetime(2026, 11, 1)
    han_tra = dt + timedelta(days=14)
    book_tl2 = sample_data['books'][10]
    book_tl2.ma_the_loai = tl2.id
    test_session.commit()
    data_setup = [(sample_data['books'][0], 3), (book_tl2, 1)]
    for book, count in data_setup:
        for _ in range(count):
            p = PhieuMuon(ma_nguoi_dung=user.id, ngay_muon=dt,
                          han_tra=han_tra, trang_thai=TrangThaiMuon.DA_TRA)
            test_session.add(p)
            test_session.commit()
            test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book.id))
            test_session.commit()
    report = thong_ke_muon_tra(month=11, year=2026)
    stats = {row[0]: row[2] for row in report}
    assert stats[tl1.ten_the_loai] in [75.0, 0.75]
    assert stats[tl2.ten_the_loai] in [25.0, 0.25]

def test_thong_ke_muon_tra_no_data(test_session, sample_data):
    report = thong_ke_muon_tra(month=1, year=1990)
    assert isinstance(report, list)
    assert len(report) == 0

def test_thong_ke_muon_tra_boundary_dates_full(test_session, sample_data):
    user = sample_data['users'][0]
    book = sample_data['books'][0]
    test_month, test_year = 12, 2026
    dates = [
        datetime(test_year, test_month, 1, 0, 0, 1),
        datetime(test_year, test_month, 31, 23, 59, 59)
    ]
    for d in dates:
        p = PhieuMuon(ma_nguoi_dung=user.id, ngay_muon=d, han_tra=d + timedelta(days=7),
                      trang_thai=TrangThaiMuon.DA_TRA)
        test_session.add(p)
        test_session.commit()
        test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book.id))
    test_session.commit()
    report = thong_ke_muon_tra(month=test_month, year=test_year)
    count_val = next((row[1] for row in report if book.the_loai.ten_the_loai in row[0]), 0)
    assert count_val == 2

def test_count_sach_by_theloai_empty_category(test_session, sample_data):
    from eapp.models import TheLoai
    new_tl = TheLoai(ten_the_loai="Thể loại mới tinh")
    test_session.add(new_tl)
    test_session.commit()
    stats = count_sach_by_theloai()
    target_row = next((s for s in stats if s[1] == new_tl.ten_the_loai), None)
    if target_row:
        assert target_row[2] == 0

def test_thong_ke_muon_tra_zero_borrowed(test_session, sample_data):
    test_session.query(ChiTietMuon).delete()
    test_session.query(PhieuMuon).delete()
    test_session.commit()
    report = thong_ke_muon_tra(month=2, year=2026)
    assert len(report) == 0

def test_thong_ke_muon_tra_status_isolation(test_session, sample_data):
    user = sample_data['users'][0]
    book = sample_data['books'][0]
    dt = datetime(2026, 1, 15)
    han_tra = dt + timedelta(days=14)
    p1 = PhieuMuon(ma_nguoi_dung=user.id, ngay_muon=dt, han_tra=han_tra, trang_thai=TrangThaiMuon.DA_TRA)
    p2 = PhieuMuon(ma_nguoi_dung=user.id, ngay_muon=dt, han_tra=han_tra, trang_thai=TrangThaiMuon.DANG_MUON)
    other_status = [s for s in TrangThaiMuon if s not in [TrangThaiMuon.DA_TRA, TrangThaiMuon.DANG_MUON]][0]
    p3 = PhieuMuon(ma_nguoi_dung=user.id, ngay_muon=dt, han_tra=han_tra, trang_thai=other_status)
    test_session.add_all([p1, p2, p3])
    test_session.commit()
    for p in [p1, p2, p3]:
        test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book.id))
    test_session.commit()
    report = thong_ke_muon_tra(month=1, year=2026)
    count_val = next((row[1] for row in report if book.the_loai.ten_the_loai in row[0]), 0)
    assert count_val == 3

def test_stats_data_integrity_after_book_update(test_session, sample_data):
    user = sample_data['users'][0]
    book = sample_data['books'][3]
    old_tl_name = book.the_loai.ten_the_loai
    dt = datetime(2026, 9, 10)
    p = PhieuMuon(ma_nguoi_dung=user.id, ngay_muon=dt, han_tra=dt + timedelta(days=7), trang_thai=TrangThaiMuon.DA_TRA)
    test_session.add(p)
    test_session.commit()
    test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book.id))
    test_session.commit()
    book.ten_sach = "Tên Sách Đã Thay Đổi"
    test_session.commit()
    report = thong_ke_muon_tra(month=9, year=2026)
    assert any(old_tl_name in row[0] for row in report)
    assert report[0][1] >= 1

def test_thong_ke_muon_tra_multiple_books_in_one_bill(test_session, sample_data):
    user = sample_data['users'][0]
    book1 = sample_data['books'][0]
    book2 = sample_data['books'][1]
    book2.ma_the_loai = book1.ma_the_loai
    test_session.commit()
    dt = datetime(2026, 3, 15)
    p = PhieuMuon(ma_nguoi_dung=user.id, ngay_muon=dt, han_tra=dt + timedelta(days=7), trang_thai=TrangThaiMuon.DA_TRA)
    test_session.add(p)
    test_session.commit()
    test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book1.id))
    test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book2.id))
    test_session.commit()
    report = thong_ke_muon_tra(month=3, year=2026)
    count_val = next((row[1] for row in report if book1.the_loai.ten_the_loai in row[0]), 0)
    assert count_val == 2

def test_thong_ke_muon_tra_cross_month_logic(test_session, sample_data):
    user = sample_data['users'][0]
    book = sample_data['books'][0]
    ngay_muon = datetime(2026, 1, 30)
    p = PhieuMuon(ma_nguoi_dung=user.id, ngay_muon=ngay_muon,
                  han_tra=ngay_muon + timedelta(days=14), trang_thai=TrangThaiMuon.DA_TRA)
    test_session.add(p)
    test_session.commit()
    test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book.id))
    test_session.commit()
    report_jan = thong_ke_muon_tra(month=1, year=2026)
    assert len(report_jan) > 0
    report_feb = thong_ke_muon_tra(month=2, year=2026)
    assert len(report_feb) == 0

def test_stats_category_rename_integrity(test_session, sample_data):
    cate = sample_data['categories'][0]
    book = sample_data['books'][0]
    book.ma_the_loai = cate.id
    dt = datetime(2026, 5, 15)
    p = PhieuMuon(ma_nguoi_dung=sample_data['users'][0].id, ngay_muon=dt,
                  han_tra=dt + timedelta(days=7), trang_thai=TrangThaiMuon.DA_TRA)
    test_session.add(p)
    test_session.commit()
    test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book.id))
    test_session.commit()
    cate.ten_the_loai = "TÊN MỚI"
    test_session.commit()
    report = thong_ke_muon_tra(month=5, year=2026)
    assert report[0][0] == "TÊN MỚI"

def test_api_stats_json_format(test_client, sample_data, test_session):
    admin_user = sample_data['users'][0]
    admin_user.vai_tro = VaiTro.QUAN_TRI
    test_session.commit()
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(admin_user.id)
    res = test_client.get('/api/stats?month=5&year=2026')
    assert res.status_code == 200
    json_data = res.get_json()
    assert "labels" in json_data
    assert "datasets" in json_data
    assert isinstance(json_data['labels'], list)
    assert len(json_data['datasets']) > 0

def test_admin_stats_view_unauthorized(test_client, sample_data, test_session):
    non_admin_role = [r for r in VaiTro if r != VaiTro.QUAN_TRI][0]
    user = sample_data['users'][0]
    user.vai_tro = non_admin_role
    test_session.commit()
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
    res = test_client.get('/admin/statsview/')
    assert res.status_code == 403