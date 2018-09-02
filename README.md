# MUT - Murray's Unsupported Tools

A place to share my noodlings and helper tools. Most are orientated around my work unpacking and vsiualising system performance data. Just a big bag to store my stuff. If you find them useful, great!

As the title says. These tools are not supported, but suggestions, tips, fixes!, and any other comments welcome.  

> As Abraham Maslow said in 1966, "I suppose it is tempting, if the only tool you have is a hammer, to treat everything as if it were a nail." My current favorite tool for everything is Python, so you will see a lot of that here -- as I learn Python -- so code is bound to be not best practice.

Current Python Version;

	python --version
	Python 3.6.4 :: Anaconda custom (64-bit)
	
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




    