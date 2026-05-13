import pytest
import time
from selenium.webdriver.common.by import By
from eapp.test.pages.HomePage import HomePage

pytest_plugins = ["eapp.test.test_base"]

def test_sel_search_by_book_name_success(driver, sample_data):
    home_page = HomePage(driver)
    home_page.open_page()

    home_page.search_book("Clean Code")
    time.sleep(2)

    source_lower = driver.page_source.lower()
    assert "kw=clean" in driver.current_url.lower()
    assert "clean code" in source_lower

def test_sel_search_by_author_success(driver, sample_data):
    home_page = HomePage(driver)
    home_page.open_page()

    home_page.search_book("Eric Matthes")
    time.sleep(2)

    source_lower = driver.page_source.lower()
    assert "python crash course" in source_lower
    assert "eric matthes" in source_lower

def test_sel_search_no_results(driver):
    home_page = HomePage(driver)
    home_page.open_page()

    keyword = "CuonSachNayKhongTheTonTai123"
    home_page.search_book(keyword)

    book_cards = driver.find_elements(By.CSS_SELECTOR, '.book-card-pages')

    assert len(book_cards) == 0

def test_sel_search_constraint_minlength(driver):
    home_page = HomePage(driver)
    home_page.open_page()

    search_input = driver.find_element(By.NAME, 'kw')
    search_btn = driver.find_element(By.CSS_SELECTOR, '.search-box button')

    search_input.clear()
    search_input.send_keys("A")

    driver.execute_script("arguments[0].click();", search_btn)
    time.sleep(1)

    validation_msg = driver.execute_script("return arguments[0].validationMessage;", search_input)

    assert "kw=A" not in driver.current_url

    assert "2" in validation_msg or "ít nhất" in validation_msg.lower()

def test_sel_filter_by_category(driver):
    home_page = HomePage(driver)
    home_page.open_page()

    category_select = driver.find_element(By.NAME, 'category_id')

    option_cntt = category_select.find_element(By.CSS_SELECTOR, 'option[value="1"]')
    option_cntt.click()
    time.sleep(2)
    assert "category_id=1" in driver.current_url