import numpy as np
import geopandas as gpd
from shapely.geometry import box
from shapely.ops import unary_union
from polygons import change_in_latitude, change_in_longitude, split_polygon, southwest_to_northeast
from functools import cmp_to_key

import argparse
import math


def get_arguments():
    parser = argparse.ArgumentParser(description='splits sections into sixteenths')

    parser.add_argument("input_file")
    parser.add_argument("output_file")

    args = parser.parse_args()

    return args.input_file, args.output_file


def get_indian_boundary_line_pos(gdf):
    ind_boundary = gpd.read_file("../data/ill_ind_boundary_line.json")
    line = unary_union(ind_boundary['geometry'])

    gdf['IBL'] = np.nan

    for idx, row in gdf.iterrows():
        if row.geometry.intersects(line):
            ibl = 'NIBL' if row.geometry.centroid.bounds[-1] > \
            row.geometry.intersection(line).centroid.bounds[-1] else 'SIBL'

            gdf.loc[idx, 'IBL'] = ibl


def quarter_polygon(polygon, ibl, lat_dist, long_dist):
    lat = change_in_latitude(lat_dist)
    new_polygon = split_polygon(polygon, 2, 2)
    polygons = (list(new_polygon.geoms))
    if len(polygons) != 4 or not math.isclose(polygon.minimum_rotated_rectangle.area,\
         polygon.area, rel_tol = polygon.area * .4):
        w, s, e, n = polygon.bounds
        miny = s
        maxy = s + lat
        minx = w
        maxx = w + change_in_longitude(s, long_dist)
        if ibl == 'NIBL':
            miny = n - lat
            maxy = n
            minx = w
            maxx = w + change_in_longitude(n, long_dist)
        elif ibl == 'SIBL':
            miny = s
            maxy = s + lat
            minx = e - change_in_longitude(s, long_dist)
            maxx = e

        new_polygon = split_polygon(box(minx, miny, maxx, maxy), 2, 2)
        polygons = (list(new_polygon.geoms))

    return sorted(polygons, key=cmp_to_key(southwest_to_northeast))

def get_sixteenth_sections(gdf):
    quadrant_set = [
    'SW',
    'SE',
    'NW',
    'NE']

    sixteenth_set = []

    for d1 in quadrant_set:
        for d2 in quadrant_set:
            sixteenth_set.append(d1+d2)

    quadrants = []
    townships = []
    ranges = []
    geometries = []
    section_nums = []
    indian_boundary = []
    old_objectids = []

    for idx, row in gdf.iterrows():
        ibl = row['IBL']
        quarters = quarter_polygon(row.geometry, ibl, 1, 1)

        for poly in quarters:
            sixteenths = quarter_polygon(poly, ibl, 0.5, 0.5)
            geometries.extend(sixteenths)

        quadrants.extend(sixteenth_set)
        townships.extend([row['TWPNUM'] for _ in range(16)])
        ranges.extend([row['RNGNUM'] for _ in range(16)])
        section_nums.extend([row['SECTION'] for _ in range(16)])
        indian_boundary.extend([ibl for _ in range(16)])
        old_objectids.extend([idx for _ in range(16)])


    data = {
        'TWPNUM': townships,
        'RNGNUM': ranges,
        'SECTION': section_nums,
        'PART': quadrants,
        'INDIAN_BOUNDARY': indian_boundary,
        'OLD_OBJECTID' : old_objectids,
    }

    return gpd.GeoDataFrame(data, geometry=geometries, crs=gdf.crs)


def clip_excess_area(newgdf, oldgdf):
    data = {
        'TWPNUM': [],
        'RNGNUM': [],
        'SECTION': [],
        'PART': [],
        'INDIAN_BOUNDARY': [],
        'OLD_OBJECTID' : [],
    }

    lots = gpd.GeoDataFrame(data)

    for idx, row in oldgdf.iterrows():
        sect_mask = oldgdf.index == idx
        lots_mask = newgdf['OLD_OBJECTID'] == idx
        new_lots = newgdf[lots_mask].overlay(oldgdf[sect_mask][['geometry']], how="intersection")
        lots = lots.append(new_lots, ignore_index=False)

    lots.sort_values(inplace=True, by=['TWPNUM', 'RNGNUM', 'SECTION', 'PART', 'INDIAN_BOUNDARY'],\
                ascending=[True, True, True, True, True])

    # lots.drop_duplicates(inplace=True, subset=['TWPNUM', 'RNGNUM', 'SECTION', 'PART', 'INDIAN_BOUNDARY'])
    lots.set_crs(oldgdf.crs)
    return lots

if __name__ == "__main__":
    input_file, output_file = get_arguments()

    gdf = gpd.read_file(input_file)
    get_indian_boundary_line_pos(gdf)
    newgdf = get_sixteenth_sections(gdf)

    lots = clip_excess_area(newgdf, gdf)

    lots.to_file(output_file)
