import unittest
from typing import Sequence

import JGDtrans

DATA = {
    'TKY2JGD': {
        "unit": 1,
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
    'PatchJGD(HV)': {
        "unit": 1,
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
        "unit": 5,
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
    }
}


class BilinearInterpolation(unittest.TestCase):
    def test(self):
        actual = JGDtrans.transformer.bilinear_interpolation(0, 0.5, 0.5, 1, 0.5, 0.5)
        expect = 0.5
        self.assertEqual(expect, actual)


class FromDict(unittest.TestCase):
    def test(self):
        data = {
            "unit": 1,
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

        actual = JGDtrans.from_dict(data)
        expect = JGDtrans.Transformer(
            unit=1,
            description="my param",
            parameter={
                12345678: JGDtrans.transformer.Parameter(0.1, 0.2, 0.3),
                12345679: JGDtrans.transformer.Parameter(0.4, 0.5, 0.6),
            },
        )

        self.assertEqual(expect, actual)


class Transformer(unittest.TestCase):
    def assert_equal_point(self, e: Sequence[float], a: Sequence[float]):
        # [1e-5 m] order
        self.assertAlmostEqual(e[0], a[0], delta=0.00000001)
        # [1e-5 m] order
        self.assertAlmostEqual(e[1], a[1], delta=0.00000001)
        # [mm] order
        self.assertAlmostEqual(e[2], a[2], delta=0.001)

    def assert_equal_point_exact(self, e: Sequence[float], a: Sequence[float]):
        # [1e-5 m] order
        self.assertAlmostEqual(e[0], a[0], delta=0.000000000001)
        # [1e-5 m] order
        self.assertAlmostEqual(e[1], a[1], delta=0.000000000001)
        # [mm] order
        self.assertAlmostEqual(e[2], a[2], delta=0.000000000001)

    def test_vs_web_tky2jgd(self):
        """v.s. original (web)"""
        trans = JGDtrans.from_dict(DATA["TKY2JGD"])

        # 国土地理院
        origin = (36.103774791666666, 140.08785504166664, 0)
        actual = tuple(trans.forward(*origin))
        expected = (36.106966281, 140.084576867, 0.0)
        self.assert_equal_point(expected, actual)

        actual = tuple(trans.backward(*actual))
        self.assert_equal_point(origin, actual)

    def test_vs_web_patch_jgd_hv(self):
        """v.s. original (web)"""
        # 金華山黄金山神社
        origin = (38.2985120586605, 141.5559006163195, 0)

        # merged param PatchJGD and PatchJGD(H)
        trans = JGDtrans.from_dict(DATA['PatchJGD(HV)'])

        actual = tuple(trans.forward(*origin))
        expected = (38.298495306, 141.555963019, -1.263)
        self.assert_equal_point(expected, actual)

        actual = tuple(trans.backward(*actual))
        self.assert_equal_point(origin, actual)

    def test_vs_web_semi_dyna_exe(self):
        """v.s. original (web)"""

        # 国土地理院
        origin = (36.103774791666666, 140.08785504166664, 0)

        trans = JGDtrans.from_dict(DATA["SemiDynaEXE"])

        actual = tuple(trans.forward(*origin))
        expected = (36.103773019, 140.087859244, 0.096)
        self.assert_equal_point(expected, actual)

        actual = tuple(trans.backward(*actual))
        self.assert_equal_point(origin, actual)

    def test_vs_exact_semi_dyna_exe(self):
        """v.s. exact"""

        # the exact value are calculated by `Decimal`

        # 国土地理院
        origin = (36.103774791666666, 140.08785504166664, 0.0)

        trans = JGDtrans.from_dict(DATA["SemiDynaEXE"])

        actual = tuple(trans.forward(*origin))
        expected = (36.10377301875335, 140.08785924400115, 0.09631385775572238)
        self.assert_equal_point_exact(expected, actual)

        actual = tuple(trans.backward(*actual))
        expected = (36.10377479166668, 140.08785504166664, -4.2175864502150125955E-10)
        self.assert_equal_point_exact(expected, actual)

    def test_transform(self):
        """equivalent test"""
        # TKY2JGD
        trans = JGDtrans.from_dict(DATA["TKY2JGD"])

        # equivalent test 1
        # 国土地理院 with altitude
        origin = (36.103774791666666, 140.08785504166664, 0)

        expected = tuple(trans.forward(*origin))
        actual = tuple(trans.transform(*origin))
        self.assert_equal_point(expected, actual)

        expected = tuple(trans.backward(*origin))
        actual = tuple(trans.transform(*origin, backward=True))
        self.assert_equal_point(expected, actual)

        # equivalent test 2
        # 国土地理院 without altitude
        origin = (36.103774791666666, 140.08785504166664)

        expected = tuple(trans.forward(*origin))
        actual = tuple(trans.transform(*origin))
        self.assert_equal_point(expected, actual)

        expected = tuple(trans.backward(*origin))
        actual = tuple(trans.transform(*origin, backward=True))
        self.assert_equal_point(expected, actual)


if __name__ == "__main__":
    unittest.main()
