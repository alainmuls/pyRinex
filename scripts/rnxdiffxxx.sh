#!/bin/bash

ROOTDIR=${HOME}/Nextcloud/E6BEL

for YY in 18 19
do
	for DOY in 353 017 027 037 047 057 067 077 087 097 107 117
	do
		echo ${ROOTDIR}/${YY}${DOY}
		if [ -d ${ROOTDIR}/${YY}${DOY} ]
		then
			# ls -l ${ROOTDIR}/${YY}${DOY}
			/home/amuls/amPython/pyRinex/am/rnxdiff.py -g "Galileo PRS" -s S1A S6A -d ${ROOTDIR}/${YY}${DOY}/csv/ -f BEGP${DOY}0-${YY}-nc-E-S1A.csv BEGP${DOY}0-${YY}-nc-E-S6A.csv -m 600

		fi
	done
done

