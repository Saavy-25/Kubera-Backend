class StoreProduct:
    def __init__(self, line_item, count, total_price, store_name=None, recent_prices=None, _id=None, store_product_name=None, generic_matches=None, generic_id=None) -> None:
        self.line_item = line_item
        self.count = count
        self.total_price = total_price

        if not isinstance(count, int) or not isinstance(total_price, float):
            raise ValueError("Count must be an integer. Total price must be a float.")
        if count < 0:
            raise ValueError(str("Count must be greater or equal to 1 to create a store product"))
        if total_price < 0.0:
            raise ValueError("Valid price required to create a store product")

        self.price_per_count = round( float(self.total_price)/ self.count, 2)

        self.store_name = store_name
        self.recent_prices = recent_prices
        self.id = _id #_id in mongo
        self.store_product_name = store_product_name # expanded name
        self.generic_matches = generic_matches
        self.generic_id = generic_id

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
