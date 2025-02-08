
class GenericItem:
    def __init__(self, generic_name, category, product_ids):
        #attributes matching db
        self.pk = "" # this should be _id#generic_name
        self.product_ids = product_ids
        self.category = category

        #fields not included in db
        self.generic_name = generic_name