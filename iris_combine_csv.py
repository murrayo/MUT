#!/usr/bin/env python3

# iris_combine_csv.py -d directory_with_csv_files

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
    # This is nice because you dont care whether its 2 or 20.
    
    list_of_dfs = [pd.read_csv(filename) for filename in filenames]
    
    for dataframe, filename in zip(list_of_dfs, filenames):
    
        # Sometimes work on files from dozens of sharded systems so need to identify them.    
        # Suffix is based on how I set up the prefix of the csv files, for example;
        #     yape -c --mgstat --vmstat --iostat --prefix "master_" *.html
        #     yape -c --mgstat --vmstat --iostat --prefix "shard1_" *.html        
    
        file_suffix = os.path.basename(filename).split("_")[0]
        file_suffix = file_suffix+"_"+os.path.basename(filename).rsplit("_",1)[1].replace(".", "_")
        file_suffix = file_suffix.rsplit("_csv")[0]
        print(file_suffix)
    
        dataframe["suffix"] = file_suffix   # handy for breaking up the csv file visually.
        dataframe.columns = [str(col) + "_"+file_suffix for col in dataframe.columns]
        dataframe.rename(columns={'datetime_'+file_suffix:'Time'}, inplace=True)

    # align time formats from different commands
    
    for count in range(len(list_of_dfs)):
        list_of_dfs[count]['Time'] = pd.to_datetime(list_of_dfs[count]['Time'])
            
    # Now merge on inner join (which means each time must exist in all files!)
            
    data_all = reduce(lambda x, y: pd.merge(x, y, on = 'Time'), list_of_dfs)
    data_all.columns = data_all.columns.str.replace("[/]", "_") 
    
    # Special case vmstat lets add a Total usage column for each idle time.
    
    col_list=list(data_all)
    col_list[:] = [cols for cols in col_list if "id_"in cols]
    
    for colname in col_list:
        colloc = data_all.columns.get_loc(colname)
        data_all.insert(colloc,"Total_CPU_"+colname, 100-data_all[colname])   
        
    # Now lets output to a super csv file    
    
    data_all.to_csv(FILEPATH+'/all_csv.csv' , sep=',', index=False)    
    
    
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
