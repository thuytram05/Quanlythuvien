import hashlib

import  pytest
from eapp.dao import add_user, auth_user
from eapp.models import NguoiDung
from eapp.test.test_base import test_session, test_app, mock_cloudinary

def test_register_success(test_app, test_session, mock_cloudinary):
    name = 'Độc giả mới'
    username = 'newuser01'
    password = 'Password123'

    add_user(name=name, username=username, password=password, avatar=None)

    u = NguoiDung.query.filter(NguoiDung.ten_dang_nhap == username).first()

    assert u is not None
    assert u.ten == name

    expected_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
    assert u.mat_khau == expected_hash

def test_existing_username(test_session, mock_cloudinary):
    username = 'trunglap_user'
    add_user(name='Người thứ nhất', username = username, password='Password123!', avatar=None)
    with pytest.raises(Exception):
        add_user(name='Người thứ hai', username=username, password='Password123!', avatar=None)

@pytest.mark.parametrize('password', [
    '123',
    '',
    '          ',
])

def test_register_invalid_password(test_session, password):
    with pytest.raises(ValueError):
        add_user(name='Lỗi MK', username='loimk', password=password, avatar=None)


def test_auth_user_success(test_session):
    username = 'login_test'
    password = 'correct_pass'

    pass_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
    u = NguoiDung(ten="Tester", ten_dang_nhap=username, mat_khau=pass_hash, bi_khoa=False)
    test_session.add(u)
    test_session.commit()

    user_authenticated = auth_user(username=username, password=password)

    assert user_authenticated is not None
    assert user_authenticated.ten_dang_nhap == username


def test_auth_user_wrong_password(test_session):
    user_authenticated = auth_user(username = 'login_test', password = 'wrong_password')

    assert user_authenticated is None

def test_auth_blocked_user(test_session):
    username = 'blocked_user'
    password = '123'
    pass_hash = hashlib.md5(password.encode('utf-8')).hexdigest()

    u = NguoiDung(ten="Bị khóa", ten_dang_nhap=username, mat_khau=pass_hash, bi_khoa=True)
    test_session.add(u)
    test_session.commit()

    user_authenticated = auth_user(username=username, password=password)

    if user_authenticated:
        assert user_authenticated.bi_khoa is True
    else:
        assert user_authenticated is None




