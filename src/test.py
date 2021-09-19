import unittest

from main import *


class DistanceCalculatorTest(unittest.TestCase):

    def setUp(self):
        self.dc = DistanceCalculator()

    def test_angle_of_vector(self):
        # test for basic angles - there is a shift towards the center of the MKAD
        self.assertEqual(90.0, self.dc.angle_of_vector(0.0 + self.dc.center[1], 1.0 + self.dc.center[2]))
        self.assertEqual(180.0, self.dc.angle_of_vector(-1.0 + self.dc.center[1], 0.0 + self.dc.center[2]))
        self.assertEqual(270.0, self.dc.angle_of_vector(0.0 + self.dc.center[1], -1.0 + self.dc.center[2]))

    def test_do_intersect(self):
        # test if 2 segments intersects
        self.assertEqual(False, do_intersect(3.0, 3.0, 2.0, 1.0, 1.0, 2.0, 1.0, 1.0))
        self.assertEqual(True, do_intersect(4.0, 2.0, 2.0, 1.0, 1.0, 2.0, 3.0, 1.0))
        self.assertEqual(True, do_intersect(3.0, 1.0, 3.0, 3.0, 4.0, 2.0, 2.0, 2.0))

    def test_outside_bounding_box(self):
        # Inside bounding box - Moscow coordinates -> "latitude": 55.741469, "longitude": 37.615561
        self.assertEqual(False, self.dc.outside_bounding_box(37.615561, 55.741469))
        # On the line of bounding box, 4 corners
        self.assertEqual(False, self.dc.outside_bounding_box(self.dc.maxlong, self.dc.maxlat))
        self.assertEqual(False, self.dc.outside_bounding_box(self.dc.maxlong, self.dc.minlat))
        self.assertEqual(False, self.dc.outside_bounding_box(self.dc.minlong, self.dc.maxlat))
        self.assertEqual(False, self.dc.outside_bounding_box(self.dc.maxlong, self.dc.minlat))
        # Outside bounding box - Budapest coordinates -> "latitude": 47.516581, "longitude": 19.092281
        self.assertEqual(True, self.dc.outside_bounding_box(19.092281, 47.516581))

    def test_find_two_closest_point(self):
        # the average of the 2 adjacent point should have these 2 points as closest points
        for i in range(len(mkad_km)):
            if i < len(mkad_km)-1:
                index2 = i+1
            else:
                index2 = 0
            x = (mkad_km[i][1] + mkad_km[index2][1]) / 2
            y = (mkad_km[i][2] + mkad_km[index2][2]) / 2
            angle = self.dc.angle_of_vector(x, y)
            a, b = self.dc.find_two_closest_point(angle)
            self.assertEqual(True, mkad_km[i][0] in {a[0], b[0]})
            self.assertEqual(True, mkad_km[index2][0] in {a[0], b[0]})

    def test_inside_mkad(self):
        self.assertEqual(False, self.dc.inside_mkad(self.dc.maxlong, self.dc.maxlat))
        # Test that any point in mkad_km is inside MKAD
        for record in mkad_km:
            self.assertEqual(True, self.dc.inside_mkad(record[1], record[2]))
        # Moscow coordinates ("latitude": 55.741469, "longitude": 37.615561) are inside MKAD
        self.assertEqual(True, self.dc.inside_mkad(37.615561, 55.741469))
        # Center of MKAD
        self.assertEqual(True, self.dc.inside_mkad(self.dc.center[1], self.dc.center[2]))

        min_v1 = 100.0
        max_v1 = 0.0
        for record in mkad_km:
            v1, v2 = record[1] - self.dc.center[1], record[2] - self.dc.center[2]
            # any point shifted with its distance from the center should be outside of MKAD
            self.assertEqual(False, self.dc.inside_mkad(record[1] + v1, record[2] + v2))
            # min and max search
            if np.abs(v1) < min_v1:
                min_v1 = np.abs(v1)
            if np.abs(v1) > max_v1:
                max_v1 = np.abs(v1)

        # min distance for longitude should be inside
        self.assertEqual(True, self.dc.inside_mkad(self.dc.center[1] + min_v1, self.dc.center[2]))
        self.assertEqual(True, self.dc.inside_mkad(self.dc.center[1] - min_v1, self.dc.center[2]))

        # max distance for longitude should be outside (with a really small shift)
        self.assertEqual(False, self.dc.inside_mkad(self.dc.center[1] + max_v1 + 0.0000001, self.dc.center[2]))
        self.assertEqual(False, self.dc.inside_mkad(self.dc.center[1] - max_v1 - 0.0000001, self.dc.center[2]))

if __name__ == '__main__':
    unittest.main()
