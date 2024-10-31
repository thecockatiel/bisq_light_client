import unittest
from utils.formatting import to_truncated_string

class TestFormatting(unittest.TestCase):

    def test_to_truncated_string_none(self):
        self.assertEqual(to_truncated_string(None), "null")

    def test_to_truncated_string_empty(self):
        self.assertEqual(to_truncated_string(""), "")

    def test_to_truncated_string_short_message(self):
        self.assertEqual(to_truncated_string("Hello, World!"), "Hello, World!")

    def test_to_truncated_string_long_message(self):
        long_message = "a" * 300
        self.assertEqual(to_truncated_string(long_message, max_length=200), "a" * 197 + "...")

    def test_to_truncated_string_with_line_breaks(self):
        message = "Hello\nWorld"
        self.assertEqual(to_truncated_string(message, remove_line_breaks=True), "HelloWorld")
        self.assertEqual(to_truncated_string(message, remove_line_breaks=False), "Hello\nWorld")

    def test_to_truncated_string_non_string_input(self):
        self.assertEqual(to_truncated_string(1234567890, max_length=5), "12...")

if __name__ == '__main__':
    unittest.main()