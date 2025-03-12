class StoreProduct:
    def __init__(self, line_item, count, total_price, store_name=None, recent_prices=None, store_product_name=None, generic_matches=None) -> None:
        self.line_item = line_item

        try:
            self.count = int(count)
            self.total_price = float(total_price)
        except Exception:
            raise TypeError("Valid count and price required to create a store product")
        
        # if int(count) < 0:
        #         raise ValueError(str("Count must be greater or equal to 1 to create a store product"))
        # if float(total_price) <= 0.0:
        #     print(total_price)
        #     raise ValueError("Valid price required to create a store product")

        self.price_per_count = round( float(self.total_price)/ self.count, 2)

        self.store_name = store_name
        self.recent_prices = recent_prices
        self.store_product_name = store_product_name # expanded name
        self.generic_matches = generic_matches
        self.date = None
        self.id = None #_id in mongo
        self.generic_id = None

    def print(self) -> None:
        '''print info stored in model'''
        print("Id: ", self.id)
        print("Line Item: ", self.line_item)
        print("Count: ", self.count)
        print("Total Price: ", self.total_price)
        print("Generic Matches: ", self.generic_matches)
        print("Store Product Name: ", self.store_product_name)
        print("Generic Id: ", self.generic_id)
        return

    def mongo_receipt_entry(self) -> dict:
        '''return object as a dictionary for use in mongo receipts collection'''
        return {
            "pricePerCount": self.price_per_count,
            "storeProductId": self.id,
            "count": self.count
        }
    
    def first_mongo_entry(self) -> dict:
        '''return object as a dictionary for use for first insertion into mongo storeProducts collection'''
        return {
            "storeProductName": self.store_product_name,
            "storeName": self.store_name,
            "genericId": self.generic_id,
            "recentPrices": [[self.price_per_count, self.date]]
        }
    
    def get_map(self) -> dict:
        '''return object as a dictionary for use for first insertion into mongo storeProducts collection'''
        return {
            "lineItem": self.line_item,
            "count": self.count,
            "totalPrice": self.total_price,
            "pricePerCount": self.price_per_count,
            "storeName": self.store_name,
            "recentPrices": self.recent_prices,
            "storeProductName": self.store_product_name,
            "genericMatches": self.generic_matches,
            "date": self.date,
            "id": self.id,
            "genericId": self.generic_id
        }
