#!/bin/bash

/home/amuls/amPython/pyRinex/am/rnxdiff.py -g "Galileo PRS" -s S1A S6A -d ~/Nextcloud/E6BEL/19217/csv/ -f BEGP2170-19-nc-E-S1A.csv BEGP2170-19-nc-E-S6A.csv -m 600

/home/amuls/amPython/pyRinex/am/rnxdiff.py -g "Galileo PRS" -s S1A S6A -d ~/Nextcloud/E6BEL/19217/csv/ -f BEGP217KL-19-nc-E-S1A.csv BEGP217KL-19-nc-E-S6A.csv -m 600
