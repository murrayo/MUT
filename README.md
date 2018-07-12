# MUT - Murray's Unsupported Tools

A place to share my noodlings and helper tools. Most are orientated around my work unpacking and vsiualising system performance data. Just a big bag to store my stuff. If you find them useful, great!

As the title says. These tools are not supported, but suggestions, tips, fixes!, and any other comments welcome. I am a hacker, in the sense "...a person who loves to stay up all night, he and the machine in a love-hate relationship...". 

> As Abraham Maslow said in 1966, "I suppose it is tempting, if the only tool you have is a hammer, to treat everything as if it were a nail." My current favorite tool for everything is Python, so you will see a lot of that here -- as I learn Python -- so code is bound to be not best practice.

Current Python Version;

	python --version
	Python 3.6.4 :: Anaconda custom (64-bit)

<hr>

## Manipulating csv files

Many of the tools in this section are built to further process csv files output from [yape](https://github.com/murrayo/yape), but they could be bent to other uses. The date+time indexed csv files include; mgstat, vmstat, and iostat. Ultimately the plan is for standalone functionality in these scripts will be included in yape.

iris\_resample\_csv.py 
- refactor set of timestamped csv files so that all times are in synch. This is useful if you run iris\_combine\_csv.py to merge csv files, eg mgstat, vmstat, and iostat into a super csv file for further processing.

iris\_combine\_csv.py
- Build a master list of dataframes for each csv file. This is nice because you dont' care whether its 2 or 20. Then merge them (left inner) to create a single date+time indexed csv files with metrics across the row.


