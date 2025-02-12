from . import StoreProduct

class Receipt:
    def __init__(self, store_name="", date="", products=[]):
        #attributes same as in db
        self.pk = "None" #generated by mongo
        self.sk = "None" # date#store
        self.store_name = store_name

        #attributes differing from db
        self.products = products #list of product objects
        self.date = date

    def print(self):
        print("Store Name: ", self.store_name)
        print("Date: ", self.date)
        print("Products: ")

        for item_number, product in enumerate(self.products):
            print("----------Product ", item_number + 1, "----------")
            product.print()