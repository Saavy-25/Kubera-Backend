import json

class StoreProduct:
    def __init__(self, line_item="", unit="", price="", date=None):
        #attribues same as in db
        self.pk = "None" # store#name#id(or UPC)
        self.unit = unit #or quantity
        self.generic_pk = "None"
        
        #attributes differing from db schema
        self.price = price #list of timestamps/prices db, one value here for this object
        self.date = date
        self.line_item = line_item #abbreviation not decoded
        self.generic_matches = [] #return value from matching service
        self.product_name = "None" #determined by aberviation expansion service
        self.generic_name = "None" #should be verified by user before filled in

    def print(self):
        print("Line Item: ", self.line_item)
        print("Product Name (determined by abreviation expansion service): ", self.product_name)
        print("Unit: ", self.unit)
        print("Price: ", self.price)
        print("Date: ", self.date)
        print("Generic matching from ML service: ", self.generic_matches)
        print("Generic Name (verified/selected by user): ", self.generic_name)
