#!/bin/bash

#configure the env variable below based on how your system is configured

PYTHON_EXEC=/opt/Python-2.7/bin/python
export PYTHONPATH=/home/rafael/globo.tv/plugin.video.globotv-plugin.video.globotv-0.5.5.1/


cd $(dirname $0)
#Store start time in a variable to calculate total execution time
START=$($PYTHON_EXEC -c "from time import *; print int(time())")

echo "******************************************** "
echo "**    run on $(date) "
echo "******************************************** "


running=$(ps -eaf | grep globoDownloader.py | grep -v grep | wc -l)
echo "** running job $(basename $0) on $(date) running = $running"

if [ $running -gt 0 ]; then
    echo "** job already running @ running = $running ..."
    echo "** will not run again... "
else
    $PYTHON_EXEC ./globoDownloader.py $@
fi



END=$($PYTHON_EXEC -c "from time import *; print int(time())")

#Calculates difference
DIFF=$(( $END - $START ))
DIFF_MIN=$(( $DIFF / 60 ))

echo "******************************************** "
echo "**    End run on $(date) - Total Execution (Minutes) - $DIFF_MIN "
echo "******************************************** "
