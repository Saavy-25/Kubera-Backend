from flask_login import UserMixin

class User(UserMixin):
    '''store infromation for currect user'''

    def __init__(self, username, pw, receipts, lists):
        self.username = username
        self.password = pw
        self.receipt_ids = receipts
        self.list_ids = lists
    
    def get_id(self):
           return (self.username)