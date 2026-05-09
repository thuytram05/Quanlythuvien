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
    # Kiểm tra xem có thống kê cho thể loại 'Công nghệ' không
    assert any("Công nghệ" in str(s) for s in stats)


# --- NHÓM 2: BÁO CÁO TẦN SUẤT MƯỢN TRẢ THEO THÁNG ---

def test_thong_ke_muon_tra_has_data(test_session, sample_data):
    """2. Kiểm tra báo cáo khi có dữ liệu phát sinh trong tháng"""
    user = sample_data['users'][0]
    book = sample_data['books'][0]
    test_month, test_year = 5, 2026
    test_date = datetime(test_year, test_month, 15)

    p = PhieuMuon(ma_nguoi_dung=user.id, ngay_muon=test_date, ngay_tao=test_date,
                  han_tra=test_date + timedelta(days=14), trang_thai=TrangThaiMuon.DA_TRA)
    test_session.add(p)
    test_session.commit()
    test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book.id))
    test_session.commit()

    report = thong_ke_muon_tra(month=test_month, year=test_year)
    assert len(report) > 0
    assert any(book.the_loai.ten_the_loai in str(row) or book.ten_sach in str(row) for row in report)


def test_thong_ke_muon_tra_no_data(test_session, sample_data):
    """3. Kiểm tra báo cáo tháng không có dữ liệu (Negative Case)"""
    report = thong_ke_muon_tra(month=1, year=1990)
    assert isinstance(report, list)
    assert len(report) == 0


def test_thong_ke_muon_tra_logic_sum(test_session, sample_data):
    """4. Kiểm tra logic cộng dồn (Group By) khi mượn nhiều lần"""
    user = sample_data['users'][0]
    book = sample_data['books'][1]
    test_month, test_year = 8, 2026
    test_date = datetime(test_year, test_month, 20)

    for _ in range(2):
        p = PhieuMuon(ma_nguoi_dung=user.id, ngay_muon=test_date, ngay_tao=test_date,
                      han_tra=test_date + timedelta(days=7), trang_thai=TrangThaiMuon.DA_TRA)
        test_session.add(p)
        test_session.commit()
        test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book.id))
        test_session.commit()

    report = thong_ke_muon_tra(month=test_month, year=test_year)

    count_val = 0
    target = book.the_loai.ten_the_loai
    for row in report:
        if target in str(row) or book.ten_sach in str(row):
            count_val = next((item for item in reversed(row) if isinstance(item, (int, float))), 0)
            break
    assert count_val >= 2


def test_thong_ke_muon_tra_isolation(test_session, sample_data):
    """5. Kiểm tra tính cô lập: Dữ liệu tháng này không được lẫn vào tháng khác"""
    user = sample_data['users'][0]
    book = sample_data['books'][2]

    # Xóa sạch phiếu cũ trong session này để test độc lập hoàn toàn
    test_session.query(ChiTietMuon).delete()
    test_session.query(PhieuMuon).delete()
    test_session.commit()

    # Tạo 1 phiếu tháng 5, 2 phiếu tháng 8
    dates = [(datetime(2026, 5, 1), 1), (datetime(2026, 8, 1), 2)]
    for date_val, count in dates:
        for _ in range(count):
            p = PhieuMuon(ma_nguoi_dung=user.id, ngay_muon=date_val, ngay_tao=date_val,
                          han_tra=date_val + timedelta(days=7), trang_thai=TrangThaiMuon.DA_TRA)
            test_session.add(p)
            test_session.commit()
            test_session.add(ChiTietMuon(ma_phieu=p.id, ma_sach=book.id))
            test_session.commit()

    # Truy vấn tháng 8, kết quả phải là 2 (không được tính cái của tháng 5)
    report_aug = thong_ke_muon_tra(month=8, year=2026)
    count_aug = 0
    for row in report_aug:
        if book.the_loai.ten_the_loai in str(row):
            count_aug = next((item for item in reversed(row) if isinstance(item, (int, float))), 0)

    assert count_aug == 2