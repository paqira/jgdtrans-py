from __future__ import annotations

import math
import unittest
from typing import Sequence

import jgdtrans
from jgdtrans.error import PointOutOfBoundsError

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


class BilinearInterpolation(unittest.TestCase):
    def test(self):
        actual = jgdtrans.transformer.bilinear_interpolation(0, 0.5, 0.5, 1, 0.5, 0.5)
        expect = 0.5
        self.assertEqual(expect, actual)


class FromDict(unittest.TestCase):
    def test(self):
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

        actual = jgdtrans.from_dict(data)
        expect = jgdtrans.Transformer(
            format="TKY2JGD",
            description="my param",
            parameter={
                12345678: jgdtrans.transformer.Parameter(0.1, 0.2, 0.3),
                12345679: jgdtrans.transformer.Parameter(0.4, 0.5, 0.6),
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
        self.assertAlmostEqual(e[0], a[0], delta=0.0000000000001)
        # [1e-5 m] order
        self.assertAlmostEqual(e[1], a[1], delta=0.0000000000001)
        # [mm] order
        self.assertAlmostEqual(e[2], a[2], delta=0.0000000000001)

    def test_vs_web_tky2jgd(self):
        """v.s. original (web)"""
        trans = jgdtrans.from_dict(DATA["TKY2JGD"])

        # 国土地理院
        origin = (36.103774791666666, 140.08785504166664, 0)
        actual = tuple(trans.forward(*origin))
        expected = (36.106966281, 140.084576867, 0.0)
        self.assert_equal_point(expected, actual)

        origin = (36.10696628160147, 140.08457686629436, 0.0)
        actual = tuple(trans.backward_compat(*origin))
        expected = (36.103774792, 140.087855042, 0.0)
        self.assert_equal_point(expected, actual)

    def test_vs_web_patch_jgd_hv(self):
        """v.s. original (web)"""
        # merged param PatchJGD and PatchJGD(H)
        trans = jgdtrans.from_dict(DATA["PatchJGD(HV)"])

        # 金華山黄金山神社
        origin = (38.2985120586605, 141.5559006163195, 0)
        actual = tuple(trans.forward(*origin))
        expected = (38.298495306, 141.555963019, -1.263)
        self.assert_equal_point(expected, actual)

        origin = (38.29849530463122, 141.55596301776936, 0.0)
        actual = tuple(trans.backward_compat(*origin))
        expected = (38.298512058, 141.555900614, 1.264)
        self.assert_equal_point(expected, actual)

    def test_vs_web_semi_dyna_exe(self):
        """v.s. original (web)"""
        trans = jgdtrans.from_dict(DATA["SemiDynaEXE"])

        # 国土地理院
        origin = (36.103774791666666, 140.08785504166664, 0)
        actual = tuple(trans.forward(*origin))
        expected = (36.103773019, 140.087859244, 0.096)
        self.assert_equal_point(expected, actual)

        origin = (36.10377301875336, 140.08785924400115, 0.0)
        actual = tuple(trans.backward_compat(*origin))
        expected = (36.103774792, 140.087855042, -0.096)
        self.assert_equal_point(expected, actual)

    def test_vs_exact_semi_dyna_exe(self):
        """v.s. exact"""
        # the exact value are calculated by `Decimal`

        trans = jgdtrans.from_dict(DATA["SemiDynaEXE"])

        # 国土地理院
        origin = (36.103774791666666, 140.08785504166664, 0.0)
        actual = tuple(trans.forward(*origin))
        expected = (36.10377301875335, 140.08785924400115, 0.09631385775572238)
        self.assert_equal_point_exact(expected, actual)

        actual = tuple(trans.backward_compat(*actual))
        expected = (36.10377479166668, 140.08785504166664, -4.2175864502150125955e-10)
        self.assert_equal_point_exact(expected, actual)

    def test_transform(self):
        """Equivalent test"""
        # TKY2JGD
        trans = jgdtrans.from_dict(DATA["TKY2JGD"])

        # equivalent test 1
        # 国土地理院 with altitude
        origin = (36.103774791666666, 140.08785504166664, 0)

        expected = tuple(trans.forward(*origin))
        actual = tuple(trans.transform(*origin))
        self.assert_equal_point(expected, actual)

        expected = tuple(trans.backward_compat(*origin))
        actual = tuple(trans.transform(*origin, backward=True))
        self.assert_equal_point(expected, actual)

        # equivalent test 2
        # 国土地理院 without altitude
        origin = (36.103774791666666, 140.08785504166664)

        expected = tuple(trans.forward(*origin))
        actual = tuple(trans.transform(*origin))
        self.assert_equal_point(expected, actual)

        expected = tuple(trans.backward_compat(*origin))
        actual = tuple(trans.transform(*origin, backward=True))
        self.assert_equal_point(expected, actual)

    def test_forward_corr(self):
        tf = jgdtrans.from_dict(DATA["SemiDynaEXE"])

        with self.assertRaises(PointOutOfBoundsError):
            tf.forward_corr(-1, 0)
        with self.assertRaises(PointOutOfBoundsError):
            tf.forward_corr(67, 0)
        with self.assertRaises(PointOutOfBoundsError):
            tf.forward_corr(0, 99)
        with self.assertRaises(PointOutOfBoundsError):
            tf.forward_corr(0, 181)

    def test_backward_compat_corr(self):
        tf = jgdtrans.from_dict(DATA["SemiDynaEXE"])

        with self.assertRaises(PointOutOfBoundsError):
            tf.backward_compat_corr(0, 0)
        with self.assertRaises(PointOutOfBoundsError):
            tf.backward_compat_corr(67, 0)
        with self.assertRaises(PointOutOfBoundsError):
            tf.backward_compat_corr(0, 99)
        with self.assertRaises(PointOutOfBoundsError):
            tf.backward_compat_corr(0, 181)

    def test_backward_corr(self):
        tf = jgdtrans.from_dict(DATA["SemiDynaEXE"])

        with self.assertRaises(PointOutOfBoundsError):
            tf.backward_corr(-1, 0)
        with self.assertRaises(PointOutOfBoundsError):
            tf.backward_corr(67, 0)
        with self.assertRaises(PointOutOfBoundsError):
            tf.backward_corr(0, 99)
        with self.assertRaises(PointOutOfBoundsError):
            tf.backward_corr(0, 181)

    def test_statistics(self):
        stats = jgdtrans.from_dict(DATA["SemiDynaEXE"]).statistics()
        self.assertEqual(
            jgdtrans.transformer.StatisticData(
                4, -0.006422499999999999, 0.00021264700797330775, 0.006422499999999999, -0.00664, -0.0062
            ),
            stats.latitude,
        )
        self.assertEqual(
            jgdtrans.transformer.StatisticData(4, 0.0151075, 0.00013553136168429814, 0.0151075, 0.01492, 0.01529),
            stats.longitude,
        )
        self.assertEqual(
            jgdtrans.transformer.StatisticData(4, 0.0972325, 0.005453133846697696, 0.0972325, 0.08972, 0.10374),
            stats.altitude,
        )
        self.assertEqual(
            jgdtrans.transformer.StatisticData(
                4,
                0.016417802947905496,
                6.630508084291115e-05,
                0.016417802947905496,
                0.016326766366920303,
                0.016499215132847987,
            ),
            stats.horizontal,
        )

        stats = jgdtrans.Transformer("TKY2JGD", {}).statistics()
        self.assertEqual(
            jgdtrans.transformer.StatisticData(
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
            jgdtrans.transformer.StatisticData(
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
            jgdtrans.transformer.StatisticData(
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
            jgdtrans.transformer.StatisticData(
                None,
                None,
                None,
                None,
                None,
                None,
            ),
            stats.horizontal,
        )

        stats = jgdtrans.Transformer(
            "TKY2JGD", {54401005: jgdtrans.transformer.Parameter(1.0, 0.0, math.nan)}
        ).statistics()
        self.assertEqual(
            jgdtrans.transformer.StatisticData(1, 1.0, 0.0, 1.0, 1.0, 1.0),
            stats.latitude,
        )
        self.assertEqual(
            jgdtrans.transformer.StatisticData(1, 0.0, 0.0, 0.0, 0.0, 0.0),
            stats.longitude,
        )
        self.assertEqual(stats.altitude.count, 1)
        self.assertTrue(math.isnan(stats.altitude.mean))
        self.assertTrue(math.isnan(stats.altitude.std))
        self.assertTrue(math.isnan(stats.altitude.abs))
        self.assertTrue(math.isnan(stats.altitude.min))
        self.assertTrue(math.isnan(stats.altitude.max))
        self.assertEqual(
            jgdtrans.transformer.StatisticData(1, 1.0, 0.0, 1.0, 1.0, 1.0),
            stats.horizontal,
        )


if __name__ == "__main__":
    unittest.main()
