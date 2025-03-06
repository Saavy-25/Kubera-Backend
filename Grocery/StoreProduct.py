class StoreProduct:
    def __init__(self, line_item="", count="", unit="", unit_price="", total_price="") -> None:
        self.pk = "None" # store#name#id(or UPC)
        self.generic_pk = "None"
        # self.date = date -- REMOVING THIS ATTRIBUTE, SHOULD BE STORED AT RECEIPT LEVEL AND REFERENCED ONLY WHEN ENTERING IN DB
        self.line_item = line_item #abbreviation not decoded
        self.count = count # count purchaced
        self.unit = unit # unit of measurement
        self.unit_price = unit_price # price for an individual unit
        self.total_price = total_price # total price for line item
        
        self.generic_matches = []
        self.product_name = "None" #determined by aberviation expansion service
        self.generic_name = "None" #should be verified by user before filled in

    def print(self) -> None:
        '''print attributes of object'''
        print("Line Item: ", self.line_item)
        print("Product Name (determined by abreviation expansion service): ", self.product_name)
        print("Unit of measurment: ", self.unit)
        print("Count: ", self.count)
        print("Price for a single unit: ", self.unit_price)
        print("Price for line item: ", self.total_price)
        print("Generic matching from ML service: ", self.generic_matches)
        print("Generic Name (verified/selected by user): ", self.generic_name)
