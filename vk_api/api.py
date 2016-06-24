from __future__ import print_function, unicode_literals

import time
import requests
import webbrowser
import re
import os

import logging

from . import conf
from . import utils
from . import vk_exceptions
from .import errorhandlers

logging.basicConfig(level=logging.INFO)


def process_error_response(vk, json_response):
    """
    When response with error code is returned it is processed
    correct error handler is chosed by this method

    :param vk: VK API object instance
    :param json_response: VK API response, containing error code and message
    :type json_response: dict
    :type vk: API
    """
    if "error" not in json_response:
        msg = "API response is not a valid error response."
        raise vk_exceptions.IncorrectErrorResponse(msg)

    json_response = json_response["error"]

    error_code = json_response["error_code"]

    error_handler = errorhandlers.get_handler_by_error_code(error_code)
    error_handler(vk, json_response).handle()


class MethodChunk(object):

    __slots__ = ("_name", "_api", "_parent")

    def __init__(self, name, api, parent=None):
        self._name = name
        self._api = api
        self._parent = parent

    def resolve_method_name(self):
        """Assembles full method name from parent names"""
        name_parts = []
        node = self
        while isinstance(node, MethodChunk):
            name_parts.append(node._name)
            node = node._parent
        method_name = ".".join(reversed(name_parts))
        return method_name

    def __call__(self, **kwargs):
        method_name = self.resolve_method_name()
        return self._api.api_method(method_name, **kwargs)

    def __getattr__(self, attr):
        if attr not in self.__slots__:
            return MethodChunk(attr, self._api, self)
        return object.__getattr__(self, attr)


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
            utils.json_to_file({"access_token": value}, self._settings_file)

    def manage_settings(self):
        """Makes sure that settings file always exists"""
        if not self._use_settings:
            return
        f = self._settings_file
        if not os.path.exists(f) or not os.path.isfile(f):
            # Write empty settings if no file present
            if not self._access_token:
                utils.json_to_file(conf.DEFAULT_SETTINGS, f)
            else:
                utils.json_to_file({"access_token": self._access_token}, f)
            return
        if not self._access_token:
            # We try to get access token from settings file
            d = utils.json_from_file(self._settings_file)
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
            err_msg = "No access token found in url."
            raise vk_exceptions.IncorrectAccessToken(err_msg)

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
            return process_error_response(self, r)
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

    def __getattr__(self, attr):
        if attr in conf.METHOD_DOMAINS:
            return MethodChunk(attr, api=self)
        return object.__getattr__(self, attr)



def main():
    api = API(use_settings=False)
    print("Has valid access token: ", api.is_valid_access_token())
    print(api.api_method("wall.get", owner_id="1", offset=20, count=30))
    print(api.wall.get(owner_id=1, offset=20, count=30))

if __name__ == "__main__":
    main()
