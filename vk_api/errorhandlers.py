import sys
import inspect
import webbrowser

import requests

from . import vk_exceptions


def get_handler_by_error_code(error_code):
    module_classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    print(module_classes)
    handlers = (h[1] for h in module_classes
                if hasattr(h[1], 'ERROR_CODE'))
    handler = None
    for h in handlers:
        if int(h.ERROR_CODE) == int(error_code):
            handler = h
    if handler is None:
        handler = DefaultHandler
    return handler


class CaptchaHandler(object):
    ERROR_CODE = 14

    def __init__(self, vk, error_response):
        self.vk = vk
        self.error_response = error_response

    def handle(self):
        captcha_url = self.error_response["captcha_img"]
        captcha_sid = self.error_response["captcha_sid"]
        print("Now your browser will be opened with captcha:")
        webbrowser.open_new(captcha_url)
        while True:
            captcha_solution = input("Please, enter recognized image:")
            args = (self.last_method_url, captcha_sid, captcha_solution)
            new_method_url = "{}&captcha_sid={}&captcha_key={}".format(*args)

            # FIXME: this logic is completely broken!
            r = requests.get(new_method_url)
            if "error" not in r:
                self.last_method_url = new_method_url
                return r.json()
            raise vk_exceptions.CaptchaNeededError("Wrong captcha supplied!")
        raise vk_exceptions.CaptchaNeededError


class DefaultHandler(object):
    ERROR_CODE = 1

    def __init__(self, vk, error_response):
        self.vk = vk
        self.error_response = error_response

    def handle(self):
        error_code = self.error_response["error_code"]
        err_cls = vk_exceptions.get_exception_class_by_code(error_code)
        err_msg = "Error code {}\n".format(error_code)
        err_msg += err_cls.error_msg
        err_msg += self.error_response['error_msg']
        raise err_cls(err_msg)
