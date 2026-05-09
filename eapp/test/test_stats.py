import pytest
from datetime import datetime
from eapp.dao import count_sach_by_theloai, thong_ke_muon_tra
from eapp.models import PhieuMuon, ChiTietMuon, TrangThaiMuon, NguoiDung
from eapp.test.test_base import test_session, test_app, sample_data

def test_count_sach_by_theloai(test_session, sample_data):
    stats = count_sach_by_theloai()

    assert len(stats) >= 1

    for s in stats:
        if s[1] == "Công Nghệ":
            assert s[2] == 52

def test_thong_ke_muon_tra(test_session, sample_data):
    user = sample_data['users'][0]
    book = sample_data['books'][0]
    now = datetime.now()

    p = PhieuMuon(ma_nguoi_dung = user.id, han_tra = now, trang_thai = TrangThaiMuon.DANG_MUON)
    test_session.add(p)
    test_session.commit()

    ct = ChiTietMuon(ma_phieu = p.id, ma_sach = book.id)
    test_session.add(ct)
    test_session.commit()

    report = thong_ke_muon_tra(month=now.month, year=now.year)
    assert len(report) > 0