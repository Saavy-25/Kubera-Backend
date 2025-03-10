class Receipt:

    def __init__(self, store_name="", date="", store_address="", total_receipt_price=0, products=None) -> None:
        self.store_name = store_name
        self.store_address = store_address
        self.date = date
        self.total_receipt_price = total_receipt_price
        self.products = products #list of product objects

    def print(self) -> None:
        '''print info stores in model'''
        print("Store Name: ", self.store_name)
        print("Date: ", self.date)
        print("Address: ", self.store_address)
        print("Total Receipt Price: ", self.total_receipt_price)
        print("Products: ")

        for item_number, product in enumerate(self.products):
            print("----------Product ", item_number + 1, "----------")
            product.print()

    def get_map(self):
         '''convert model to map for use in jsonify() when getting receipt scan confirmation'''
         return{
            "store_name": self.store_name,
            "store_address": dict(self.store_address),
            "date": self.date,
            "total_receipt_price": self.total_receipt_price,
            "products": [product.__dict__ for product in self.products]
        }
    
    def get_mongo_entry(self):
        '''convert model to map for use in mongo'''
        return{
            "storeName": self.store_name,
            "storeAddress": self.store_address,
            "date": self.date, 
            "totalReceiptPrice": self.date, 
            "lineItems": [product.mongo_receipt_entry() for product in self.products]
        }
