import geopandas
import numpy as np
import math
from shapely.geometry import LineString, MultiPolygon, Polygon, Point, box
from shapely.ops import split, linemerge, unary_union, polygonize
from functools import cmp_to_key


earth_radius = 3960.0
degrees_to_radians = math.pi/180.0
radians_to_degrees = 180.0/math.pi

def change_in_latitude(miles):
    "Given a distance north, return the change in latitude."
    return (miles/earth_radius)*radians_to_degrees

def change_in_longitude(latitude, miles):
    "Given a latitude and a distance west, return the change in longitude."
    # Find the radius of a circle around the earth at given latitude.
    r = earth_radius*math.cos(latitude*degrees_to_radians)
    return (miles/r)*radians_to_degrees

def split_polygon(polygon, nx, ny):
    minx, miny, maxx, maxy = polygon.bounds
    dx = (maxx - minx) / nx  # width of a small part
    dy = (maxy - miny) / ny  # height of a small part
    horizontal_splitters = [LineString([(minx, miny + i*dy), (maxx, miny + i*dy)]) for i in range(ny)]
    vertical_splitters = [LineString([(minx + i*dx, miny), (minx + i*dx, maxy)]) for i in range(nx)]
    splitters = horizontal_splitters + vertical_splitters
    result = polygon
    for splitter in splitters:
        result = MultiPolygon(split(result, splitter))
    return result


def southwest_to_northeast(a, b):
    if np.isclose(a.bounds[1], b.bounds[1], atol=0.001):
        if a.bounds[0] < b.bounds[0]:
            return -1
        else:
            return 1
    if a.bounds[1] < b.bounds[1]:
        return -1
    return 1


def ns(a, b):
    return b.bounds[3] - a.bounds[3]

def ew(a, b):
    return b.bounds[2] - a.bounds[2]

def we(a, b):
    return a.bounds[0] - b.bounds[0]

def sn(a, b):
    return a.bounds[1] - b.bounds[1]

rows_dict = {
    "NE": (ew, we, ns),
    "NW": (we, ew, ns),
    "SE": (ew, we, sn),
    "SW": (we, ew, sn)
}

cols_dict = {
    "NE": (ns, sn, ew),
    "NW": (ns, sn, we),
    "SE": (sn, ns, ew),
    "SW": (sn, ns, we)
}

def snake_sort(polygons, snake_length, starting_position, cols=False):
    funcs = rows_dict[starting_position]
    if cols:
        funcs = cols_dict[starting_position]

    new_polygons = []
    polygon_arrays = np.array_split(sorted(polygons, key=cmp_to_key(funcs[2])), math.ceil(len(polygons)/snake_length))
    func_no = 0

    for polygon_array in polygon_arrays:
        new_polygons.extend(sorted(polygon_array.tolist(), key=cmp_to_key(funcs[func_no])))
        func_no = (func_no + 1) % 2

    return new_polygons
