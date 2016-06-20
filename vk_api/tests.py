import unittest

from .api import get_exception_class_by_code
from . import vk_exceptions


class TestException(unittest.TestCase):

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

if __name__ == '__main__':
    unittest.main()
