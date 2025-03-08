from flask_login import UserMixin

class User(UserMixin):
    '''store infromation for currect user'''

    def __init__(self, username, password, receipt_ids=None, shopping_list_ids=None, favorite_store_ids=None):
        self.username = username
        self.password = password
        self.receipt_ids = receipt_ids if receipt_ids is not None else []
        self.shopping_list_ids = shopping_list_ids if receipt_ids is not None else []
        self.favorite_store_ids = favorite_store_ids if receipt_ids is not None else []

    def mongo_entry(self):
        '''return user object as a dictionary'''
        return {
            "username": self.username,
            "password": self.password,
            "receiptIds": self.receipt_ids,
            "shoppingListIds": self.shopping_list_ids,
            "favoriteStoreIds": self.favorite_store_ids
        }

    def get_id(self):
           return (self.username)
