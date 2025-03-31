import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from FlutterService.flutter_routes import update_recent_prices

def test_report_new_price():
    recent_prices = [{"price": 5.45, "reportCount": 1, "lastReportDate": "2025-01-01"}]
    updated_prices = update_recent_prices(6.45, "2025-01-02", recent_prices)

    assert len(updated_prices) == 2
    assert updated_prices[0]["price"] == 6.45

def test_report_old_price():
    recent_prices = [{"price": 5.45, "reportCount": 1, "lastReportDate": "2025-01-01"}]
    updated_prices = update_recent_prices(6.45, "2024-12-25", recent_prices)

    assert len(updated_prices) == 2
    assert updated_prices[0]["price"] == 5.45

def test_report_existing_price():
    recent_prices = [{"price": 5.45, "reportCount": 1, "lastReportDate": "2025-01-01"}]
    updated_prices = update_recent_prices(5.45, "2025-01-02", recent_prices)

    assert len(updated_prices) == 1
    assert updated_prices[0]["reportCount"] == 2
    assert updated_prices[0]["lastReportDate"] == "2025-01-02"

def test_report_price_drop():
    recent_prices = [{'price': 5.45, 'reportCount': 3, 'lastReportDate': '2025-01-09'}, 
                     {'price': 5.2, 'reportCount': 2, 'lastReportDate': '2025-01-05'}]
    updated_prices = update_recent_prices(5.2, '2025-01-10', recent_prices)

    assert len(updated_prices) == 3
    assert updated_prices[0]['price'] == 5.2
    assert updated_prices[0]['reportCount'] == 1
    assert updated_prices[0]['lastReportDate'] == '2025-01-10'

def test_report_more_than_10():
    recent_prices = [{'price': 5.45, 'reportCount': 3, 'lastReportDate': '2025-01-10'}, 
                     {'price': 5.44, 'reportCount': 2, 'lastReportDate': '2025-01-09'},
                     {'price': 5.43, 'reportCount': 2, 'lastReportDate': '2025-01-08'},
                     {'price': 5.42, 'reportCount': 2, 'lastReportDate': '2025-01-07'},
                     {'price': 5.41, 'reportCount': 2, 'lastReportDate': '2025-01-06'},
                     {'price': 5.40, 'reportCount': 2, 'lastReportDate': '2025-01-05'},
                     {'price': 5.39, 'reportCount': 2, 'lastReportDate': '2025-01-04'},
                     {'price': 5.38, 'reportCount': 2, 'lastReportDate': '2025-01-03'},
                     {'price': 5.37, 'reportCount': 2, 'lastReportDate': '2025-01-02'},
                     {'price': 5.36, 'reportCount': 2, 'lastReportDate': '2025-01-01'}]
    updated_prices = update_recent_prices(5.46, "2025-01-11", recent_prices)

    assert len(updated_prices) == 10
    assert updated_prices[0]['price'] == 5.46
    assert updated_prices[0]['lastReportDate'] == '2025-01-11'


def run_all_tests():
    test_report_new_price()
    test_report_old_price()
    test_report_existing_price()
    test_report_price_drop()
    test_report_more_than_10()
    print("All tests passed!")

if __name__ == "__main__":
    run_all_tests()