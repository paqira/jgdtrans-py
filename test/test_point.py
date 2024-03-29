import unittest

from JGDtrans import Point, mesh
from JGDtrans import point as _point
from JGDtrans.mesh import MeshCoord, MeshNode


class Normalize(unittest.TestCase):
    def test_latitude(self):
        cases = [
            (35.0, 35.0),
            (-35.0, -35.0),
            (80.0, 100.0),
            (-10.0, 190.0),
            (-80.0, -100.0),
            (10.0, -190.0),
        ]
        for e, a in cases:
            self.assertEqual(e, _point.normalize_latitude(a))

    def test_longitude(self):
        cases = [
            (145.0, 145.0),
            (-145.0, -145.0),
            (-170.0, 190.0),
            (170.0, -190.0),
        ]
        for e, a in cases:
            self.assertEqual(e, _point.normalized_longitude(a))


class Point_(unittest.TestCase):
    def test_init(self):
        for e, v in (
            (0, 0),
            (-0, -0),
            (20, 20),
            (-20, -20),
            (0, 360),
            (-90, 270),
            (0, 180),
            (90, 90),
            (-0, -360),
            (90, -270),
            (-0, -180),
            (-90, -90),
            (20, 360 + 20),
            (-70, 270 + 20),
            (-20, 180 + 20),
            (70, 90 + 20),
            (-20, -360 - 20),
            (70, -270 - 20),
            (20, -180 - 20),
            (-70, -90 - 20),
        ):
            actual = Point(v, 0)
            expected = Point(e, 0)
            self.assertEqual(expected, actual)

        for e, v in (
            (0, 0),
            (-0, -0),
            (20, 20),
            (-20, -20),
            (0, 360),
            (-90, 270),
            (180, 180),
            (90, 90),
            (-0, -360),
            (90, -270),
            (-180, -180),
            (-90, -90),
            (20, 360 + 20),
            (-70, 270 + 20),
            (-160, 180 + 20),
            (110, 90 + 20),
            (-20, -360 - 20),
            (70, -270 - 20),
            (160, -180 - 20),
            (-110, -90 - 20),
        ):
            actual = Point(0, v)
            expected = Point(0, e)
            self.assertEqual(expected, actual)

    def test_from_mesh_node(self):
        node = MeshNode(MeshCoord(54, 1, 2), MeshCoord(40, 0, 7))
        actual = Point.from_node(node)
        expected = Point(latitude=36.1, longitude=140.0875, altitude=0.0)
        self.assertEqual(expected, actual)

    def test_from_key(self):
        actual = Point.from_meshcode(54401027)
        expected = Point(latitude=36.1, longitude=140.0875, altitude=0.0)
        self.assertEqual(expected, actual)

    def test_mesh_cell(self):
        point = Point(36.103774791666666, 140.08785504166664, 10.0)

        actual = point.mesh_cell(unit=1)
        expected = mesh.MeshCell(
            sw=mesh.MeshNode(mesh.MeshCoord(54, 1, 2), mesh.MeshCoord(40, 0, 7)),
            se=mesh.MeshNode(mesh.MeshCoord(54, 1, 2), mesh.MeshCoord(40, 0, 8)),
            nw=mesh.MeshNode(mesh.MeshCoord(54, 1, 3), mesh.MeshCoord(40, 0, 7)),
            ne=mesh.MeshNode(mesh.MeshCoord(54, 1, 3), mesh.MeshCoord(40, 0, 8)),
            unit=1,
        )
        self.assertEqual(expected, actual, msg="unit 1")

        actual = point.mesh_cell(unit=5)
        expected = mesh.MeshCell(
            sw=mesh.MeshNode(mesh.MeshCoord(54, 1, 0), mesh.MeshCoord(40, 0, 5)),
            se=mesh.MeshNode(mesh.MeshCoord(54, 1, 0), mesh.MeshCoord(40, 1, 0)),
            nw=mesh.MeshNode(mesh.MeshCoord(54, 1, 5), mesh.MeshCoord(40, 0, 5)),
            ne=mesh.MeshNode(mesh.MeshCoord(54, 1, 5), mesh.MeshCoord(40, 1, 0)),
            unit=5,
        )
        self.assertEqual(expected, actual, msg="unit 5")

        with self.assertRaises(ValueError):
            point.mesh_cell(unit=2)


if __name__ == "__main__":
    unittest.main()
