import pytest
from eapp import utils

# --- NHÓM 1: KIỂM THỬ stats_cart (Thống kê giỏ hàng) ---

def test_stats_cart_empty():
    """Kiểm tra giỏ hàng trống"""
    assert utils.stats_cart({}) == {'total_quantity': 0}
    assert utils.stats_cart(None) == {'total_quantity': 0}

def test_stats_cart_with_items():
    """Kiểm tra đếm số lượng item trong giỏ hàng"""
    cart = {
        "1": {"id": 1, "name": "Sách A"},
        "2": {"id": 2, "name": "Sách B"},
        "10": {"id": 10, "name": "Sách C"}
    }
    # Hàm len(cart) sẽ đếm số lượng key (đầu sách) trong dict
    assert utils.stats_cart(cart) == {'total_quantity': 3}


# --- NHÓM 2: KIỂM THỬ check_borrow_limit (Hạn mức mượn) ---

@pytest.mark.parametrize("borrowed, in_cart, expected", [
    (0, 0, True),   # Không mượn gì -> True
    (2, 2, True),   # Tổng 4 < 5 -> True
    (3, 2, True),   # Tổng 5 == 5 -> True (Biên trên)
    (3, 3, False),  # Tổng 6 > 5 -> False
    (5, 1, False),  # Đã mượn đủ 5 cuốn -> False
])
def test_check_borrow_limit_default(borrowed, in_cart, expected):
    """Kiểm tra hạn mức mượn mặc định (limit=5)"""
    assert utils.check_borrow_limit(borrowed, in_cart) == expected

def test_check_borrow_limit_custom():
    """Kiểm tra với hạn mức tùy chỉnh"""
    # Đang mượn 2, thêm 1, hạn mức chỉ cho 2 cuốn
    assert utils.check_borrow_limit(2, 1, limit=2) == False
    # Đang mượn 1, thêm 1, hạn mức cho 10 cuốn
    assert utils.check_borrow_limit(1, 1, limit=10) == True


# --- NHÓM 3: KIỂM THỬ get_total_potential_borrow (Tính tổng dự kiến) ---

def test_get_total_potential_borrow():
    """Kiểm tra phép cộng tổng số lượng sách"""
    assert utils.get_total_potential_borrow(2, 3) == 5
    assert utils.get_total_potential_borrow(0, 0) == 0
    assert utils.get_total_potential_borrow(5, 0) == 5

def test_check_borrow_limit_negative():
    """Trường hợp hy hữu: Số lượng truyền vào bị âm"""
    # Về lý thuyết không xảy ra, nhưng hàm nên xử lý an toàn
    assert utils.check_borrow_limit(-1, 2) == True
    assert utils.get_total_potential_borrow(-1, 5) == 4