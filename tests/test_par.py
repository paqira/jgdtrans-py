from __future__ import annotations

import math
import unittest

import jgdtrans
from jgdtrans import ParData, Parameter
from jgdtrans.par import is_format, StatisticData

DATA = {
    "TKY2JGD": {
        "format": "TKY2JGD",
        "parameter": {
            # forward
            54401027: {
                "latitude": 11.49105,
                "longitude": -11.80078,
                "altitude": 0.0,
            },
            54401037: {
                "latitude": 11.48732,
                "longitude": -11.80198,
                "altitude": 0.0,
            },
            54401028: {
                "latitude": 11.49096,
                "longitude": -11.80476,
                "altitude": 0.0,
            },
            54401038: {
                "latitude": 11.48769,
                "longitude": -11.80555,
                "altitude": 0.0,
            },
            # backward
            54401047: {
                "latitude": 11.48373,
                "longitude": -11.80318,
                "altitude": 0.0,
            },
            54401048: {
                "latitude": 11.48438,
                "longitude": -11.80689,
                "altitude": 0.0,
            },
        },
    },
    "PatchJGD(HV)": {
        "format": "PatchJGD_HV",
        "parameter": {
            # forward
            57413454: {
                "latitude": -0.05984,
                "longitude": 0.22393,
                "altitude": -1.25445,
            },
            57413464: {
                "latitude": -0.06011,
                "longitude": 0.22417,
                "altitude": -1.24845,
            },
            57413455: {
                "latitude": -0.0604,
                "longitude": 0.2252,
                "altitude": -1.29,
            },
            57413465: {
                "latitude": -0.06064,
                "longitude": 0.22523,
                "altitude": -1.27667,
            },
            # backward
            57413474: {
                "latitude": -0.06037,
                "longitude": 0.22424,
                "altitude": -0.35308,
            },
            57413475: {
                "latitude": -0.06089,
                "longitude": 0.22524,
                "altitude": 0.0,
            },
        },
    },
    "SemiDynaEXE": {
        "format": "SemiDynaEXE",
        "parameter": {
            54401005: {
                "latitude": -0.00622,
                "longitude": 0.01516,
                "altitude": 0.0946,
            },
            54401055: {
                "latitude": -0.0062,
                "longitude": 0.01529,
                "altitude": 0.08972,
            },
            54401100: {
                "latitude": -0.00663,
                "longitude": 0.01492,
                "altitude": 0.10374,
            },
            54401150: {
                "latitude": -0.00664,
                "longitude": 0.01506,
                "altitude": 0.10087,
            },
        },
    },
}


class TestIsFormat(unittest.TestCase):
    def test(self):
        self.assertTrue(is_format("TKY2JGD"))
        self.assertTrue(is_format("SemiDynaEXE"))
        self.assertFalse(is_format("Hi!"))


class TestParData(unittest.TestCase):
    def test_from_dict(self):
        data = {
            "format": "TKY2JGD",
            "description": "my param",
            "parameter": {
                12345678: {
                    "latitude": 0.1,
                    "longitude": 0.2,
                    "altitude": 0.3,
                },
                12345679: {
                    "latitude": 0.4,
                    "longitude": 0.5,
                    "altitude": 0.6,
                },
            },
        }

        actual = ParData.from_dict(data)
        expect = ParData(
                format="TKY2JGD",
                description="my param",
                parameter={
                    12345678: Parameter(0.1, 0.2, 0.3),
                    12345679: Parameter(0.4, 0.5, 0.6),
                },
        )

        self.assertEqual(expect, actual)

    def test_statistics(self):
        stats = ParData.from_dict(DATA["SemiDynaEXE"]).statistics()
        self.assertEqual(
            StatisticData(
                4, -0.006422499999999999, 0.00021264700797330775, 0.006422499999999999, -0.00664, -0.0062
            ),
            stats.latitude,
        )
        self.assertEqual(
            StatisticData(4, 0.0151075, 0.00013553136168429814, 0.0151075, 0.01492, 0.01529),
            stats.longitude,
        )
        self.assertEqual(
            StatisticData(4, 0.0972325, 0.005453133846697696, 0.0972325, 0.08972, 0.10374),
            stats.altitude,
        )
        self.assertEqual(
            StatisticData(
                4,
                0.016417802947905496,
                6.630508084291115e-05,
                0.016417802947905496,
                0.016326766366920303,
                0.016499215132847987,
            ),
            stats.horizontal,
        )

        stats = ParData("TKY2JGD", {}).statistics()
        self.assertEqual(
            StatisticData(
                None,
                None,
                None,
                None,
                None,
                None,
            ),
            stats.latitude,
        )
        self.assertEqual(
            StatisticData(
                None,
                None,
                None,
                None,
                None,
                None,
            ),
            stats.longitude,
        )
        self.assertEqual(
            StatisticData(
                None,
                None,
                None,
                None,
                None,
                None,
            ),
            stats.longitude,
        )
        self.assertEqual(
            StatisticData(
                None,
                None,
                None,
                None,
                None,
                None,
            ),
            stats.horizontal,
        )

        stats = ParData(
            "TKY2JGD", {54401005: Parameter(1.0, 0.0, math.nan)}
        ).statistics()
        self.assertEqual(
            StatisticData(1, 1.0, 0.0, 1.0, 1.0, 1.0),
            stats.latitude,
        )
        self.assertEqual(
            StatisticData(1, 0.0, 0.0, 0.0, 0.0, 0.0),
            stats.longitude,
        )
        self.assertEqual(stats.altitude.count, 1)
        self.assertTrue(math.isnan(stats.altitude.mean))
        self.assertTrue(math.isnan(stats.altitude.std))
        self.assertTrue(math.isnan(stats.altitude.abs))
        self.assertTrue(math.isnan(stats.altitude.min))
        self.assertTrue(math.isnan(stats.altitude.max))
        self.assertEqual(
            StatisticData(1, 1.0, 0.0, 1.0, 1.0, 1.0),
            stats.horizontal,
        )


class TestError(unittest.TestCase):
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


class TestTKY2JGD(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 2

        actual = jgdtrans.par.loads(text, format="TKY2JGD")
        expected = ParData(format="TKY2JGD", description="\n" * 2, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 2 + "12345678   0.00001   0.00002"

        actual = jgdtrans.par.loads(text, format="TKY2JGD")
        expected = ParData(
            format="TKY2JGD",
            description="\n" * 2,
            parameter={12345678: Parameter(0.00001, 0.00002, 0.0)},

        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 2 + "12345678   0.00001   0.00002\n"

        actual = jgdtrans.par.loads(text, format="TKY2JGD")
        expected = ParData(
            format="TKY2JGD",
            description="\n" * 2,
            parameter={12345678: Parameter(0.00001, 0.00002, 0.0)},
        )

        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 2 + "12345678   0.00001   0.00002\n90123345 -10.00001 -10.00002"

        actual = jgdtrans.par.loads(text, format="TKY2JGD")
        expected = ParData(
            format="TKY2JGD",
            description="\n" * 2,
            parameter={
                12345678: Parameter(0.00001, 0.00002, 0.0),
                90123345: Parameter(-10.00001, -10.00002, 0.0),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 2

        actual = jgdtrans.par.loads(text, format="TKY2JGD", description="hi!")
        expected = ParData(format="TKY2JGD", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class TestPatchJGD(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 16

        actual = jgdtrans.par.loads(text, format="PatchJGD")
        expected = ParData(format="PatchJGD", description="\n" * 16, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002"

        actual = jgdtrans.par.loads(text, format="PatchJGD")
        expected = ParData(
            format="PatchJGD",
            description="\n" * 16,
            parameter={12345678: Parameter(0.00001, 0.00002, 0.0)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 16 + "12345678   0.00001   0.00002\n"

        actual = jgdtrans.par.loads(text, format="PatchJGD")
        expected = ParData(
            format="PatchJGD",
            description="\n" * 16,
            parameter={12345678: Parameter(0.00001, 0.00002, 0.0)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002\n90123345 -10.00001 -10.00002"

        actual = jgdtrans.par.loads(text, format="PatchJGD")
        expected = ParData(
            format="PatchJGD",
            description="\n" * 16,
            parameter={
                12345678: Parameter(0.00001, 0.00002, 0.0),
                90123345: Parameter(-10.00001, -10.00002, 0.0),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 16

        actual = jgdtrans.par.loads(text, format="PatchJGD", description="hi!")
        expected = ParData(format="PatchJGD", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class TestPatchJGD_H(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 16

        actual = jgdtrans.par.loads(text, format="PatchJGD_H")
        expected = ParData(format="PatchJGD_H", description="\n" * 16, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 16 + "12345678   0.00001   0.00000"

        actual = jgdtrans.par.loads(text, format="PatchJGD_H")
        expected = ParData(
            format="PatchJGD_H",
            description="\n" * 16,
            parameter={12345678: Parameter(0.0, 0.0, 0.00001)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 16 + "12345678   0.00001   0.00000\n"

        actual = jgdtrans.par.loads(text, format="PatchJGD_H")
        expected = ParData(
            format="PatchJGD_H",
            description="\n" * 16,
            parameter={12345678: Parameter(0.0, 0.0, 0.00001)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 16 + "12345678   0.00001   0.00000\n90123345 -10.00001   0.0000"

        actual = jgdtrans.par.loads(text, format="PatchJGD_H")
        expected = ParData(
            format="PatchJGD_H",
            description="\n" * 16,
            parameter={
                12345678: Parameter(0.0, 0.0, 0.00001),
                90123345: Parameter(0.0, 0.0, -10.00001),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 16

        actual = jgdtrans.par.loads(text, format="PatchJGD_H", description="hi!")
        expected = ParData(format="PatchJGD_H", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class TestPatchJGD_HV(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 16

        actual = jgdtrans.par.loads(text, format="PatchJGD_HV")
        expected = ParData(format="PatchJGD_HV", description="\n" * 16, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003"

        actual = jgdtrans.par.loads(text, format="PatchJGD_HV")
        expected = ParData(
            format="PatchJGD_HV",
            description="\n" * 16,
            parameter={
                12345678: Parameter(0.00001, 0.00002, 0.00003),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003\n"

        actual = jgdtrans.par.loads(text, format="PatchJGD_HV")
        expected = ParData(
            format="PatchJGD_HV",
            description="\n" * 16,
            parameter={
                12345678: Parameter(0.00001, 0.00002, 0.00003),
            },
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003\n90123345 -10.00001 -10.00002 -10.00003"

        actual = jgdtrans.par.loads(text, format="PatchJGD_HV")
        expected = ParData(
            format="PatchJGD_HV",
            description="\n" * 16,
            parameter={
                12345678: Parameter(0.00001, 0.00002, 0.00003),
                90123345: Parameter(-10.00001, -10.00002, -10.00003),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 16

        actual = jgdtrans.par.loads(text, format="PatchJGD_HV", description="hi!")
        expected = ParData(format="PatchJGD_HV", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class TestHyokoRev(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 16

        actual = jgdtrans.par.loads(text, format="HyokoRev")
        expected = ParData(format="HyokoRev", description="\n" * 16, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 16 + "12345678      0.00001      0.00000"

        actual = jgdtrans.par.loads(text, format="HyokoRev")
        expected = ParData(
            format="HyokoRev",
            description="\n" * 16,
            parameter={
                12345678: Parameter(0.0, 0.0, 0.00001),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 16 + "12345678      0.00001      0.00000\n"

        actual = jgdtrans.par.loads(text, format="HyokoRev")
        expected = ParData(
            format="HyokoRev",
            description="\n" * 16,
            parameter={
                12345678: Parameter(0.0, 0.0, 0.00001),
            },
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 16 + "12345678      0.00001      0.00000\n90123345    -10.00001   0.0000"

        actual = jgdtrans.par.loads(text, format="HyokoRev")
        expected = ParData(
            format="HyokoRev",
            description="\n" * 16,
            parameter={
                12345678: Parameter(0.0, 0.0, 0.00001),
                90123345: Parameter(0.0, 0.0, -10.00001),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 16

        actual = jgdtrans.par.loads(text, format="HyokoRev", description="hi!")
        expected = ParData(format="HyokoRev", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class TestSemiDynaExe(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 16

        actual = jgdtrans.par.loads(text, format="SemiDynaEXE")
        expected = ParData(format="SemiDynaEXE", description="\n" * 16, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003"

        actual = jgdtrans.par.loads(text, format="SemiDynaEXE")
        expected = ParData(
            format="SemiDynaEXE",
            description="\n" * 16,
            parameter={12345678: Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003\n"

        actual = jgdtrans.par.loads(text, format="SemiDynaEXE")
        expected = ParData(
            format="SemiDynaEXE",
            description="\n" * 16,
            parameter={12345678: Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 16 + "12345678   0.00001   0.00002   0.00003\n90123345 -10.00001 -10.00002 -10.00003"

        actual = jgdtrans.par.loads(text, format="SemiDynaEXE")
        expected = ParData(
            format="SemiDynaEXE",
            description="\n" * 16,
            parameter={
                12345678: Parameter(0.00001, 0.00002, 0.00003),
                90123345: Parameter(-10.00001, -10.00002, -10.00003),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 16

        actual = jgdtrans.par.loads(text, format="SemiDynaEXE", description="hi!")
        expected = ParData(format="SemiDynaEXE", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class TestgeonetF3(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 18

        actual = jgdtrans.par.loads(text, format="geonetF3")
        expected = ParData(format="geonetF3", description="\n" * 18, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003"

        actual = jgdtrans.par.loads(text, format="geonetF3")
        expected = ParData(
            format="geonetF3",
            description="\n" * 18,
            parameter={12345678: Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003\n"

        actual = jgdtrans.par.loads(text, format="geonetF3")
        expected = ParData(
            format="geonetF3",
            description="\n" * 18,
            parameter={12345678: Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003\n90123345    -10.00001 -10.00002 -10.00003"

        actual = jgdtrans.par.loads(text, format="geonetF3")
        expected = ParData(
            format="geonetF3",
            description="\n" * 18,
            parameter={
                12345678: Parameter(0.00001, 0.00002, 0.00003),
                90123345: Parameter(-10.00001, -10.00002, -10.00003),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 18

        actual = jgdtrans.par.loads(text, format="geonetF3", description="hi!")
        expected = ParData(format="geonetF3", description="hi!", parameter={})
        self.assertEqual(expected, actual)


class TestITRF2014(unittest.TestCase):
    def test_no_parameter(self):
        text = "\n" * 18

        actual = jgdtrans.par.loads(text, format="ITRF2014")
        expected = ParData(format="ITRF2014", description="\n" * 18, parameter={})
        self.assertEqual(expected, actual)

    def test_single(self):
        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003"

        actual = jgdtrans.par.loads(text, format="ITRF2014")
        expected = ParData(
            format="ITRF2014",
            description="\n" * 18,
            parameter={12345678: Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003\n"

        actual = jgdtrans.par.loads(text, format="ITRF2014")
        expected = ParData(
            format="ITRF2014",
            description="\n" * 18,
            parameter={12345678: Parameter(0.00001, 0.00002, 0.00003)},
        )
        self.assertEqual(expected, actual, msg="with EOF \\n")

    def test_lines(self):
        text = "\n" * 18 + "12345678      0.00001   0.00002   0.00003\n90123345    -10.00001 -10.00002 -10.00003"

        actual = jgdtrans.par.loads(text, format="ITRF2014")
        expected = ParData(
            format="ITRF2014",
            description="\n" * 18,
            parameter={
                12345678: Parameter(0.00001, 0.00002, 0.00003),
                90123345: Parameter(-10.00001, -10.00002, -10.00003),
            },
        )
        self.assertEqual(expected, actual, msg="no EOF \\n")

    def test_description(self):
        text = "\n" * 18

        actual = jgdtrans.par.loads(text, format="ITRF2014", description="hi!")
        expected = ParData(format="ITRF2014", description="hi!", parameter={})
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
