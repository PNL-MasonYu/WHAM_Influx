import traceback
import concurrent.futures
import logging

from serial_logging import *

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
    
    #executor.submit(persistent_write_to_db, write_api, "Helium", org, read_Lakeshore_Kelvin, "lakeshore")
    executor.submit(persistent_write_to_db, write_api, "Helium", org, read_Cryomech_Compressor, 'C:/Users/WHAMuser/Desktop/Influxdb Data Logging/CPTLog.txt')
    executor.submit(persistent_write_to_db, write_api, "Helium", org, read_LN2_scale, 'LN2_SCALE')
    #executor.submit(persistent_write_to_db, write_api, "Vacuum", org, read_Extorr_RGA, "E:\RGALogs")
    #executor.submit(persistent_write_to_db, write_api, "Helium", org, read_recondenser_controller, "recondenser")
    #executor.submit(persistent_write_to_db, write_api, "Vacuum", org, read_vacuum_pressure, "PM31")
    #executor.submit(persistent_write_to_db, write_api, "Helium", org, read_gyrotron_lvl, "AM1700")
    executor.submit(persistent_write_to_db, write_api, "Helium", org, read_Lakeshore_Telnet, "192.168.1.87")
    #executor.submit(persistent_write_to_db, write_api, "Control_System", org, michael.read_michael_data, michael_controlfile)
    #executor.submit(persistent_write_to_db, write_api, "Control_System", org, michael.read_shot_data, michael_shotfile)

    return

if __name__ == '__main__':
    # Configure logging file
    start_time = time.localtime()
    err_file = "log_" + time.strftime("%Y_%m_%d_%H-%M", start_time) + ".csv"
    logging.basicConfig(filename=err_file, level=logging.DEBUG)

    # The token is unique to WHAM AWS service, do not delete it
    cloud_token = "4AMxSRRqZ-F5y35r7WFM9kyU9oDL50AfyVfcB2lAKrZUDeRHaEZMRPjn9K2TIUfL4iMW4Os7H2OfhKFemU1S1w=="
    cloud_org = "WHAM_Influx"

    # This token is for the localhost DB
    local_token = "1S49cxWeukQNzk-M0No48Sz1PocbtgSf2Q8l9w5C2j17nj7Q4yoj-cV0UEeSGam3GP46oywU7DyEfauLoPnEwQ=="
    local_org = "WHAM"

    # This is for the DB running on Andrew
    #token = "VgX10ZPPxNYECSjl9qlZVOqMm0FU4DZmfkzED9qwevwTR_--MpNvx0LSFGOp87rCc9Kmq2fyuNz9Dcsoe3RRNQ=="
    #org = "WHAM"

    cloud_client = InfluxDBClient(url="https://us-east-1-1.aws.cloud2.influxdata.com", token=cloud_token, org=cloud_org)
    local_client = InfluxDBClient(url="http://localhost:8086", token=local_token, org=local_org)
    #client = InfluxDBClient(url="http://andrew.psl.wisc.edu:8080", token=token, org=org)

    cloud_write_api = cloud_client.write_api(write_options=SYNCHRONOUS)
    local_write_api = local_client.write_api(write_options=SYNCHRONOUS)

    serial_set_up()
    with concurrent.futures.ThreadPoolExecutor(max_workers=18) as executor:
        #write_to_DB(executor, cloud_write_api, cloud_org)
        write_to_DB(executor, local_write_api, local_org)