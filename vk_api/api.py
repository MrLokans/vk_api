from __future__ import print_function, unicode_literals

import time
import requests
import json
import webbrowser
import re
import os

import logging

from . import vk_exceptions

logging.basicConfig(level=logging.INFO)


# TODO:
# (-) move API_CALL_DELAY to class property
# and add an extra method
# to set it
# (+) add user authorisation
# (+) add access token settings
# (-) Cover with tests
# (-) Make base class that handles all the routines?
API_CALL_DELAY = 0.36

app_token = ""
API_BASE_URL = "https://api.vk.com/method/"
AUTH_BASE_URL = "https://oauth.vk.com/authorize?"
APP_ID = "4169750"
AUTH_ERROR_CODE = 5
CAPTCHA_ERROR_CODE = 14
CAPTCHA_ENTER_RETRIES = 3
DEFAULT_SETTINGS_FILE = "settings.json"
DEFAULT_API_VERSION = "5.52"
DEFAULT_SETTINGS = {"access_token": ""}
DEFAULT_PERMISSIONS = ("friends", "photos", "audio", "video", "status",
                       "wall", "messages",)


def get_exception_class_by_code(code):
    """Gets exception with the corresponding error code,
    otherwise returns UnknownError"""
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
                 api_version=DEFAULT_API_VERSION,
                 request_delay=API_CALL_DELAY,
                 permissions=DEFAULT_PERMISSIONS):

        self._use_settings = use_settings
        self._access_token = access_token
        if self._use_settings:
            self._settings_file = settings_file if settings_file else DEFAULT_SETTINGS_FILE
        self.manage_settings()

        self.temp_settings = self.settings
        self.first_time = time.time()

        self.api_version = api_version
        self.delay = request_delay
        self.permissions = permissions

        if not self._access_token:
            logging.info("No access token provided, using public methods.")

    @staticmethod
    def from_login_pass(login, password):
        """
        :param login: login string
        :param password: password string
        :return: api object
        """
        pass

    def manage_settings(self):
        """Makes sure that settings file always exists"""
        if not self._use_settings:
            return
        f = self._settings_file
        if not os.path.exists(f) or not os.path.isfile(f):
            # Write empty settings if no file present
            json_to_file(DEFAULT_SETTINGS, f)
        if not self._access_token:
            # We try to get access token from settings file
            d = json_from_file(self._settings_file)
            if d.get('access_token'):
                self._access_token = d.get('access_token')

    @property
    def settings(self):
        if self._use_settings:
            return json_from_file(self._settings_file)
        return {}

    @settings.setter
    def settings(self, value):
        if self._use_settings:
            json_to_file(value, self._settings_file)

    @property
    def access_token(self):
        # t = self.settings["access_token"]
        # self._access_token = t
        # return t
        return self._access_token

    @access_token.setter
    def access_token(self, value):
        self._access_token = value
        # self.temp_settings["access_token"] = value
        # self.settings = self.temp_settings

    def get_access_token(self):
        """Authorizes user"""
        print("You will now be redirected to the authorisation page.")
        print("If you're asked to login - login and copy paste page url when asked.")
        print("Otherwise copy paste page url when asked.")
        url = self.construct_auth_dialog_url()
        webbrowser.open_new(url)
        in_url = input("Please, enter URL with access token:")
        self.validate_url(in_url)
        access_token = self.parse_token_url(in_url)

        self.temp_settings["access_token"] = access_token
        self.settings = self.temp_settings

    def validate_url(self, url):
        """Checks whether the correct url is supplied"""
        if "#access_token=" not in url:
            raise ValueError("Wrong URL supplied.")

    def parse_token_url(self, url):
        """Gets access token from supplied url"""
        s = re.search(r'#access_token=([A-Za-z0-9]+)', url)
        if s:
            return s.groups()[0]
        else:
            raise vk_exceptions.IncorrectAccessToken("No acces token parsed.")

    def is_valid_access_token(self):
        is_valid = True
        try:
            self.api_method("isAppUser")
        except vk_exceptions.API_Error:
            is_valid = False
        return is_valid

    def api_method(self, method_name, **kwargs):
        """Low-level implementation of API calls.
        >>>api = API()
        >>>api.api_method("wall.get", owner_id="1", offset=20, count=30))
        :param method_name: name of the VK API method to be called
        :type method_name: str or unicode
        :param **kwargs: method parameters passed to method
        :returns: api response dictionary
        :rtype: dictionary
        """
        # Calculate time difference between requests
        # and prohibit API calls in single-threaded environment
        second_time = time.time()
        request_time_diff = second_time - self.first_time
        if request_time_diff < API_CALL_DELAY:
            time_to_sleep = API_CALL_DELAY - request_time_diff
            time.sleep(time_to_sleep + 0.01)

        request_api_version = kwargs.get('v')
        if not request_api_version:
            kwargs["v"] = self.api_version
        if self._access_token:
            kwargs["access_token"] = self._access_token

        url = API_BASE_URL + method_name
        r = requests.get(url, params=kwargs)
        self.last_method_url = r.url
        r = r.json()
        if "error" in r:
            return self.handle_error(r["error"])
        return r

    def construct_auth_dialog_url(self):
        """Constructs url to get the access token"""
        perms = ",".join(self.permissions)
        url = '{}\
client_id={}&\
scope={}&\
redirect_uri=https://oauth.vk.com/blank.html&\
display=page&\
v={}&\
response_type=token'.format(AUTH_BASE_URL, APP_ID, perms, self.api_version)
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
        if error_code == CAPTCHA_ERROR_CODE:
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

if __name__ == "__main__":
    main()
