class API_Error(Exception):
    pass


class UnknownError(Exception):
    error_code = 1
    error_msg = """
Unknown error occurred. Try again later.
"""


class ApplicationDisabledError(Exception):
    error_code = 2
    error_msg = """
Application is disabled. Enable your application or use test mode
You need to switch on the app in Settings (https://vk.com/editapp?id={Your API_ID} 
or use the test mode (test_mode=1).
"""


class UnknownMethodError(API_Error):
    error_code = 3
    error_msg = """
Unknown method passed
Check the method name: http://vk.com/dev/methods .
"""


class IncorrectSignatureError(API_Error):
    error_code = 4
    error_msg = """
Incorrect signature
Check if the signature has been formed correctly: https://vk.com/dev/api_nohttps.
"""


class UserAuthorizationError(API_Error):
    error_code = 5
    error_msg = """
User authorization failed
Make sure that you use a correct authorization type. To work with the methods without a secureprefix you need to authorize a user with one of these ways: 
http://vk.com/dev/auth_sites, http://vk.com/dev/auth_mobile.
"""


class TooManyRequestsError(API_Error):
    error_code = 6
    error_msg = """
Too many requests per second
Decrease the request frequency or use the execute method.
More details on frequency limits here: http://vk.com/dev/api_requests.
"""


class PermissionDeniedError(API_Error):
    error_code = 7
    error_msg = """
Permission to perform this action is denied
Make sure that your have received required permissions during the authorization. You can do it with the account.getAppPermissions method.
"""


class InvalidRequestError(API_Error):
    error_code = 8
    error_msg = """
Invalid request
Check the request syntax (https://new.vk.com/dev/api_requests) and used parameters list (it can be found on a method description page) .
"""


class FloodControlError(API_Error):
    error_code = 9
    error_msg = """
Flood control
You need to decrease the count of identical requests. For more efficient work you may use execute or JSONP.
"""


class InternalServerError(API_Error):
    error_code = 10
    error_msg = """
Internal server error
Try again later.
"""


class TestModeError(API_Error):
    error_code = 11
    error_msg = """
In test mode application should be disabled or user should be authorized
Switch the app off in Settings: https://vk.com/editapp?id={Your API_ID}.
"""


class CaptchaNeededError(API_Error):
    error_code = 14
    error_msg = """
Captcha needed
Work with this error is explained in detail on the separate page
"""


class AccessDeniedError(API_Error):
    error_code = 15
    error_msg = """
Access denied
Make sure that you use correct identifiers and the content is available for the user in the full version of the site.
"""


class HTTPAuthorizationError(API_Error):
    error_code = 16
    error_msg = """
HTTP authorization failed
To avoid this error check if a user has the 'Use secure connection' option enabled with the account.getInfo method.
"""


class ValidationRequiredError(API_Error):
    error_code = 17
    error_msg = """
Validation required
Make sure that you don't use a token received with http://vk.com/dev/auth_mobile for a request from the server. It's restricted. The validation process is described on the separate page
(https://new.vk.com/dev/need_validation).
"""


class NonStandaloneAppPermissionError(API_Error):
    error_code = 20
    error_msg = """
Permission to perform this action is denied for non-standalone applications
If you see this error despite your app has the Standalone type, make sure that you use redirect_uri=https://oauth.vk.com/blank.html. Details here: http://vk.com/dev/auth_mobile.
"""


class StandaloneAppPermissonError(API_Error):
    error_code = 21
    error_msg = """
Permission to perform this action is allowed only for Standalone and OpenAPI applications
"""


class DisabledMethodError(API_Error):
    error_code = 23
    error_msg = """
This method was disabled
All the methods available now are listed here: http://vk.com/dev/methods
"""


class ConfirmationRequiredError(API_Error):
    error_code = 24
    error_msg = """
Confirmation required
Confirmation process is described on the separate page
(https://new.vk.com/dev/need_confirmation).
"""


class MissingOrInvalidParameterError(API_Error):
    error_code = 100
    error_msg = """
One of the parameters specified was missing or invalid
Check the reqired parameters list and their format on a method description page.
"""


class InvalidAPIIDError(API_Error):
    error_code = 101
    error_msg = """
Invalid application API ID
Find the app in the administrated list in settings: http://vk.com/apps?act=settings 
And set the correct API_ID in the request.
"""


class InvalidUserID(API_Error):
    error_code = 113
    error_msg = """
Invalid user id
Make sure that you use a correct id. You can get an id using a screen name with the utils.resolveScreenName method
"""


class InvalidTimestampError(API_Error):
    error_code = 150
    error_msg = """
Invalid timestamp
You may get a correct value with the utils.getServerTime method
"""


class AlbumAccessError(API_Error):
    error_code = 200
    error_msg = """
Access to album denied
Make sure you use correct ids (owner_id is always positive for users, negative for communities) and the current user has access to the requested content in the full version of the site.
"""


class AudioAccessError(API_Error):
    error_code = 201
    error_msg = """
Access to audio denied
Make sure you use correct ids (owner_id is always positive for users, negative for communities) and the current user has access to the requested content in the full version of the site.
"""


class GroupAccessError(API_Error):
    error_code = 203
    error_msg = """
Access to group denied
Make sure that the current user is a member or admin of the community (for closed and private groups and events).
"""


class FullAlbumError(API_Error):
    error_code = 300
    error_msg = """
This album is full
You need to delete the odd objects from the album or use another album.
"""


class VotesPermissionError(API_Error):
    error_code = 500
    error_msg = """
Permission denied. You must enable votes processing in application settings
Check the app settings: http://vk.com/editapp?id={Your API_ID}&section=payments
"""


class ObjectPermissionError(API_Error):
    error_code = 600
    error_msg = """
Permission denied. You have no access to operations specified with given object(s)
"""


class AdsError(API_Error):
    error_code = 603
    error_msg = """
Some ads error occured
"""
