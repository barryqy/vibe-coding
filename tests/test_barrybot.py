import unittest

from dojo_app import barrybot


class BarryBotStarterTests(unittest.TestCase):
    def test_starter_answer_requires_prompt(self):
        with self.assertRaises(ValueError):
            barrybot.answer("   ")

    def test_starter_answer_echoes_prompt(self):
        self.assertIn("hello", barrybot.answer("hello"))


if __name__ == "__main__":
    unittest.main()
