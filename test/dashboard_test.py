import copy
import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timedelta
from Dashboard.DashboardManager import DashboardManager
from Dashboard.Dashboard import Dashboard  
from Grocery.ScannedReceipt import ScannedReceipt
from Grocery.ScannedLineItem import ScannedLineItem

@pytest.fixture
def manager():
    return DashboardManager()

def make_dashboard(dashboard_attributes):
    dashboard_attributes = copy.deepcopy(dashboard_attributes)
    return Dashboard(
        user_id=dashboard_attributes[0],
        weekly_spending=dashboard_attributes[1],
        monthly_spending=dashboard_attributes[2],
        yearly_spending=dashboard_attributes[3],
        average_grocery_run_cost=dashboard_attributes[4],
        total_runs=dashboard_attributes[5],
        most_expensive_item=dashboard_attributes[6],
        favorite_items=dashboard_attributes[7],
        current_month_item_frequency=dashboard_attributes[8]
    )

# update weekly spending tests
def test_add_new_week(manager):
    dashboard = make_dashboard(DASHBOARD_EMPTY)
    manager._DashboardManager__update_weekly_spending(dashboard, RECEIPT_DATE_1, RECEIPT_TOTAL_1)

    assert dashboard.weekly_spending == {
        WEEK_START_1: RECEIPT_TOTAL_1,
    }

def test_update_existing_week(manager):
    dashboard = make_dashboard(DASHBOARD_1)
    manager._DashboardManager__update_weekly_spending(dashboard, RECEIPT_DATE_1, RECEIPT_TOTAL_3)

    assert dashboard.weekly_spending == {
        WEEK_START_1: WEEK_1_CURRENT_TOTAL + RECEIPT_TOTAL_3,
        WEEK_START_2: WEEK_2_CURRENT_TOTAL
    }

def test_receipt_on_week_start(manager):
    dashboard = make_dashboard(DASHBOARD_1)

    manager._DashboardManager__update_weekly_spending(dashboard, RECEIPT_DATE_2, RECEIPT_TOTAL_2)

    assert dashboard.weekly_spending == {
        WEEK_START_1: WEEK_1_CURRENT_TOTAL,
        WEEK_START_2: WEEK_2_CURRENT_TOTAL + RECEIPT_TOTAL_2
    }

# update monthly spending tests
def test_add_new_month(manager):
    dashboard = make_dashboard(DASHBOARD_EMPTY)
    manager._DashboardManager__update_monthly_spending(dashboard, RECEIPT_DATE_1, MONTH_TOTAL_1)

    assert dashboard.monthly_spending == {
        MONTH_START_1: MONTH_TOTAL_1
    }

def test_update_existing_month(manager):
    dashboard = make_dashboard(DASHBOARD_1)
    manager._DashboardManager__update_monthly_spending(dashboard, RECEIPT_DATE_1, MONTH_TOTAL_2)

    assert dashboard.monthly_spending == {
        MONTH_START_1: MONTH_1_CURRENT_TOTAL + MONTH_TOTAL_2
    }

def test_receipt_on_same_month(manager):
    dashboard = make_dashboard(DASHBOARD_1)
    manager._DashboardManager__update_monthly_spending(dashboard, RECEIPT_DATE_2, MONTH_TOTAL_2)

    assert dashboard.monthly_spending == {
        MONTH_START_1: MONTH_1_CURRENT_TOTAL + MONTH_TOTAL_2
    }

# test yearly spending
def test_add_new_year(manager):
    dashboard = make_dashboard(DASHBOARD_EMPTY)
    manager._DashboardManager__update_yearly_spending(dashboard, RECEIPT_DATE_1, YEAR_TOTAL_1)

    assert dashboard.yearly_spending == {
        YEAR_START_1: YEAR_TOTAL_1
    }

def test_update_existing_year(manager):
    dashboard = make_dashboard(DASHBOARD_1)
    manager._DashboardManager__update_yearly_spending(dashboard, RECEIPT_DATE_1, YEAR_TOTAL_2)

    assert dashboard.yearly_spending == {
        YEAR_START_1: YEAR_TOTAL_1 + YEAR_TOTAL_2
    }

def test_receipt_on_same_year(manager):
    dashboard = make_dashboard(DASHBOARD_1)
    manager._DashboardManager__update_yearly_spending(dashboard, RECEIPT_DATE_2, YEAR_TOTAL_2)

    assert dashboard.yearly_spending == {
        YEAR_START_1: YEAR_TOTAL_1 + YEAR_TOTAL_2
    }

# test update average grocery run
def test_update_average_grocery_run_cost(manager):
    dashboard = make_dashboard(DASHBOARD_EMPTY)

    for item in SCANNED_RECEIPT_1.scanned_line_items:
        item.generic_id = "item_1"

    manager._DashboardManager__update_average_grocery_run_cost(dashboard, SCANNED_RECEIPT_1)

    assert dashboard.average_grocery_run_cost == 30
    assert dashboard.total_runs == 1

    for item in SCANNED_RECEIPT_2.scanned_line_items:
        item.generic_id = "item_2"

    manager._DashboardManager__update_average_grocery_run_cost(dashboard, SCANNED_RECEIPT_2)

    assert dashboard.average_grocery_run_cost == 37.5
    assert dashboard.total_runs == 2

# test update favorite item
def test_update_favorite_item(manager):
    dashboard = make_dashboard(DASHBOARD_1)

    for item in SCANNED_RECEIPT_1.scanned_line_items:
        item.generic_id = "item_1"
    
    manager._DashboardManager__update_favorite_item_of_the_month(dashboard, SCANNED_RECEIPT_1)

    assert dashboard.favorite_items == [{
        "date": MONTH_START_1,
        "name": "item_1",
        "frequency": 1
    }]

    for item in SCANNED_RECEIPT_2.scanned_line_items:
        item.generic_id = "item_2"

    manager._DashboardManager__update_favorite_item_of_the_month(dashboard, SCANNED_RECEIPT_2)

    assert dashboard.favorite_items == [{
        "date": MONTH_START_1,
        "name": "item_1",
        "frequency": 1
    }]

    for item in SCANNED_RECEIPT_3.scanned_line_items:
        item.generic_id = "item_2"

    manager._DashboardManager__update_favorite_item_of_the_month(dashboard, SCANNED_RECEIPT_3)

    assert dashboard.favorite_items == [{
        "date": MONTH_START_1,
        "name": "item_2",
        "frequency": 2
    }]

# test update most expensive item
def test_update_most_expensive_item(manager):
    dashboard = make_dashboard(DASHBOARD_EMPTY)

    for item in SCANNED_RECEIPT_1.scanned_line_items:
        item.generic_id = "item_1"

    manager._DashboardManager__update_most_expensive_item(dashboard, SCANNED_RECEIPT_1)
    
    assert dashboard.most_expensive_item == {
        "name": "item_1",
        "price": 30.00,
        "date": MONTH_START_1
    }

    for item in SCANNED_RECEIPT_2.scanned_line_items:
        item.generic_id = "item_2"

    manager._DashboardManager__update_most_expensive_item(dashboard, SCANNED_RECEIPT_2)
    
    assert dashboard.most_expensive_item == {
        "name": "item_1",
        "price": 30.00,
        "date": MONTH_START_1
    }

    for item in SCANNED_RECEIPT_3.scanned_line_items:
        item.generic_id = "item_2"

    manager._DashboardManager__update_most_expensive_item(dashboard, SCANNED_RECEIPT_3)
    
    assert dashboard.most_expensive_item == {
        "name": "item_2",
        "price": 45.00,
        "date": MONTH_START_1
    }

# test update dashboard
def test_update_dashboard_with_valid_receipt(manager):
    item1 = ScannedLineItem("Bananas", 2, 1.00, store_name="Trader Joe's", store_product_name="Organic Bananas")
    item2 = ScannedLineItem("Apples", 3, 3.00, store_name="Trader Joe's", store_product_name="Honeycrisp Apples")
    item1.generic_id = "Bananas"
    item2.generic_id = "Apples"
    receipt = ScannedReceipt("Trader Joe's", "2025-04-01", "123 Market St", 7.00, [item1, item2, item2])
    dashboard = make_dashboard(DASHBOARD_EMPTY)

    manager.update_dashboard(dashboard, receipt)

    # weekly_spending
    receipt_date = datetime.strptime(receipt.date, '%Y-%m-%d').date()
    start_of_week = receipt_date - timedelta(days=receipt_date.weekday())
    start_of_week_key = start_of_week.isoformat()
    weekly_spending = dashboard.weekly_spending
    assert weekly_spending[start_of_week_key] == 7.00

    # monthly_spending
    receipt_date = datetime.strptime(receipt.date, "%Y-%m-%d").date()
    month_key = receipt_date.strftime("%Y-%m")
    monthly_spending = dashboard.monthly_spending
    assert monthly_spending[month_key] == 7.00

    # yearly_spending
    receipt_date = datetime.strptime(receipt.date, "%Y-%m-%d").date()
    year_key = str(receipt_date.year)
    yearly_spending = dashboard.yearly_spending
    assert yearly_spending[year_key] == 7.00

    # average_grocery_run_cost
    assert dashboard.average_grocery_run_cost == 7.00

    # total_runs
    assert dashboard.total_runs == 1

    # most_expensive_item
    most_expensive_item = dashboard.most_expensive_item
    assert most_expensive_item["name"] == "Apples"
    
    # favorite_items
    favorite_items = dashboard.favorite_items
    assert favorite_items[0]["name"] == "Apples"

    # current_month_item_frequency
    freq = dashboard.current_month_item_frequency
    assert "Bananas" in freq
    assert freq["Bananas"] == 1
    assert "Apples" in freq
    assert freq["Apples"] == 2

# attribute constants
# relative dates
TODAY = datetime.today()
RECEIPT_DATE_1_DT = TODAY.replace(day=8)
RECEIPT_DATE_2_DT = TODAY.replace(day=15)
WEEK_START_2_DT = RECEIPT_DATE_2_DT - timedelta(days=RECEIPT_DATE_2_DT.weekday())
RECEIPT_DATE_3_DT = WEEK_START_2_DT + timedelta(days=2)
RECEIPT_DATE_4_DT = TODAY.replace(month=(TODAY.month - 1))
WEEK_START_1_DT = RECEIPT_DATE_1_DT - timedelta(days=RECEIPT_DATE_1_DT.weekday())
MONTH_START_1 = TODAY.strftime("%Y-%m")
YEAR_START_1 = TODAY.strftime("%Y")

RECEIPT_DATE_1 = RECEIPT_DATE_1_DT.strftime("%Y-%m-%d")
RECEIPT_DATE_2 = RECEIPT_DATE_2_DT.strftime("%Y-%m-%d")
RECEIPT_DATE_3 = RECEIPT_DATE_3_DT.strftime("%Y-%m-%d")
RECEIPT_DATE_4 = RECEIPT_DATE_4_DT.strftime("%Y-%m-%d")
WEEK_START_1 = WEEK_START_1_DT.strftime("%Y-%m-%d")
WEEK_START_2 = WEEK_START_2_DT.strftime("%Y-%m-%d")

RECEIPT_TOTAL_1 = 15.75
RECEIPT_TOTAL_2 = 12.50
RECEIPT_TOTAL_3 = 5.00
MONTH_TOTAL_1 = 50.00
MONTH_TOTAL_2 = 20.00
YEAR_TOTAL_1 = 100.00
YEAR_TOTAL_2 = 200.00

WEEK_1_CURRENT_TOTAL = 25.00
WEEK_1_SMALLER_TOTAL = 10.00
WEEK_2_CURRENT_TOTAL = 20.00

MONTH_1_CURRENT_TOTAL = 100.00

TOTAL_RECEIPT_PRICE_1 = 30.00
TOTAL_RECEIPT_PRICE_2 = 45.00
TOTAL_RECEIPT_PRICE_3 = 90.00

# dashboard constants
DASHBOARD_EMPTY = [
    "test-user",
    {},    # weekly_spending
    {},    # monthly_spending
    {},    # yearly_spending
    0,     # average_grocery_run_cost
    0,     # total_runs
    {},    # most_expensive_item
    [],    # favorite_items
    {}     # current_month_item_frequency
]

DASHBOARD_1 = [
    "test-user",                                       
    {WEEK_START_1: WEEK_1_CURRENT_TOTAL, WEEK_START_2: WEEK_2_CURRENT_TOTAL},
    {MONTH_START_1: MONTH_1_CURRENT_TOTAL},
    {YEAR_START_1: YEAR_TOTAL_1},
    25,
    1,
    {},
    [],
    {}
]

# receipt constants
SCANNED_RECEIPT_1 = ScannedReceipt(
    scanned_line_items= [
        ScannedLineItem(line_item = "", count= 1, total_price= 30.00)
    ],
    date= RECEIPT_DATE_2,
    total_receipt_price= TOTAL_RECEIPT_PRICE_1
)

SCANNED_RECEIPT_2 = ScannedReceipt(
    scanned_line_items= [
        ScannedLineItem(line_item = "", count= 1, total_price= 45.00)
    ],
    date= RECEIPT_DATE_4,
    total_receipt_price= TOTAL_RECEIPT_PRICE_2
)

SCANNED_RECEIPT_3 = ScannedReceipt(
    scanned_line_items= [
        ScannedLineItem(line_item = "", count= 1, total_price= 45.00),
        ScannedLineItem(line_item = "", count= 1, total_price= 45.00)
    ],
    date= RECEIPT_DATE_2,
    total_receipt_price= TOTAL_RECEIPT_PRICE_3
)