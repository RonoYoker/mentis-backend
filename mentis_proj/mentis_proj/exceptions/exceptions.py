class UnauthorizedException(Exception):
    pass

class ValidationFailedException(Exception):
    def __init__(self, **kwargs):
        self.method_name = kwargs.get("method_name")
        self.error = kwargs.get("error")
        self.reason = kwargs.get("reason")
        self.data = kwargs.get("data")

class BadRequestException(Exception):
    def __init__(self, **kwargs):
        self.method_name = kwargs.get("method_name")
        self.error = kwargs.get("error")
        self.reason = kwargs.get("reason")

class NotFoundException(Exception):
    def __init__(self, **kwargs):
        self.method_name = kwargs.get("method_name")
        self.error = kwargs.get("error")
        self.reason = kwargs.get("reason")

class InternalServerError(Exception):
    def __init__(self, **kwargs):
        self.method_name = kwargs.get("method_name")
        self.error = kwargs.get("error")
        self.reason = kwargs.get("reason")

