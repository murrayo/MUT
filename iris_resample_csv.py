#!/usr/bin/env python3

# iris_resample_csv.py -d directory_with_csv_files

import pandas as pd
import os
import glob
from functools import reduce
import argparse

def mainline(FILEPATH):

    # This script depends on files being named as below:
    
    filenames = glob.glob(FILEPATH+"/*stat*.csv")
    filenames.sort(reverse=True)
    
    # Build a master list of dataframes for each csv file.
    # This is nice because you dont care whether its 2 or 20, eg with shards.
    
    list_of_dfs = [pd.read_csv(filename) for filename in filenames]
    
    for dataframe, filename in zip(list_of_dfs, filenames):
    
        dataframe = pd.read_csv(filename, parse_dates=['datetime'])
        dataframe.datetime = pd.to_datetime(dataframe.datetime) 
        
        # Left here as a reference for a way to downsample
        #dataframe = dataframe.reset_index().set_index('datetime').resample('1S').interpolate(method='linear')
        
        # This resample at same sample size and base=0
        # will realign starting on 0, eg 00:01:06 will end up as 12:01:05 am
        
        dataframe = dataframe.reset_index().set_index('datetime').resample('5S', base=0).mean()       
        dataframe = dataframe.drop('index',1)   
        dataframe = dataframe.dropna()          # mgstat sometimes drops times
        
        new_name = os.path.basename(filename)
        print(new_name)
        
        os.makedirs(os.path.dirname(FILEPATH+"/resampled/"), exist_ok=True)
        
        dataframe.to_csv(FILEPATH+"/resampled/aligned_"+new_name , sep=',', index=True)       
    
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Combine any number of csv files")
    parser.add_argument("-d", "--directory", help="directory with ^SystemPerformance csv files")    
    args = parser.parse_args()
    
    if args.directory is not None:
        FILEPATH = args.directory
    else:
        print('Error: -d "Directory containing csv files"')
        exit(0)
 
    try:
         mainline(FILEPATH)       
    except OSError as e:
        print('Could not process files because: {}'.format(str(e)))
