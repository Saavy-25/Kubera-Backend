import json

class StoreProduct:
    def __init__(self, product_name="", unit="", price="", date=None):
        #attribues same as in db
        self.pk = "None" # store#name#id(or UPC)
        self.unit = unit #or quantity
        self.generic_pk = "None"
        
        #attributes differing from db schema
        self.price = price #list of timestamps/prices db, one value here for this object
        self.date = date
        self.product_name = product_name
        self.generic_name = "None"

    def print(self):
        print("Product Name: ", self.product_name)
        print("Unit: ", self.unit)
        print("Price: ", self.price)
        print("Date: ", self.date)
        print("Generic Name: ", self.generic_name)
