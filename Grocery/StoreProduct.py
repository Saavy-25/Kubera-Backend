class StoreProduct:
    def __init__(self, line_item="", count=1, unit="", unit_price="", total_price="") -> None:
        self.line_item = line_item #abbreviation not decoded
        self.count = count # count purchaced
        self.unit = unit # unit of measurement
        self.unit_price = unit_price # price for an individual unit
        self.total_price = total_price # total price for line item
        
        self.id = None #_id in mongo
        self.generic_matches = None
        self.store_product_name = None #determined by aberviation expansion service
        self.generic_id = None #should be verified by user before filled in

    def print(self) -> None:
        '''print info stored in model'''
        print("Id: ", self.id)
        print("Line Item: ", self.line_item)
        print("Count: ", self.count)
        print("Unit: ", self.unit)
        print("Unit Price: ", self.unit_price)
        print("Total Price: ", self.total_price)
        print("Generic Matches: ", self.generic_matches)
        print("Store Product Name: ", self.store_product_name)
        print("Generic Id: ", self.generic_id)
        return

    def mongo_receipt_entry(self) -> dict:
        '''return object as a dictionary for use in mongo receipts collection'''
        price_per_count = round( float(self.total_price)/ self.count, 2)

        return {
            "pricePerCount": price_per_count,
            "storeProductId": self.id,
            "count": self.count
        }
