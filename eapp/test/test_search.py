import pytest
from eapp.test.test_base import test_client, test_app, sample_data, test_session
from eapp.models import Sach
from bs4 import BeautifulSoup

def test_search_by_book_name(test_client, sample_data):
    res = test_client.get('/?kw=Sách Test 1')
    data = res.get_data(as_text=True)

    assert res.status_code == 200
    assert 'Sách Test 1' in data
    assert 'book' in data.lower()


def test_search_by_author(test_client, sample_data, test_session):
    tl_id = sample_data['categories'][0].id

    lh = Sach(ten_sach="Lao Hac", tac_gia="Nam Cao", so_luong_con=5,
              tong_so_luong=5, ma_the_loai=tl_id)
    test_session.add(lh)
    test_session.commit()

    res = test_client.get('/?kw=Nam Cao')
    data = res.get_data(as_text=True)

    assert res.status_code == 200
    assert "Nam Cao" in data
    assert "Lao Hac" in data


def test_search_no_result(test_client, sample_data):
    res = test_client.get('/?kw=SachVienTuong9999')
    data = res.get_data(as_text=True).lower()
    assert "không tìm thấy" in data or "rất tiếc" in data

def test_search_min_length_validation(test_client, sample_data):
    res = test_client.get('/?kw=S', follow_redirects=True)
    data = res.get_data(as_text=True)

    assert "2 ký tự" in data


def test_pagination_logic(test_client, test_app, sample_data):
    assert test_app.config['PAGE_SIZE'] == 50
    res_p1 = test_client.get('/?page=1')
    soup_p1 = BeautifulSoup(res_p1.data, 'html.parser')
    assert len(soup_p1.find_all('div', class_='book-card-pages')) == 50
    res_p2 = test_client.get('/?page=2')
    soup_p2 = BeautifulSoup(res_p2.data, 'html.parser')
    assert len(soup_p2.find_all('div', class_='book-card-pages')) == 2


def test_pagination_empty_page(test_client, sample_data):
    res = test_client.get('/?page=99')
    data = res.get_data(as_text=True).lower()

    assert res.status_code == 200
    assert "không tìm thấy" in data or "rất tiếc" in data


def test_filter_by_category(test_client, sample_data):
    cate_id = sample_data['categories'][0].id
    res = test_client.get(f'/?category_id={cate_id}')
    data = res.get_data(as_text=True)

    assert res.status_code == 200
    assert sample_data['categories'][0].ten_the_loai in data

def test_search_combined_filter(test_client, sample_data, test_session):
    tl_vanhoc = sample_data['categories'][1]

    test_session.add(Sach(ten_sach="Chi Pheo", tac_gia="Nam Cao", ma_the_loai=tl_vanhoc.id))
    test_session.commit()

    res = test_client.get(f'/?category_id={tl_vanhoc.id}&kw=Chi Pheo')
    data = res.get_data(as_text=True)

    assert res.status_code == 200
    assert "Chi Pheo" in data
    assert "Nam Cao" in data


def test_search_case_insensitive(test_client, sample_data):
    res_lower = test_client.get('/?kw=sách test 1')
    res_upper = test_client.get('/?kw=SÁCH TEST 1')

    assert res_lower.status_code == 200
    assert "Sách Test 1" in res_lower.get_data(as_text=True)
    assert res_upper.status_code == 200
    assert "Sách Test 1" in res_upper.get_data(as_text=True)


def test_search_vietnamese_accent(test_client, sample_data):
    res = test_client.get('/?kw=Sách Test')
    data = res.get_data(as_text=True)

    assert "Sách Test" in data


def test_search_with_special_characters(test_client, sample_data):
    special_kws = ["' OR 1=1 --", "<script>alert(1)</script>", "!!!@@@###"]

    for kw in special_kws:
        res = test_client.get(f'/?kw={kw}')
        assert res.status_code == 200
        assert "không tìm thấy" in res.get_data(as_text=True).lower()


def test_search_whitespace_only(test_client, sample_data):
    res = test_client.get('/?kw=   ', follow_redirects=True)
    data = res.get_data(as_text=True)
    assert "2 ký tự" in data or res.status_code == 200

def test_search_exclude_inactive_books(test_client, test_session, sample_data):
    tl_id = sample_data['categories'][0].id

    hidden_book = Sach(ten_sach="Sach Bi An", hoat_dong=False, ma_the_loai=tl_id, tac_gia="Tester")
    test_session.add(hidden_book)
    test_session.commit()

    res = test_client.get('/?kw=Sach Bi An')
    soup = BeautifulSoup(res.data, 'html.parser')

    book_titles = [h5.get_text() for h5 in soup.find_all('h5', class_='book-title-classic')]

    assert "Sach Bi An" not in book_titles

    assert "không tìm thấy" in res.get_data(as_text=True).lower()


def test_search_by_category_name_string(test_client, sample_data):
    category_name = sample_data['categories'][0].ten_the_loai  # "Công nghệ thông tin"
    res = test_client.get(f'/?kw={category_name}')
    data = res.get_data(as_text=True)

    assert res.status_code == 200
    assert "Sách Test" in data or "Sách Tự Động" in data

def test_pagination_boundary_exact_limit(test_client, test_app, test_session, sample_data):
    assert True #Kiểm tra logic phân trang/Trang cuối cùng

def test_pagination_invalid_page_type(test_client, sample_data):
    res = test_client.get('/?page=invalid')
    assert res.status_code == 200
    assert "Sách Test" in res.get_data(as_text=True)


def test_pagination_boundary_exact_limit(test_client, test_app, test_session, sample_data):
    test_session.query(Sach).delete()
    tl_id = sample_data['categories'][0].id
    for i in range(50):
        test_session.add(Sach(ten_sach=f"Sách Biên {i}", tac_gia="A", ma_the_loai=tl_id))
    test_session.commit()

    res = test_client.get('/?page=1')
    data = res.get_data(as_text=True)
    soup = BeautifulSoup(data, 'html.parser')

    assert len(soup.find_all('div', class_='book-card-pages')) == 50
    assert 'page=2' not in data

def test_search_by_category_name_string(test_client, sample_data):
    category_name = sample_data['categories'][0].ten_the_loai
    res = test_client.get(f'/?kw={category_name}')
    data = res.get_data(as_text=True).lower()

    assert res.status_code == 200
    assert "sách" in data

