import  pytest
from eapp.dao import add_user
from eapp.models import NguoiDung
from eapp.test.test_base import test_session, test_app

def test_register_success(test_session):
    add_user(name='Độc giả 1', username='docgia01', password='Password123!', avatar=None)
    u = NguoiDung.query.filter(NguoiDung.ten_dang_nhap =='docgia01').first()

    assert u is not None
    assert u.ten == 'Độc giả 1'

@pytest.mark.parametrize('password', [
    '12345',
    'abcdefgh',
    '12345678',
])

def test_register_invalid_password(test_session, password):
    with pytest.raises(ValueError):
        add_user(name='Lỗi MK', username='loimk123', password=password, avatar=None)

def test_existing_username(test_session):
    add_user(name='Test 1', username='trunglap', password='Password123!', avatar=None)
    with pytest.raises(ValueError):
        add_user(name='Test 2', username='trunglap', password='Password123!', avatar=None)

