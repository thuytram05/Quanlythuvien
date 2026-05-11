import pytest
from datetime import datetime, timedelta
from eapp.dao import count_sach_by_theloai, thong_ke_muon_tra
from eapp.models import PhieuMuon, ChiTietMuon, TrangThaiMuon, Sach
from eapp.test.test_base import test_session, test_app, sample_data


# --- NHÓM 1: THỐNG KÊ MẬT ĐỘ SÁCH ---

def test_count_sach_by_theloai(test_session, sample_data):
    """1. Kiểm tra tính chính xác của việc đếm mật độ sách hiện có"""
    stats = count_sach_by_theloai()
    assert len(stats) >= 1
    assert any("Công nghệ" in str(s) for s in stats)


def test_count_sach_by_theloai_exact_math(test_session, sample_data):
    """2. Kiểm tra số lượng sách đếm được phải khớp tuyệt đối với DB"""
    tl = sample_data['categories'][0]
    # Làm sạch sách cũ của thể loại này
    test_session.query(Sach).filter_by(ma_the_loai=tl.id).delete()

    # Thêm mới đúng 7 cuốn
    for i in range(7):
        test_session.add(Sach(ten_sach=f"Sách Test {i}", tac_gia="TG", ma_the_loai=tl.id))
    test_session.commit()

    stats = count_sach_by_theloai()
    target_row = next(s for s in stats if s[1] == tl.ten_the_loai)
    assert target_row[2] == 7


# --- NHÓM 2: BÁO CÁO TẦN SUẤT MƯỢN TRẢ THEO THÁNG ---

def test_thong_ke_muon_tra_logic_sum(test_session, sample_data):
    """3. Kiểm tra logic cộng dồn (Group By) khi mượn nhiều lần"""
    user = sample_data['users'][0]
    book = sample_data['books'][1]
    test_month, test_year = 8, 2026
    test_date = datetime(test_year, test_month, 20)
    # FIX: Thêm han_tra để tránh lỗi IntegrityError
    han_tra = test_date + timedelta(days=14)

    for _ in range(2):
        p = PhieuMuon(ma_nguoi_dung=user.id, ngay_muon=test_date,
                      han_tra=han_tra, trang_thai=TrangThaiMuon.DA_TRA)
        test_session.add(p);
        test_session.commit()
        test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book.id))
        test_session.commit()

    report = thong_ke_muon_tra(month=test_month, year=test_year)
    count_val = next((row[1] for row in report if book.the_loai.ten_the_loai in row[0]), 0)
    assert count_val == 2


def test_thong_ke_muon_tra_isolation(test_session, sample_data):
    """4. Kiểm tra tính cô lập: Dữ liệu tháng này không được lẫn vào tháng khác"""
    user = sample_data['users'][0]
    book = sample_data['books'][2]
    test_session.query(ChiTietMuon).delete()
    test_session.query(PhieuMuon).delete()
    test_session.commit()

    dates = [(datetime(2026, 5, 1), 1), (datetime(2026, 8, 1), 2)]
    for date_val, count in dates:
        # FIX: Thêm han_tra
        han_tra = date_val + timedelta(days=14)
        for _ in range(count):
            p = PhieuMuon(ma_nguoi_dung=user.id, ngay_muon=date_val,
                          han_tra=han_tra, trang_thai=TrangThaiMuon.DA_TRA)
            test_session.add(p);
            test_session.commit()
            test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book.id))
            test_session.commit()

    report_aug = thong_ke_muon_tra(month=8, year=2026)
    count_aug = report_aug[0][1] if report_aug else 0
    assert count_aug == 2


def test_thong_ke_muon_tra_year_isolation(test_session, sample_data):
    """5. RÀNG BUỘC: Dữ liệu cùng tháng nhưng khác năm không được lẫn lộn"""
    user = sample_data['users'][0]
    book = sample_data['books'][0]
    years = [(2025, 1), (2026, 3)]
    for year, count in years:
        dt = datetime(year, 5, 10)
        # FIX: Thêm han_tra
        han_tra = dt + timedelta(days=14)
        for _ in range(count):
            p = PhieuMuon(ma_nguoi_dung=user.id, ngay_muon=dt,
                          han_tra=han_tra, trang_thai=TrangThaiMuon.DA_TRA)
            test_session.add(p);
            test_session.commit()
            test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book.id))
            test_session.commit()

    report = thong_ke_muon_tra(month=5, year=2026)
    count_2026 = report[0][1] if report else 0
    assert count_2026 == 3


def test_thong_ke_muon_tra_percentage(test_session, sample_data):
    """6. Kiểm tra tính toán tỷ lệ % lượt mượn chính xác"""
    user = sample_data['users'][0]
    tl1, tl2 = sample_data['categories'][0], sample_data['categories'][1]
    dt = datetime(2026, 11, 1)
    han_tra = dt + timedelta(days=14)

    # SỬA LỖI PERCENTAGE: Đảm bảo 2 cuốn sách thuộc 2 thể loại khác nhau
    book_tl2 = sample_data['books'][10]
    book_tl2.ma_the_loai = tl2.id  # Ép sang thể loại Văn học
    test_session.commit()

    # Thể loại 1 mượn 3 lần, Thể loại 2 mượn 1 lần (Tổng = 4) -> Tỷ lệ 75% và 25%
    data_setup = [(sample_data['books'][0], 3), (book_tl2, 1)]
    for book, count in data_setup:
        for _ in range(count):
            p = PhieuMuon(ma_nguoi_dung=user.id, ngay_muon=dt,
                          han_tra=han_tra, trang_thai=TrangThaiMuon.DA_TRA)
            test_session.add(p);
            test_session.commit()
            test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book.id))
            test_session.commit()

    report = thong_ke_muon_tra(month=11, year=2026)
    stats = {row[0]: row[2] for row in report}

    # Tỷ lệ: 3/4 = 75% và 1/4 = 25%
    assert stats[tl1.ten_the_loai] in [75.0, 0.75]
    assert stats[tl2.ten_the_loai] in [25.0, 0.25]

def test_thong_ke_muon_tra_no_data(test_session, sample_data):
    """Kiểm tra báo cáo tháng không có dữ liệu (Ví dụ: Tháng 1 năm 1990)"""
    report = thong_ke_muon_tra(month=1, year=1990)
    assert isinstance(report, list)
    assert len(report) == 0