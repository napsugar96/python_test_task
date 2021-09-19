from flask import Flask, request
import numpy as np
import math
import haversine as hs

from mkad_points import *
from geocoding import *

app = Flask(__name__)


def do_intersect(X1, Y1, X2, Y2, X3, Y3, X4, Y4) -> bool:
    """ Calculate if 2 segments intersect
        Segment1: (x1, y1) - (x2, y2)
        Segment2: (x3, y3) - (x4, y4)
    """

    point_set = set([(X1, Y1), (X2, Y2), (X3, Y3), (X4, Y4)])
    if len(point_set) < 4:
        # if any point is the same as other, then the point should be inside mkad
        return False

    if max(X1, X2) < min(X3, X4):
        return False

    if X1 - X2 == 0 and X3 - X4 == 0:
        return False

    # Not divide by zero
    if X1 - X2 == 0:
        if min(X3, X4) <= X1 <= max(X3, X4) and (not min(Y1, Y2) > max(Y3, Y4) or not max(Y1, Y2) < min(Y3, Y4)):
            return True
        else:
            return False
    # Not divide by zero
    if X3 - X4 == 0:
        if min(X1, X2) <= X3 <= max(X1, X2) and (not min(Y3, Y4) > max(Y1, Y2) or not max(Y3, Y4) < min(Y1, Y2)):
            return True
        else:
            return False

    A1 = (Y1 - Y2) / (X1 - X2)
    A2 = (Y3 - Y4) / (X3 - X4)

    if A1 == A2:
        return False  # Parallel segments

    b1 = Y1 - A1 * X1
    b2 = Y3 - A2 * X3

    Xa = (b2 - b1) / (A1 - A2)

    if ((Xa < max(min(X1, X2), min(X3, X4))) or
            (Xa > min(max(X1, X2), max(X3, X4)))):
        return False  # intersection is out of bound
    else:
        return True


class DistanceCalculator:
    """Class for calculate distance from given address to MKAD"""

    def __init__(self):
        """ Initialize values for further calculation of bounding box and two closest points"""
        self.mkad_np = np.array(mkad_km)
        amin = np.amin(self.mkad_np, 0)
        amax = np.amax(self.mkad_np, 0)
        self.minlong = amin[1]
        self.maxlong = amax[1]
        self.minlat = amin[2]
        self.maxlat = amax[2]
        self.center = np.mean(self.mkad_np, 0)
        self.mkad_angles = self.angle_of_mkad_points()
        print("DistanceCalculator setup OK")

    def angle_of_mkad_points(self) -> np.array:
        """ Calculates the angle of all the points of MKAD and stores them in degree format in ascendant order."""
        result = []
        for record in mkad_km:
            result.append([record[0], self.angle_of_vector(record[1], record[2])])

        result = np.array(result)
        # sort array by angle
        result = result[result[:, 1].argsort()]
        return result

    def post(self, address: str) -> bool:
        """ Get the coordinates of the given address and calculate the distance from MKAD if it is outside.
            Write the result in the .log file.
            Returns True if there was no error during the geocoding of the address.
        """
        print("POST request inside")
        print("address", address)
        geo_location = get_geocode(address)
        long, lat = get_location(geo_location)
        if long is None:
            return False

        if self.inside_mkad(long, lat):
            print("the adress is inside MKAD.")
        else:
            print("long, lat", long, lat)
            distance = self.min_distance_from_mkad((long, lat))
            with open('log.log', 'a') as file:
                file.write("Address: " + address + " distance to MKAD: " + str(distance) + " km\n")
            print("distance:", distance)
        return True

    def angle_of_vector(self, x: float, y: float) -> float:
        """ Calculate the angle of a vector which is shifted by the center of MKAD ring"""
        radian_value = math.atan2(y - self.center[2], x - self.center[1])
        degrees = math.degrees(radian_value)
        degrees = degrees if degrees >= 0 else degrees + 360
        return degrees

    def inside_mkad(self, long: float, lat: float) -> bool:
        """ Returns True if the coordinate (longitude, latitude) is inside MKAD. """
        if self.outside_bounding_box(long, lat):
            return False

        angle_of_address = self.angle_of_vector(long, lat)
        bigger, smaller = self.find_two_closest_point(angle_of_address)

        if do_intersect(long, lat, self.center[1], self.center[2], bigger[1], bigger[2], smaller[1], smaller[2]):
            return False
        else:
            return True

    def find_two_closest_point(self, angle: float):
        """ Returns 2 points which has the nearest angle compared to the given "angle" parameter.  """
        bigger = self.mkad_angles[np.where(self.mkad_angles[:, 1] >= angle)]
        smaller = self.mkad_angles[np.where(self.mkad_angles[:, 1] < angle)]
        if len(bigger) == 0:
            bigger = self.mkad_angles[0]
        else:
            bigger = bigger[0]

        if len(smaller) == 0:
            smaller = self.mkad_angles[-1]
        else:
            smaller = smaller[-1]
        return self.mkad_np[round(bigger[0] - 1)], self.mkad_np[round(smaller[0] - 1)]

    def outside_bounding_box(self, long: float, lat: float) -> bool:
        """ Returns True if a coordinate (longitude, latitude) is outside of the minimum bounding rectangle of MKAD."""
        if long < self.minlong or long > self.maxlong or lat < self.minlat or lat > self.maxlat:
            return True
        else:
            return False

    def min_distance_from_mkad(self, loc: (float, float)) -> float:
        """ Calculate the distance between the address and all the points of MKAD in kilometers.
            Returns the smallest distance. """

        def distance(y): return hs.haversine(loc, (y[1], y[2]))

        distances = np.apply_along_axis(distance, 1, self.mkad_np)
        return np.min(distances)


dc = DistanceCalculator()


@app.route('/', methods=['POST'])
def post_address():
    content = request.get_json()
    print(content)
    if "address" in content:
        print(content["address"])
        if dc.post(address=content["address"]):
            return '', 204
        else:
            return 'Invalid address!', 400
    else:
        return 'Invalid HTTP Request Body! Example of messsage body: {"address": "Moscow"}', 400


if __name__ == '__main__':
    app.run(debug=True)
