import traceback
import concurrent.futures
import logging

from serial_logging import *
from AMI_1700_liquid_level import read_AMI_Telnet
from srs_rga import read_SRS_RGA
from baratron import read_baratron_rp
from read_ion_gauge import read_ion_gauge
from NBI_ion_gauge import read_NBI_gauge_rp
from shot_number import read_shot_number
from osaka_turbo_controller import read_osaka_turbo

from ssh_logging import remote_logging
from influxdb_client import InfluxDBClient, ReturnStatement
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
from influxdb_client.client import write_api

def persistent_write_to_db(write_api, bucket, org, read_function, arg):
    # Persistently write data to the database in bucket after executing the read_function
    while True:
        try:
            result = read_function(arg)
            # Check that the read function has actually returned something with active instruments
            if result == None:
                log_detail = "No results returned from " + read_function.__name__
                log_error(log_detail)

            elif result == 0:
            # This is returned if the function is reading from a remote location and there's nothing new
                pass
                
            elif len(result) > 0:
                write_api.write(bucket, org, result)
            
        except KeyboardInterrupt:
            print("logging ended")
            break
        except:
            # writing error to csv file, timeout to prevent filling the hard drive
            exception_details = traceback.format_exc()
            log_error(exception_details)
            # Just close and open all the serial ports to see if the issue will fix itself
            time.sleep(1)
            #for port in all_ports.items():
            #    close_open_port(port)
            #serial_set_up()


def write_to_DB(executor, write_api, org):
    """
    Write to the InfluxDB by starting threads
    """
    #michael = michael_logging_setup()
    #michael_controlfile = "/mnt/c/Users/WHAMuser/Documents/Data Logging/Control_System_Data.csv"
    #michael_shotfile = "/mnt/c/Users/WHAMuser/Documents/Data Logging/shot_data.csv"
    
    # Comment out things that does not need to be logged
    
    
    executor.submit(persistent_write_to_db, write_api, "helium", org, read_Lakeshore_Kelvin, "lakeshore_NBI")
    #executor.submit(persistent_write_to_db, write_api, "helium", org, read_Cryomech_Compressor, 'C:/Users/WHAMuser/Desktop/Influxdb Data Logging/CPTLog.txt')
    #executor.submit(persistent_write_to_db, write_api, "helium", org, read_LN2_scale, 'LN2_SCALE')
    #executor.submit(persistent_write_to_db, write_api, "Vacuum", org, read_Extorr_RGA, "E:\RGALogs")
    #executor.submit(persistent_write_to_db, write_api, "helium", org, read_recondenser_controller, "recondenser")
    #executor.submit(persistent_write_to_db, write_api, "Vacuum", org, read_vacuum_pressure, "PM31")
    #executor.submit(persistent_write_to_db, write_api, "helium", org, read_gyrotron_lvl, "AM1700")
    executor.submit(persistent_write_to_db, write_api, "helium", org, read_AMI_Telnet, "192.168.130.200") #gyrotron liquid level
    executor.submit(persistent_write_to_db, write_api, "helium", org, read_AMI_Telnet, "192.168.130.232") #NBI liquid level
    #executor.submit(persistent_write_to_db, write_api, "Control_System", org, michael.read_michael_data, michael_controlfile)
    #executor.submit(persistent_write_to_db, write_api, "Control_System", org, michael.read_shot_data, michael_shotfile)
    executor.submit(persistent_write_to_db, write_api, "Vacuum", org, read_maxigauge, "192.168.130.195")
    executor.submit(persistent_write_to_db, write_api, "Vacuum", org, read_ADAM_6015, "192.168.130.126") #end cell bolometers
    executor.submit(persistent_write_to_db, write_api, "Vacuum", org, read_ADAM_6015, "192.168.130.125") #cc bolometers
    executor.submit(persistent_write_to_db, write_api, "Vacuum", org, read_baratron_rp, "192.168.130.212")
    #executor.submit(persistent_write_to_db, write_api, "Vacuum", org, read_ion_gauge, "rp-f09303.local")
    #executor.submit(persistent_write_to_db, write_api, "Vacuum", org, read_ion_gauge, "rp-f0be68.local")
    executor.submit(persistent_write_to_db, write_api, "Vacuum", org, read_SRS_RGA, '/dev/ttyUSB0') #CC RGA
    executor.submit(persistent_write_to_db, write_api, "Vacuum", org, read_SRS_RGA, '/dev/ttyUSB3') #SEC RGA
    executor.submit(persistent_write_to_db, write_api, "Vacuum", org, read_NBI_gauge_rp, "rp-f0bd65.local")
    executor.submit(persistent_write_to_db, write_api, "Vacuum", org, read_osaka_turbo, "/dev/ttyUSB4")
    executor.submit(persistent_write_to_db, write_api, "Vacuum", org, read_osaka_turbo, "/dev/ttyUSB5")
    executor.submit(persistent_write_to_db, write_api, "Vacuum", org, read_osaka_turbo, "/dev/ttyUSB6")
    #executor.submit(persistent_write_to_db, write_api, "System", org, read_shot_number, "andrew.psl.wisc.edu")

    return

if __name__ == '__main__':
    # Configure logging file
    start_time = time.localtime()
    err_file = "/mnt/n/whamdata/InfluxDB_logs/log_" + time.strftime("%Y_%m_%d_%H-%M", start_time) + ".csv"
    logging.basicConfig(filename=err_file, level=logging.ERROR)

    # The token is unique to WHAM AWS service, do not delete it
    cloud_token = "4AMxSRRqZ-F5y35r7WFM9kyU9oDL50AfyVfcB2lAKrZUDeRHaEZMRPjn9K2TIUfL4iMW4Os7H2OfhKFemU1S1w=="
    cloud_org = "WHAM_Influx"

    # This token is for the localhost DB
    #local_token = "1S49cxWeukQNzk-M0No48Sz1PocbtgSf2Q8l9w5C2j17nj7Q4yoj-cV0UEeSGam3GP46oywU7DyEfauLoPnEwQ=="
    #local_org = "WHAM"

    # This is for the DB running on Andrew
    token = "_h8EHu5V5jF_u9dHjqHPH4eL1uDYOY25auKPTa9Z9e0R_jJMHhvqbhlcxQfeq9QG2KsJnlvurS1IsSVym5D7UA=="
    andrew_org = "WHAM"

    #cloud_client = InfluxDBClient(url="https://us-east-1-1.aws.cloud2.influxdata.com", token=cloud_token, org=cloud_org)
    #local_client = InfluxDBClient(url="http://localhost:8086", token=local_token, org=local_org)
    andrew_client = InfluxDBClient(url="http://andrew.psl.wisc.edu:8086", token=token, org=andrew_org)

    #cloud_write_api = cloud_client.write_api(write_options=SYNCHRONOUS)
    #local_write_api = local_client.write_api(write_options=SYNCHRONOUS)
    andrew_write_api = andrew_client.write_api(write_options=SYNCHRONOUS)

    serial_set_up()
    with concurrent.futures.ThreadPoolExecutor(max_workers=18) as executor:
        #write_to_DB(executor, cloud_write_api, cloud_org)
        #write_to_DB(executor, local_write_api, local_org)
        write_to_DB(executor, andrew_write_api, andrew_org)