#!/bin/bash

/home/amuls/amPython/pyRinex/am/rnxdiff.py -g Galileo -s S1A S6A -d ~/Nextcloud/E6BEL/19255/csv/ -f STNK2550-19-nc-E-S1A.csv STNK2550-19-nc-E-S6A.csv

/home/amuls/amPython/pyRinex/am/rnxdiff.py -g Galileo -s C1A C6A -d ~/Nextcloud/E6BEL/19255/csv/ -f STNK2550-19-nc-E-S1A.csv STNK2550-19-nc-E-S6A.csv
