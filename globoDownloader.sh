#!/bin/bash

cd $(dirname $0)

#Store start time in a variable to calculate total execution time
START=$(/opt/Python-2.7/bin/python -c "from time import *; print int(time())")

echo "******************************************** "
echo "**    run on $(date) "
echo "******************************************** "


PYTHONPATH=/home/rafael/globo.tv/plugin.video.globotv-plugin.video.globotv-0.5.5.1/ /opt/Python-2.7/bin/python globoDownloader.py $@

END=$(/opt/Python-2.7/bin/python -c "from time import *; print int(time())")

#Calculates difference
DIFF=$(( $END - $START ))
DIFF_MIN=$(( $DIFF / 60 ))

echo "******************************************** "
echo "**    End run on $(date) - Total Execution (Minutes) - $DIFF_MIN "
echo "******************************************** "
