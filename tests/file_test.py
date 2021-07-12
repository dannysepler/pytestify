from unittest import TestCase


class FakeTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_my_check(self):
        self.assertTrue(True)
        self.assertFalse(False)
        self.assertEqual(1, 1)
        self.assertNotEqual(1, 2)
        self.assertEqual(
            1,
            1,
        )
