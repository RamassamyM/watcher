#!/bin/bash
# make it executable
# 2 parameters needed : filedirectory and filename
filedirectory=$1
filename=$2
# the parser_controller use regexp formats on filename to find the good parser to use
format_NGBactionlog="Log\.txt$"
action_NGBactionlog="./parsers/parse_ngb_actionlog"

format_NGBxplog=".*\.csv$"
action_NGBxplog="./parsers/parse_ngb_xplog"

format_NGBsensorlog="\d{4}\-\d{2}\-\d{2}\_logNGB\.csv$"
action_NGBsensorlog="./parsers/parse_ngb_sensorlog"

format_NGBphoto=".*\.bmp$"
action_NGBphoto="./parsers/parse_ngb_photo"

# the parser_controller send result of parsing to a transmitter that requires an api access_token
SEND_COMMAND="send_thingsboard"
access_token="NnQwUUeh2lPUniZXnBaL"

# common function to call the parser then call thingsboard parser
function parse_and_send {
  COMMAND=$0
  filedirectory=$1
  filename=$2
  PARSED_LOG="$(ruby $COMMAND $filedirectory $filename)"
  if [ ! $PARSED_LOG == "ERROR" ]
    ./log $0 "SUCCESS : parsed log is ${$PARSED_LOG:0:100}...${$PARSED_LOG: -100}"
    ruby $SEND_COMMAND "$PARSED_LOG" "$access_token" && ./log $0 "SUCCESS : transfer thingsboard" || ./log $0 "ERROR : transfer thingsboard"
  else
  ./log $0 "ERROR : while parsing $filedirectory/$filename"
  fi
}

# redirect to good parser according to format of filename
./log $0 "CHECK parsing format of $filename in $filedirectory"
if [[ $filename =~ $format_NGBactionlog ]]
then
  COMMAND=$action_NGBactionlog
  ./log $0 "FORMAT NGBactionlog detected..."
  parse_and_send $COMMAND $directory $filename
elif [[ $filename =~ $format_NGBsensorlog ]]
then
  COMMAND=$action_NGBsensorlog
  ./log $0 "FORMAT NGBsensorlog detected..."
  parse_and_send $COMMAND $directory $filename
elif [[ $filename =~ $format_NGBxplog ]]
then
  COMMAND=$action_NGBxplog
  ./log $0 "FORMAT NGBxplog detected..."
  # parse_and_send $COMMAND $directory $filename
elif [[ $filename =~ $format_NGBphoto ]]
then
  COMMAND=$action_NGBphoto
  ./log $0 "FORMAT NGBphoto detected..."
  # parse_and_send $COMMAND $directory $filename
else
  ./log $0 "PASS : no existing parser for this format"
fi
