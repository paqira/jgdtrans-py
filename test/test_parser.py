import datetime as dt
import unittest

import jgdtrans


class Version(unittest.TestCase):
    def test(self):
        actual = jgdtrans.parser.version("JGD2000-TokyoDatum Ver.0.1.2")
        expected = "JGD2000-TokyoDatum", jgdtrans.parser.Version(0, 1, 2, None)
        self.assertEqual(expected, actual)

        actual = jgdtrans.parser.version("for PatchJGD        Ver.1.2.3　 010")
        expected = "PatchJGD", jgdtrans.parser.Version(1, 2, 3, "010")
        self.assertEqual(expected, actual)

        actual = jgdtrans.parser.version("for PatchJGD(H)     Ver.1.0.0　 010")
        expected = "PatchJGD(H)", jgdtrans.parser.Version(1, 0, 0, "010")
        self.assertEqual(expected, actual)

        actual = jgdtrans.parser.version("for SemiDynaEXE    Ver.1.0.0")
        expected = "SemiDynaEXE", jgdtrans.parser.Version(1, 0, 0, None)
        self.assertEqual(expected, actual)

        with self.assertRaises(ValueError):
            jgdtrans.parser.version("")


class MetaData(unittest.TestCase):
    def test(self):
        text = r"""GRIDDED CORRECTION PARAMETER FOR POS2JGD
FORMAT_VERSION            = 1.00
PUBLISHED_BY               = GEOSPATIAL INFORMATION AUTHORITY OF JAPAN
NATIONAL_DATUM             = JGD2011
POSITIONING_DATUM          = ITRF2014+GRS80
VERSION_OF_PARAMETER       = Ver.1.0.0
EPOCH_OF_PARAMETER         = 20230401
RELEASE_DATE               = 20230531
APPLICABLE_AREA            = INHABITED AREA OF JAPAN
START_OF_APPLICABLE_PERIOD = 20230601
END_OF_APPLICABLE_PERIOD   = 20230831
DATA_FIELDS                = '4 MeshCode dB dL dH'
DATA_FIELD_SEPARATOR       = \s+
BASED_ON                   = GEONET_CORS"""
        actual = jgdtrans.parser.metadata(text)
        expected = jgdtrans.parser.MetaData(
            format_version=jgdtrans.parser.FormatVersion(major=1, minor=0),
            published_by="GEOSPATIAL INFORMATION AUTHORITY OF JAPAN",
            national_datum="JGD2011",
            positioning_datum="ITRF2014+GRS80",
            version_of_parameter=jgdtrans.parser.Version(major=1, minor=0, patch=0, supplemental=None),
            epoch_of_parameter=dt.date(2023, 4, 1),
            release_date=dt.date(2023, 5, 31),
            applicable_area="INHABITED AREA OF JAPAN",
            start_of_applicable_period=dt.date(2023, 6, 1),
            end_of_applicable_period=dt.date(2023, 8, 31),
            data_fields="'4 MeshCode dB dL dH'",
            data_field_separator="\\s+",
            based_on="GEONET_CORS",
        )

        self.assertEqual(expected, actual)


class TKY2JGD(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 2

        actual = jgdtrans.parser.TKY2JGD(text)
        expected = jgdtrans.Transformer(unit=1, description="\n" * 1, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 2 + "12345678   0.00001   0.00002"

        actual = jgdtrans.parser.TKY2JGD(text)
        expected = jgdtrans.Transformer(
            unit=1,
            description="\n" * 1,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.0)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 2 + "12345678   0.00001   0.00002\n"

        actual = jgdtrans.parser.TKY2JGD(text)
        expected = jgdtrans.Transformer(
            unit=1,
            description="\n" * 1,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.0)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 2 + "12345678   0.00001   0.00002\n90123345 -10.00001 -10.00002"

        actual = jgdtrans.parser.TKY2JGD(text)
        expected = jgdtrans.Transformer(
            unit=1,
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
        expected = jgdtrans.Transformer(unit=1, description="hi!", parameter={})
        self.assertEqual(expected, actual)


class PatchJGD(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 16

        actual = jgdtrans.parser.PatchJGD(text)
        expected = jgdtrans.Transformer(unit=1, description="\n" * 15, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002"

        actual = jgdtrans.parser.PatchJGD(text)
        expected = jgdtrans.Transformer(
            unit=1,
            description="\n" * 15,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.0)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 16 + "12345678   0.00001   0.00002\n"

        actual = jgdtrans.parser.PatchJGD(text)
        expected = jgdtrans.Transformer(
            unit=1,
            description="\n" * 15,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.0)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002\n90123345 -10.00001 -10.00002"

        actual = jgdtrans.parser.PatchJGD(text)
        expected = jgdtrans.Transformer(
            unit=1,
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
        expected = jgdtrans.Transformer(unit=1, description="hi!", parameter={})
        self.assertEqual(expected, actual)


class PatchJGD_H(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 16

        actual = jgdtrans.parser.PatchJGD_H(text)
        expected = jgdtrans.Transformer(unit=1, description="\n" * 15, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 16 + "12345678   0.00001   0.00000"

        actual = jgdtrans.parser.PatchJGD_H(text)
        expected = jgdtrans.Transformer(
            unit=1,
            description="\n" * 15,
            parameter={12345678: jgdtrans.transformer.Parameter(0.0, 0.0, 0.00001)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 16 + "12345678   0.00001   0.00000\n"

        actual = jgdtrans.parser.PatchJGD_H(text)
        expected = jgdtrans.Transformer(
            unit=1,
            description="\n" * 15,
            parameter={12345678: jgdtrans.transformer.Parameter(0.0, 0.0, 0.00001)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 16 + "12345678   0.00001   0.00000\n90123345 -10.00001   0.0000"

        actual = jgdtrans.parser.PatchJGD_H(text)
        expected = jgdtrans.Transformer(
            unit=1,
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
        expected = jgdtrans.Transformer(unit=1, description="hi!", parameter={})
        self.assertEqual(expected, actual)


class PatchJGD_HV(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 16

        actual = jgdtrans.parser.PatchJGD_HV(text)
        expected = jgdtrans.Transformer(unit=1, description="\n" * 15, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003"

        actual = jgdtrans.parser.PatchJGD_HV(text)
        expected = jgdtrans.Transformer(
            unit=1,
            description="\n" * 15,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003\n"

        actual = jgdtrans.parser.PatchJGD_HV(text)
        expected = jgdtrans.Transformer(
            unit=1,
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
            unit=1,
            description="\n" * 15,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003),
                90123345: jgdtrans.transformer.Parameter(-10.00001, -10.00002, -10.00003),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 16

        actual = jgdtrans.parser.PatchJGD_H(text, "hi!")
        expected = jgdtrans.Transformer(unit=1, description="hi!", parameter={})
        self.assertEqual(expected, actual)


class HyokoRev(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 16

        actual = jgdtrans.parser.HyokoRev(text)
        expected = jgdtrans.Transformer(unit=1, description="\n" * 15, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 16 + "12345678      0.00001      0.00000"

        actual = jgdtrans.parser.HyokoRev(text)
        expected = jgdtrans.Transformer(
            unit=1,
            description="\n" * 15,
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.0, 0.0, 0.00001),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 16 + "12345678      0.00001      0.00000\n"

        actual = jgdtrans.parser.HyokoRev(text)
        expected = jgdtrans.Transformer(
            unit=1,
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
            unit=1,
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
        expected = jgdtrans.Transformer(unit=1, description="hi!", parameter={})
        self.assertEqual(expected, actual)


class SemiDynaExe(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 16

        actual = jgdtrans.parser.SemiDynaEXE(text)
        expected = jgdtrans.Transformer(unit=5, description="\n" * 15, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003"

        actual = jgdtrans.parser.SemiDynaEXE(text)
        expected = jgdtrans.Transformer(
            unit=5,
            description="\n" * 15,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003\n"

        actual = jgdtrans.parser.SemiDynaEXE(text)
        expected = jgdtrans.Transformer(
            unit=5,
            description="\n" * 15,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003\n90123345 -10.00001 -10.00002 -10.00003"

        actual = jgdtrans.parser.SemiDynaEXE(text)
        expected = jgdtrans.Transformer(
            unit=5,
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
        expected = jgdtrans.Transformer(unit=5, description="hi!", parameter={})
        self.assertEqual(expected, actual)


class geonetF3(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 18

        actual = jgdtrans.parser.geonetF3(text)
        expected = jgdtrans.Transformer(unit=5, description="\n" * 17, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003"

        actual = jgdtrans.parser.geonetF3(text)
        expected = jgdtrans.Transformer(
            unit=5,
            description="\n" * 17,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003\n"

        actual = jgdtrans.parser.geonetF3(text)
        expected = jgdtrans.Transformer(
            unit=5,
            description="\n" * 17,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003\n90123345    -10.00001 -10.00002 -10.00003"

        actual = jgdtrans.parser.geonetF3(text)
        expected = jgdtrans.Transformer(
            unit=5,
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
        expected = jgdtrans.Transformer(unit=5, description="hi!", parameter={})
        self.assertEqual(expected, actual)


class ITRF2014(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 18

        actual = jgdtrans.parser.ITRF2014(text)
        expected = jgdtrans.Transformer(unit=5, description="\n" * 17, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003"

        actual = jgdtrans.parser.ITRF2014(text)
        expected = jgdtrans.Transformer(
            unit=5,
            description="\n" * 17,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003\n"

        actual = jgdtrans.parser.ITRF2014(text)
        expected = jgdtrans.Transformer(
            unit=5,
            description="\n" * 17,
            parameter={12345678: jgdtrans.transformer.Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003\n90123345    -10.00001 -10.00002 -10.00003"

        actual = jgdtrans.parser.ITRF2014(text)
        expected = jgdtrans.Transformer(
            unit=5,
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
        expected = jgdtrans.Transformer(unit=5, description="hi!", parameter={})
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
