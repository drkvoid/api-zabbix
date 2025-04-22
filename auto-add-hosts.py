#!/usr/bin/env python
# -*- coding: utf-8 -*-

#author: Janssen dos Reis Lima
#
#Forked by Scott Cunningham <scott@netaddicted.ca>
#Modified 2025/04 to work with the zabbix-bulk-add-template.ods sheet and add some flexability and readablility.
#Some assistance from Copilot and ChatGPT
#This script is designed to read a CSV file containing host information and create hosts in Zabbix using the Zabbix API.
#It uses the pyzabbix library to interact with the Zabbix API and the progressbar library to show progress.
#The CSV file should contain the following columns:
#hostname;ip;dns;groupid;templateid;inttype;port


from pyzabbix import ZabbixAPI
import csv
from progressbar import ProgressBar, Percentage, ETA, ReverseBar, RotatingMarker, Timer
import json
import sys
import os
# Add the directory containing the local library to the Python path
local_library_path = os.path.join(os.path.dirname(__file__), 'conf')
if os.path.exists(local_library_path):
    sys.path.append(local_library_path)
else:
    print(f"Configuration directory not found: {local_library_path}")
    exit(1)

# Import the local Configuration file
try:
    from vars import ZBX_SERVER, ZBX_USER, ZBX_PASS

except ImportError:
    print("Failed to import 'vars'. Ensure the 'conf' directory contains 'vars.py'.")
    exit(1)
    

#Uncomment for debugging
#=======================
#import logging
#stream = logging.StreamHandler(sys.stdout)
#stream.setLevel(logging.DEBUG)
#log = logging.getLogger('pyzabbix')
#log.addHandler(stream)
#log.setLevel(logging.DEBUG)
#=======================

hostsfile = "/tmp/hosts.csv"

#Set up the Zabbix API connection
zapi = ZabbixAPI(ZBX_SERVER)
zapi.login(ZBX_USER,ZBX_PASS)

#This code takes the input file into variable arq which is examined for the number of lines (records)
#for generating the ProgressBar (linhas)
#File is read a second time into ImportList to get the individual elements for each record, then call the zapi.host.create API.
#Need to build in error/bounds checking.

try:
    with open(hostsfile, 'r') as file:
        arq = csv.reader(file)
        linhas = sum(1 for linha in arq)        
except FileNotFoundError:
    print("File not found. Please check the file path and name.")
    exit(1)
except Exception as e:
    print(f"An error occurred: {e}")
    exit(1)
finally:
    # Close the file if it was opened
    pass  # File is automatically closed by the 'with' statement

try:
    # Reopen the file for processing
    with open(hostsfile, 'r') as file:
        ImportList = csv.reader(file, delimiter=';')
        bar = ProgressBar(maxval=linhas, widgets=[Percentage(), ReverseBar(), ETA(), RotatingMarker(), Timer()]).start()
        i = 0

        for row in ImportList:
            try:
                # Validate row length
                if len(row) != 7:
                    print(f"Skipping invalid row: {row}")
                    continue

                hostname, ip, dns, groupid, templateid, inttype, port = row

                # Validate required fields
                if not hostname or not ip or not groupid or not templateid:
                    print(f"Skipping row with missing required fields: {row}")
                    continue

                # Create host
                hostcreated = zapi.host.create(
                    host=hostname,
                    status=0,
                    interfaces=[{
                        "type": int(inttype),
                        "main": 1,
                        "useip": 1,
                        "ip": ip,
                        "dns": dns,
                        "port": port
                    }],
                    groups=[{
                        "groupid": groupid
                    }],
                    templates=[{
                        "templateid": templateid
                    }]
                )

                # Check API response
                if 'error' in hostcreated:
                    print(f"Error creating host {hostname}: {hostcreated['error']['message']} - {hostcreated['error']['data']}")
                else:
                    print(f"Host {hostname} created successfully.")

            except Exception as e:
                print(f"Error processing row {row}: {e}")

            i += 1
            bar.update(i)

        bar.finish()

except Exception as e:
    print(f"Error processing the file: {e}")
    exit(1)

print("Processing completed.")
