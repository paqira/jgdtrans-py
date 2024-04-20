from __future__ import annotations

import unittest

from jgdtrans import Point, mesh
from jgdtrans.mesh import MeshCell, MeshCoord, MeshNode, is_meshcode


class IsMeshcode(unittest.TestCase):
    def test(self):
        self.assertTrue(is_meshcode(54401027))
        self.assertFalse(is_meshcode(-1))
        self.assertFalse(is_meshcode(100000000))
        self.assertFalse(is_meshcode(10810000))
        self.assertFalse(is_meshcode(10100800))


class MeshCoordTest(unittest.TestCase):
    def test_init(self):
        with self.assertRaises(ValueError):
            MeshCoord(-1, 0, 0)
        with self.assertRaises(ValueError):
            MeshCoord(100, 0, 0)

        with self.assertRaises(ValueError):
            MeshCoord(0, -1, 0)
        with self.assertRaises(ValueError):
            MeshCoord(0, 8, 0)

        with self.assertRaises(ValueError):
            MeshCoord(0, 0, -1)
        with self.assertRaises(ValueError):
            MeshCoord(0, 0, 10)

    def test_le_lt(self):
        node = MeshCoord(10, 0, 0)
        other = MeshCoord(0, 0, 0)
        while other != node:
            self.assertFalse(node < other)
            other = other.next_up(1)
        self.assertFalse(node < other)
        other = other.next_up(1)
        while other != MeshCoord(99, 7, 9):
            self.assertTrue(node < other)
            other = other.next_up(1)

        node = MeshCoord(10, 0, 0)
        other = MeshCoord(10, 0, 0)
        while other != node:
            self.assertFalse(node <= other)
            other = other.next_up(1)
        self.assertTrue(node <= other)
        other = other.next_up(1)
        while other != MeshCoord(99, 7, 9):
            self.assertTrue(node <= other)
            other = other.next_up(1)

    def test_ge_gt(self):
        node = MeshCoord(10, 0, 0)
        other = MeshCoord(0, 0, 0)
        while other != node:
            self.assertFalse(other > node)
            other = other.next_up(1)
        self.assertFalse(other > node)
        other = other.next_up(1)
        while other != MeshCoord(99, 7, 9):
            self.assertTrue(other > node)
            other = other.next_up(1)

        node = MeshCoord(10, 0, 0)
        other = MeshCoord(10, 0, 0)
        while other != node:
            self.assertFalse(other >= node)
            other = other.next_up(1)
        self.assertTrue(other >= node)
        other = other.next_up(1)
        while other != MeshCoord(99, 7, 9):
            self.assertTrue(other >= node)
            other = other.next_up(1)

    def test_is_unit(self):
        for third in range(10):
            self.assertTrue(MeshCoord(1, 2, third).is_mesh_unit(1))

        self.assertTrue(MeshCoord(1, 2, 0).is_mesh_unit(5))
        self.assertTrue(MeshCoord(1, 2, 5).is_mesh_unit(5))
        for third in (1, 2, 3, 4, 6, 7, 8, 9):
            self.assertFalse(MeshCoord(1, 2, third).is_mesh_unit(5))

    def test_from_latitude(self):
        actual = MeshCoord.from_latitude(36.103774791666666, 1)
        expected = MeshCoord(54, 1, 2)
        self.assertEqual(expected, actual)

        actual = MeshCoord.from_latitude(36.103774791666666, 5)
        expected = MeshCoord(54, 1, 0)
        self.assertEqual(expected, actual)

        args = [(-1, 1), (66.666667, 1)]
        for arg in args:
            with self.subTest():
                with self.assertRaises(ValueError, msg="error"):
                    MeshCoord.from_latitude(*arg)

        with self.assertRaises(TypeError, msg="error"):
            MeshCoord.from_latitude(0, 2)

    def test_from_longitude(self):
        actual = MeshCoord.from_longitude(140.08785504166664, 1)
        expected = MeshCoord(40, 0, 7)
        self.assertEqual(expected, actual)

        actual = MeshCoord.from_longitude(140.08785504166664, 5)
        expected = MeshCoord(40, 0, 5)
        self.assertEqual(expected, actual)

        args = [(-1, 1), (181, 1)]
        for arg in args:
            with self.subTest():
                with self.assertRaises(ValueError, msg="error"):
                    MeshCoord.from_longitude(*arg)

        with self.assertRaises(TypeError, msg="error"):
            MeshCoord.from_longitude(0, 2)

    def test_to_latitude(self):
        expected = 36.1
        actual = MeshCoord.from_latitude(36.103774791666666, 1).to_latitude()
        self.assertEqual(expected, actual)

        expected = 36.083333333333336
        actual = MeshCoord.from_latitude(36.103774791666666, 5).to_latitude()
        self.assertEqual(expected, actual)

    def test_to_longitude(self):
        value = 140.08785504166664

        expected = 140.0875
        actual = MeshCoord._from_degree(value, 1).to_longitude()
        self.assertEqual(expected, actual)

        expected = 140.0625
        actual = MeshCoord._from_degree(value, 5).to_longitude()
        self.assertEqual(expected, actual)

    def test_next_up(self):
        # increment
        actual = MeshCoord(0, 0, 0).next_up(1)
        expected = MeshCoord(0, 0, 1)
        self.assertEqual(expected, actual, msg="trivial case")

        actual = MeshCoord(0, 0, 0).next_up(5)
        expected = MeshCoord(0, 0, 5)
        self.assertEqual(expected, actual, msg="trivial case")

        # carry case of 1
        actual = MeshCoord(0, 0, 9).next_up(1)
        expected = MeshCoord(0, 1, 0)
        self.assertEqual(expected, actual, msg="carry case of 1")

        actual = MeshCoord(0, 7, 9).next_up(1)
        expected = MeshCoord(1, 0, 0)
        self.assertEqual(expected, actual, msg="carry case of 1")

        actual = MeshCoord(0, 0, 5).next_up(5)
        expected = MeshCoord(0, 1, 0)
        self.assertEqual(expected, actual, msg="carry case of 5")

        actual = MeshCoord(0, 7, 5).next_up(5)
        expected = MeshCoord(1, 0, 0)
        self.assertEqual(expected, actual, msg="carry case of 5")

        # error
        with self.assertRaises(ValueError, msg="error"):
            MeshCoord(0, 7, 2).next_up(5)

        with self.assertRaises(TypeError, msg="error"):
            MeshCoord(0, 0, 0).next_up(2)

        with self.assertRaises(OverflowError, msg="error"):
            MeshCoord(99, 7, 9).next_up(1)
        with self.assertRaises(OverflowError, msg="error"):
            MeshCoord(99, 7, 5).next_up(5)

    def test_next_down(self):
        # decrement
        actual = MeshCoord(0, 0, 1).next_down(1)
        expected = MeshCoord(0, 0, 0)
        self.assertEqual(expected, actual, msg="trivial case")

        actual = MeshCoord(0, 0, 5).next_down(5)
        expected = MeshCoord(0, 0, 0)
        self.assertEqual(expected, actual, msg="trivial case")

        # carry case of 1
        actual = MeshCoord(0, 1, 0).next_down(1)
        expected = MeshCoord(0, 0, 9)
        self.assertEqual(expected, actual, msg="carry case of 1")

        actual = MeshCoord(1, 0, 0).next_down(1)
        expected = MeshCoord(0, 7, 9)
        self.assertEqual(expected, actual, msg="carry case of 1")

        actual = MeshCoord(0, 1, 0).next_down(5)
        expected = MeshCoord(0, 0, 5)
        self.assertEqual(expected, actual, msg="carry case of 5")

        actual = MeshCoord(1, 0, 0).next_down(5)
        expected = MeshCoord(0, 7, 5)
        self.assertEqual(expected, actual, msg="carry case of 5")

        # error
        with self.assertRaises(ValueError, msg="error"):
            MeshCoord(0, 7, 2).next_down(5)

        with self.assertRaises(TypeError, msg="error"):
            MeshCoord(0, 0, 0).next_down(2)

    def test_identity_on_coord_to_lat_lng(self):
        bound = MeshCoord(99, 7, 9)
        coord = MeshCoord(0, 0, 0)
        while coord < bound:
            with self.subTest(kind="latitude", node=coord, v=str(coord.to_latitude())):
                self.assertEqual(coord, MeshCoord.from_latitude(coord.to_latitude(), 1))
            coord = coord.next_up(1)
        else:
            with self.subTest(kind="latitude", node=coord, v=str(coord.to_latitude())):
                self.assertEqual(coord, MeshCoord.from_latitude(coord.to_latitude(), 1))

        bound = MeshCoord(80, 0, 0)
        coord = MeshCoord(0, 0, 0)
        while coord < bound:
            with self.subTest(kind="longitude", node=coord, v=str(coord.to_longitude())):
                self.assertEqual(coord, MeshCoord.from_longitude(coord.to_longitude(), 1))
            coord = coord.next_up(1)
        else:
            with self.subTest(kind="latitude", node=coord, v=str(coord.to_latitude())):
                self.assertEqual(coord, MeshCoord.from_longitude(coord.to_longitude(), 1))


class MeshNodeTest(unittest.TestCase):
    def test_init(self):
        coord = MeshCoord(0, 0, 0)
        while coord != MeshCoord(80, 0, 0):
            with self.subTest():
                MeshNode(MeshCoord(0, 0, 0), coord)
            coord = coord.next_up(1)

        # case: MeshCoord(80, 0, 0)
        MeshNode(MeshCoord(0, 0, 0), coord)
        coord = coord.next_up(1)

        while coord != MeshCoord(99, 7, 9):
            with self.subTest():
                with self.assertRaises(ValueError):
                    MeshNode(MeshCoord(0, 0, 0), coord)
            coord = coord.next_up(1)

        # case: MeshCoord(99, 7, 9)
        with self.assertRaises(ValueError):
            MeshNode(MeshCoord(0, 0, 0), coord)

    def test_is_unit(self):
        node = MeshNode.from_meshcode(54401027)
        self.assertTrue(node.is_mesh_unit(1))
        self.assertFalse(node.is_mesh_unit(5))

    def test_from_code(self):
        actual = MeshNode.from_meshcode(54401027)
        expected = MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7))
        self.assertEqual(expected, actual)

        sample = [
            (544010270,),
            (-1,),
        ]
        for args in sample:
            with self.subTest():
                with self.assertRaises(ValueError) as cm:
                    MeshNode.from_meshcode(*args)

        with self.assertRaises(ValueError) as cm:
            MeshNode.from_meshcode(10000_00_00)

    def test_from_point(self):
        point = Point(36.103774791666666, 140.08785504166664, 10.0)

        expected = MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7))
        actual = MeshNode.from_point(point, 1)
        self.assertEqual(expected, actual)

        expected = MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 0, 5))
        actual = MeshNode.from_point(point, 5)
        self.assertEqual(expected, actual)

        with self.assertRaises(TypeError):
            MeshNode.from_point(point, 2)

    def test_from_pos(self):
        lat, lng = 36.103774791666666, 140.08785504166664

        expected = MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7))
        actual = MeshNode.from_pos(lat, lng, 1)
        self.assertEqual(expected, actual)

        expected = MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 0, 5))
        actual = MeshNode.from_pos(lat, lng, 5)
        self.assertEqual(expected, actual)

        with self.assertRaises(TypeError):
            MeshNode.from_pos(lat, lng, 2)

    def test_to_code(self):
        expected = 54401027
        actual = MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)).to_meshcode()
        self.assertEqual(expected, actual)

    def test_to_point(self):
        expected = Point(latitude=36.1, longitude=140.0875, altitude=0.0)
        actual = MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)).to_point()
        self.assertEqual(expected, actual)

    def test_to_pos(self):
        expected = (36.1, 140.0875)
        actual = MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)).to_pos()
        self.assertEqual(expected, actual)

    def test_identity_on_node_to_code(self):
        bound = MeshNode(MeshCoord(0, 0, 0), MeshCoord(80, 0, 0))
        node = MeshNode(MeshCoord(0, 0, 0), MeshCoord(0, 0, 0))
        while node != bound:
            with self.subTest():
                self.assertEqual(node, MeshNode.from_meshcode(node.to_meshcode()))
            node = MeshNode(node.latitude, node.longitude.next_up(1))
        with self.subTest():
            self.assertEqual(node, MeshNode.from_meshcode(node.to_meshcode()))

        bound = MeshNode(MeshCoord(99, 7, 9), MeshCoord(0, 0, 0))
        node = MeshNode(MeshCoord(0, 0, 0), MeshCoord(0, 0, 0))
        while node != bound:
            with self.subTest():
                self.assertEqual(node, MeshNode.from_meshcode(node.to_meshcode()))
            node = MeshNode(node.latitude.next_up(1), node.longitude)
        with self.subTest():
            self.assertEqual(node, MeshNode.from_meshcode(node.to_meshcode()))


class MeshCellTest(unittest.TestCase):
    def test_init(self):
        with self.assertRaises(ValueError):
            MeshCell(
                south_west=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)),
                south_east=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 8)),
                north_west=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 7)),
                north_east=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 8)),
                mesh_unit=5,
            )
        with self.assertRaises(ValueError):
            MeshCell(
                south_west=MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 0, 5)),
                south_east=MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 1, 0)),
                north_west=MeshNode(MeshCoord(54, 1, 5), MeshCoord(40, 0, 5)),
                north_east=MeshNode(MeshCoord(54, 1, 5), MeshCoord(40, 1, 0)),
                mesh_unit=1,
            )

        # longitude
        with self.assertRaises(ValueError):
            MeshCell(
                south_west=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)),
                south_east=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)),
                north_west=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 7)),
                north_east=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 8)),
                mesh_unit=1,
            )
        with self.assertRaises(ValueError):
            MeshCell(
                south_west=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)),
                south_east=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 8)),
                north_west=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 6)),
                north_east=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 8)),
                mesh_unit=5,
            )
        with self.assertRaises(ValueError):
            MeshCell(
                south_west=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)),
                south_east=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 8)),
                north_west=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 7)),
                north_east=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 7)),
                mesh_unit=5,
            )

        # latitude
        with self.assertRaises(ValueError):
            MeshCell(
                south_west=MeshNode(MeshCoord(54, 1, 1), MeshCoord(40, 0, 7)),
                south_east=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 8)),
                north_west=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 7)),
                north_east=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 8)),
                mesh_unit=5,
            )
        with self.assertRaises(ValueError):
            MeshCell(
                south_west=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)),
                south_east=MeshNode(MeshCoord(54, 1, 1), MeshCoord(40, 0, 8)),
                north_west=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 7)),
                north_east=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 8)),
                mesh_unit=5,
            )
        with self.assertRaises(ValueError):
            MeshCell(
                south_west=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)),
                south_east=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 8)),
                north_west=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)),
                north_east=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 8)),
                mesh_unit=5,
            )
        with self.assertRaises(ValueError):
            MeshCell(
                south_west=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)),
                south_east=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 8)),
                north_west=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 7)),
                north_east=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 8)),
                mesh_unit=5,
            )

    def test_from_code(self):
        actual = MeshCell.from_meshcode(54401027, mesh_unit=1)
        expected = MeshCell(
            south_west=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)),
            south_east=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 8)),
            north_west=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 7)),
            north_east=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 8)),
            mesh_unit=1,
        )
        self.assertEqual(expected, actual)

        actual = MeshCell.from_meshcode(54401005, mesh_unit=5)
        expected = MeshCell(
            south_west=MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 0, 5)),
            south_east=MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 1, 0)),
            north_west=MeshNode(MeshCoord(54, 1, 5), MeshCoord(40, 0, 5)),
            north_east=MeshNode(MeshCoord(54, 1, 5), MeshCoord(40, 1, 0)),
            mesh_unit=5,
        )
        self.assertEqual(expected, actual)

        with self.assertRaises(ValueError):
            MeshCell.from_meshcode(54401027, mesh_unit=5)

        with self.assertRaises(TypeError):
            MeshCell.from_meshcode(54401027, mesh_unit=2)

    def test_from_point(self):
        point = Point(36.10377479, 140.087855041, 10.0)

        actual = MeshCell.from_point(point, mesh_unit=1)
        expected = MeshCell(
            south_west=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)),
            south_east=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 8)),
            north_west=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 7)),
            north_east=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 8)),
            mesh_unit=1,
        )
        self.assertEqual(expected, actual)

        actual = MeshCell.from_point(point, mesh_unit=5)
        expected = MeshCell(
            south_west=MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 0, 5)),
            south_east=MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 1, 0)),
            north_west=MeshNode(MeshCoord(54, 1, 5), MeshCoord(40, 0, 5)),
            north_east=MeshNode(MeshCoord(54, 1, 5), MeshCoord(40, 1, 0)),
            mesh_unit=5,
        )
        self.assertEqual(expected, actual)

        with self.assertRaises(TypeError):
            MeshCell.from_point(point, mesh_unit=2)

    def test_from_pos(self):
        lat, lng = 36.10377479, 140.087855041

        actual = MeshCell.from_pos(lat, lng, mesh_unit=1)
        expected = MeshCell(
            south_west=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)),
            south_east=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 8)),
            north_west=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 7)),
            north_east=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 8)),
            mesh_unit=1,
        )
        self.assertEqual(expected, actual)

        actual = MeshCell.from_pos(lat, lng, mesh_unit=5)
        expected = MeshCell(
            south_west=MeshNode(mesh.MeshCoord(54, 1, 0), MeshCoord(40, 0, 5)),
            south_east=MeshNode(mesh.MeshCoord(54, 1, 0), MeshCoord(40, 1, 0)),
            north_west=MeshNode(mesh.MeshCoord(54, 1, 5), MeshCoord(40, 0, 5)),
            north_east=MeshNode(mesh.MeshCoord(54, 1, 5), MeshCoord(40, 1, 0)),
            mesh_unit=5,
        )
        self.assertEqual(expected, actual)

        with self.assertRaises(TypeError):
            MeshCell.from_pos(lat, lng, mesh_unit=2)

    def test_from_node(self):
        node = MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7))
        actual = MeshCell.from_node(node, mesh_unit=1)
        expected = MeshCell(
            south_west=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7)),
            south_east=MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 8)),
            north_west=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 7)),
            north_east=MeshNode(MeshCoord(54, 1, 3), MeshCoord(40, 0, 8)),
            mesh_unit=1,
        )
        self.assertEqual(expected, actual)

        node = MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 0, 5))
        actual = MeshCell.from_node(node, mesh_unit=5)
        expected = MeshCell(
            south_west=MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 0, 5)),
            south_east=MeshNode(MeshCoord(54, 1, 0), MeshCoord(40, 1, 0)),
            north_west=MeshNode(MeshCoord(54, 1, 5), MeshCoord(40, 0, 5)),
            north_east=MeshNode(MeshCoord(54, 1, 5), MeshCoord(40, 1, 0)),
            mesh_unit=5,
        )
        self.assertEqual(expected, actual)

        node = MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7))
        with self.assertRaises(ValueError):
            MeshCell.from_node(node, mesh_unit=5)

        with self.assertRaises(TypeError):
            MeshCell.from_node(node, mesh_unit=2)

    def test_position_in_cell(self):
        lat, lng = 36.10377479, 140.087855041
        cell = MeshCell.from_pos(lat, lng, mesh_unit=1)

        actual = cell.position(lat, lng)
        expected = (0.4529748000001632, 0.028403280000475206)
        self.assertEqual(expected, actual)

        cell = MeshCell.from_pos(lat, lng, mesh_unit=5)
        actual = cell.position(lat, lng)
        expected = (0.4905949600000099, 0.405680656000186)
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
