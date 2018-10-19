#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
# need a file called logger.py in same directory
from logger import initialize_logger
import re
import csv
import json
import requests
import time
import yaml
from datetime import datetime
from time import sleep

formats = [{'name': 'myparser1', 'regexp': '.*\d{4}\-\d{2}\-\d{2}\_log\.csv$', 'parser': 'self.myparser1'},]
with open('secrets.yml', 'r') as secrets:
    api_token = yaml.load(secrets)['api_token']
MAX_SIZE_FOR_API_POSTING = 8000

# Configuring logging system
logger = initialize_logger()

class ParserController(object):
    """Controller to dispatch file to good parser and to good transmitter"""

    def __init__(self, filepath):
        self.filepath = filepath
        self.parsed_log = None

    def identify_format_and_parse(self):
        for format in formats:
            # logger.debug("Test formats : %s on %s", format['name'], self.filepath)
            if re.match(format['regexp'], self.filepath):
                logger.debug("RIGHT Format %s for %s", format['name'], self.filepath)
                try:
                    exec(format['parser'])
                except Exception as e:
                    logger.debug("Error : %s", e)
                break
            else:
                logger.debug("WRONG Format %s for %s", format['name'], self.filepath)
        if self.parsed_log:
            logger.debug("Send to API : %s", self.filepath)
            self.send_json_to_API()
        else:
            logger.error("ABORT sending to API : %s", self.filepath)

    def myparser1(self):
        logger.debug("START parser1")
        datematch = re.match('.*(?P<date>\d{4}-\d{2}-\d{2}).*', self.filepath)
        with open(self.filepath, newline='', 'r', encoding='ISO-8859-1', errors='ignore') as csvfile:
            filereader = csv.DictReader(csvfile, delimiter=';', quotechar="\"")
            logs = []
            logger.debug("START parsing csv file")
            for row in filereader:
                ts_in_ms = datetime.strptime(datematch.group('date') + ' ' + row['Heure'], '%Y-%m-%d %H:%M:%S').timestamp() * 1000
                log = { 'ts': ts_in_ms }
                values = {}
                for key, value in row.items():
                        if key != 'Heure' and key:
                            values[key] = value
                log['values'] = values
                logs.append(log)
        try:
            pretty_json = str(json.dumps(logs, sort_keys=True, indent=4))
            logger.debug("json generated is :\n%s", pretty_json[0:400] + '\n...\n...\n' + pretty_json[-400:])
            self.parsed_log = logs
        except (TypeError, OverflowError) as e:
            logger.debug("Could not convert in json the logs : %s", e)

    def send_json_to_API(self):
        logger.debug("Begin transfer json to API")
        parsed_log = self.parsed_log
        payload = json.dumps(parsed_log)
        api_url = "url/to/api/%s" %thingsboard_device_api_token
        total_payload_size = len(payload)
        total_payload_elements = len(parsed_log)
        nb_of_slices = total_payload_size / MAX_SIZE_FOR_API_POSTING
        max_nb_elts_by_slice = int(round(total_payload_elements / nb_of_slices))
        payloads = [parsed_log[x:x+max_nb_elts_by_slice] for x in range(0, total_payload_elements, max_nb_elts_by_slice)]
        logger.debug("Will send data in %d slices", nb_of_slices + 1)
        success_status = True #initialize status
        for index, each_payload in enumerate(payloads):
            for x in range(3):
                logger.debug("Trying to send payload n°%d among %d", index + 1, nb_of_slices + 1)
                status = self.post_api(api_url, each_payload)
                sleep(2)
                if status:
                    break
                elif x == 2:
                    logger.error("FAIL posting to API : filepath %s ; payload %d / %d : %s", self.filepath, index + 1, nb_of_slices + 1, each_payload)
                    success = False
                else:
                    logger.debug("Attempt to post to API failed, may retry")
        logger.debug("Finished sending to API")
        if success:
            logger.warning("SUCCESS : send %s", self.filepath)
        else:
            logger.error("ERROR : send %s", self.filepath)

    def post_api(self, api_url, payload):
        r = requests.post(api_url, json=payload)
        status = r.status_code == requests.codes.ok
        if status:
            logger.debug('API response status : ' + str(r.status_code) + ' - ' + r.text[:300])
        else:
            logger.debug('API response status : ' + str(r.status_code) + ' - ' + str(r.reason) + r.text[:300] + str(r.headers))
        return status

if __name__ == '__main__':
    logger.debug("Parser_controller started")
    args = sys.argv
    if len(args) >= 2:
        filepath = args[1]
        regexp_matching = re.match('^\'(.*)\'$', filepath) # clean filepath
        if regexp_matching:
            filepath = regexp_matching.group(1)
        logger.debug("File to parse and send : %s", filepath)
        p = ParserController(filepath)
        p.identify_format_and_parse()
    else:
        logger.debug('Error 1 parameter needed : filepath')
