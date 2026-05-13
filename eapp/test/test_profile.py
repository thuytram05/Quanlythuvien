import pytest
from eapp.test.test_base import test_client, test_app, sample_data, test_session
from eapp.models import PhieuMuon
from datetime import datetime, timedelta

def test_profile_access_denied_for_guest(test_client):
    res = test_client.get('/profile', follow_redirects=True)
    assert "/login" in res.request.path


def test_profile_display_correct_user_info(test_client, sample_data):
    user = sample_data['users'][0]

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.get('/profile')
    assert res.status_code == 200

    data = res.get_data(as_text=True)
    assert user.ten in data
    assert user.ten_dang_nhap in data

    assert str(user.vai_tro.value) in data or "Thành viên" in data


def test_profile_role_visibility(test_client, sample_data):
    user = sample_data['users'][1]

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.get('/profile')
    data = res.get_data(as_text=True)

    assert "Trạng thái thẻ độc giả" in data
    assert "TÀI KHOẢN BỊ KHÓA" in data
    assert user.ten in data


def test_profile_statistics_display(test_client, sample_data):
    user = sample_data['users'][0]

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.get('/profile')
    data = res.get_data(as_text=True)

    assert "ĐANG MƯỢN" in data
    assert "LƯỢT MƯỢN" in data
    assert "0" in data


def test_profile_display_active_status(test_client, sample_data):
    user = sample_data['users'][0]
    user.bi_khoa = False

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.get('/profile')
    data = res.get_data(as_text=True)
    assert "ĐANG HOẠT ĐỘNG" in data or "Bình thường" in data


def test_profile_avatar_rendering(test_client, sample_data):
    user = sample_data['users'][0]
    user.anh_dai_dien = "https://example.com/avatar.jpg"

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.get('/profile')
    assert "avatar.jpg" in res.get_data(as_text=True)


def test_profile_real_statistics_count(test_client, test_session, sample_data):
    user = sample_data['users'][0]

    p1 = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now() + timedelta(days=7))
    p2 = PhieuMuon(ma_nguoi_dung=user.id, han_tra=datetime.now() + timedelta(days=7))
    test_session.add_all([p1, p2])
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.get('/profile')
    data = res.get_data(as_text=True)

    assert "2" in data

def test_profile_special_characters_display(test_client, test_session, sample_data):
    user = sample_data['users'][0]
    user.ten = "Nguyễn Văn A <script>"
    test_session.commit()

    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.get('/profile')
    assert "Nguyễn Văn A" in res.get_data(as_text=True)

def test_profile_default_avatar_visibility(test_client, sample_data):
    user = sample_data['users'][0]
    with test_client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)

    res = test_client.get('/profile')

    assert "cloudinary" in res.get_data(as_text=True) or "sample.jpg" in res.get_data(as_text=True)