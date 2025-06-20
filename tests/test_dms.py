from __future__ import annotations

import unittest

from jgdtrans import dms


class TestDMS(unittest.TestCase):
    def test_to_str(self):
        cases = (
            ("0.0", dms.DMS(1, 0, 0, 0, 0.0).to_str()),
            ("-0.0", dms.DMS(-1, 0, 0, 0, 0.0).to_str()),
            ("0.000012", dms.DMS(1, 0, 0, 0, 0.000012).to_str()),
            ("-0.000012", dms.DMS(-1, 0, 0, 0, 0.000012).to_str()),
            ("1.0", dms.DMS(1, 0, 0, 1, 0.0).to_str()),
            ("-1.0", dms.DMS(-1, 0, 0, 1, 0.0).to_str()),
            ("10.0", dms.DMS(1, 0, 0, 10, 0.0).to_str()),
            ("-10.0", dms.DMS(-1, 0, 0, 10, 0.0).to_str()),
            ("100.0", dms.DMS(1, 0, 1, 0, 0.0).to_str()),
            ("-100.0", dms.DMS(-1, 0, 1, 0, 0.0).to_str()),
            ("10000.0", dms.DMS(1, 1, 0, 0, 0.0).to_str()),
            ("-10000.0", dms.DMS(-1, 1, 0, 0, 0.0).to_str()),
            ("10101.0", dms.DMS(1, 1, 1, 1, 0.0).to_str()),
            ("-10101.0", dms.DMS(-1, 1, 1, 1, 0.0).to_str()),
        )
        for e, a in cases:
            with self.subTest(e=e, a=a):
                self.assertEqual(e, a)

        self.assertEqual("360613.58925", dms.DMS(1, 36, 6, 13, 0.58925).to_str())
        self.assertEqual("1400516.27815", dms.DMS(1, 140, 5, 16, 0.27815).to_str())

    def test_to_str_primed(self):
        cases = (
            ("0.0″", dms.DMS(1, 0, 0, 0, 0.0).to_primed_str()),
            ("-0.0″", dms.DMS(-1, 0, 0, 0, 0.0).to_primed_str()),
            ("0.000012″", dms.DMS(1, 0, 0, 0, 0.000012).to_primed_str()),
            ("-0.000012″", dms.DMS(-1, 0, 0, 0, 0.000012).to_primed_str()),
            ("1.0″", dms.DMS(1, 0, 0, 1, 0.0).to_primed_str()),
            ("-1.0″", dms.DMS(-1, 0, 0, 1, 0.0).to_primed_str()),
            ("10.0″", dms.DMS(1, 0, 0, 10, 0.0).to_primed_str()),
            ("-10.0″", dms.DMS(-1, 0, 0, 10, 0.0).to_primed_str()),
            ("1′00.0″", dms.DMS(1, 0, 1, 0, 0.0).to_primed_str()),
            ("-1′00.0″", dms.DMS(-1, 0, 1, 0, 0.0).to_primed_str()),
            ("1°00′00.0″", dms.DMS(1, 1, 0, 0, 0.0).to_primed_str()),
            ("-1°00′00.0″", dms.DMS(-1, 1, 0, 0, 0.0).to_primed_str()),
            ("1°01′01.0″", dms.DMS(1, 1, 1, 1, 0.0).to_primed_str()),
            ("-1°01′01.0″", dms.DMS(-1, 1, 1, 1, 0.0).to_primed_str()),
        )
        for e, a in cases:
            with self.subTest(e=e, a=a):
                self.assertEqual(e, a)

        self.assertEqual("36°06′13.58925″", dms.DMS(1, 36, 6, 13, 0.58925).to_primed_str())
        self.assertEqual("140°05′16.27815″", dms.DMS(1, 140, 5, 16, 0.27815).to_primed_str())

    def test_from_str(self):
        cases = (
            # sign
            ("00", dms.DMS(1, 0, 0, 0, 0.0)),
            ("-00", dms.DMS(-1, 0, 0, 0, 0.0)),
            ("00.0", dms.DMS(1, 0, 0, 0, 0.0)),
            ("-00.0", dms.DMS(-1, 0, 0, 0, 0.0)),
            ("00.", dms.DMS(1, 0, 0, 0, 0.0)),
            ("-00.", dms.DMS(-1, 0, 0, 0, 0.0)),
            (".0", dms.DMS(1, 0, 0, 0, 0.0)),
            ("-.0", dms.DMS(-1, 0, 0, 0, 0.0)),
            # healthy
            ("12_34_56", dms.DMS(1, 12, 34, 56, 0.0)),
            ("-12_34_56", dms.DMS(-1, 12, 34, 56, 0.0)),
            ("12_34_56.7_8", dms.DMS(1, 12, 34, 56, 0.78)),
            ("-12_34_56.7_8", dms.DMS(-1, 12, 34, 56, 0.78)),
            ("0.7_8", dms.DMS(1, 0, 0, 0, 0.78)),
            ("-0.7_8", dms.DMS(-1, 0, 0, 0, 0.78)),
            (".7_8", dms.DMS(1, 0, 0, 0, 0.78)),
            ("-.7_8", dms.DMS(-1, 0, 0, 0, 0.78)),
        )

        for e, a in cases:
            with self.subTest(e=e, a=a):
                self.assertEqual(dms.DMS.from_str(e), a)

        # error
        cases = ("", "-", "a", "-a", ".", "-.", "..0", "-..0", ".0.", "-.0.", "0..", "-0..")
        for v in cases:
            with self.assertRaises(ValueError):
                dms.DMS.from_str(v)

        self.assertEqual(dms.DMS(1, 36, 6, 13, 0.58925), dms.DMS.from_str("360613.58925"))
        self.assertEqual(dms.DMS(1, 140, 5, 16, 0.27815), dms.DMS.from_str("1400516.27815"))

    def test_to_dd(self):
        expected = 36.103774791666666
        actual = dms.DMS(1, 36, 6, 13, 0.58925).to_dd()
        self.assertEqual(expected, actual)

        expected = 140.08785504166667
        actual = dms.DMS(1, 140, 5, 16, 0.27815).to_dd()
        self.assertEqual(expected, actual)

    def test_from_dd(self):
        actual = dms.DMS.from_dd(36.103774791666666)
        expected = dms.DMS(1, 36, 6, 13, 0.589249999997719)
        self.assertEqual(expected, actual)

        actual = dms.DMS.from_dd(140.08785504166667)
        expected = dms.DMS(1, 140, 5, 16, 0.27815000001646695)
        self.assertEqual(expected, actual)

    def test_identity_1(self):
        for deg in range(45):
            for min in range(60):
                for sec in range(60):
                    # plus
                    origin = dms.DMS(1, deg, min, sec, 0).to_dd()
                    z = dms.DMS.from_dd(origin)
                    self.assertLess(abs(z.to_dd() - origin), 3e-15)

                    # minus
                    origin = dms.DMS(-1, deg, min, sec, 0).to_dd()
                    z = dms.DMS.from_dd(origin)
                    self.assertLess(abs(z.to_dd() - origin), 3e-15)

    def test_identity_2(self):
        for deg in range(45, 90):
            for min in range(60):
                for sec in range(60):

                    # plus
                    origin = dms.DMS(1, deg, min, sec, 0).to_dd()
                    z = dms.DMS.from_dd(origin)
                    self.assertLess(abs(z.to_dd() - origin), 3e-15)

                    # minus
                    origin = dms.DMS(-1, deg, min, sec, 0).to_dd()
                    z = dms.DMS.from_dd(origin)
                    self.assertLess(abs(z.to_dd() - origin), 3e-15)

    def test_identity_3(self):
        for deg in range(90, 135):
            for min in range(60):
                for sec in range(60):
                    # plus
                    origin = dms.DMS(1, deg, min, sec, 0).to_dd()
                    z = dms.DMS.from_dd(origin)
                    self.assertLess(abs(z.to_dd() - origin), 3e-15)

                    # minus
                    origin = dms.DMS(-1, deg, min, sec, 0).to_dd()
                    z = dms.DMS.from_dd(origin)
                    self.assertLess(abs(z.to_dd() - origin), 3e-15)

    def test_identity_4(self):
        for deg in range(135, 180):
            for min in range(60):
                for sec in range(60):
                    # plus
                    origin = dms.DMS(1, deg, min, sec, 0).to_dd()
                    z = dms.DMS.from_dd(origin)
                    self.assertLess(abs(z.to_dd() - origin), 3e-15)

                    # minus
                    origin = dms.DMS(-1, deg, min, sec, 0).to_dd()
                    z = dms.DMS.from_dd(origin)
                    self.assertLess(abs(z.to_dd() - origin), 3e-15)


class TestToFromDMS(unittest.TestCase):
    def test_to(self):
        self.assertEqual("360613.589249999997719", dms.to_dms(36.103774791666666))
        self.assertEqual("1400516.278150000016467", dms.to_dms(140.08785504166667))

    def test_from(self):
        self.assertEqual(36.103774791666666, dms.from_dms("360613.58925"))
        self.assertEqual(140.08785504166667, dms.from_dms("1400516.27815"))


if __name__ == "__main__":
    unittest.main()
