import os
import serial
import time
import csv
import traceback
import concurrent.futures

from influxdb_client import InfluxDBClient, ReturnStatement
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client import write_api

n_row = 0

def serial_set_up():
    # Setting up all the serial ports
    # Returns a list of ports that are opened
    all_ports = {}
    print("Attempting to open all serial ports")
    # Lakeshore temperature monitor
    ser_lakeshore = serial.Serial()
    ser_lakeshore.baudrate = 9600
    ser_lakeshore.port = "COM12"
    ser_lakeshore.parity = serial.PARITY_ODD
    ser_lakeshore.bytesize = serial.SEVENBITS
    ser_lakeshore.timeout=0.5
    if not ser_lakeshore.is_open:
        try:
            ser_lakeshore.open()
        except:
            log_error(err_file, "Failed to open Lakeshore temperature monitor port " + ser_lakeshore.port)
    all_ports["lakeshore"] = ser_lakeshore

    # HRC-100 Helium recondenser controller serial port
    ser_recondenser = serial.Serial()
    ser_recondenser.baudrate = 9600
    ser_recondenser.port = "COM14"
    ser_recondenser.timeout = 0.5
    if not ser_recondenser.is_open:
        try:
            ser_recondenser.open()
            # Skip through the initialization screen from the HRC-100 and get into monitor mode
            ser_recondenser.write(bytes("\n", "ASCII"))
            time.sleep(1)
            ser_recondenser.write(bytes("t\n", "ASCII"))
            # Clear serial buffer
            ser_recondenser.readlines()
        except:
            log_error(err_file, "Failed to open HRC-100 recondenser controller serial port " + ser_recondenser.port)
    all_ports["recondenser"] = ser_recondenser

    # PM31 Gauge Controller (Main chamber)
    ser_PM31 = serial.Serial()
    ser_PM31.baudrate = 2400
    ser_PM31.port = "COM13"
    ser_PM31.timeout = 0.5
    ser_PM31.parity = serial.PARITY_NONE
    if not ser_PM31.is_open:
        try:
            ser_PM31.open()
        except:
            log_error(err_file, "Failed to open PM31 Gauge Controller serial port " + ser_PM31.port)
    all_ports["PM31"] = ser_PM31

    # American Magnetics Model 1700 liquid level instrument
    ser_1700 = serial.Serial()
    ser_1700.baudrate = 115200
    ser_1700.port = "COM10"
    ser_1700.parity = serial.PARITY_NONE
    ser_1700.stopbits = serial.STOPBITS_ONE
    ser_1700.bytesize = serial.EIGHTBITS
    if not ser_1700.is_open:
        try:
            ser_1700.open()
            """
            # Set the unit of measurement to be %
            ser_1700.write(bytes("CONFigure:N2:UNIT 0\r", "ASCII"))
            time.sleep(0.5)
            ser_1700.readline()
            ser_1700.write(bytes("CONFigure:HE:UNIT 0\r", "ASCII"))
            time.sleep(0.5)
            ser_1700.readline()
            """
        except:
            log_error(err_file, "Failed to open American Magnetics 1700 liquid level instrument port " + ser_1700.port)
    all_ports["AM1700"] = ser_1700

    print(all_ports)
    return all_ports

def read_Lakeshore_Kelvin(port):
    port.write(bytes("KRDG? 0\n", "ASCII"))
    data = str(port.readlines()[0])[2:-5].split(',')
    temps = []
    for n in range(len(data)):
        temps.append("temperature,sensor=ch{:} temp={:}".format(n+1,float(data[n])))
    time.sleep(10)
    return temps

def read_Cryomech_Compressor(file):
    # Read the logged file from the LabView program that monitors the Cryomech compressor
    with open(file, "r") as CPTLog:
        csvreader = csv.reader(CPTLog, delimiter="	")
        title = next(csvreader)
        heading = next(csvreader)
        for row in csvreader:
            pass
        latest_status = []
        for n in range(1, len(row)):
            latest_status.append("CP1000_Compressor,sensor="+ heading[n].replace(" ", "") + " data_field={:}".format(float(row[n])))
        CPTLog.close()
        #print(latest_status)
    time.sleep(10)
    return latest_status

def read_Extorr_RGA(dir):
    # Read the logged directory from the Extorr Vacuum Plus software
    # Reads the rows after n_row from last time it was read
    global n_row
    log_files = os.listdir(dir)
    current_time = time.localtime()
    # Generate the current date
    date_string = time.strftime("%Y%m%d", current_time)
    for file_name in log_files:
        if file_name.split('-')[2] == date_string:
            file = dir + "\\" + file_name
            break
        else:
            # Could not find entry corresponding to the current date
            return
    with open(file, "r") as RGALog:
        csvreader = csv.reader(RGALog)
        latest_data = []
        for row in csvreader:
            last_row = row
        latest_data.append("ExTorr_X100_RGA,sensor=" + str(float(last_row[1])) +
                          " intensity=" + str(float(last_row[2])))
        #print(latest_data)
        RGALog.close()
        time.sleep(10)
        return

def read_recondenser_controller(port):
    # Reads the recondenser controller heater power and temperature monitor
    data = str(port.readline())
    #print(data)
    empty_counter = 0
    if data == "b''":
        # Just keep reading lines every 500 ms if there's nothing from the monitor
        while data == "b''":
            empty_counter += 1
            time.sleep(0.5)
            data = str(port.readline())
            # If the controller does not respond within 10 seconds, send a command to enable monitor mode and break
            if empty_counter > 20:
                port.write(bytes("t\n", "ASCII"))
                #print(port.readlines())
                empty_counter = 0
                break

    if not data == "b''":
        #print(data)
        pressure = data.split(' ')[1]
        heater_pwr = data.split(' ')[5]
        return ["Cryomech_HRC-100_Recondenser,sensor=pressure PSI=" + pressure,
                "Cryomech_HRC-100_Recondenser,sensor=heater power_watt=" + heater_pwr]
    else:
        return 

def read_vacuum_pressure(port):
    # Reads the PM31 gauge controller pressure output from channel 1
    port.write(bytes("MESr PM1\r", "ASCII"))
    # PM31 takes maximum of 500 ms to return a result
    time.sleep(0.5)
    data = str(port.readline()).split(":")
    # Check that the message length is as expected
    if len(data) == 3:
        pressure_torr = float(data[2].split("\\")[0])
        return ["PM31_Pressure,sensor=PR37_chamber TORR=" + str(pressure_torr)]
    else:
        return

def read_gyrotron_lvl(port):
    # First clear the buffer of any data
    port.reset_input_buffer()

    # Reads the gyrotron nitrogen liquid levels
    port.write(bytes("MEASure:N2:LEVel?\r", "ASCII"))
    time.sleep(0.5)
    data = str(port.readline()).split("\\")
    print(data)
    msg = []
    if len(data[0]) > 3:
        N2_lvl = data[0].split('\'')[-1].strip()
        msg.append("AMI_1700,sensor=N2_lvl n2_percent=" + N2_lvl)

    # Reads the gyrotron He liquid levels
    port.write(bytes("MEASure:HE:LEVel?\r", "ASCII"))
    time.sleep(0.5)
    data = str(port.readline()).split("\\")
    if len(data[0]) > 3:
        HE_lvl = data[0].split('\'')[-1].strip()
        msg.append("AMI_1700,sensor=HE_lvl he_percent=" + HE_lvl)
    
    # Reads the gyrotron He liquid Voltage
    port.write(bytes("MEASure:HE:VOLTage?\r", "ASCII"))
    time.sleep(0.5)
    data = str(port.readline()).split("\\")
    if len(data[0]) > 3:
        HE_volt = data[0].split('\'')[-1].strip()
        msg.append("AMI_1700,sensor=HE_lvl he_Volt=" + HE_volt)

    # Reads the gyrotron He liquid excitation current
    port.write(bytes("MEASure:ADC2?\r", "ASCII"))
    time.sleep(0.5)
    data = str(port.readline()).split("\\")
    if len(data[0]) > 3:
        HE_mA = data[0].split('\'')[-1].strip()
        msg.append("AMI_1700,sensor=HE_lvl he_mA=" + HE_mA)
    
    if len(msg) > 0:
        return msg
    else:
        return
        
def persistent_write_to_db(write_api, bucket, read_function, arg):
    # Persistently write data to the database in bucket after executing the read_function
    while True:
        try:
            result = read_function(arg)
            # Check that the read function has actually returned something with active instruments
            if not result == None:
                if len(result) > 0:
                    write_api.write(bucket, org, result)
            else:
                log_detail = "No results returned from " + read_function.__name__
                log_error(err_file, log_detail)

        except KeyboardInterrupt:
            print("logging ended")
            break
        except:
            # writing error to csv file, timeout to prevent filling the hard drive
            exception_details = traceback.format_exc()
            log_error(err_file, exception_details)
            time.sleep(15)
            # It should not be necessary to pass the ports dictionary back to the executors because they should have stayed the same
            serial_set_up()
            pass

def log_error(err_file, exception_details):
    with open(err_file, 'a') as csvfile: 
        csvwriter = csv.writer(csvfile)
        current_time = time.localtime()
        csvwriter.writerow([time.strftime("%Y %m %d %H:%M:%S", current_time)])
        csvwriter.writerow([exception_details])
    return


def write_to_DB(write_api):
    """
    Write to the InfluxDB by starting threads
    """
    all_ports = serial_set_up()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Comment out things that does not need to be logged

        executor.submit(persistent_write_to_db, write_api, "Helium", read_Lakeshore_Kelvin, all_ports["lakeshore"])
        executor.submit(persistent_write_to_db, write_api, "Helium", read_Cryomech_Compressor, ".\CPTLog.txt")
        #executor.submit(persistent_write_to_db, write_api, "Vacuum", read_Extorr_RGA, "E:\RGALogs")
        #executor.submit(persistent_write_to_db, write_api, "Helium", read_recondenser_controller, all_ports["recondenser"])
        #executor.submit(persistent_write_to_db, write_api, "Vacuum", read_vacuum_pressure, all_ports["PM31"])
        executor.submit(persistent_write_to_db, write_api, "Helium", read_gyrotron_lvl, all_ports["AM1700"])

if __name__ == '__main__':

    start_time = time.localtime()
    err_file = "error_log_" + time.strftime("%Y_%m_%d_%H-%M", start_time) + ".csv"

    # The token is unique to WHAM AWS service, do not delete it
    token = "4AMxSRRqZ-F5y35r7WFM9kyU9oDL50AfyVfcB2lAKrZUDeRHaEZMRPjn9K2TIUfL4iMW4Os7H2OfhKFemU1S1w=="
    org = "WHAM_Influx"

    # This token is for the localhost DB
    #token = "1S49cxWeukQNzk-M0No48Sz1PocbtgSf2Q8l9w5C2j17nj7Q4yoj-cV0UEeSGam3GP46oywU7DyEfauLoPnEwQ=="
    
    # This is for the DB running on Andrew
    #token = "VgX10ZPPxNYECSjl9qlZVOqMm0FU4DZmfkzED9qwevwTR_--MpNvx0LSFGOp87rCc9Kmq2fyuNz9Dcsoe3RRNQ=="
    #org = "WHAM"

    client = InfluxDBClient(url="https://us-east-1-1.aws.cloud2.influxdata.com", token=token, org=org)
    #client = InfluxDBClient(url="http://localhost:8086", token=token, org=org)
    #client = InfluxDBClient(url="http://andrew.psl.wisc.edu:8080", token=token, org=org)

    write_api = client.write_api(write_options=SYNCHRONOUS)
    write_to_DB(write_api)