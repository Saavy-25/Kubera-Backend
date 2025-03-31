class ScannedLineItem:
    def __init__(self, line_item, count, total_price, store_name=None, recent_prices=None, store_product_name=None, generic_matches=None) -> None:

        try:
            self.count = int(count)
            self.total_price = float(total_price)
        except Exception:
            raise TypeError("Valid count and price required to create a store product")

        self.date = None
        self.generic_id = None
        self.generic_matches = generic_matches
        self.id = None #_id in mongo
        self.line_item = line_item
        self.price_per_count = round( float(self.total_price)/ self.count, 2)
        self.store_name = store_name
        self.store_product_name = store_product_name # expanded name

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
            "recentPrices": [
                {
                    "price": self.price_per_count,
                    "reportCount": 1,
                    "lastReportDate": self.date
                }
            ]
        }
    
    def flutter_response(self) -> dict:
        '''return object as a dictionary for use for first insertion into mongo storeProducts collection'''
        return {
            "count": self.count,
            "genericMatches": self.generic_matches,
            "lineItem": self.line_item,
            "pricePerCount": self.price_per_count,
            "storeProductName": self.store_product_name,
            "totalPrice": self.total_price,
        }
