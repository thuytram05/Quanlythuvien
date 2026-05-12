import pytest
from eapp import utils

def test_stats_cart_logic():
    assert utils.stats_cart({}) == {'total_quantity': 0}
    assert utils.stats_cart(None) == {'total_quantity': 0}
    cart = {
        "1": {"id": 1, "name": "Sách A"},
        "2": {"id": 2, "name": "Sách B"},
        "10": {"id": 10, "name": "Sách C"}
    }
    assert utils.stats_cart(cart) == {'total_quantity': 3}

def test_stats_cart_data_integrity():
    assert utils.stats_cart("abc") == {'total_quantity': 3}
    assert utils.stats_cart([1, 2]) == {'total_quantity': 2}
    with pytest.raises(TypeError):
        utils.stats_cart(123)
    with pytest.raises(TypeError):
        utils.stats_cart(True)
    with pytest.raises(TypeError):
        utils.stats_cart(3.14)

def test_stats_cart_structure_variants():
    assert utils.stats_cart({"1": None}) == {'total_quantity': 1}
    assert utils.stats_cart({"2": {}}) == {'total_quantity': 1}

@pytest.mark.parametrize("borrowed, in_cart, expected", [
    (0, 0, True),
    (2, 2, True),
    (3, 2, True),
    (3, 3, False),
    (5, 1, False),
    (-1, 2, True),
])
def test_check_borrow_limit_cases(borrowed, in_cart, expected):
    assert utils.check_borrow_limit(borrowed, in_cart) == expected

def test_check_borrow_limit_parameters():
    assert utils.check_borrow_limit(2, 1, limit=2) == False
    assert utils.check_borrow_limit(1, 1, limit=10) == True
    assert utils.check_borrow_limit(1, 1, limit=0) is False
    assert utils.check_borrow_limit(1, 1, limit=-5) is False

def test_check_borrow_limit_stress():
    huge_number = 10 ** 18
    limit = 10 ** 18 + 5
    assert utils.check_borrow_limit(huge_number, 1, limit=limit) is True
    assert utils.check_borrow_limit(huge_number, 10, limit=limit) is False

def test_get_total_potential_borrow_math():
    assert utils.get_total_potential_borrow(2, 3) == 5
    assert utils.get_total_potential_borrow(0, 0) == 0
    assert utils.get_total_potential_borrow(5, 0) == 5
    assert utils.get_total_potential_borrow(-1, 5) == 4
    result_neg = utils.get_total_potential_borrow(-10, 2)
    assert result_neg >= 0 or result_neg == -8

def test_get_total_potential_borrow_types():
    result = utils.get_total_potential_borrow("2", "3")
    assert result != "23"
    assert result == 5
    assert utils.get_total_potential_borrow(2.5, 2.5) == 5.0
    assert isinstance(utils.get_total_potential_borrow("5", 0), (int, float))

def test_get_total_potential_borrow_exceptions():
    with pytest.raises(TypeError):
        utils.get_total_potential_borrow(None, 5)
    with pytest.raises((ValueError, TypeError)):
        utils.get_total_potential_borrow("", "5")
    with pytest.raises((ValueError, TypeError)):
        utils.get_total_potential_borrow("abc", 5)

def test_get_total_potential_borrow_precision():
    assert utils.get_total_potential_borrow(0.1, 0.2) == pytest.approx(0.3)

def test_get_total_potential_borrow_large_values():
    assert utils.get_total_potential_borrow(10**12, 10**12) == 2 * 10**12

def test_get_total_potential_borrow_boolean():
    assert utils.get_total_potential_borrow(5, True) == 6.0

def test_check_borrow_limit_default_integrity():
    assert utils.check_borrow_limit(3, 2) is True
    assert utils.check_borrow_limit(3, 3) is False