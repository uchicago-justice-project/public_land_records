import pandas as pd
import numpy as np

import argparse

def get_arguments():
    parser = argparse.ArgumentParser(description='cleans tract data scraped from\
         ilsos website')

    parser.add_argument("input_file")
    parser.add_argument("output_file")

    args = parser.parse_args()

    return args.input_file, args.output_file



if __name__ == "__main__":
    input_file, output_file = get_arguments()

    df = pd.read_csv(input_file)
    df.drop_duplicates(inplace=True)
    df['Voided'] = (df['Aliquot Parts or Lot'].str.contains("VO")) | \
        (df['Aliquot Parts or Lot'].str[-1] == 'V')
    df.drop_duplicates(subset=["Purchaser", "Aliquot Parts or Lot", 'Section Number',\
         'Township', 'Range', 'Meridian', 'Voided'], inplace=True)

    df['Date'] = pd.to_datetime(df['Date of Purchase'], errors="coerce")
    df['Year'] = df['Date'].dt.year

    df.to_csv(output_file)
