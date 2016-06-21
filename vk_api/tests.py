import unittest
from unittest.mock import patch

import httpretty

from .api import get_exception_class_by_code, API
from . import vk_exceptions


class TestExceptions(unittest.TestCase):

    def test_correct_exception_classes_returned_by_error_code(self):
        correspondencies = [
            (20, vk_exceptions.NonStandaloneAppPermissionError),
            (203, vk_exceptions.GroupAccessError),
            (500, vk_exceptions.VotesPermissionError)
        ]
        for err_code, exc_class in correspondencies:
            expected_class = get_exception_class_by_code(err_code)
            self.assertEqual(exc_class, expected_class,
                             msg="Incorrect exception class returned.")

    def test_correct_exception_class_returned_by_nonexistent_error_code(self):
        exception_class = get_exception_class_by_code(999999999999)
        self.assertEqual(vk_exceptions.UnknownError, exception_class,
                         msg="UnknownError should be returned if error code does not exist.")


class TestAPIAuth(unittest.TestCase):

    def test_correctly_extracts_token_from_url_with_token(self):
        expected_token = "sometokentobeparsed"
        u = "https://oauth.vk.com/blank.html#access_token={}&expires_in=86400&user_id=1".format(expected_token)
        self.assertEqual(API().parse_token_url(u), expected_token)

    def test_exception_raised_for_token_with_no_token_in_url(self):
        expected_token = "sometokentobeparsed"
        u = "https://oauth.vk.com/blank.html&expires_in=86400&user_id=1"
        with self.assertRaises(vk_exceptions.IncorrectAccessToken):
            self.assertEqual(API().parse_token_url(u), expected_token)


class TestAPI(unittest.TestCase):

    @httpretty.activate
    def test_api_request_url_is_correctly_formed(self):
        httpretty.register_uri(httpretty.GET,
                               "https://api.vk.com/method/wall.get?owner_id=1",
                               body='{"response": [1, {}]}',
                               headers={'content-type': 'text/json', })
        api = API()
        r = api.api_method("wall.get", owner_id=1)
        self.assertTrue('response' in r)

    @httpretty.activate
    def test_exceptions_are_raised_accrodingly_to_error_code(self):
        httpretty.register_uri(httpretty.GET,
                               "https://api.vk.com/method/wall.get",
                               body='{"error":{"error_code":100,"error_msg":"One of the parameters specified was missing or invalid: owner_id is undefined","request_params":[{"key":"oauth","value":"1"},{"key":"method","value":"wall.get"}]}}',
                               headers={'content-type': 'text/json', })
        api = API()
        with self.assertRaises(vk_exceptions.MissingOrInvalidParameterError):
            api.api_method('wall.get')


if __name__ == '__main__':
    unittest.main()
