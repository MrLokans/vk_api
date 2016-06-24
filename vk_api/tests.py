import re
import unittest
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

import httpretty

from .api import API, process_error_response
from . import vk_exceptions


class TestExceptions(unittest.TestCase):

    def test_correct_exception_classes_returned_by_error_code(self):
        correspondencies = [
            (20, vk_exceptions.NonStandaloneAppPermissionError),
            (203, vk_exceptions.GroupAccessError),
            (500, vk_exceptions.VotesPermissionError)
        ]
        for err_code, exc_class in correspondencies:
            expected_class = vk_exceptions.get_exception_class_by_code(err_code)
            self.assertEqual(exc_class, expected_class,
                             msg="Incorrect exception class returned.")

    def test_correct_exception_class_returned_by_nonexistent_error_code(self):
        exception_class = vk_exceptions.get_exception_class_by_code(999999999999)
        self.assertEqual(vk_exceptions.UnknownError, exception_class,
                         msg="UnknownError should be returned if error code does not exist.")

    def test_incorrect_response_error_text_raises_exception(self):
        incorrect_error_response = {"some": "random data"}
        with self.assertRaises(vk_exceptions.IncorrectErrorResponse):
            process_error_response(None, incorrect_error_response)


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


class TestAPImethods(unittest.TestCase):

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

    @httpretty.activate
    def test_access_token_added_to_requests_when_present(self):
        httpretty.register_uri(httpretty.GET,
                               re.compile(r"https://api.vk.com/method/wall.get*"),
                               body='{"response": [1, {}]}',
                               headers={'content-type': 'text/json', })
        api = API(access_token="accesstoken")
        api.api_method('wall.get')
        self.assertIn("access_token=accesstoken",
                      httpretty.last_request().path)

    def test_api_token_returned_with_property(self):
        access_token = "testtoken"
        api = API(access_token=access_token)
        self.assertEqual(api.access_token, access_token)

    @patch('vk_api.api.API.manage_settings')
    @patch('vk_api.utils.json_to_file')
    def test_api_token_is_written_to_file(self, json_to_file_mock,
                                          manage_settings_mock):
        access_token = "testtoken"
        settings_file = "test_settings.json"
        api = API(use_settings=True, settings_file=settings_file)
        api.access_token = access_token
        json_to_file_mock.assert_called_with({'access_token': access_token},
                                             settings_file)

    @patch('os.path.isfile')
    @patch('os.path.exists')
    @patch('vk_api.utils.json_from_file')
    def test_access_token_is_read_from_settings_file(self,
                                                     json_from_file_mock,
                                                     exists_mock, isfile_mock):
        settings_file = "test_settings.json"
        access_token = "testtoken"
        exists_mock.return_value = True
        isfile_mock.return_value = True
        json_from_file_mock.return_value = {"access_token": access_token}

        api = API(use_settings=True, settings_file=settings_file)
        self.assertEqual(api.access_token, access_token)

    @patch('os.path.isfile')
    @patch('os.path.exists')
    @patch('vk_api.utils.json_to_file')
    def test_settings_are_written_to_non_existent_file(self,
                                                       json_to_file_mock,
                                                       exists_mock,
                                                       isfile_mock):
        settings_file = "test_settings.json"
        exists_mock.return_value = False
        isfile_mock.return_value = False
        API(use_settings=True, settings_file=settings_file)
        json_to_file_mock.assert_called_with({'access_token': ''},
                                             settings_file)

    @patch('os.path.isfile')
    @patch('os.path.exists')
    @patch('vk_api.utils.json_to_file')
    def test_default_settings_are_written_to_non_existent_file(self,
                                                               json_to_file_mock,
                                                               exists_mock,
                                                               isfile_mock):
        settings_file = "test_settings.json"
        access_token = "testtoken"
        exists_mock.return_value = False
        isfile_mock.return_value = False
        API(use_settings=True, settings_file=settings_file,
            access_token=access_token)
        json_to_file_mock.assert_called_with({'access_token': access_token},
                                             settings_file)

    def test_auth_url_is_constructed_correctly(self):
        url = "https://oauth.vk.com/"
        url += "authorize?client_id=100&scope=wall,friends"
        url += "&redirect_uri=https://oauth.vk.com/blank.html"
        url += "&display=page&v=5.00&response_type=token"
        self.assertEqual(url,
                         API.construct_auth_dialog_url(("wall", "friends"),
                                                       "5.00", "100"))

    @patch('vk_api.api.API.api_method')
    def test_simple_dot_method_works(self, api_method_mock):
        api = API()
        code = "return;"
        api.execute(code=code)
        api_method_mock.assert_called_with('execute', code=code)

    @httpretty.activate
    def test_compound_methods_are_correctly_parsed(self):
        api = API()
        httpretty.register_uri(httpretty.GET,
                               re.compile(r"https://api.vk.com/method/wall.get*"),
                               body='{"response": [1, {}]}',
                               headers={'content-type': 'text/json', })
        r = api.wall.get(owner_id=1)
        self.assertEqual(r["response"][0], 1)


    class TestBunchContextManager(unittest.TestCase):

        def test_basic_usage(self):
            pass

if __name__ == '__main__':
    unittest.main()
