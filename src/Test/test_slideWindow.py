import unittest
from Frontend.slideWindow import SendingWindow


class MyTestCase(unittest.TestCase):

    def test_slide_window_small_size(self):
        small_window = SendingWindow(10)
        res = small_window.send()
        self.assertEqual(len(res), 1)
        res = small_window.send_all()
        self.assertEqual(len(res), 9)

    def test_slide_window_normal_size(self):
        window = SendingWindow(1024)
        res = window.send()
        self.assertEqual(len(res), 1)
        res = window.send(10)
        self.assertEqual(len(res), 10)
        res = window.send(10)
        self.assertNotEqual(len(res), 10)
        res = window.send(10)
        self.assertEqual(len(res), 0)
        res = window.resend()
        self.assertEqual(len(res), 20)
        window.ack(0)
        res = window.resend()
        self.assertEqual(len(res), 19)
        window.ack(10)
        res = window.resend()
        self.assertEqual(len(res), 18)

    def test_slide_window_big_size(self):
        window = SendingWindow(0x20000, window_size=0x10000)
        res = window.send(0xffff)
        self.assertEqual(len(res), 0xffff)
        for i in range(0xffff):
            window.ack(i)
        res = window.send(0xffff)
        self.assertEqual(len(res), 0xffff)
        for i in range(0xffff + 1):
            window.ack(i)
        res = window.send()
        self.assertEqual(res, [])
        res = window.send()
        self.assertEqual(res, [])
        res = window.send()
        self.assertEqual(res, [])


if __name__ == '__main__':
    unittest.main()
