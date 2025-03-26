import pytest
import sys
import os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Grocery.ScannedLineItem import ScannedLineItem

def test_process_receipt():
    '''test minimum constructor argumenbts'''
    p = ScannedLineItem("BUTTER CHICKEN W/BASMATI", 2, 8.98)
    
    assert p.line_item == "BUTTER CHICKEN W/BASMATI"
    assert p.count == 2
    assert p.total_price == 8.98
    assert p.price_per_count == 4.49
    assert p.store_name == None
    assert p.id == None
    assert p.store_product_name == None
    assert p.generic_matches == None
    assert p.generic_id == None

def test_no_count():
    '''test count set to None'''
    error_raised = False

    try:
        p = ScannedLineItem("BUTTER CHICKEN W/BASMATI", None, 8.98)
    except TypeError:
        error_raised = True
    
    assert error_raised

def test_no_price():
    '''test count set to None'''
    error_raised = False

    try:
        p = ScannedLineItem("BUTTER CHICKEN W/BASMATI", 2, None)
    except TypeError:
        error_raised = True
    
    assert error_raised

# def test_illegal_count():
#     '''negative count'''
#     error_raised = False

#     try:
#         p = StoreProduct("BUTTER CHICKEN W/BASMATI", -2, 8.98)
#     except ValueError:
#         error_raised = True
    
#     assert error_raised

# def test_illegal_price():
#     '''negative price'''
#     error_raised = False

#     try:
#         p = StoreProduct("BUTTER CHICKEN W/BASMATI", 2, -8.98)
#     except ValueError:
#         error_raised = True
    
#     assert error_raised