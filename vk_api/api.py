from __future__ import print_function, unicode_literals

import time
import requests
import json
import webbrowser
import re
import os

import logging

from . import vk_exceptions
from . import conf

logging.basicConfig(level=logging.INFO)


app_token = ""


def get_exception_class_by_code(code):
    """Gets exception with the corresponding error code,
    otherwise returns UnknownError
    :param code: error code
    :type code: int
    """
    code = int(code)

    api_error_classes = {}
    for e in vk_exceptions.__dict__.keys():
        err_cls = vk_exceptions.__dict__[e]
        if not e.endswith('Error'):
            continue
        if not hasattr(err_cls, 'error_code'):
            continue
        api_error_classes[int(err_cls.error_code)] = err_cls
    return api_error_classes.get(code, vk_exceptions.UnknownError)


def json_to_file(data_dict, file_name):
    """
    Dump python dictionary to json file
    :param data_dict: python dictionary to be dumped
    :type data_dict: dict
    :param file_name: filepath to dump data to
    :type file_name: str
    """
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data_dict, f, indent=4)


def json_from_file(file_name):
    """Read data from file and return as dict,
    if any exception occurs - return empty dict
    :param file_name: filepath to dump data to
    :type file_name: str
    :return: dictionary with data from json file
    :rtype: dict
    """
    data = {}
    with open(file_name, "r", encoding="utf-8") as f_in:
        data = json.load(f_in)
    return data


class API(object):

    permissions = ("friends", "photos", "audio", "video", "status",
                   "wall", "messages",)

    def __init__(self,
                 access_token=None,
                 use_settings=False,
                 settings_file=None,
                 api_version=conf.DEFAULT_API_VERSION,
                 request_delay=conf.API_CALL_DELAY,
                 permissions=conf.DEFAULT_PERMISSIONS):

        self._use_settings = use_settings
        self._access_token = access_token
        if self._use_settings:
            self._settings_file = settings_file if settings_file else conf.DEFAULT_SETTINGS_FILE
        self.manage_settings()

        self.first_time = time.time()
        self._called_first_time = True

        self.api_version = api_version
        self.delay = request_delay
        self.permissions = permissions

        if not self._access_token:
            logging.info("No access token provided, using public methods.")

    @property
    def access_token(self):
        return self._access_token

    @access_token.setter
    def access_token(self, value):
        self._access_token = value
        if self._use_settings and self._settings_file:
            json_to_file({"access_token": value}, self._settings_file)

    def manage_settings(self):
        """Makes sure that settings file always exists"""
        if not self._use_settings:
            return
        f = self._settings_file
        if not os.path.exists(f) or not os.path.isfile(f):
            # Write empty settings if no file present
            json_to_file(conf.DEFAULT_SETTINGS, f)
        if not self._access_token:
            # We try to get access token from settings file
            d = json_from_file(self._settings_file)
            if d.get('access_token'):
                self._access_token = d.get('access_token')

    @classmethod
    def get_access_token(cls,
                         permissions=conf.DEFAULT_PERMISSIONS,
                         api_version=conf.DEFAULT_API_VERSION,
                         app_id=conf.APP_ID):
        """
        Obtain access token from the user with given permissions.
        User is prompted to copy URL from his browser containing access-token.
        Access token itself is NOT copied to the library owner or any 3rdparties

        :param permissions: sequence of permissions_ names access_token should provide
        :param api_version: version of VK API.
        :param app_id: application ID
        :type permissions: tuple
        :type api_version: str or unicode
        :type app_id: str or unicode
        :return: access token
        :rtype: str or unicode

        .. _permissions: https://new.vk.com/dev/permissions
        """
        print("You will now be redirected to the authorisation page.")
        print("If you're asked to login - login and copy paste page url when asked.")
        print("Otherwise copy paste page url when asked.")
        url = cls.construct_auth_dialog_url(permissions=permissions,
                                             api_version=api_version,
                                             app_id=app_id)
        webbrowser.open_new(url)
        in_url = input("Please, enter URL with access token:")
        access_token = cls.parse_token_url(in_url)
        return access_token

    @classmethod
    def parse_token_url(cls, url):
        """Extracts access token from the specified url,
        if there is no token - raises IncorrectAccessToken error.

        :param url: URL string to extract access token from
        :type url: str or unicode
        :return: Access token string
        :rtype: str or unicode
        """
        s = re.search(r'#access_token=([A-Za-z0-9]+)', url)
        if s:
            return s.groups()[0]
        else:
            raise vk_exceptions.IncorrectAccessToken("No access token found in url.")

    def is_valid_access_token(self):
        is_valid = True
        try:
            self.api_method("isAppUser")
        except vk_exceptions.API_Error:
            is_valid = False
        return is_valid

    def api_method(self, method_name, **kwargs):
        """Low-level implementation of API calls.
        Usage example:

        >>> api = API()
        >>> api.api_method("wall.get", owner_id="1", offset=20, count=30))

        :param method_name: name of the VK API method_ to be called
        :type method_name: str or unicode
        :param kwargs: method parameters passed to method
        :returns: api response dictionary
        :rtype: dictionary

        .. _method: https://new.vk.com/dev/methods
        """

        # Calculate time difference between requests
        # and prohibit API calls in single-threaded environment
        second_time = time.time()
        request_time_diff = second_time - self.first_time
        if request_time_diff < conf.API_CALL_DELAY:
            if not self._called_first_time:
                time_to_sleep = conf.API_CALL_DELAY - request_time_diff
                time.sleep(time_to_sleep + 0.01)
            else:
                self._called_first_time = True

        request_api_version = kwargs.get('v')
        if not request_api_version:
            kwargs["v"] = self.api_version
        if self._access_token:
            kwargs["access_token"] = self._access_token

        url = conf.API_BASE_URL + method_name
        r = requests.get(url, params=kwargs)
        self.last_method_url = r.url
        r = r.json()
        if "error" in r:
            return self.handle_error(r["error"])
        return r

    @staticmethod
    def construct_auth_dialog_url(permissions=conf.DEFAULT_PERMISSIONS,
                                  api_version=conf.DEFAULT_API_VERSION,
                                  app_id=conf.APP_ID):
        """Constructs url to get the access token

        :param permissions: sequence of permissions_ names access_token should provide
        :param api_version: version of VK API.
        :param app_id: application ID
        :type permissions: tuple
        :type api_version: str or unicode
        :type app_id: str or unicode
        :return: URL to obtain user's access token with given permissions
        :rtype: str or unicode

        .. _permissions: https://new.vk.com/dev/permissions
        """
        perms = ",".join(permissions)
        url = '{}\
client_id={}&\
scope={}&\
redirect_uri=https://oauth.vk.com/blank.html&\
display=page&\
v={}&\
response_type=token'.format(conf.AUTH_BASE_URL, app_id, perms, api_version)
        return url

    def handle_captcha(self, req):
        captcha_url = req["captcha_img"]
        captcha_sid = req["captcha_sid"]
        print("Now your browser will be opened with captcha:")
        webbrowser.open_new(captcha_url)
        while True:
            captcha_solution = input("Please, enter recognized image:")
            args = (self.last_method_url, captcha_sid, captcha_solution)
            new_method_url = "{}&captcha_sid={}&captcha_key={}".format(*args)
            r = requests.get(new_method_url)
            if "error" not in r:
                self.last_method_url = new_method_url
                return r.json()
            raise vk_exceptions.CaptchaNeededError("Wrong captcha supplied!")

    def handle_error(self, error_request):
        # TODO:
        # (+) Add actual handlers
        # (-) Somehow download and solve captcha (add some GUI)
        error_code = error_request["error_code"]
        if error_code == conf.CAPTCHA_ERROR_CODE:
            return self.handle_captcha(error_request)
        else:
            err_msg = "Error code {}\n".format(error_code)
            err_cls = get_exception_class_by_code(error_code)
            err_msg += err_cls.error_msg
            err_msg += error_request['error_msg']
            raise err_cls(err_msg)


def main():
    api = API(use_settings=True)
    print("Has valid access token: ", api.is_valid_access_token())
    print(api.api_method("wall.get", owner_id="1", offset=20, count=30))
    code = """
var friends = API.friends.get({"user_id": 1});
return friends;
"""
    print(api.api_method("execute", code=code))
    print(api.construct_auth_dialog_url)

if __name__ == "__main__":
    main()
