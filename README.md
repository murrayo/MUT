# MUT - Murray's Unsupported Tools

A place to share my noodlings and helper tools. Most are orientated around my work unpacking and vsiualising system performance data. Just a big bag to store my stuff. If you find them useful, great!

As the title says. These tools are not supported, but suggestions, tips, fixes!, and any other comments welcome.  

> As Abraham Maslow said in 1966, "I suppose it is tempting, if the only tool you have is a hammer, to treat everything as if it were a nail." My current favorite tool for everything is Python, so you will see a lot of that here -- as I learn Python -- so code is bound to be not best practice.

Current Python Version;

	python --version
	Python 3.7.3
	
For safety you can use a docker container (instructions below)	

<hr>

## Manipulating csv files

Many of the tools in this section are built to further process csv files output from [yape](https://github.com/murrayo/yape), but they could be bent to other uses. The date+time indexed csv files include; mgstat, vmstat, and iostat. Ultimately the plan is for standalone functionality in these scripts will be included in yape.

`yape_deep.sh`
- This script loops through multiple subdirectories to run yape and collate results, importantly it sorts csv files to a folder so its easy to run the csv processing scripts below.

`iris_resample_csv.py`
- Refactor set of timestamped csv files so that all times are in synch. This is useful if you run iris\_combine\_csv.py to merge csv files, eg mgstat, vmstat, and iostat into a super csv file for further processing.

`iris_combine_csv.py`
- Build a master list of dataframes for each csv file. This is nice because you dont' care whether its 2 or 20. Then merge them (left inner) to create a single date+time indexed csv files with metrics across the row. If you have a 1 second tick on your vmstat and iostat etc then the merge will be OK, if you are using longer ticks like 5 or 10 seconds then there coulld be drift, so use iris\_resample\_csv.py to line up the times first (using the hammer).

`TrakCare_Monitor.py`
- Quickly process TrakCare Monitor Data to collate and visualise some interesting metrics. Source data must be exported from the TrakCare Monitor Tool using "ExportAll".

### Pretty pButtons Charts

The script `pretty_pButtons.py` uses the sqlite database created using yape to make charts that can combine metrics for **Red Hat** (RHEL): vmstat, iostat and mgstat.
For example, this is handy if you need to output charts for performance reports. This is a preview, working towards an interactive solution.

There is also an option to output merged vmstat, iostat and mgstat as a csv file for you to work within other ways.

Formatting and chart creation is driven from two yml files, I have included samples;
`pretty_pButtons_input.yml` - instance details such as name and key disks eg: /dev/sde is sde. Also formatting details similar to yape.
`pretty_pButtons_chart.yml` - Attributes of charts to produce.

The workflow is;

0. Edit `pretty_pButtons_input.yml` and  `pretty_pButtons_chart.yml`. 
Maybe run yape first to see what it is you want to look at at or deep dive in to.
You will need the disk /dev names for Database, Primary and Alternate Journal, WIJ, and Caché/IRIS disk. The can all be the same.

1. Create sqlite file using yape;
`yape --filedb myfile.sqlite3 pButtonsHTMLfilename.html`

2. Here is an example:
`pretty_pButtons.py -f myfile.sqlite3 -s 10:00 -e 11:00 -p pretty_pButtons_input.yml -i -m -c pretty_pButtons_chart.yml -o ./pretty

_**There is very little error checking in the script**_

## Build docker image to run Python scripts

Docker file is included, you must have docker installed already
NOTE: the container is for Python scripts only, for example yape\_deep.sh cannot be run

```
$ docker build -t mut .
```
Check exists

```
$ docker image ls
REPOSITORY          TAG                 IMAGE ID            CREATED              SIZE
mut                 latest              e640c19160be        About a minute ago   1.1GB    
```

Run a script with included sample data

```
$ docker run -v `pwd`/INPUT:/data  --rm --name muttly mut  \
> ./iris_combine_csv.py -d /data
```

A file `all_csv.csv` will be created in folder `./INPUT`




    