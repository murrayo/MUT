#!/usr/bin/env python3

# Quick process TrakCare Monitor Data to collate and visualise some interesting metrics
# Source data must be exported from the TrakCare Monitor Tool

# Example usage: TrakCare_Monitor.py -d directory
#                Globals take a minute or so to process, explicitly request with -g 

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

def generic_plot(df, column, Title, yLabel, saveAs, pres=False):

        plt.style.use('seaborn')
        plt.figure(num=None, figsize=(10, 6), dpi=80)
        plt.plot(df[column])
        plt.title(Title, fontsize=14)
        plt.ylabel(yLabel, fontsize=10)
        plt.tick_params(labelsize=10)       
        ax = plt.gca()
#        ax.set_ylim(ymin=0)  # Always zero start
        if pres :
            ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.2f}'))
        else :
            ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))    
        ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(mdates.WeekdayLocator(byweekday=MO)))
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        plt.tight_layout()        
        plt.savefig(saveAs)
        plt.close()

    
def make_autopct(values):
    def my_autopct(pct):
        total = sum(values)
        val = int(round(pct*total/100000.0))
        return '{p:.0f}%  ({v:,d} GB)'.format(p=pct,v=val) if pct > 2 else ''
    return my_autopct

        
def mainline(DIRECTORY, Do_Globals):

    # Get list of files in directory, can have multiples of same type if follow regex
    
    MonitorAppName=glob.glob(DIRECTORY+'/*MonitorApp.txt')
    MonitorDatabaseName=glob.glob(DIRECTORY+'/*MonitorDatabase.txt')
    MonitorGlobalsName=glob.glob(DIRECTORY+'/*MonitorGlobals.txt')   
    MonitorJournalsName=glob.glob(DIRECTORY+'/*MonitorJournals.txt')     
    MonitorPageSummaryName=glob.glob(DIRECTORY+'/*MonitorPageSummary.txt')   
    
    
    # Top N values
    
    TopNDatabaseByGrowth    = 10
    TopNDatabaseByGrowthPie = 5
    
    # Journals -------------------------------------------------------------------------
    # Total by day and output chart and processed data as csv
    
    for filename in MonitorJournalsName :
        outputName = os.path.splitext(os.path.basename(filename))[0]
        outputFile = os.path.dirname(filename)+"/000_"+outputName+"_Summary"      
        print("\nJournals: %s" % outputName)
    
        df_master = pd.read_csv(filename, sep='\t', encoding = "ISO-8859-1", parse_dates=[0], index_col=0)
        df_master = df_master.dropna(axis=1, how='all') 
        
        df_master.index.names = ['Date']        
        df_master.to_csv(outputFile+".csv", sep=',')

        df_day = df_master.groupby('Date').sum()
        df_day['Journal Size GB'] = df_day['Size']/1000000000
        df_day['Size'] = df_day['Size'].map('{:,.0f}'.format)
        df_day['Journal Size GB'] = df_day['Journal Size GB'].map('{:,.0f}'.format).astype(int)
    
        generic_plot(df_day, 'Journal Size GB', 'Total Journal Size Per Day (GB)', 'GB per Day', outputFile+".png" )
        df_day.to_csv(outputFile+"_by_Day.csv", sep=',')
    
        
    # Episodes  -------------------------------------------------------------------------
    # Output a few useful charts and convert input to csv
    
    for filename in MonitorAppName :
        outputName = os.path.splitext(os.path.basename(filename))[0]
        outputFile = os.path.dirname(filename)+"/000_"+outputName+"_Summary"            
        print("Episodes: %s" % outputName)
    
        df_master_ep = pd.read_csv(filename, sep='\t', encoding = "ISO-8859-1", parse_dates=[0], index_col=0)
        df_master_ep = df_master_ep.dropna(axis=1, how='all') 
        df_master_ep.index.names = ['Date']
        df_master_ep.to_csv(outputFile+".csv", sep=',')
    
        generic_plot(df_master_ep, 'EpisodeCountTotal', 'Total Episodes Per Day', 'Episodes per Day', outputFile+"_Ttl_Episodes.png" )
        generic_plot(df_master_ep, 'OrderCountTotal', 'Total Orders Per Day', 'Orders per Day', outputFile+"_Ttl_Orders.png" )
         
        # Example of multiple charts, make this a function to accept any number of items
        
        plt.style.use('seaborn')
        plt.figure(num=None, figsize=(10, 6), dpi=80)
        
        plt.plot(df_master_ep['EpisodeCountTotal'], label='Total Episodes Per Day')
        plt.plot(df_master_ep['OrderCountTotal'], label='Total Orders Per Day')
        plt.legend(loc='best')
        
        plt.title('Episodes and Orders by Day', fontsize=14)
        plt.ylabel('Count', fontsize=10)
        plt.tick_params(labelsize=10)       
        ax = plt.gca()
        ax.set_ylim(ymin=0)  # Always zero start
        ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
        ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(mdates.WeekdayLocator(byweekday=MO)))
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(outputFile+"_Episodes_Orders.png")
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
        #plt.savefig(outputFile+"_All_Episodes.png")
        #plt.close()       
                
           
    # Databases  -------------------------------------------------------------------------
    # Total by day and output full list, by day list, top 10 growth and chart top 10 growth

    for filename in MonitorDatabaseName:
    
        outputName = os.path.splitext(os.path.basename(filename))[0]
        outputFile = os.path.dirname(filename)+"/000_"+outputName+"_Summary"            
        print("Databases: %s" % outputName)
    
        dirName = DIRECTORY+"/zoutput_database"

        if not os.path.exists(dirName):
            os.mkdir(dirName)
            #print("Directory " , dirName ,  " Created ")
        else:    
            print("Directory " , dirName ,  " already exists")        

        
        # What is the total size of all databases?
        
        df_master_db = pd.read_csv(filename, sep='\t', encoding = "ISO-8859-1", parse_dates=[0], index_col=0)
        df_master_db = df_master_db.dropna(axis=1, how='all') 
        
        df_master_db.index.names = ['Date']        
        df_master_db['Database Size MB'] = df_master_db['SizeinMB'] - df_master_db['FreeSpace']
        df_master_db.to_csv(outputFile+"_by_date.csv", sep=',')

        generic_plot(df_master_db.groupby('Date').sum(), 'Database Size MB', 'Total All Database Size Per Day', '(MB)', outputFile+"_Ttl_Database_Size.png" )
        
        
        # What are the high growth databases? Get database sizes, dont key by date as we will use this field

        df_master_db = pd.read_csv(filename, sep='\t', encoding = "ISO-8859-1")
        df_master_db = df_master_db.dropna(axis=1, how='all')
        df_master_db = df_master_db.rename(columns = {'RunDate':'Date'})
        df_master_db['Database Size MB'] = df_master_db['SizeinMB'] - df_master_db['FreeSpace']


        # create a new file per database for later deep dive if needed
        
        df_databases = pd.DataFrame({'Name':df_master_db.Name.unique()}) # Get unique database names
        
        cols = ['Database', 'Start MB', 'End MB' ,'Growth MB']
        lst = []
        for index, row in df_databases.iterrows():
            df_temp = df_master_db.loc[df_master_db['Name'] == row['Name']].iloc[[0, -1]]   
            lst.append([row['Name'],df_temp['Database Size MB'].iloc[0],df_temp['Database Size MB'].iloc[1],df_temp['Database Size MB'].iloc[1] - df_temp['Database Size MB'].iloc[0]])
            df_master_db.loc[df_master_db['Name'] == row['Name']].to_csv(dirName+"/Database_"+row['Name']+".csv", sep=',', index=False)    


        # Lets see growth over sample period in some charts
                
        df_out = pd.DataFrame(lst, columns=cols).sort_values(by=['Growth MB'], ascending=False)                    
        df_out.to_csv(outputFile+".csv", sep=',', index=False)  
        
        
        # What are the top N databses by growth? df_out will hold the sorted list
        
        df_out.head(TopNDatabaseByGrowth).to_csv(outputFile+"_top_"+str(TopNDatabaseByGrowth)+".csv", sep=',', index=False)
        
        
        # Bar chart top N Total Growth

        plt.style.use('seaborn')
        plt.figure(num=None, figsize=(10, 6), dpi=80)
        index = np.arange(len(df_out['Database'].head(TopNDatabaseByGrowth)))
        
        # df_out 
        plt.barh(df_out['Database'].head(TopNDatabaseByGrowth), df_out['Growth MB'].head(10))

        plt.title('Top '+str(TopNDatabaseByGrowth)+' - Database Growth', fontsize=14)
        plt.xlabel('Growth over period (MB)', fontsize=10)
        plt.tick_params(labelsize=10)  
        plt.yticks(index, df_out['Database'].head(TopNDatabaseByGrowth), fontsize=10)
        ax = plt.gca()
        ax.xaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
        plt.tight_layout()
        plt.savefig(outputFile+"_Top_"+str(TopNDatabaseByGrowth)+"_Bar.png")
        plt.close()     
        
        
        # Growth of top n databases over time

        df_master_db['Date'] = pd.to_datetime(df_master_db['Date']) # Convert text field to date time
        
        top_List = df_out['Database'].head(TopNDatabaseByGrowthPie).tolist()
        grpd = df_master_db.groupby('Name') 

        plt.style.use('seaborn')
        plt.figure(num=None, figsize=(10, 6), dpi=80)
            
        for name, data in grpd:        
            if name in top_List:        
               plt.plot(data.Date.values, data.SizeinMB.values, '-', label = name)
                
        plt.title('Top Growth Databases Over Period', fontsize=14)
        plt.ylabel('MB', fontsize=10)
        plt.tick_params(labelsize=10) 
        plt.legend(loc='upper left')      
        ax = plt.gca()
        ax.set_ylim(ymin=0)  # Always zero start
        ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
        ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(mdates.WeekdayLocator(byweekday=MO)))
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(outputFile+"_Top_"+str(TopNDatabaseByGrowthPie)+"_Growth_Time.png")
        plt.close()               


        # Pie chart like Dave's to show relative sizes, Last day of sample period
        
        LastDay=df_master_db['Date'].iloc[-1]
        df_temp = df_master_db.loc[df_master_db['Date'] == LastDay] 

        df_sorted = df_temp.sort_values(by=['Database Size MB'], ascending=False )
        
        TOTAL_ALL_DB=df_sorted['Database Size MB'].sum()/1000

        plt.style.use('seaborn')
        plt.figure(num=None, figsize=(10, 6), dpi=80)
        pie_exp = tuple(0.1 if i < 2 else 0 for i in range(df_sorted['Name'].count()))
        
        plt.pie(df_sorted['Database Size MB'], labels = df_sorted['Name'], autopct=make_autopct(df_sorted['Database Size MB']), startangle=60, explode=pie_exp, shadow=True)
        plt.title('Top Database Sizes at '+str(LastDay)+' - Total '+'{v:,.0f}'.format(v=TOTAL_ALL_DB)+' GB' , fontsize=14)
        
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(outputFile+"_Total_DB_Size_Pie.png")
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
            Lists[listName] = df_A['Database Size MB'].tolist()
        
        all_keys=[]
        all_items=[]
        for i,j in Lists.items():
            all_keys.append(i)
            all_items.append(j)
            
        pal = sns.color_palette("Set1")
        plt.style.use('seaborn')
        plt.figure(num=None, figsize=(10, 6), dpi=80)

        plt.stackplot(dates, all_items, labels=all_keys, colors=pal, alpha=0.5)

        plt.title('Top '+str(TopNDatabaseByGrowthPie)+' - Database Growth', fontsize=14)
        plt.ylabel('MB', fontsize=10)
        plt.tick_params(labelsize=10)  
        ax = plt.gca()
        ax.set_ylim(ymin=0)  # Always zero start
        ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
        ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(mdates.WeekdayLocator(byweekday=MO)))
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        plt.tight_layout()
        plt.legend(loc='upper left')    
        
        plt.savefig(outputFile+"_Top_"+str(TopNDatabaseByGrowthPie)+"_Growth_Time_Stack.png")
        plt.close()
        
        
    # Average Episode size is good to know   

    for index in range( len(MonitorAppName)) :

        df_master_ep = pd.read_csv(MonitorAppName[index], sep='\t', encoding = "ISO-8859-1")
        df_master_ep = df_master_ep.dropna(axis=1, how='all') 
        df_master_ep = df_master_ep.rename(columns = {'RunDate':'Date'})

        df_master_db = pd.read_csv(MonitorDatabaseName[index], sep='\t', encoding = "ISO-8859-1")
        df_master_db = df_master_db.dropna(axis=1, how='all')
        df_master_db = df_master_db.rename(columns = {'RunDate':'Date'})
        df_master_db['Database Size MB'] = df_master_db['SizeinMB'] - df_master_db['FreeSpace']
        
        outputName = os.path.splitext(os.path.basename(MonitorAppName[index]))[0]
        outputFile = os.path.dirname(MonitorAppName[index])+"/000_"+outputName+"_Summary_EP_Size"      
        print("\nEpisode size: %s" % outputName)
    

        # Group by date, sum by date
        df_db_by_date = df_master_db.groupby('Date').sum().diff().dropna() 
        #df_db_by_date = df_db_by_date.shift(-1)
        
        df_db_by_date.reset_index(level=0, inplace=True) # Remove index for merge

        df_ep_db = pd.merge(df_master_ep, df_db_by_date )
        df_ep_db["Episode Size MB"] = df_ep_db["Database Size MB"] / df_ep_db["EpisodeCountTotal"]
        
        # Print some useful stats
        
        with open( outputFile+'_Basic_Stats.txt', 'w') as f:
            f.write('Days                 : '+'{v:,.0f}'.format(v=df_ep_db["Database Size MB"].count())+"\n")        
            f.write('Sum Database Growth  : '+'{v:,.0f}'.format(v=df_ep_db["Database Size MB"].sum())+' MB\n')
            f.write('Peak Database Growth : '+'{v:,.0f}'.format(v=df_ep_db["Database Size MB"].max())+' MB\n')        
            f.write('Database Growth/Day  : '+'{v:,.0f}'.format(v=df_ep_db["Database Size MB"].sum()/df_ep_db["Database Size MB"].count())+' MB\n')
            f.write('Sum Episodes         : '+'{v:,.0f}'.format(v=df_ep_db["EpisodeCountTotal"].sum())+"\n")
            f.write('Average Episodes/Day : '+'{v:,.0f}'.format(v=df_ep_db["EpisodeCountTotal"].mean())+"\n")  
            f.write('Peak Episodes/Day    : '+'{v:,.0f}'.format(v=df_ep_db["EpisodeCountTotal"].max())+"\n")        
            f.write('Est Episodes/year    : '+'{v:,.0f}'.format(v=df_ep_db["EpisodeCountTotal"].mean()*365)+"\n")       
            f.write('Average Episode Size : '+'{v:,.2f}'.format(v=df_ep_db["Database Size MB"].sum()/df_ep_db["EpisodeCountTotal"].sum())+' MB\n')
            f.write('Mean    Episode Size : '+'{v:,.2f}'.format(v=df_ep_db["Episode Size MB"].mean())+' MB - Split the difference\n')
        
        df_ep_db.to_csv(outputFile+"Database_Growth.csv", sep=',', index=False)  
        
        AverageEpisodeSize = df_ep_db["Database Size MB"].sum()/df_ep_db["EpisodeCountTotal"].sum()
        
        df_ep_db['Date'] = pd.to_datetime(df_ep_db['Date'])
        df_ep_db.set_index('Date', inplace=True)

        generic_plot(df_ep_db, 'Episode Size MB', 'Average Growth per Episode per Day -- Overall average: '+'{v:,.2f}'.format(v=AverageEpisodeSize)+' MB', '(MB)', outputFile+"_Avg_Episodes"+str(index)+".png", True )      

    # Globals - takes a while, explicitly run it with -g option -------------------------
    
    if Do_Globals :
    
        for filename in MonitorGlobalsName:
            outputName = os.path.splitext(os.path.basename(filename))[0]
            outputFile = os.path.dirname(filename)+"/000_"+outputName+"_Summary"            
            print("Globals: %s" % outputName)
    
            dirName = DIRECTORY+"/zoutput_globals"
            if not os.path.exists(dirName):
                os.mkdir(dirName)
                #print("Directory " , dirName ,  " Created ")
            else:    
                print("Directory " , dirName ,  " already exists")        
            
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

                df_master_gb.loc[df_master_gb['Full_Global'] == row['Full_Global']].to_csv(dirName+"/Globals_"+row['Full_Global']+".csv", sep=',', index=False)   
            
                dots+='.'     
                if dots == '..............':
                    dots = '.'
            
                print('\r'+dots, end='')

            df_out = pd.DataFrame(lst, columns=cols).sort_values(by=['Growth Size'], ascending=False)    
            df_out.to_csv(outputFile+".csv", sep=',', index=False)
            
            df_out.head(20).to_csv(outputFile+"_top_20.csv", sep=',', index=False)
        
        
            # Lets see the highest growth globals
        
            plt.style.use('seaborn')
            plt.figure(num=None, figsize=(10, 6), dpi=80)
            index = np.arange(len(df_out['Full_Global'].head(20)))
            plt.barh(df_out['Full_Global'].head(20), df_out['Growth Size'].head(20))

            plt.title('Top 20 - Globals by Growth', fontsize=14)
            plt.xlabel('Growth over period (MB)', fontsize=10)
            plt.tick_params(labelsize=10)  
            plt.yticks(index, df_out['Full_Global'].head(20), fontsize=10)
            ax = plt.gca()
            ax.xaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
            plt.tight_layout()
            plt.savefig(outputFile+"_Top_20.png")
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
    
            plt.title('Top Growth Globals Over Period', fontsize=14)
            plt.ylabel('MB', fontsize=10)
            plt.tick_params(labelsize=10)       
            ax = plt.gca()
            ax.set_ylim(ymin=0)  # Always zero start
            ax.yaxis.set_major_formatter(mpl.ticker.StrMethodFormatter('{x:,.0f}'))
            ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(mdates.WeekdayLocator(byweekday=MO)))
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
            plt.tight_layout()
            plt.savefig(outputFile+"_Top_"+str(TopNDatabaseByGrowthPie)+"_Growth.png")
            plt.close()        


    print("Finished\n") 
        
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="TrakCare Monitor Process")
    parser.add_argument("-d", "--directory", help="Directory with Monitor files", required=True)  
    parser.add_argument("-g", "--globals", help="Globals take a long time", action="store_true")      
    args = parser.parse_args()
   
    if args.directory is not None:
        DIRECTORY = args.directory
    else:
        print('Error: -d "Directory with Monitor files"')
        exit(0)
 
    try:
         mainline(DIRECTORY, args.globals)       
    except OSError as e:
        print('Could not process files because: {}'.format(str(e)))
        


    
    
