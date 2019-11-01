#!/bin/bash

/home/amuls/amPython/pyRinex/am/rnxdiff.py -g "Galileo PRS" -s S1A S6A -d ~/Nextcloud/E6BEL/19219/csv/ -f BEGP219G-19-nc-E-S1A.csv BEGP219G-19-nc-E-S6A.csv

/home/amuls/amPython/pyRinex/am/rnxdiff.py -g "Galileo PRS" -s C1A C6A -d ~/Nextcloud/E6BEL/19219/csv/ -f BEGP219G-19-nc-E-C1A.csv BEGP219G-19-nc-E-C6A.csv
