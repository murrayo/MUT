#!/bin/sh

# This script loops through multiple subdirectories to run yape and collates results
# 
# 
# Useful for benchmarks especially 

# Beware spaces in file path
# Example Usage: yape_deep.sh -d "dm-0 dm-1 sdb sdc sdn"

# I run ^SystemPerformance in iris (or ^pButtons in Caché) and collate the data back to a central location for processing.
# html files files end up in a tree like below. But this script can be used for single files as well.

# Run the command from the top of the tree.
# For example run from .

#.
#├── MASTER
#│   └── irismaster
#│       └── irismaster_IRISQP3_20180704_054851_irismaster_55_min.html
#└── SHARD
#    ├── irisshard1
#    │   └── irisshard1_IRISQP3_20180704_054851_irisshard1_55_min.html
#    ├── irisshard2
#    │   └── irisshard2_IRISQP3_20180704_054852_irisshard2_55_min.html
#    ├── irisshard3
#    │   └── irisshard3_IRISQP3_20180704_054853_irisshard3_55_min.html
#    └── irisshard4
#        └── irisshard4_IRISQP3_20180704_054853_irisshard4_55_min.html
#

Usage="Usage: $0 [-d \"disk list\"] -w (windows default is linux)"

while getopts d:wh o
do	case "$o" in
	d)  intreasting_disks="$OPTARG" ;;
    w)  Windows="Y" ;;  
	h)  printf %s"${Usage}\n"; exit;;	
	[?])	echo 
	exit 1;;
	esac
done

ServerList=""

# Where are we now folder
CurrentFolder=`pwd`
echo "Current: ${CurrentFolder}"

# Get list of files and process them

for f in `find . -name *.html`
do	echo "File: ${f}"
	
	Directoryname=`dirname ${f}`
	Filename=`basename ${f}`
	echo "Processing directory: ${Directoryname} : ${Filename}"	
	
	fileName=`echo ${Filename} | awk -F. '{print $1}'`  # Drop the html for the prefix
	ServerName=`echo ${Filename} | awk -F_ '{print $1}'` # servername at start of file name
	ServerList="$ServerList $ServerName" 
	
	cd ${Directoryname} # We want output with the html file
	    
	if [[ "$Windows" != "" ]]; then   
	    yape -c --mgstat --perfmon --prefix "${fileName}_" "${Filename}"
	else
	    #yape -c --mgstat --vmstat --iostat --prefix "${fileName}_" --plotDisks "${intreasting_disks}" ${Filename}
	    yape -c --mgstat --vmstat --prefix "${fileName}_"  ${Filename}
	fi    
	
	cd "${CurrentFolder}"
done

# Put the csv files separate to for easy processing, all in one directory

mkdir -p csvfiles
    
for f in `find . -name *.csv`
do
    cp $f csvfiles 2>/dev/null
done


# Get disk files I am interested in
if [[ "$Windows" == "" ]]; then 

    echo "Processing Servers: $ServerList"
    
    for i in $ServerList
    do
        mkdir -p ${i}"_disks"
        echo "Disk : ${i}"
        
        for f in `find . -name "*_${i}_*iostat*.png"`
        do
            echo $f
            cp $f ${i}"_disks" 2>/dev/null
        done
    done    
fi

exit 0
