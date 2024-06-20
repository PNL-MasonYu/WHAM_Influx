import os
import serial
import time
import csv
import traceback
from telnetlib import Telnet
from pymodbus.client import ModbusTcpClient

from ssh_logging import remote_logging
from influxdb_client import InfluxDBClient, ReturnStatement
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client import write_api

import logging
import matplotlib.pyplot as plt
import pyrga # install package

# turn off logging
logging.getLogger('pyrga').setLevel(logging.CRITICAL)

# SINGLE MASS SCAN ##
if __name__ == "__main__":
    # initialize client with non-default noise floor setting
    RGA = pyrga.RGAClient("/dev/ttyUSB0", noise_floor=0)
    # check filament status and turn it on if necessary
    if not RGA.get_filament_status():
        RGA.turn_on_filament()
    # read partial pressures of air constituent
    MASSES = {
        18: "H2O",
        28: "N2",
        32: "O2",
        40: "Ar",
    }
    for m, i in MASSES.items():
        print("partial pressure of element {} is {} Torr".format(i, RGA.read_mass(m)))

# ## SPECTRUM SCAN ##
# if __name__ == "__main__":
#     # initialize client with default settings
#     RGA = pyrga.RGAClient("/dev/ttyUSB0")
#     # check filament status and turn it on if necessary
#     if not RGA.get_filament_status():
#         RGA.turn_on_filament()
#     # read analog scan of 1-50 mass range with max resolution of 25 steps per amu
#     masses, pressures, total = RGA.read_spectrum(1, 50, 25)

#     plt.plot(masses, pressures)
#     plt.yscale('log')
#     plt.ylim(1e-9, 1e-6)
#     plt.show()


def read_SRS_RGA(port_key):
    msg = []
    msg.append("RGA_100,sensor= pressure=" + )
    return msg
