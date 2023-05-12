#!/bin/sh
# @Author: xiaocao
# @Date:   2023-05-12 09:46:24
# @Last Modified by:   xiaocao
# @Last Modified time: 2023-05-12 10:15:53

: ${SLEEP_SECOND:=2}

wait_for() {
    echo Waiting for $1 to listen on $2...
    while ! nc -z $1 $2; do
        echo waiting...
        sleep $SLEEP_SECOND
    done
}


while getopts "d:c:" arg; do
    case $arg in
    d)
        DEPENDS=$OPTARG
        ;;
    c)
        CMD=$OPTARG
        ;;
    ?)
        echo "unkonw argument"
        exit 1
        ;;
    esac
done

for var in ${DEPENDS//,/ }; do
    host=${var%:*}
    port=${var#*:}
    wait_for $host $port
done

eval $CMD
