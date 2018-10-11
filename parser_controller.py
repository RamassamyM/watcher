#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import logging
import re
import csv
import json
import requests
import time
import yaml
from datetime import datetime
from time import sleep

formats = [{'name': 'actionlog', 'regexp': 'Log\.txt$', 'parser': 'self.parse_actionlog()'},
           {'name': 'sensorlog', 'regexp': '\d{4}\-\d{2}\-\d{2}\_logNGB\.csv$', 'parser': 'self.parse_sensorlog()'},
           {'name': 'xplog', 'regexp': '.*\.csv$', 'parser': 'self.parse_xplog()'},
           {'name': 'photo', 'regexp': '.*\.bmp$', 'parser': 'self.parse_photo()'},
           ]
with open('secrets.yml', 'r') as secrets:
    thingsboard_device_api_token = yaml.load(secrets)['thingsboard_device_api_token']
MAX_SIZE_FOR_API_POSTING = 8000

class ParserController(object):
    """Controller to dispatch file to good parser and to good transmitter"""

    def __init__(self, filepath):
        self.filepath = filepath
        self.parsed_log = None

    def identify_format_and_parse(self):
        for format in formats:
            if re.match(format['regexp'], self.filepath):
                logger.debug("File format is %s", format['name'])
                exec(format['parser'])
                break
        if self.parsed_log:
            self.send_json_to_thingsboard()
        else:
            logger.warning("Abort sending to Thingsboard")

    # def parse_actionlog(self):
    #     # TODO
    #
    #
    # def parse_sensorlog(self):
    #     # TODO

    def parse_xplog(self):
        with open(self.filepath) as csvfile:
            nb_of_unuseful_lines = 6
            headers = ['production_reference', 'operation_reference', 'date',
                       'time', 'plate', 'well', 'layer', 'job',
                       'temperature_°c', 'hygrometry_%', 'distance_um',
                       'z_auto_um', 'z_focus_um']
            filereader = csv.reader(csvfile, delimiter=';', quotechar="\"")
            logs = []
            ts_previous_base = 0
            ts_previous = 0
            for index, row in enumerate(filereader, start=1):
                if index > nb_of_unuseful_lines:
                    ts_in_s = datetime.strptime(row[2] + ' ' + row[3], '%Y-%m-%d %H:%M').timestamp()
                    ts_in_ms = ts_previous + 1 if ts_in_s == ts_previous_base else ts_in_s * 1000
                    ts_previous_base = ts_in_s
                    ts_previous = ts_in_ms
                    log = { 'ts': ts_in_ms }
                    values = {}
                    for num, header in enumerate(headers):
                        try:
                            # we do not want to log a date and time value and empty value
                            if row[num] and row[num].strip() and num != 2 and num != 3 :
                                values[header] = row[num]
                        except IndexError:
                            pass
                    log['values'] = values
                    logs.append(log)
        try:
            pretty_json = str(json.dumps(logs, sort_keys=True, indent=4))
            logger.debug("json generated is :\n%s", pretty_json[0:400] + '\n...\n...\n' + pretty_json[-400:])
            self.parsed_log = logs
        except (TypeError, OverflowError):
           logger.critical("Could not convert in json the logs")

    # def parse_photo(self):
    #     # TODO

    def send_json_to_thingsboard(self):
        logger.debug("Begin transfer json to thingsboard")
        parsed_log = self.parsed_log
        payload = json.dumps(parsed_log)
        api_url = "http://192.168.0.216:8080/api/v1/%s/telemetry" %thingsboard_device_api_token
        total_payload_size = len(payload)
        total_payload_elements = len(parsed_log)
        nb_of_slices = total_payload_size / MAX_SIZE_FOR_API_POSTING
        max_nb_elts_by_slice = int(round(total_payload_elements / nb_of_slices))
        payloads = [parsed_log[x:x+max_nb_elts_by_slice] for x in range(0, total_payload_elements, max_nb_elts_by_slice)]
        logger.debug("Will send data in %d slices", nb_of_slices + 1)
        for index, each_payload in enumerate(payloads):
            for x in range(3):
                logger.debug("Trying to send payload n°%d among %d", index + 1, nb_of_slices + 1)
                status = self.post_api(api_url, each_payload)
                sleep(2)
                if status:
                    break
                else:
                    logger.warning("Attempt to post to api failed, may retry")
        logger.debug("Finished sending to Thingsboard")

    def post_api(self, api_url, payload):
        r = requests.post(api_url, json=payload)
        status = r.status_code == requests.codes.ok
        if status:
            logger.debug('Api response status : ' + str(r.status_code) + ' - ' + r.text[:300])
        else:
            logger.critical('Api response status : ' + str(r.status_code) + ' - ' + str(r.reason) + r.text[:300] + str(r.headers))
        return status

if __name__ == '__main__':
    logging.basicConfig(filename='/tmp/watcher.log',
                        format='%(asctime)s\t%(levelname)s  -- P_%(process)d:%(filename)s:%(funcName)s:%(lineno)s \t-- %(message)s',
                        datefmt='%Y-%m-%dT%H:%M:%S,%03d.%z',
                        level=logging.DEBUG)
    logger = logging.getLogger()
    logger.info("Parser_controller started")
    args = sys.argv
    if len(args) >= 2:
        filepath = args[1]
        logger.debug("Path to file to parse and send : %s", filepath)
        p = ParserController(filepath)
        p.identify_format_and_parse()
    else:
        logger.critical('Error 1 parameter needed : filepath')
