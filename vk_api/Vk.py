import time
import requests
import json

# from vars import app_token

try:
    import ConfigParser as Config_Parser
except ImportError:
    import configparser as Config_Parser

__author__ = 'anders-lokans'

# TODO:
# - move DELAY to class property and add an extra method
# to set it
# - Reorganise and refactor code (way too abstract)

DELAY = 0.36

app_token = ""
API_BASE_URL = "https://api.vk.com/method/"
AUTH_ERROR_CODE = 5
CAPTCHA_ERROR_CODE = 14


class Vk(object):

    def __init__(self,
                 login="",
                 password="",
                 api_key="",
                 vk_version="5.27"):
        # if not any(login, password, api_key):
        #     raise Exception("No way to authorise!")
        self.first_time = time.time()
        self.second_time = time.time()
        self.login = login
        self.password = password
        self.api_key = api_key
        self.vk_version = vk_version

        if not self.api_key:
            if self.login and self.password:
                self.api_key = self.get_api_key(login, password)

        if not any([login, password, api_key]):
            # if app_token:
            #     self.api_key = self.get_settings_token()
            # else:
            print("Could not authorise. Using only public methods.")

    def get_api_key(self, login, password):
        """
        TODO: implement authorisation
        """
        self.api_key = self.api_key
        api_key = "aaaaaaaaaaaaaaaaaaaa"
        return api_key

    def get_settings_token(self):
        return app_token
        # config = Config_Parser.ConfigParser()
        # config.read('settings.cfg')
        # return config.get('user', 'api_key')

    def api_method(self, method_name, **kwargs):
        self.second_time = time.time()
        diff = self.second_time - self.first_time
        if diff < DELAY:
            time_to_sleep = DELAY - diff
            time.sleep(time_to_sleep + 0.03)
        self.second_time = time.time()

        pars = dict(kwargs)

        pars["v"] = self.vk_version
        if self.api_key:
            pars["access_token"] = self.api_key

        url = API_BASE_URL + method_name
        print(url)
        r = requests.get(url, params=pars)

        r = r.json()
        if "error" in r:
            self.handle_error(r["error"])
        return r

    def handle_error(self, error_request):
        error_code = error_request["error_code"]
        if error_code == AUTH_ERROR_CODE:
            raise Exception("Could not authorise! Invalid Session.")
        elif error_code == CAPTCHA_ERROR_CODE:
            raise Exception("Could not authorise! Captcha Needed.")
        else:
            raise Exception("Unknown Error. {message}".format(message=error_request["error_msg"]))


def main():
    vk = Vk()
    print(vk.api_method("friends.get", user_id="100000"))

if __name__ == "__main__":
    main()
