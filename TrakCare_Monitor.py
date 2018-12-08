#!/usr/bin/env python3

# Quick process TrakCare Monitor Data to collate and visualise some interesting metrics
# Source data must be exported from the TrakCare Monitor Tool

# Example usage: TrakCare_Monitor.py -d directory [-l list of databases to include/exclude from episode size] -g 
#                Globals take a minute or so to process, explicitly request with -g 
# example: TrakCare_Monitor.py -d SINO_monitor -l TRAK-DOCUMENT TRAK-MONITOR -g      

import os
import pandas as pd
import matplotlib as mpl
import seaborn as sns
import string

from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import MO, TU, WE, TH, FR, SA, SU


import numpy as np
import glob
import argparse

# Generic plot by date, single line, ticks on a Monday.

def generic_plot(df, column, Title, yLabel, saveAs, pres=False, yzero=True, TextString=""):

        plt.style.use('seaborn')
        plt.figure(num=None, figsize=(10, 6), dpi=300)
        plt.plot(df[column])
        plt.title(Title, fontsize=14)
        plt.ylabel(yLabel, fontsize=10)
        plt.tick_params(labelsize=10)  
    
        ax = plt.gca()
        if yzero:
                ax.set_ylim(ymin=0)  # Always zero start                
        if pres :
            ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.2f}'))
        else :
            ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))    
        ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(mdates.WeekdayLocator(byweekday=MO)))
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        plt.text(0.01,.95,TextString, ha='left', va='center', transform=ax.transAxes, fontsize=12)
        plt.tight_layout()        
        plt.savefig(saveAs, format='pdf')
        plt.close()

# Dont crowd the pie chart. To do; bucket 'Other' after 2pct
    
def make_autopct(values):
    def my_autopct(pct):
        total = sum(values)
        val = int(round(pct*total/100000.0))
        return '{p:.0f}%  ({v:,d} GB)'.format(p=pct,v=val) if pct > 2 else ''
    return my_autopct    

def average_episode_size(DIRECTORY, MonitorAppFile, MonitorDatabaseFile, TRAKDOCS, INCLUDE):

    # Get the episode data 
    outputName = os.path.splitext(os.path.basename(MonitorDatabaseFile))[0]
    outputFile_pdf = DIRECTORY+"/all_out_pdf/"+outputName+"_Summary"  
    outputFile_csv = DIRECTORY+"/all_out_csv/"+outputName+"_Summary"       
    print("Episode size: %s" % outputName)

    df_master_ep = pd.read_csv(MonitorAppFile, sep='\t', encoding = "ISO-8859-1")
    df_master_ep = df_master_ep.dropna(axis=1, how='all') 
    df_master_ep = df_master_ep.rename(columns = {'RunDate':'Date'})

    # Cut down to just what we care about
    df_master_ep = df_master_ep[['Date','RunTime','EpisodeCountTotal' ]]

    # Get the database growth data
    df_master_db = pd.read_csv(MonitorDatabaseFile, sep='\t', encoding = "ISO-8859-1")
    df_master_db = df_master_db.dropna(axis=1, how='all')
    df_master_db = df_master_db.rename(columns = {'RunDate':'Date'})

    # Calculate actual database used
    df_master_db['DatabaseUsedMB'] = df_master_db['SizeinMB'] - df_master_db['FreeSpace']
    df_master_db = df_master_db[['Date','DatabaseUsedMB', 'Name']]

    df_master_db.to_csv(outputFile_csv+"Database_With_Docs.csv", sep=',', index=False)

    # Always exclude CACHETEMP
    df_master_db = df_master_db[df_master_db.Name != "CACHETEMP"]
           
    # If all databases including docs
    if TRAKDOCS == ["all"] :
        includew = ' with '
        df_master_db_dm = df_master_db
        outputFile_pdf_x = outputFile_pdf+"_All_EP_Size.pdf" 
    else:        
        # INCLUDE only the document database ? = True 
        if INCLUDE:
            includew = ' only '
            df_master_db_dm = df_master_db[df_master_db['Name'].isin(TRAKDOCS)] 
            outputFile_pdf_x = outputFile_pdf+"_"+'_'.join(TRAKDOCS)+"_EP_Size.pdf"
        # All databases except document database    
        else:
            includew = ' without '
            df_master_db_dm = df_master_db[~df_master_db['Name'].isin(TRAKDOCS)] 
            outputFile_pdf_x = outputFile_pdf+"_Not_"+'_'.join(TRAKDOCS)+"_EP_Size.pdf" 
                
    # Group databases by date, add column for growth per day, remove date index for merging
    df_db_by_date = df_master_db_dm.groupby('Date').sum()

    df_db_by_date['DatabaseGrowthMB'] = df_db_by_date['DatabaseUsedMB'] - df_db_by_date['DatabaseUsedMB'].shift(1)
    df_db_by_date = df_db_by_date[np.isfinite(df_db_by_date['DatabaseGrowthMB'])]
    df_db_by_date.reset_index(level=0, inplace=True)

    # Merge episodes and database growth on date, create column for daily plot
    df_result = pd.merge(df_master_ep, df_db_by_date )
    df_result["AvgEpisodeSizeMB"] = df_result["DatabaseGrowthMB"] / df_result["EpisodeCountTotal"]
    df_result['Date'] = pd.to_datetime(df_result['Date'])
    df_result.set_index('Date', inplace=True)
    
    if TRAKDOCS == ["all"] :
        df_result.to_csv(outputFile_csv+"Database_Growth.csv", sep=',', index=True )

    # Build the plot

    DatabaseGrowthTotal = df_result.iloc[-1]['DatabaseUsedMB'] - df_result.iloc[0]['DatabaseUsedMB']
    TotalEpisodes       = df_result['EpisodeCountTotal'].sum()
    AverageEpisodeSize  = round(DatabaseGrowthTotal / TotalEpisodes,2)
    TextString='Average growth/episode{}{}: {} MB'.format(includew,', '.join(TRAKDOCS), AverageEpisodeSize)

    RunDateStart = df_result.head(1).index.tolist()
    RunDateStart = RunDateStart[0].strftime('%d/%m/%Y')
    RunDateEnd = df_result.tail(1).index.tolist()
    RunDateEnd = RunDateEnd[0].strftime('%d/%m/%Y')

    plt.style.use('seaborn')
    plt.figure(num=None, figsize=(10, 6), dpi=80)
    plt.plot(df_result['AvgEpisodeSizeMB'])
    plt.title('Average Episode Size '+RunDateStart+' - '+RunDateEnd, fontsize=14)
    plt.tick_params(labelsize=10)
    ax = plt.gca()
    ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.2f}'))    
    ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(mdates.WeekdayLocator(byweekday=MO)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%y - %H:%M'))
    plt.ylabel("Average episode size (MB)", fontsize=10)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    plt.text(0.01,.95,TextString, ha='left', va='center', transform=ax.transAxes, fontsize=12)
    plt.tight_layout() 
    plt.savefig(outputFile_pdf_x, format='pdf')
    #plt.show()
    plt.close()        
    
    # Print some useful stats to txt file 
    # Note on individual days there will be rounding errors of MBs 
    #          - for totals use start and end figures where possible, eg end-start not growth_column.sum()
    
    if TRAKDOCS == ["all"] :
        with open( DIRECTORY+"/all_"+outputName+'_Basic_Stats.txt', 'w') as f:
            f.write('Number of days data            : '+'{v:,.0f}'.format(v=df_result['DatabaseUsedMB'].count())+"\n")      
            f.write('Database size at start         : '+'{v:,.0f}'.format(v=df_result.iloc[0]['DatabaseUsedMB']/1000)+" GB\n") 
            f.write('Database size at end           : '+'{v:,.0f}'.format(v=df_result.iloc[-1]['DatabaseUsedMB']/1000)+" GB\n")  
                         
            f.write('\nTotal database growth          : '+'{v:,.3f}'.format(v=DatabaseGrowthTotal/1000)+' GB\n')
            f.write('Peak database growth/day       : '+'{v:,.3f}'.format(v=df_result['DatabaseGrowthMB'].max()/1000)+' GB\n')        
            f.write('Average database growth/day    : '+'{v:,.3f}'.format(v=(DatabaseGrowthTotal/1000)/df_result['DatabaseGrowthMB'].count())+' GB\n')
            f.write('Estimated database growth/year : '+'{v:,.0f}'.format(v=((DatabaseGrowthTotal/1000)/df_result['DatabaseGrowthMB'].count())*365)+' GB\n\n')

            f.write('Sum episodes                   : '+'{v:,.0f}'.format(v=df_result['EpisodeCountTotal'].sum())+"\n")
            f.write('Average episodes/day           : '+'{v:,.0f}'.format(v=df_result['EpisodeCountTotal'].mean())+"\n")  
            f.write('Peak episodes/day              : '+'{v:,.0f}'.format(v=df_result['EpisodeCountTotal'].max())+"\n")        
            f.write('Estimated episodes/year        : '+'{v:,.0f}'.format(v=df_result['EpisodeCountTotal'].mean()*365)+"\n\n")       

            f.write('Total database growth{0}{1} databases: {2:,.3f}'.format(includew, ', '.join(TRAKDOCS), DatabaseGrowthTotal/1000)+" GB\n")
            f.write('Average growth/episode{0}{1} databases: {2:,.0f} KB (per episode size)'.format(includew, ', '.join(TRAKDOCS), AverageEpisodeSize*1000)+"\n")
            
            TextString = 'Database size at end : '+'{v:,.0f}'.format(v=df_result.iloc[-1]['DatabaseUsedMB']/1000)+" GB\n"
            generic_plot(df_result, 'DatabaseUsedMB', 'Total Database Size (MB)  '+RunDateStart+' to '+RunDateEnd, 'MB', outputFile_pdf+"_All_Total.pdf", False, True, TextString )
            TextString = 'Average database growth/day : '+'{v:,.3f}'.format(v=DatabaseGrowthTotal/1000/df_result['DatabaseGrowthMB'].count())+' GB'
            generic_plot(df_result, 'DatabaseGrowthMB', 'Database Growth per Day (MB)  '+RunDateStart+' to '+RunDateEnd, 'MB', outputFile_pdf+"_All_Growth.pdf", False, True, TextString  )
    else:
        with open( DIRECTORY+"/all_"+outputName+'_Basic_Stats.txt', 'a') as f:
            f.write('\nTotal database growth{0}{1}: {2:,.2f}'.format(includew, ', '.join(TRAKDOCS), DatabaseGrowthTotal/1000)+" GB\n")
            f.write('Average growth/episode{0}{1}: {2:,.0f} KB (per episode size)'.format(includew, ', '.join(TRAKDOCS), AverageEpisodeSize*1000)+"\n")
            
            ChartTitle = 'Total Database Size (MB)'+includew+', '.join(TRAKDOCS)+' '+RunDateStart+' to '+RunDateEnd
            if INCLUDE:
                outputFile_pdf_y = outputFile_pdf+'_'+'_'.join(TRAKDOCS)+"_Total.pdf"
            else:
                outputFile_pdf_y = outputFile_pdf+'_Not_'+'_'.join(TRAKDOCS)+"_Total.pdf"
            TextString = 'Database size at end : '+'{v:,.0f}'.format(v=df_result.iloc[-1]['DatabaseUsedMB']/1000)+" GB"    
            generic_plot(df_result, 'DatabaseUsedMB', ChartTitle, "MB", outputFile_pdf_y, False, True, TextString )
            
            ChartTitle = 'Database Growth per Day'+includew+', '.join(TRAKDOCS)+' '+RunDateStart+' to '+RunDateEnd
            if INCLUDE:
                outputFile_pdf_y = outputFile_pdf+'_'+'_'.join(TRAKDOCS)+"_Growth.pdf"
            else:
                outputFile_pdf_y = outputFile_pdf+'_Not_'+'_'.join(TRAKDOCS)+"_Growth.pdf" 
            TextString = 'Average database growth/day : '+'{v:,.3f}'.format(v=DatabaseGrowthTotal/1000/df_result['DatabaseGrowthMB'].count())+' GB'              
            generic_plot(df_result, 'DatabaseGrowthMB', ChartTitle, "MB", outputFile_pdf_y, False, True, TextString  )
        
def mainline(DIRECTORY, TRAKDOCS, Do_Globals):

    # Top N values. To do; make parameters
    TopNDatabaseByGrowth    = 10
    TopNDatabaseByGrowthPie = 5
    
    # Get list of files in directory, can have multiples of same type if follow regex
    MonitorAppName=glob.glob(DIRECTORY+'/*MonitorApp.txt')
    MonitorDatabaseName=glob.glob(DIRECTORY+'/*MonitorDatabase.txt')
    MonitorGlobalsName=glob.glob(DIRECTORY+'/*MonitorGlobals.txt')   
    MonitorJournalsName=glob.glob(DIRECTORY+'/*MonitorJournals.txt')     
    MonitorPageSummaryName=glob.glob(DIRECTORY+'/*MonitorPageSummary.txt')   
    
    # Create directories for generated csv and pdf files
    if not os.path.exists(DIRECTORY+"/all_out_pdf"):
        os.mkdir(DIRECTORY+"/all_out_pdf")
    if not os.path.exists(DIRECTORY+"/all_out_csv"):
        os.mkdir(DIRECTORY+"/all_out_csv")
    if not os.path.exists(DIRECTORY+"/all_database"):
        os.mkdir(DIRECTORY+"/all_database")
               
    # Journals -------------------------------------------------------------------------
    # Total by day and output chart and processed data as csv
    
    for filename in MonitorJournalsName :
        outputName = os.path.splitext(os.path.basename(filename))[0]
        outputFile_pdf = DIRECTORY+"/all_out_pdf/"+outputName  
        outputFile_csv = DIRECTORY+"/all_out_csv/"+outputName     
        print("Journals: %s" % outputName)
    
        df_master = pd.read_csv(filename, sep='\t', encoding = "ISO-8859-1", parse_dates=[0], index_col=0)
        df_master = df_master.dropna(axis=1, how='all') 
        
        df_master.index.names = ['Date']        
        df_master.to_csv(outputFile_csv+".csv", sep=',')
        
        # Lets get the start and end dates to display 
        #                                              - use for all titles
        
        RunDateStart = df_master.head(1).index.tolist()
        RunDateStart = RunDateStart[0].strftime('%d/%m/%Y')
        RunDateEnd = df_master.tail(1).index.tolist()
        RunDateEnd = RunDateEnd[0].strftime('%d/%m/%Y')
        TITLEDATES = RunDateStart+' to '+RunDateEnd
        
        df_day = df_master.groupby('Date').sum()
        df_day['Journal Size GB'] = df_day['Size']/1000000000
        df_day['Size'] = df_day['Size'].map('{:,.0f}'.format)
        df_day['Journal Size GB'] = df_day['Journal Size GB'].map('{:,.0f}'.format).astype(int)
    
        TextString = 'Average Journals/day : '+'{v:,.0f}'.format(v=df_day['Journal Size GB'].mean())+' GB' 
        TextString = TextString+', Peak Journals/day : '+'{v:,.0f}'.format(v=df_day['Journal Size GB'].max())+' GB'
        generic_plot(df_day, 'Journal Size GB', 'Total Journal Size Per Day (GB)  '+TITLEDATES, 'GB per Day', outputFile_pdf+".pdf", False, True, TextString )
        df_day.to_csv(outputFile_csv+"_by_Day.csv", sep=',')
    
        
    # Episodes  -------------------------------------------------------------------------
    # Output a few useful charts and convert input to csv
    
    for filename in MonitorAppName :
        outputName = os.path.splitext(os.path.basename(filename))[0]
        outputFile_pdf = DIRECTORY+"/all_out_pdf/"+outputName 
        outputFile_csv = DIRECTORY+"/all_out_csv/"+outputName           
        print("Episodes: %s" % outputName)
    
        df_master_ep = pd.read_csv(filename, sep='\t', encoding = "ISO-8859-1", parse_dates=[0], index_col=0)
        df_master_ep = df_master_ep.dropna(axis=1, how='all') 
        df_master_ep.index.names = ['Date']
        df_master_ep.to_csv(outputFile_csv+".csv", sep=',')
    
        TextString = 'Average Episodes/day : '+'{v:,.0f}'.format(v=df_master_ep['EpisodeCountTotal'].mean()) 
        TextString = TextString+', Peak Episodes/day : '+'{v:,.0f}'.format(v=df_master_ep['EpisodeCountTotal'].max())  
        TextString = TextString+', Est Episodes/year : '+'{v:,.0f}'.format(v=df_master_ep['EpisodeCountTotal'].mean()*365) 
        
        generic_plot(df_master_ep, 'EpisodeCountTotal', 'Total Episodes Per Day  '+TITLEDATES, 'Episodes per Day', outputFile_pdf+"_Ttl_Episodes.pdf", False, True, TextString )
        generic_plot(df_master_ep, 'OrderCountTotal', 'Total Orders Per Day  '+TITLEDATES, 'Orders per Day', outputFile_pdf+"_Ttl_Orders.pdf", False, True )
         
        # Example of multiple charts. To do; Make this a function to accept any number of items
        
        plt.style.use('seaborn')
        plt.figure(num=None, figsize=(10, 6), dpi=80)
        
        plt.plot(df_master_ep['EpisodeCountTotal'], label='Total Episodes Per Day')
        plt.plot(df_master_ep['OrderCountTotal'], label='Total Orders Per Day')
        plt.legend(loc='best')
        
        plt.title('Episodes and Orders by Day  '+TITLEDATES, fontsize=14)
        plt.ylabel('Count', fontsize=10)
        plt.tick_params(labelsize=10)       
        ax = plt.gca()
        ax.set_ylim(ymin=0)  # Always zero start
        ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
        ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(mdates.WeekdayLocator(byweekday=MO)))
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(outputFile_pdf+"_Ttl_Episodes_Orders.pdf", format='pdf')
        plt.close()        

        #plt.style.use('seaborn')
        #plt.figure(num=None, figsize=(10, 6), dpi=80)
        
        #plt.plot(df_master_ep['EpisodeCountEmergency'], label='Emergency')
        #plt.plot(df_master_ep['EpisodeCountInpatient'], label='Inpatient')
        #plt.plot(df_master_ep['EpisodeCountOutpatient'], label='Outpatient')
        #plt.plot(df_master_ep['EpisodeCountTotal'], label='Total Episodes')
        #plt.legend(loc='best')
        
        #plt.title('Episodes by Type', fontsize=14)
        #plt.ylabel('Count', fontsize=10)
        #plt.tick_params(labelsize=10)       
        #ax = plt.gca()
        #ax.set_ylim(ymin=0)  # Always zero start
        #ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
        #ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(mdates.WeekdayLocator(byweekday=MO)))
        #plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        #plt.tight_layout()
        #plt.savefig(outputFile_pdf+"_All_Episodes.pdf")
        #plt.close()       
                
           
    # Databases  -------------------------------------------------------------------------
    # Total by day and output full list, by day list, top n growth and chart top n growth

    for filename in MonitorDatabaseName:
    
        outputName = os.path.splitext(os.path.basename(filename))[0]
        outputFile_pdf = DIRECTORY+"/all_out_pdf/"+outputName+"_Summary"  
        outputFile_csv = DIRECTORY+"/all_out_csv/"+outputName+"_Summary"             
        print("Databases: %s" % outputName)
    
        # What is the total size of all databases? includes CACHETEMP
        
        df_master_db = pd.read_csv(filename, sep='\t', encoding = "ISO-8859-1", parse_dates=[0], index_col=0)
        df_master_db = df_master_db.dropna(axis=1, how='all') 

        df_master_db.index.names = ['Date']        
        df_master_db['DatabaseUsedMB'] = df_master_db['SizeinMB'] - df_master_db['FreeSpace']
        
        df_db_by_date = df_master_db.groupby('Date').sum()

        df_master_db.to_csv(outputFile_csv+"_Size.csv", sep=',')
        df_db_by_date.to_csv(outputFile_csv+"_Size_by_date.csv", sep=',')

        # Data growth 
        TextString = 'Database size used at end : '+'{v:,.0f}'.format(v=df_db_by_date.iloc[-1]['DatabaseUsedMB']/1000)+" GB (includes CACHETEMP)\n"
        generic_plot(df_db_by_date, 'DatabaseUsedMB', 'Total Database Used  '+TITLEDATES, '(MB)', outputFile_pdf+"_Ttl_Database_Used.pdf", False, True, TextString )
        
        # Actual usage on disk
        TextString = 'Database size on disk (inc Freespace) at end : '+'{v:,.0f}'.format(v=df_db_by_date.iloc[-1]['SizeinMB']/1000)+" GB (includes CACHETEMP)\n"
        generic_plot(df_db_by_date, 'SizeinMB', 'Total Database Size on Disk  '+TITLEDATES, '(MB)', outputFile_pdf+"_Ttl_Database_Size_On_Disk.pdf", False, True, TextString )
        
        TextString = 'Database free at end : '+'{v:,.0f}'.format(v=df_db_by_date.iloc[-1]['FreeSpace']/1000)+" GB (includes CACHETEMP)\n"
        generic_plot(df_db_by_date, 'FreeSpace', 'Total Database Freespace on Disk  '+TITLEDATES, '(MB)', outputFile_pdf+"_Ttl_Database_Free.pdf", False, True, TextString )
        
        # What are the high growth databases in this period? 
        # Get database sizes, dont key by date as we will use this field

        df_master_db = pd.read_csv(filename, sep='\t', encoding = "ISO-8859-1")
        df_master_db = df_master_db.dropna(axis=1, how='all')
        df_master_db = df_master_db.rename(columns = {'RunDate':'Date'})
        df_master_db['DatabaseUsedMB'] = df_master_db['SizeinMB'] - df_master_db['FreeSpace']

        # create a new file per database for later deep dive if needed
        df_databases = pd.DataFrame({'Name':df_master_db.Name.unique()}) # Get unique database names
        
        cols = ['Database', 'Start MB', 'End MB' ,'Growth MB']
        lst = []
        for index, row in df_databases.iterrows():
            df_temp = df_master_db.loc[df_master_db['Name'] == row['Name']].iloc[[0, -1]]   
            lst.append([row['Name'],df_temp['DatabaseUsedMB'].iloc[0],df_temp['DatabaseUsedMB'].iloc[1],df_temp['DatabaseUsedMB'].iloc[1] - df_temp['DatabaseUsedMB'].iloc[0]])
            df_master_db.loc[df_master_db['Name'] == row['Name']].to_csv(DIRECTORY+"/all_database/Database_"+row['Name']+".csv", sep=',', index=False)    

        # Lets see growth over sample period in some charts    
        df_out = pd.DataFrame(lst, columns=cols).sort_values(by=['Growth MB'], ascending=False)                    
        df_out.to_csv(outputFile_csv+".csv", sep=',', index=False)  
        
        # What are the top N databses by growth? df_out will hold the sorted list
        df_out.head(TopNDatabaseByGrowth).to_csv(outputFile_csv+"_top_"+str(TopNDatabaseByGrowth)+".csv", sep=',', index=False)
        
        # Bar chart - top N Total Growth
        plt.style.use('seaborn')
        plt.figure(num=None, figsize=(10, 6), dpi=80)
        index = np.arange(len(df_out['Database'].head(TopNDatabaseByGrowth)))
        
        # df_out
        plt.barh(df_out['Database'].head(TopNDatabaseByGrowth), df_out['Growth MB'].head(10))

        plt.title('Top '+str(TopNDatabaseByGrowth)+' - Database Growth  '+TITLEDATES, fontsize=14)
        plt.xlabel('Growth over period (MB)', fontsize=10)
        plt.tick_params(labelsize=10)  
        plt.yticks(index, df_out['Database'].head(TopNDatabaseByGrowth), fontsize=10)
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
        plt.tight_layout()
        plt.savefig(outputFile_pdf+"_Top_"+str(TopNDatabaseByGrowth)+"_Bar.pdf", format='pdf')
        plt.close()     
        
        
        # Growth of top n databases over time (not stacked)
        df_master_db['Date'] = pd.to_datetime(df_master_db['Date']) # Convert text field to date time
        
        top_List = df_out['Database'].head(TopNDatabaseByGrowthPie).tolist()
        grpd = df_master_db.groupby('Name') 

        plt.style.use('seaborn')
        plt.figure(num=None, figsize=(10, 6), dpi=80)
            
        for name, data in grpd:        
            if name in top_List:        
                plt.plot(data.Date.values, data.DatabaseUsedMB.values, '-', label = name)
                
        plt.title('Top Growth Databases (Not Stacked)  '+TITLEDATES, fontsize=14)
        plt.ylabel('MB', fontsize=10)
        plt.tick_params(labelsize=10) 
        plt.legend(loc='upper left')      
        ax = plt.gca()
        ax.set_ylim(ymin=0)  # Always zero start
        ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
        ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(mdates.WeekdayLocator(byweekday=MO)))
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(outputFile_pdf+"_Top_"+str(TopNDatabaseByGrowthPie)+"_Growth_Time.pdf", format='pdf')
        plt.close()               

        
        # Pie chart like Dave's to show relative sizes, Last day of sample period
        LastDay=df_master_db['Date'].iloc[-1]
        df_temp = df_master_db.loc[df_master_db['Date'] == LastDay] 

        df_sorted = df_temp.sort_values(by=['DatabaseUsedMB'], ascending=False )
        df_sorted.to_csv(outputFile_csv+"_pie.csv", sep=',', index=False)
        
        # Drop rows with unmounted databases - size shows up as NaN
        # df_sorted = df_sorted.dropna() <--- cant use this drops too much

        Total_all_db=df_sorted['DatabaseUsedMB'].sum()
        TOTAL_ALL_DB=Total_all_db/1000
        
        df_sorted["Labels"] = np.where(df_sorted['DatabaseUsedMB']*100/Total_all_db > 2, df_sorted['Name'], '')
        
        plt.style.use('seaborn')
        plt.figure(num=None, figsize=(10, 6), dpi=80)
        pie_exp = tuple(0.1 if i < 2 else 0 for i in range(df_sorted['Name'].count())) # Pie explode 
        
        plt.pie(df_sorted['DatabaseUsedMB'], labels = df_sorted["Labels"], autopct=make_autopct(df_sorted['DatabaseUsedMB']), startangle=60, explode=pie_exp, shadow=True)
        plt.title('Top Database Sizes at '+str(LastDay)+' - Total '+'{v:,.0f}'.format(v=TOTAL_ALL_DB)+' GB' , fontsize=14)
        
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(outputFile_pdf+"_Total_DB_Size_Pie.pdf")
        plt.close()


        # Stacked Chart is a good way to look at Top N
        
        top_List = df_out['Database'].head(TopNDatabaseByGrowthPie).tolist()
        df_top_List = df_master_db[df_master_db['Name'].isin( top_List )]
        
        dates = pd.DataFrame({'Date':df_master_db.Date.unique()}) # Get unique database names in list
        
        # Build some lists to plot
        dates = dates['Date'].tolist()
        
        Lists = {} # Dictionary to hold top N database Names and sizes over time

        for i in top_List:
            df_A = df_top_List[df_top_List['Name'] == i]
            listName = i.replace('-', '_') # Dashes screw with Python    
            Lists[listName] = df_A['DatabaseUsedMB'].tolist()
        
        all_keys=[]
        all_items=[]
        for i,j in Lists.items():
            all_keys.append(i)
            all_items.append(j)
            
        pal = sns.color_palette("Set1")
        plt.style.use('seaborn')
        plt.figure(num=None, figsize=(10, 6), dpi=80)

        plt.stackplot(dates, all_items, labels=all_keys, colors=pal, alpha=0.5)

        plt.title('Top '+str(TopNDatabaseByGrowthPie)+' - Database Growth  '+TITLEDATES, fontsize=14)
        plt.ylabel('MB', fontsize=10)
        plt.tick_params(labelsize=10)  
        ax = plt.gca()
        ax.set_ylim(ymin=0)  # Always zero start
        ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
        ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(mdates.WeekdayLocator(byweekday=MO)))
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        plt.tight_layout()
        plt.legend(loc='upper left')    
        
        plt.savefig(outputFile_pdf+"_Top_"+str(TopNDatabaseByGrowthPie)+"_Growth_Time_Stack.pdf", format='pdf')
        plt.close()
        
        
    # Average Episode size is good to know  - Merge Episodes and Database growth (grouped by date) 

    for index in range( len(MonitorAppName)) :
    
        # Now plot the data
        
        average_episode_size(DIRECTORY, MonitorAppName[index], MonitorDatabaseName[index], ["all"], True ) 
        
        if TRAKDOCS == [""] :
            print('TrakCare document database not defined - use -t "TRAK-DOCDBNAME" to calculate growth with/without docs')
        else:
            if len(TRAKDOCS) > 1 :
                for options in TRAKDOCS :
                    average_episode_size(DIRECTORY, MonitorAppName[index], MonitorDatabaseName[index], [options], True)
                    average_episode_size(DIRECTORY, MonitorAppName[index], MonitorDatabaseName[index], [options], False)
                
            average_episode_size(DIRECTORY, MonitorAppName[index], MonitorDatabaseName[index], TRAKDOCS, True)
            average_episode_size(DIRECTORY, MonitorAppName[index], MonitorDatabaseName[index], TRAKDOCS, False)


    # Globals - takes a while, explicitly run it with -g option -------------------------
    
    if Do_Globals :
    
        for filename in MonitorGlobalsName:
        
            if not os.path.exists(DIRECTORY+"/all_globals"):
                os.mkdir(DIRECTORY+"/all_globals") 
                
            outputName = os.path.splitext(os.path.basename(filename))[0]
            outputFile_pdf = DIRECTORY+"/all_out_pdf/"+outputName+"_Summary"  
            outputFile_csv = DIRECTORY+"/all_out_csv/"+outputName+"_Summary"                                  
            
            print("Globals: %s" % outputName)
            
            df_master_gb = pd.read_csv(filename, sep='\t', encoding = "ISO-8859-1")
            df_master_gb = df_master_gb.dropna(axis=1, how='all')
            df_master_gb = df_master_gb.rename(columns = {'RunDate':'Date'})
   
            # substring mapping is a thing - one global can have many parts, need to break on path and Global
            #  DataBasePath	        GlobalName	SizeAllocated
            # /trak/ufh/live/db/AUDIT0/	AUD	    57949
            # /trak/ufh/live/db/AUDIT1/	AUD	    103617
            # /trak/ufh/live/db/AUDIT2/	AUD	    45235
            # /trak/ufh/live/db/AUDIT3/	AUD	    41815
            # etc
   
            df_master_gb['DataBasePath'].replace("\\\\", "_",inplace=True, regex=True)
            df_master_gb['DataBasePath'].replace(":", "_",inplace=True, regex=True)             
            df_master_gb['DataBasePath'].replace("/", "_",inplace=True, regex=True)
            df_master_gb['DataBasePath'].replace("__", "",inplace=True, regex=True)
            
            df_master_gb['Full_Global'] = df_master_gb['DataBasePath'].str[1:]+df_master_gb['GlobalName']

            
            # Get unique names and use that as a key to create a new dataframe per global
        
            df_globals = pd.DataFrame({'Full_Global':df_master_gb.Full_Global.unique()}) # Get unique names

            cols = ['Full_Global', 'Start Size', 'End Size' ,'Growth Size']
            lst = []

            print('Please wait while globals growth calculated')
            dots = '.'
        
            for index, row in df_globals.iterrows():

                df_temp = df_master_gb.loc[df_master_gb['Full_Global'] == row['Full_Global']].iloc[[0, -1]]
    
                lst.append([row['Full_Global'],df_temp['SizeAllocated'].iloc[0],df_temp['SizeAllocated'].iloc[1],df_temp['SizeAllocated'].iloc[1] - df_temp['SizeAllocated'].iloc[0]])

                df_master_gb.loc[df_master_gb['Full_Global'] == row['Full_Global']].to_csv(DIRECTORY+"/all_globals/Globals_"+row['Full_Global']+".csv", sep=',', index=False)   
                        
                dots+='.'     
                if dots == '..............':
                    dots = '.'
            
                print('\r'+dots, end='')

            print('\n')
            
            df_out = pd.DataFrame(lst, columns=cols).sort_values(by=['Growth Size'], ascending=False)    
            df_out.to_csv(outputFile_csv+".csv", sep=',', index=False)
            
            df_out.head(20).to_csv(outputFile_csv+"_top_20.csv", sep=',', index=False)
        
        
            # Lets see the highest growth globals
        
            plt.style.use('seaborn')
            plt.figure(num=None, figsize=(10, 6), dpi=80)
            index = np.arange(len(df_out['Full_Global'].head(20)))
            plt.barh(df_out['Full_Global'].head(20), df_out['Growth Size'].head(20))

            plt.title('Top 20 - Globals by Growth  '+TITLEDATES, fontsize=14)
            plt.xlabel('Growth over period (MB)', fontsize=10)
            plt.tick_params(labelsize=10)  
            plt.yticks(index, df_out['Full_Global'].head(20), fontsize=10)
            ax = plt.gca()
            ax.xaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
            plt.tight_layout()
            plt.savefig(outputFile_pdf+"_Top_20.pdf", format='pdf')
            plt.close()     
            
            
            # Growth of top n globals
            
            TopNDatabaseByGrowthPie=6
            
            df_master_gb['Date'] = pd.to_datetime(df_master_gb['Date'])
            
            top_List = df_out['Full_Global'].head(TopNDatabaseByGrowthPie).tolist()
            grpd = df_master_gb.groupby('Full_Global') 

            plt.style.use('seaborn')
            plt.figure(num=None, figsize=(10, 6), dpi=80)
                
            for name, data in grpd:        
                if name in top_List:        
                    plt.plot(data.Date.values, data.SizeAllocated.values, '-', label = name)
            plt.legend(loc='best')
    
            plt.title('Top Growth Globals Over Period  '+TITLEDATES, fontsize=14)
            plt.ylabel('MB', fontsize=10)
            plt.tick_params(labelsize=10)       
            ax = plt.gca()
            ax.set_ylim(ymin=0)  # Always zero start
            ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
            ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(mdates.WeekdayLocator(byweekday=MO)))
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
            plt.tight_layout()
            plt.savefig(outputFile_pdf+"_Top_"+str(TopNDatabaseByGrowthPie)+"_Growth.pdf", format='pdf')
            plt.close()        


    print("Finished\n") 
        
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="TrakCare Monitor Process")
    parser.add_argument("-d", "--directory", help="Directory with Monitor files", required=True)  
    parser.add_argument("-l", "--listofDBs", nargs='+', help="TrakCare databases names to exclude from episode size") 
    parser.add_argument("-g", "--globals", help="Globals take a long time", action="store_true")    

    args = parser.parse_args()
   
    if args.directory is not None:
        DIRECTORY = args.directory
    else:
        print('Error: -d "Directory with Monitor files"')
        exit(0)
 
    if args.listofDBs is not None:
        TRAKDOCS = args.listofDBs
    else:
        TRAKDOCS = [""] 
        
    try:
         mainline(DIRECTORY, TRAKDOCS, args.globals)       
    except OSError as e:
        print('Could not process files because: {}'.format(str(e)))
        


    
    
