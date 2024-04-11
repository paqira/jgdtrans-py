import datetime as dt
import unittest

import jgdtrans


class TKY2JGD(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 2

        actual = jgdtrans.parser.TKY2JGD(text)
        expected = jgdtrans.Transformer(format="TKY2JGD", description="\n" * 1, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 2 + "12345678   0.00001   0.00002"

        actual = jgdtrans.parser.TKY2JGD(text)
        expected = jgdtrans.Transformer(
            format="TKY2JGD",
            description="\n" * 1,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.0)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 2 + "12345678   0.00001   0.00002\n"

        actual = jgdtrans.parser.TKY2JGD(text)
        expected = jgdtrans.Transformer(
            format="TKY2JGD",
            description="\n" * 1,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.0)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 2 + "12345678   0.00001   0.00002\n90123345 -10.00001 -10.00002"

        actual = jgdtrans.parser.TKY2JGD(text)
        expected = jgdtrans.Transformer(
            format="TKY2JGD",
            description="\n" * 1,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.0),
                90123345: jgdtrans.transformer.Parameter(-10.00001, -10.00002, 0.0),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 2

        actual = jgdtrans.parser.TKY2JGD(text, "hi!")
        expected = jgdtrans.Transformer(format="TKY2JGD", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class PatchJGD(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 16

        actual = jgdtrans.parser.PatchJGD(text)
        expected = jgdtrans.Transformer(format="PatchJGD", description="\n" * 15, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002"

        actual = jgdtrans.parser.PatchJGD(text)
        expected = jgdtrans.Transformer(
            format="PatchJGD",
            description="\n" * 15,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.0)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 16 + "12345678   0.00001   0.00002\n"

        actual = jgdtrans.parser.PatchJGD(text)
        expected = jgdtrans.Transformer(
            format="PatchJGD",
            description="\n" * 15,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.0)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002\n90123345 -10.00001 -10.00002"

        actual = jgdtrans.parser.PatchJGD(text)
        expected = jgdtrans.Transformer(
            format="PatchJGD",
            description="\n" * 15,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.0),
                90123345: jgdtrans.transformer.Parameter(-10.00001, -10.00002, 0.0),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 16

        actual = jgdtrans.parser.PatchJGD(text, "hi!")
        expected = jgdtrans.Transformer(format="PatchJGD", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class PatchJGD_H(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 16

        actual = jgdtrans.parser.PatchJGD_H(text)
        expected = jgdtrans.Transformer(format="PatchJGD_H", description="\n" * 15, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 16 + "12345678   0.00001   0.00000"

        actual = jgdtrans.parser.PatchJGD_H(text)
        expected = jgdtrans.Transformer(
            format="PatchJGD_H",
            description="\n" * 15,
            parameter={12345678: jgdtrans.transformer.Parameter(0.0, 0.0, 0.00001)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 16 + "12345678   0.00001   0.00000\n"

        actual = jgdtrans.parser.PatchJGD_H(text)
        expected = jgdtrans.Transformer(
            format="PatchJGD_H",
            description="\n" * 15,
            parameter={12345678: jgdtrans.transformer.Parameter(0.0, 0.0, 0.00001)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 16 + "12345678   0.00001   0.00000\n90123345 -10.00001   0.0000"

        actual = jgdtrans.parser.PatchJGD_H(text)
        expected = jgdtrans.Transformer(
            format="PatchJGD_H",
            description="\n" * 15,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.0, 0.0, 0.00001),
                90123345: jgdtrans.transformer.Parameter(0.0, 0.0, -10.00001),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 16

        actual = jgdtrans.parser.PatchJGD_H(text, "hi!")
        expected = jgdtrans.Transformer(format="PatchJGD_H", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class PatchJGD_HV(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 16

        actual = jgdtrans.parser.PatchJGD_HV(text)
        expected = jgdtrans.Transformer(format="PatchJGD_HV", description="\n" * 15, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003"

        actual = jgdtrans.parser.PatchJGD_HV(text)
        expected = jgdtrans.Transformer(
            format="PatchJGD_HV",
            description="\n" * 15,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003\n"

        actual = jgdtrans.parser.PatchJGD_HV(text)
        expected = jgdtrans.Transformer(
            format="PatchJGD_HV",
            description="\n" * 15,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003),
            },
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003\n90123345 -10.00001 -10.00002 -10.00003"

        actual = jgdtrans.parser.PatchJGD_HV(text)
        expected = jgdtrans.Transformer(
            format="PatchJGD_HV",
            description="\n" * 15,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003),
                90123345: jgdtrans.transformer.Parameter(-10.00001, -10.00002, -10.00003),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 16

        actual = jgdtrans.parser.PatchJGD_HV(text, "hi!")
        expected = jgdtrans.Transformer(format="PatchJGD_HV", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class HyokoRev(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 16

        actual = jgdtrans.parser.HyokoRev(text)
        expected = jgdtrans.Transformer(format="HyokoRev", description="\n" * 15, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 16 + "12345678      0.00001      0.00000"

        actual = jgdtrans.parser.HyokoRev(text)
        expected = jgdtrans.Transformer(
            format="HyokoRev",
            description="\n" * 15,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.0, 0.0, 0.00001),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 16 + "12345678      0.00001      0.00000\n"

        actual = jgdtrans.parser.HyokoRev(text)
        expected = jgdtrans.Transformer(
            format="HyokoRev",
            description="\n" * 15,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.0, 0.0, 0.00001),
            },
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 16 + "12345678      0.00001      0.00000\n90123345    -10.00001   0.0000"

        actual = jgdtrans.parser.HyokoRev(text)
        expected = jgdtrans.Transformer(
            format="HyokoRev",
            description="\n" * 15,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.0, 0.0, 0.00001),
                90123345: jgdtrans.transformer.Parameter(0.0, 0.0, -10.00001),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 16

        actual = jgdtrans.parser.HyokoRev(text, "hi!")
        expected = jgdtrans.Transformer(format="HyokoRev", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class SemiDynaExe(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 16

        actual = jgdtrans.parser.SemiDynaEXE(text)
        expected = jgdtrans.Transformer(format="SemiDynaEXE", description="\n" * 15, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003"

        actual = jgdtrans.parser.SemiDynaEXE(text)
        expected = jgdtrans.Transformer(
            format="SemiDynaEXE",
            description="\n" * 15,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003\n"

        actual = jgdtrans.parser.SemiDynaEXE(text)
        expected = jgdtrans.Transformer(
            format="SemiDynaEXE",
            description="\n" * 15,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003\n90123345 -10.00001 -10.00002 -10.00003"

        actual = jgdtrans.parser.SemiDynaEXE(text)
        expected = jgdtrans.Transformer(
            format="SemiDynaEXE",
            description="\n" * 15,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003),
                90123345: jgdtrans.transformer.Parameter(-10.00001, -10.00002, -10.00003),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 16

        actual = jgdtrans.parser.SemiDynaEXE(text, "hi!")
        expected = jgdtrans.Transformer(format="SemiDynaEXE", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class geonetF3(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 18

        actual = jgdtrans.parser.geonetF3(text)
        expected = jgdtrans.Transformer(format="geonetF3", description="\n" * 17, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003"

        actual = jgdtrans.parser.geonetF3(text)
        expected = jgdtrans.Transformer(
            format="geonetF3",
            description="\n" * 17,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003\n"

        actual = jgdtrans.parser.geonetF3(text)
        expected = jgdtrans.Transformer(
            format="geonetF3",
            description="\n" * 17,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003\n90123345    -10.00001 -10.00002 -10.00003"

        actual = jgdtrans.parser.geonetF3(text)
        expected = jgdtrans.Transformer(
            format="geonetF3",
            description="\n" * 17,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003),
                90123345: jgdtrans.transformer.Parameter(-10.00001, -10.00002, -10.00003),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 18

        actual = jgdtrans.parser.geonetF3(text, "hi!")
        expected = jgdtrans.Transformer(format="geonetF3", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class ITRF2014(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 18

        actual = jgdtrans.parser.ITRF2014(text)
        expected = jgdtrans.Transformer(format="ITRF2014", description="\n" * 17, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003"

        actual = jgdtrans.parser.ITRF2014(text)
        expected = jgdtrans.Transformer(
            format="ITRF2014",
            description="\n" * 17,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003\n"

        actual = jgdtrans.parser.ITRF2014(text)
        expected = jgdtrans.Transformer(
            format="ITRF2014",
            description="\n" * 17,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003\n90123345    -10.00001 -10.00002 -10.00003"

        actual = jgdtrans.parser.ITRF2014(text)
        expected = jgdtrans.Transformer(
            format="ITRF2014",
            description="\n" * 17,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003),
                90123345: jgdtrans.transformer.Parameter(-10.00001, -10.00002, -10.00003),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 18

        actual = jgdtrans.parser.ITRF2014(text, "hi!")
        expected = jgdtrans.Transformer(format="ITRF2014", description="hi!", parameter={})
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
