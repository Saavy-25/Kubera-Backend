import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from FlutterService.flutter_routes import update_recent_prices

def asrt(updated_prices, assert_len, assert_price, assert_count, assert_date, assert_idx=0):
    if assert_idx >= len(updated_prices):
        raise IndexError
    
    assert len(updated_prices) == assert_len
    assert updated_prices[assert_idx]['price'] == assert_price
    assert updated_prices[assert_idx]['lastReportDate'] == assert_date
    assert updated_prices[assert_idx]['reportCount'] == assert_count

def test_report_new_price():
    recent_prices = [{"price": "5.45", "reportCount": 1, "lastReportDate": "2025-01-01"}]
    updated_prices = update_recent_prices("6.45", "2025-01-02", recent_prices)

    asrt(updated_prices, assert_len=2, assert_date='2025-01-02', assert_count=1, assert_price='6.45')

def test_report_old_price():
    recent_prices = [{"price": "5.45", "reportCount": 1, "lastReportDate": "2025-01-01"}]
    updated_prices = update_recent_prices("6.45", "2024-12-25", recent_prices)

    asrt(updated_prices, assert_len=2, assert_date='2025-01-01', assert_count=1, assert_price='5.45')
    asrt(updated_prices, assert_len=2, assert_date='2024-12-25', assert_count=1, assert_price='6.45', assert_idx=1)

def test_report_existing_price():
    recent_prices = [{"price": "5.45", "reportCount": 1, "lastReportDate": "2025-01-01"}]
    updated_prices = update_recent_prices("5.45", "2025-01-02", recent_prices)

    asrt(updated_prices, assert_len=1, assert_date='2025-01-02', assert_count=2, assert_price='5.45')

def test_report_price_drop():
    recent_prices = [{'price': "5.45", 'reportCount': 3, 'lastReportDate': '2025-01-09'}, 
                     {'price': "5.2", 'reportCount': 2, 'lastReportDate': '2025-01-05'}]
    updated_prices = update_recent_prices("5.2", '2025-01-10', recent_prices)

    asrt(updated_prices, assert_len=3, assert_date='2025-01-10', assert_count=1, assert_price='5.2')

def test_report_more_than_10():
    recent_prices = [{'price': "5.45", 'reportCount': 3, 'lastReportDate': '2025-01-10'}, 
                     {'price': "5.44", 'reportCount': 2, 'lastReportDate': '2025-01-09'},
                     {'price': "5.43", 'reportCount': 2, 'lastReportDate': '2025-01-08'},
                     {'price': "5.42", 'reportCount': 2, 'lastReportDate': '2025-01-07'},
                     {'price': "5.41", 'reportCount': 2, 'lastReportDate': '2025-01-06'},
                     {'price': "5.40", 'reportCount': 2, 'lastReportDate': '2025-01-05'},
                     {'price': "5.39", 'reportCount': 2, 'lastReportDate': '2025-01-04'},
                     {'price': "5.38", 'reportCount': 2, 'lastReportDate': '2025-01-03'},
                     {'price': "5.37", 'reportCount': 2, 'lastReportDate': '2025-01-02'},
                     {'price': "5.36", 'reportCount': 2, 'lastReportDate': '2025-01-01'}]
    updated_prices = update_recent_prices("5.46", "2025-01-11", recent_prices)

    asrt(updated_prices, assert_len=10, assert_date='2025-01-11', assert_count=1, assert_price='5.46')

# def test_no_squash_reports():
#     recent_prices = [{'price': "5.45", 'reportCount': 8, 'lastReportDate': '2025-01-10'}, 
#                      {'price': "5.44", 'reportCount': 7, 'lastReportDate': '2025-01-10'},
#                      {'price': "5.43", 'reportCount': 1, 'lastReportDate': '2025-01-10'}]
#     updated_prices = update_recent_prices("5.45", "2025-01-10", recent_prices)

#     assert len(updated_prices) == 3
#     assert updated_prices[0]['price'] == "5.45"
#     assert updated_prices[0]['lastReportDate'] == '2025-01-10'
#     assert updated_prices[0]['reportCount'] == 9
#     asrt(updated_prices, assert_len=3, assert_date='2025-01-10', assert_count=9, assert_price='5.45')

# def test_squash_reports():
#     recent_prices = [{'price': "5.45", 'reportCount': 3, 'lastReportDate': '2025-01-10'}, 
#                      {'price': "5.44", 'reportCount': 2, 'lastReportDate': '2025-01-10'},
#                      {'price': "5.43", 'reportCount': 1, 'lastReportDate': '2025-01-10'}]
#     updated_prices = update_recent_prices("5.45", "2025-01-10", recent_prices)

#     asrt(updated_prices, assert_len=1, assert_date='2025-01-10', assert_count=4, assert_price='5.45')

# def test_squash_reports_more_than_10():
#     recent_prices = [{'price': "5.45", 'reportCount': 1, 'lastReportDate': '2025-01-10'}, 
#                      {'price': "5.44", 'reportCount': 1, 'lastReportDate': '2025-01-10'},
#                      {'price': "5.43", 'reportCount': 1, 'lastReportDate': '2025-01-10'},
#                      {'price': "5.42", 'reportCount': 1, 'lastReportDate': '2025-01-10'},
#                      {'price': "5.41", 'reportCount': 1, 'lastReportDate': '2025-01-06'},
#                      {'price': "5.40", 'reportCount': 1, 'lastReportDate': '2025-01-05'},
#                      {'price': "5.39", 'reportCount': 1, 'lastReportDate': '2025-01-04'},
#                      {'price': "5.38", 'reportCount': 1, 'lastReportDate': '2025-01-03'},
#                      {'price': "5.37", 'reportCount': 1, 'lastReportDate': '2025-01-02'},
#                      {'price': "5.36", 'reportCount': 1, 'lastReportDate': '2025-01-01'}]
#     updated_prices = update_recent_prices("5.42", "2025-01-10", recent_prices)

#     assert len(updated_prices) == 7
#     assert updated_prices[0]['price'] == '5.42'
#     assert updated_prices[0]['lastReportDate'] == '2025-01-10'
#     assert updated_prices[0]['reportCount'] == 2

def test_new_price_report_with_same_day():
    recent_prices = [{'price': "5.45", 'reportCount': 1, 'lastReportDate': '2025-01-10'}, 
                    {'price': "5.44", 'reportCount': 1, 'lastReportDate': '2025-01-10'},
                    {'price': "5.43", 'reportCount': 1, 'lastReportDate': '2025-01-10'},
                    {'price': "5.42", 'reportCount': 1, 'lastReportDate': '2025-01-10'}]
    updated_prices = update_recent_prices("5.42", "2025-01-10", recent_prices)

    asrt(updated_prices, assert_len=4, assert_date='2025-01-10', assert_count=2, assert_price='5.42')

def test_new_price_report_with_same_day_ext():
    recent_prices = [{'price': "5.45", 'reportCount': 1, 'lastReportDate': '2025-01-12'}, 
                    {'price': "5.44", 'reportCount': 1, 'lastReportDate': '2025-01-11'},
                    {'price': "5.43", 'reportCount': 1, 'lastReportDate': '2025-01-10'},
                    {'price': "5.42", 'reportCount': 1, 'lastReportDate': '2025-01-10'},
                    {'price': "5.48", 'reportCount': 1, 'lastReportDate': '2025-01-10'}, 
                    {'price': "5.49", 'reportCount': 1, 'lastReportDate': '2025-01-10'}]
    updated_prices = update_recent_prices("5.48", "2025-01-10", recent_prices)

    asrt(updated_prices, assert_len=6, assert_date='2025-01-12', assert_count=1, assert_price='5.45')
    asrt(updated_prices, assert_len=6, assert_date='2025-01-10', assert_count=2, assert_price='5.48', assert_idx=2)

def test_new_price_report_with_same_day_giga():
    recent_prices = []
    recent_prices = update_recent_prices("5.48", "2025-01-10", recent_prices)
    asrt(recent_prices, assert_len=1, assert_date='2025-01-10', assert_count=1, assert_price='5.48')

    recent_prices = update_recent_prices("5.48", "2025-01-10", recent_prices)
    asrt(recent_prices, assert_len=1, assert_date='2025-01-10', assert_count=2, assert_price='5.48')

    recent_prices = update_recent_prices("5.49", "2025-01-10", recent_prices)
    asrt(recent_prices, assert_len=2, assert_date='2025-01-10', assert_count=1, assert_price='5.49', assert_idx=1)

    recent_prices = update_recent_prices("5.49", "2025-01-10", recent_prices)
    asrt(recent_prices, assert_len=2, assert_date='2025-01-10', assert_count=2, assert_price='5.49', assert_idx=1)

    recent_prices = update_recent_prices("5.48", "2025-01-10", recent_prices)
    asrt(recent_prices, assert_len=2, assert_date='2025-01-10', assert_count=3, assert_price='5.48')

    recent_prices = update_recent_prices("5.47", "2025-01-10", recent_prices)
    asrt(recent_prices, assert_len=3, assert_date='2025-01-10', assert_count=1, assert_price='5.47', assert_idx=2)


def run_all_tests():
    test_report_new_price()
    test_report_old_price()
    test_report_existing_price()
    test_report_price_drop()
    test_report_more_than_10()
    # test_no_squash_reports()
    # test_squash_reports()
    test_new_price_report_with_same_day()
    test_new_price_report_with_same_day_ext()
    test_new_price_report_with_same_day_giga()
    print("All tests passed!")

if __name__ == "__main__":
    run_all_tests()