import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union
from pyproj import Geod

import argparse


def get_arguments():
    parser = argparse.ArgumentParser(description='match tract purchases to geometry')

    parser.add_argument("input_records_file")
    parser.add_argument("input_geometries_file")
    parser.add_argument("output_csv_file")
    parser.add_argument("output_geo_file")


    args = parser.parse_args()

    return args.input_records_file, args.input_geometries_file,\
         args.output_csv_file, args.output_geo_file


class TooManyMatches(Exception):
    pass

class NoMatch(Exception):
    pass

class LotMatcher:
    def __init__(self, df, gdf) -> None:
        self.to_strip = ['2', '4', 'VOID', 'VO', "V", 'PRA', 'FR', 'TB', "MA", "TE", 'NIBL', 'SIBL','SC','SK',\
        "ROAD", "SR" "CALR","R", 'SCANAL','NCANAL','CANAL', 'SECT','SEC', 'DEA', 'FEED', 'PT']
        self.geod = Geod(ellps="WGS84")
        self.preprocessing(df, gdf)
        self.df = df
        self.gdf = gdf
        self.legit_sections = ['NW', "NE", "SW", "SE"]
        self.legit_directions = {'N' : ['NE', "NW"], "E": ['NE', "SE"],\
             "S": ['SE', 'SW'], "W": ['NW', 'SW']}


    def strip_common_strings(self, row):
        lot = row["Aliquot Parts or Lot"]
        acres = row["Acres"]
        if acres >=60 and acres < 100:
            lot = lot.replace("LOT2", "W")
            lot = lot.replace("LOT1", "E")
        for string in self.to_strip:
            lot = lot.replace(string, "")

        return lot

    def preprocessing(self, df, gdf):
        for col in ['TWPNUM', 'RNGNUM', "SECTION"]:
            gdf[col] = gdf[col].astype(int)

        try:
            df['Acres'] = df['Acres'].str.replace(" ", "")
        except:
            pass
        df['Acres'] = df['Acres'].astype(float)

        df.loc[df['Aliquot Parts or Lot'].str.contains('NIBL'), "IBL"] = 'NIBL'
        df.loc[df['Aliquot Parts or Lot'].str.contains('SIBL'), "IBL"] = 'SIBL'
        df.loc[df['IBL'].isnull(), "IBL"] = ''
        gdf.loc[gdf['INDIAN_BOUNDARY'].isnull(), "INDIAN_BOUNDARY"] = ''

        new_lots = df.apply(self.strip_common_strings, axis=1)


        df['part'] = new_lots


    def get_part_geometry(self, row, lot):
        twp = int(row['Township'][:-1])
        rng = int(row["Range"][:-1])
        sect = int(row['Section Number'])

        geometries = self.gdf.loc[(self.gdf['TWPNUM'] == twp)\
        &(self.gdf['RNGNUM'] == rng)\
        &(self.gdf['SECTION'] == sect)\
        &(self.gdf["PART"] == lot)
        &(self.gdf['INDIAN_BOUNDARY'] == row['IBL']),\
        'geometry'
        ].values

        if len(geometries) > 1:
            print(row)
            print(lot)
            raise TooManyMatches

        if len(geometries) < 1:
            raise NoMatch

        return geometries[0]

    def get_parts(self, row):
        part = row['part']

        try:
            if len(part) > 1 and len(part) < 5:
                first_sect = part[-2:]

                if first_sect not in self.legit_sections:
                    return None

                if len(part) == 4:
                    last_sect = part[:-2]

                    if last_sect not in self.legit_sections:
                        return None

                    return self.get_part_geometry(row, first_sect + last_sect)


                if len(part) == 3:
                    direc = part[0]
                    last_sects = self.legit_directions.get(direc)

                    if last_sects:
                        geometries = [self.get_part_geometry(row, first_sect + last_sect) for last_sect in last_sects]
                        return unary_union(geometries)

                if len(part) == 2:
                    geometries = [self.get_part_geometry(row, first_sect + last_sect) for last_sect in self.legit_sections]
                    return unary_union(geometries)

            elif len(part) == 1 and self.legit_directions.get(part):
                first_sects = self.legit_directions.get(part)
                geometries = []
                for first_sect in first_sects:
                    for last_sect in self.legit_sections:
                        geometries.append(self.get_part_geometry(row, first_sect+last_sect))

                return unary_union(geometries)

            elif row['Acres'] > 450:
                geometries = []
                for first_sect in self.legit_sections:
                    for last_sect in self.legit_sections:
                        geometries.append(self.get_part_geometry(row, first_sect+last_sect))

                return unary_union(geometries)

        except NoMatch:
            return None

        except TooManyMatches:
            return None


        return None

    def get_geometry(self, row):
        geometry = self.get_parts(row)

        if geometry:
            return geometry

        row['IBL'] = 'NIBL'
        geometry1 = self.get_parts(row)
        row['IBL'] = 'SIBL'
        geometry2 = self.get_parts(row)

        if not geometry1 and geometry2:
            return geometry2
        elif not geometry2 and geometry1:
            return geometry1
        elif geometry1 and geometry2:
            area1 = abs(self.geod.geometry_area_perimeter(geometry1)[0]) * 0.000247105
            area2 = abs(self.geod.geometry_area_perimeter(geometry2)[0]) * 0.000247105
            diff1 = abs(row['Acres'] - area1)
            diff2 = abs(row['Acres'] - area2)

            if diff1 < diff2:
                return geometry1
            elif diff2 < diff1:
                return geometry2

        return None

    def match(self):
        geometries = self.df.apply(lambda row : self.get_geometry(row), axis=1)
        self.df['geometry'] = geometries

        newgdf = gpd.GeoDataFrame(self.df)
        newgdf.set_geometry(col="geometry", inplace=True)

        return newgdf



if __name__ == "__main__":
    records_file, geometries_file, output_csv_file, output_geo_file = get_arguments()

    df = pd.read_csv(records_file)
    gdf = gpd.read_file(geometries_file)

    lot_matcher = LotMatcher(df, gdf)
    newgdf = lot_matcher.match()

    lot_matcher.df.to_csv(output_csv_file)
    newgdf.to_file(output_geo_file)
