class ClientErrorMessage():
    '''standard error class for flutter responses'''

    def __init__(self, message, detail):
        self.message = message # user readable message, may be propogated to UI
        self.detail = detail # developer message
        
    def flutter_response(self):
        '''return dictionary formatted for json'''
        return {
            "message": self.message,
            "detail": self.detail
        }
