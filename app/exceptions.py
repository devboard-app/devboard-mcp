##AUTH
class MissingTokenException(Exception):
    pass


class UnauthorizedException(Exception):
    pass


class ForbiddenException(Exception):
    pass


##WORK SERVICE
class NotFoundException(Exception):
    pass


class InvalidRequestException(Exception):
    pass


class ServiceUnavailableException(Exception):
    pass


##LOGIN
class LoginFailedException(Exception):
    pass


class RefreshRejectedException(Exception):
    pass


##OTHER
class UnexpectedException(Exception):
    pass
