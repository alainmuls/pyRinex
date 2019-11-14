#!/bin/bash

	/home/amuls/amPython/pyRinex/am/rnxdiff.py -g Galileo -s S1C S5Q -d ~/RxTURP/BEGPIOS/ASTX/rinex/19250/nc/csv/ -f COMB2500-19O-nc-E-S1C.csv  COMB2500-19O-nc-E-S5Q.csv

	/home/amuls/amPython/pyRinex/am/rnxdiff.py -g Galileo -s C5C C5Q -d ~/RxTURP/BEGPIOS/ASTX/rinex/19250/nc/csv/ -f COMB2500-19O-nc-E-C1C.csv  COMB2500-19O-nc-E-C5Q.csv
