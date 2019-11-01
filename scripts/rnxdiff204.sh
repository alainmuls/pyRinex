#!/bin/bash

/home/amuls/amPython/pyRinex/am/rnxdiff.py -g Galileo -s C1A C6A -d ~/RxTURP/BEGPIOS/BEGP/rinex/19204/csv/ -f Inte204MN-19-nc-E-C1A.csv Inte204MN-19-nc-E-C6A.csv

/home/amuls/amPython/pyRinex/am/rnxdiff.py -g Galileo -s S1A S6A -d ~/RxTURP/BEGPIOS/BEGP/rinex/19204/csv/ -f Inte204MN-19-nc-E-S1A.csv Inte204MN-19-nc-E-S6A.csv

/home/amuls/amPython/pyRinex/am/rnxdiff.py -g Galileo -s L1A L6A -d ~/RxTURP/BEGPIOS/BEGP/rinex/19204/csv/ -f Inte204MN-19-nc-E-L1A.csv Inte204MN-19-nc-E-L6A.csv
