from __future__ import annotations

import unittest

import jgdtrans


class IsFormat(unittest.TestCase):
    def test(self):
        self.assertTrue(jgdtrans.par.is_format("TKY2JGD"))
        self.assertTrue(jgdtrans.par.is_format("SemiDynaEXE"))
        self.assertFalse(jgdtrans.par.is_format("Hi!"))


class Error(unittest.TestCase):
    def test_short_text(self):
        text = "\n" * 15

        with self.assertRaises(jgdtrans.error.ParseParFileError):
            jgdtrans.par.loads(text, format="SemiDynaEXE")

    def test_meshcode(self):
        text = "\n" * 16 + "123a5678   0.00001   0.00002   0.00003"

        with self.assertRaises(jgdtrans.error.ParseParFileError):
            jgdtrans.par.loads(text, format="SemiDynaEXE")

    def test_latitude(self):
        text = "\n" * 16 + "12345678   0.0000a   0.00002   0.00003"

        with self.assertRaises(jgdtrans.error.ParseParFileError):
            jgdtrans.par.loads(text, format="SemiDynaEXE")

    def test_longitude(self):
        text = "\n" * 16 + "12345678   0.00001   0.0000a   0.00003"

        with self.assertRaises(jgdtrans.error.ParseParFileError):
            jgdtrans.par.loads(text, format="SemiDynaEXE")

    def test_altitude(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002   0.0000a"

        with self.assertRaises(jgdtrans.error.ParseParFileError):
            jgdtrans.par.loads(text, format="SemiDynaEXE")


class TKY2JGD(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 2

        actual = jgdtrans.par.loads(text, format="TKY2JGD")
        expected = jgdtrans.Transformer(format="TKY2JGD", description="\n" * 2, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 2 + "12345678   0.00001   0.00002"

        actual = jgdtrans.par.loads(text, format="TKY2JGD")
        expected = jgdtrans.Transformer(
            format="TKY2JGD",
            description="\n" * 2,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.0)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 2 + "12345678   0.00001   0.00002\n"

        actual = jgdtrans.par.loads(text, format="TKY2JGD")
        expected = jgdtrans.Transformer(
            format="TKY2JGD",
            description="\n" * 2,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.0)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 2 + "12345678   0.00001   0.00002\n90123345 -10.00001 -10.00002"

        actual = jgdtrans.par.loads(text, format="TKY2JGD")
        expected = jgdtrans.Transformer(
            format="TKY2JGD",
            description="\n" * 2,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.0),
                90123345: jgdtrans.transformer.Parameter(-10.00001, -10.00002, 0.0),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 2

        actual = jgdtrans.par.loads(text, format="TKY2JGD", description="hi!")
        expected = jgdtrans.Transformer(format="TKY2JGD", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class PatchJGD(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 16

        actual = jgdtrans.par.loads(text, format="PatchJGD")
        expected = jgdtrans.Transformer(format="PatchJGD", description="\n" * 16, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002"

        actual = jgdtrans.par.loads(text, format="PatchJGD")
        expected = jgdtrans.Transformer(
            format="PatchJGD",
            description="\n" * 16,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.0)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 16 + "12345678   0.00001   0.00002\n"

        actual = jgdtrans.par.loads(text, format="PatchJGD")
        expected = jgdtrans.Transformer(
            format="PatchJGD",
            description="\n" * 16,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.0)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002\n90123345 -10.00001 -10.00002"

        actual = jgdtrans.par.loads(text, format="PatchJGD")
        expected = jgdtrans.Transformer(
            format="PatchJGD",
            description="\n" * 16,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.0),
                90123345: jgdtrans.transformer.Parameter(-10.00001, -10.00002, 0.0),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 16

        actual = jgdtrans.par.loads(text, format="PatchJGD", description="hi!")
        expected = jgdtrans.Transformer(format="PatchJGD", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class PatchJGD_H(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 16

        actual = jgdtrans.par.loads(text, format="PatchJGD_H")
        expected = jgdtrans.Transformer(format="PatchJGD_H", description="\n" * 16, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 16 + "12345678   0.00001   0.00000"

        actual = jgdtrans.par.loads(text, format="PatchJGD_H")
        expected = jgdtrans.Transformer(
            format="PatchJGD_H",
            description="\n" * 16,
            parameter={12345678: jgdtrans.transformer.Parameter(0.0, 0.0, 0.00001)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 16 + "12345678   0.00001   0.00000\n"

        actual = jgdtrans.par.loads(text, format="PatchJGD_H")
        expected = jgdtrans.Transformer(
            format="PatchJGD_H",
            description="\n" * 16,
            parameter={12345678: jgdtrans.transformer.Parameter(0.0, 0.0, 0.00001)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 16 + "12345678   0.00001   0.00000\n90123345 -10.00001   0.0000"

        actual = jgdtrans.par.loads(text, format="PatchJGD_H")
        expected = jgdtrans.Transformer(
            format="PatchJGD_H",
            description="\n" * 16,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.0, 0.0, 0.00001),
                90123345: jgdtrans.transformer.Parameter(0.0, 0.0, -10.00001),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 16

        actual = jgdtrans.par.loads(text, format="PatchJGD_H", description="hi!")
        expected = jgdtrans.Transformer(format="PatchJGD_H", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class PatchJGD_HV(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 16

        actual = jgdtrans.par.loads(text, format="PatchJGD_HV")
        expected = jgdtrans.Transformer(format="PatchJGD_HV", description="\n" * 16, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003"

        actual = jgdtrans.par.loads(text, format="PatchJGD_HV")
        expected = jgdtrans.Transformer(
            format="PatchJGD_HV",
            description="\n" * 16,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003\n"

        actual = jgdtrans.par.loads(text, format="PatchJGD_HV")
        expected = jgdtrans.Transformer(
            format="PatchJGD_HV",
            description="\n" * 16,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003),
            },
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003\n90123345 -10.00001 -10.00002 -10.00003"

        actual = jgdtrans.par.loads(text, format="PatchJGD_HV")
        expected = jgdtrans.Transformer(
            format="PatchJGD_HV",
            description="\n" * 16,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003),
                90123345: jgdtrans.transformer.Parameter(-10.00001, -10.00002, -10.00003),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 16

        actual = jgdtrans.par.loads(text, format="PatchJGD_HV", description="hi!")
        expected = jgdtrans.Transformer(format="PatchJGD_HV", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class HyokoRev(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 16

        actual = jgdtrans.par.loads(text, format="HyokoRev")
        expected = jgdtrans.Transformer(format="HyokoRev", description="\n" * 16, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 16 + "12345678      0.00001      0.00000"

        actual = jgdtrans.par.loads(text, format="HyokoRev")
        expected = jgdtrans.Transformer(
            format="HyokoRev",
            description="\n" * 16,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.0, 0.0, 0.00001),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 16 + "12345678      0.00001      0.00000\n"

        actual = jgdtrans.par.loads(text, format="HyokoRev")
        expected = jgdtrans.Transformer(
            format="HyokoRev",
            description="\n" * 16,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.0, 0.0, 0.00001),
            },
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 16 + "12345678      0.00001      0.00000\n90123345    -10.00001   0.0000"

        actual = jgdtrans.par.loads(text, format="HyokoRev")
        expected = jgdtrans.Transformer(
            format="HyokoRev",
            description="\n" * 16,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.0, 0.0, 0.00001),
                90123345: jgdtrans.transformer.Parameter(0.0, 0.0, -10.00001),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 16

        actual = jgdtrans.par.loads(text, format="HyokoRev", description="hi!")
        expected = jgdtrans.Transformer(format="HyokoRev", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class SemiDynaExe(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 16

        actual = jgdtrans.par.loads(text, format="SemiDynaEXE")
        expected = jgdtrans.Transformer(format="SemiDynaEXE", description="\n" * 16, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003"

        actual = jgdtrans.par.loads(text, format="SemiDynaEXE")
        expected = jgdtrans.Transformer(
            format="SemiDynaEXE",
            description="\n" * 16,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003\n"

        actual = jgdtrans.par.loads(text, format="SemiDynaEXE")
        expected = jgdtrans.Transformer(
            format="SemiDynaEXE",
            description="\n" * 16,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003\n90123345 -10.00001 -10.00002 -10.00003"

        actual = jgdtrans.par.loads(text, format="SemiDynaEXE")
        expected = jgdtrans.Transformer(
            format="SemiDynaEXE",
            description="\n" * 16,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003),
                90123345: jgdtrans.transformer.Parameter(-10.00001, -10.00002, -10.00003),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 16

        actual = jgdtrans.par.loads(text, format="SemiDynaEXE", description="hi!")
        expected = jgdtrans.Transformer(format="SemiDynaEXE", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class geonetF3(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 18

        actual = jgdtrans.par.loads(text, format="geonetF3")
        expected = jgdtrans.Transformer(format="geonetF3", description="\n" * 18, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003"

        actual = jgdtrans.par.loads(text, format="geonetF3")
        expected = jgdtrans.Transformer(
            format="geonetF3",
            description="\n" * 18,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003\n"

        actual = jgdtrans.par.loads(text, format="geonetF3")
        expected = jgdtrans.Transformer(
            format="geonetF3",
            description="\n" * 18,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003\n90123345    -10.00001 -10.00002 -10.00003"

        actual = jgdtrans.par.loads(text, format="geonetF3")
        expected = jgdtrans.Transformer(
            format="geonetF3",
            description="\n" * 18,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003),
                90123345: jgdtrans.transformer.Parameter(-10.00001, -10.00002, -10.00003),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 18

        actual = jgdtrans.par.loads(text, format="geonetF3", description="hi!")
        expected = jgdtrans.Transformer(format="geonetF3", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class ITRF2014(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 18

        actual = jgdtrans.par.loads(text, format="ITRF2014")
        expected = jgdtrans.Transformer(format="ITRF2014", description="\n" * 18, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003"

        actual = jgdtrans.par.loads(text, format="ITRF2014")
        expected = jgdtrans.Transformer(
            format="ITRF2014",
            description="\n" * 18,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003\n"

        actual = jgdtrans.par.loads(text, format="ITRF2014")
        expected = jgdtrans.Transformer(
            format="ITRF2014",
            description="\n" * 18,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003\n90123345    -10.00001 -10.00002 -10.00003"

        actual = jgdtrans.par.loads(text, format="ITRF2014")
        expected = jgdtrans.Transformer(
            format="ITRF2014",
            description="\n" * 18,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003),
                90123345: jgdtrans.transformer.Parameter(-10.00001, -10.00002, -10.00003),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 18

        actual = jgdtrans.par.loads(text, format="ITRF2014", description="hi!")
        expected = jgdtrans.Transformer(format="ITRF2014", description="hi!", parameter={})
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
