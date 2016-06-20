from __future__ import print_function, unicode_literals

import time
import requests
import json
import webbrowser
import re
import os

import logging

logging.basicConfig(level=logging.INFO)
# from vars import app_token

try:
    # Python 2
    import ConfigParser as Config_Parser
except ImportError:
    # Python 3
    import configparser as Config_Parser

from . import vk_exceptions

__author__ = 'anders-lokans'

# TODO:
# (-) move DELAY to class property
# and add an extra method
# to set it
# (+) add user authorisation
# (+) add access token settings
# (-) Cover with tests
# (-) Make base class that handles all the routines?
DELAY = 0.36

app_token = ""
API_BASE_URL = "https://api.vk.com/method/"
AUTH_BASE_URL = "https://oauth.vk.com/authorize?"
APP_ID = "4169750"
AUTH_ERROR_CODE = 5
CAPTCHA_ERROR_CODE = 14
CAPTCHA_ENTER_RETRIES = 3
DEFAULT_API_VERSION = "5.52"


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
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data_dict, f, indent=4)


def json_from_file(file_name):
    with open(file_name, "r", encoding="utf-8") as f_in:
        data = json.load(f_in)
    return data


class API(object):

    permissions = ("friends", "photos", "audio", "video", "status",
                   "wall", "messages",)

    def __init__(self,
                 api_version=DEFAULT_API_VERSION,
                 request_delay=DELAY):

        self.default_settings = {"access_token": ""}
        self.settings_file = "settings.json"
        self.check_settings()

        self.temp_settings = self.settings
        self.first_time = time.time()
        self.second_time = time.time()

        self._access_token = ""
        self.api_version = api_version
        self.delay = request_delay

        if not self.access_token:
            logging.warn("No access token provided.")
            logging.warn("Using only public methods.")

    @staticmethod
    def from_login_pass(login, password):
        """
        :param login: login string
        :param password: password string
        :return: api object
        """
        pass

    @staticmethod
    def from_access_token(access_token):
        pass

    def check_settings(self):
        """Makes sure that settings file always exists"""
        f = self.settings_file
        if not os.path.isfile(f) or os.path.getsize(f) == 0:
            logging.info("Settings file does not exist, creating.")
            json_to_file(self.default_settings, f)

    @property
    def settings(self):
        return json_from_file(self.settings_file)

    @settings.setter
    def settings(self, value):
        json_to_file(value, self.settings_file)

    @property
    def access_token(self):
        t = self.settings["access_token"]
        self._access_token = t
        return t

    @access_token.setter
    def access_token(self, value):
        self._access_token = value
        self.temp_settings["access_token"] = value
        self.settings = self.temp_settings

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
        """Implements vk api methods"""
        self.second_time = time.time()
        diff = self.second_time - self.first_time
        if diff < DELAY:
            time_to_sleep = DELAY - diff
            time.sleep(time_to_sleep + 0.03)
        self.second_time = time.time()

        kwargs["v"] = self.api_version
        if self.access_token:
            kwargs["access_token"] = self.access_token

        url = API_BASE_URL + method_name
        r = requests.get(url, params=kwargs)
        self.last_method_url = r.url
        r = r.json()
        if "error" in r:
            return self.handle_error(r["error"])
        return r

    def construct_auth_dialog_url(self):
        """Constructs url to get the access token"""
        perms = ",".join(API.permissions)
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
            new_method_url = "{}&captcha_sid={}&captcha_key={}".format(self.last_method_url,
                                                                       captcha_sid,
                                                                       captcha_solution)
            r = requests.get(new_method_url)
            if "error" not in r:
                self.last_method_url = new_method_url
                return r.json()
            raise vk_exceptions.CaptchaNeededError("Wrong captcha supplied!")

    def handle_error(self, error_request):
        # TODO:
        # (+) Add actual handlers
        # (-) Somehow download and solve captcha (add some GUI)
        # (-) May be move method ErrorHadnler Class
        error_code = error_request["error_code"]
        if error_code == CAPTCHA_ERROR_CODE:
            return self.handle_captcha(error_request)
        else:
            err_msg = "Error code {}\n".format(error_code)
            err_cls = get_exception_class_by_code(error_code)
            err_msg += err_cls.error_msg
            raise err_cls(err_msg)


def main():
    api = API()
    print("Has valid access token: ", api.is_valid_access_token())
    print(api.api_method("wall.get", owner_id="1"))

if __name__ == "__main__":
    main()
