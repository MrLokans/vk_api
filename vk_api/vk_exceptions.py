class API_Error(Exception):
    pass


class UnknownError(Exception):
    error_code = 1


class ApplicationDisableError(Exception):
    error_code = 2


class UnknownMethodError(API_Error):
    error_code = 3


class IncorrectSignatureError(API_Error):
    error_code = 4


class UserAuthorizationError(API_Error):
    error_code = 5


class TooManyRequestsError(API_Error):
    error_code = 6


class PermissionDeniedError(API_Error):
    error_code = 7


class InvalidRequestError(API_Error):
    error_code = 8


class FloodControlError(API_Error):
    error_code = 9


class InternalServerError(API_Error):
    error_code = 10


class TestModeError(API_Error):
    error_code = 11


class CaptchaNeededError(API_Error):
    error_code = 14


class AccessDeniedError(API_Error):
    error_code = 15


class HTTPAuthorizationError(API_Error):
    error_code = 16


class ValidationRequiredError(API_Error):
    error_code = 17


class NonStandaloneAppPermissionError(API_Error):
    error_code = 20


class StandaloneAppPermissonError(API_Error):
    error_code = 21


class DisabledMethodError(API_Error):
    error_code = 23


class ConfirmationRequiredError(API_Error):
    error_code = 24


class MissingOrInvalidParameterError(API_Error):
    error_code = 100


class InvalidAPIIDError(API_Error):
    error_code = 101


class InvalidUserID(API_Error):
    error_code = 113


class InvalidTimestampError(API_Error):
    error_code = 150


class AlbumAccessError(API_Error):
    error_code = 200


class AudioAccessError(API_Error):
    error_code = 201


class GroupAccessError(API_Error):
    error_code = 203


class FullAlbumError(API_Error):
    error_code = 300


class VotesPermissionError(API_Error):
    error_code = 500


class ObjectPermissionError(API_Error):
    error_code = 600


class AdsError(API_Error):
    error_code = 603
