import json

class StoreProduct:
    def __init__(self, product_name="", unit="", price="", date=None):
        #attribues same as in db
        self.pk = "" # store#name#id(or UPC)
        self.unit = unit #or quantity
        self.generic_pk = ""
        
        #attributes differing from db schema
        self.price = price #list of timestamps/prices db, one value here for this object
        self.date = date
        self.product_name = product_name
        self.generic_name = ""

    def print(self):
        print("Product Name: ", self.product_name)
        print("Unit: ", self.unit)
        print("Price: ", self.price)
        print("Date: ", self.date)
        print("Generic Name: ", self.generic_name)

    # def json(self):
    #     return json.dumps(self)
    
    # def update(self, str):
    #     response = json.loads(str)
    #     self.product_id = response["product_id"]
    #     self.unit = response["unit"]
    #     self.item_id = response["item_id"]
    #     self.prices = response["prices"]
