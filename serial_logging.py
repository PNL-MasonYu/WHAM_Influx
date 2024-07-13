import os
import serial
import time
import csv
import traceback
import logging
from telnetlib import Telnet
from pymodbus.client import ModbusTcpClient

from ssh_logging import remote_logging
from influxdb_client import InfluxDBClient, ReturnStatement
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client import write_api

def log_error(exception_details):
    current_time = time.localtime()
    logging.info(time.strftime("%Y %m %d %H:%M:%S", current_time))
    logging.debug([exception_details])
    return

def close_open_port(port):
    if port.is_open:
        port.close()
        
def telnet_client(host: str, port: int, command:str):
    tn = Telnet(host, port)
    #print(f"connected to ({host}, {port})")
    command = bytes(command, "ASCII")
    tn.write(command)
    time.sleep(1)
    data = tn.read_eager()
    output = data.decode('ascii').strip()
    tn.close()
    time.sleep(1)
    return output
    

def serial_set_up():
    # Setting up all the serial ports
    # Returns a list of ports that are opened
    global all_ports
    all_ports = {}
    logging.info("Attempting to open all serial ports")
    # Lakeshore temperature monitor
    ser_lakeshore = serial.Serial()
    ser_lakeshore.baudrate = 1200
    ser_lakeshore.port = "/dev/ttyUSB2"
    ser_lakeshore.parity = serial.PARITY_ODD
    ser_lakeshore.bytesize = serial.SEVENBITS
    ser_lakeshore.stopbits = serial.STOPBITS_ONE
    ser_lakeshore.timeout=10
    #ser_lakeshore.inter_byte_timeout = 1
    #ser_lakeshore.rtscts = True
    #ser_lakeshore.dsrdtr = True
    
    close_open_port(ser_lakeshore)
    try:
        ser_lakeshore.open()
    except:
        log_error("Failed to open Lakeshore temperature monitor port " + ser_lakeshore.port)
        exception_details = traceback.format_exc()
        log_error(exception_details)
    
    # Send the instrument a line break, wait 100ms, and clear the input buffer so that
    # any leftover communications from a prior session don't gum up the works
    #ser_lakeshore.write(b'\n')
    #time.sleep(0.1)
    #ser_lakeshore.reset_input_buffer()
    
    all_ports["lakeshore_NBI"] = ser_lakeshore
    
    # HRC-100 Helium recondenser controller serial port
    ser_recondenser = serial.Serial()
    ser_recondenser.baudrate = 9600
    ser_recondenser.port = "COM2"
    ser_recondenser.timeout = 0.5
    close_open_port(ser_recondenser)
    try:
        ser_recondenser.open()
        # Skip through the initialization screen from the HRC-100 and get into monitor mode
        ser_recondenser.write(bytes("\n", "ASCII"))
        time.sleep(1)
        ser_recondenser.write(bytes("t\n", "ASCII"))
        # Clear serial buffer
        ser_recondenser.readlines()
    except:
        log_error("Failed to open HRC-100 recondenser controller serial port " + ser_recondenser.port)
        exception_details = traceback.format_exc()
        log_error(exception_details)
    all_ports["recondenser"] = ser_recondenser
    """
    # PM31 Gauge Controller (Main chamber)
    ser_PM31 = serial.Serial()
    ser_PM31.baudrate = 2400
    ser_PM31.port = "COM5"
    ser_PM31.timeout = 0.5
    ser_PM31.parity = serial.PARITY_NONE
    close_open_port(ser_PM31)
    try:
        ser_PM31.open()
    except:
        log_error("Failed to open PM31 Gauge Controller serial port " + ser_PM31.port)
        exception_details = traceback.format_exc()
        log_error(exception_details)
    all_ports["PM31"] = ser_PM31
    """
    # American Magnetics Model 1700 liquid level instrument
    ser_1700 = serial.Serial()
    ser_1700.baudrate = 300
    ser_1700.port = "COM4"
    ser_1700.parity = serial.PARITY_NONE
    ser_1700.stopbits = serial.STOPBITS_ONE
    ser_1700.bytesize = serial.EIGHTBITS
    ser_1700.timeout = 0.5
    try:
        ser_1700.open()
        
        # Set the unit of measurement to be %
        ser_1700.write(bytes("CONFigure:N2:UNIT 0\r", "ASCII"))
        time.sleep(0.5)
        print(ser_1700.readline().decode("ASCII"))
        ser_1700.write(bytes("CONFigure:HE:UNIT 0\r", "ASCII"))
        time.sleep(0.5)
        print(ser_1700.readline())
        
    except:
        log_error("Failed to open American Magnetics 1700 liquid level instrument port " + ser_1700.port)
        exception_details = traceback.format_exc()
        log_error(exception_details)
    all_ports["AM1700"] = ser_1700

    # LN2 Dewar Scale
    ser_scale = serial.Serial()
    ser_scale.baudrate = 9600
    ser_scale.port = "COM6"
    ser_scale.parity = serial.PARITY_ODD
    ser_scale.stopbits = serial.STOPBITS_ONE
    ser_scale.bytesize = serial.SEVENBITS
    ser_scale.timeout = 0.5
    try:
        ser_scale.open()
    except:
        log_error("Failed to open LN2 Scale Serial port " + ser_scale.port)
        exception_details = traceback.format_exc()
        log_error(exception_details)
    all_ports["LN2_SCALE"] = ser_scale
    return all_ports

def michael_logging_setup():
    # Setting up connection to remote computers that are logging data into files
    #michael = remote_logging()
    #michael.connect()
    #return michael
    return 0

def read_ADAM_6015(ip):
    client = ModbusTcpClient(ip)
    raw_temps = [0] * 7
    scaled_temps = [0.0] * 7
    msg = []
    last_ip = str(ip.split(".")[-1])
    for reg in [0,1,2,3,4,5,6]:
        raw_temps[reg] = client.read_input_registers(address=reg, count=1).registers[0]
        scaled_temps[reg] = raw_temps[reg] / 65535 * 100
        msg.append("ADAM_6015_"+last_ip+",sensor=ch{:} temp_celsius={:.3f}".format(reg, scaled_temps[reg]))
    #print(raw_temps)
    #print(msg)
    time.sleep(1)
    return msg
    

def read_LN2_scale(port_key):
    port = all_ports[port_key]
    data = str(port.readline())
    if data[2] == "w":
        weight_str = data.split("   ")[-1].split("lb")[0]
        try:
            weight_lb = float(weight_str)
            print(data)
        except:
            print(data)
            port.reset_input_buffer()
            return
    else: return
    weight = "LN2_scale,sensor=lb weight={:}".format(weight_lb)
    time.sleep(0.5)
    return weight

def read_AMI_Telnet(IP="192.168.0.87"):
    LN2_lvl = telnet_client(IP, 7180, "MEASure:N2:LEVel?\r")
    HE_lvl = telnet_client(IP, 7180, "MEASure:HE:LEVel?\r")

    msg = []
    msg.append("AMI_1700,sensor=N2_lvl n2_percent=" + LN2_lvl)
    msg.append("AMI_1700,sensor=HE_lvl he_percent=" + HE_lvl)
    time.sleep(1.0)
    return msg


def read_Lakeshore_Kelvin(port_key):
    # Lakeshore model 218
    lakeshore_port = all_ports[port_key]
    temps = []
    for n in range(1,8,1):
    
        #lakeshore_port.reset_output_buffer()
        command_str = 'KRDG? ' + str(n) + '\r\n'
        command = command_str.encode('ASCII')
        lakeshore_port.write(command)
        #print(lakeshore_port.get_settings())
        #lakeshore_port.write(bytes('KRDG? 3\r\n'))
        #lakeshore_port.flush()
        #lakeshore_port.rts = True
        #lakeshore_port.dtr = True
        #serial_input = lakeshore_port.readline()
        #print(serial_input)
        #data = str(serial_input)[2:-5]
        
        try:
            serial_input = lakeshore_port.readline()
            print(serial_input)
            data = str(serial_input)[2:-5]
            temps.append("temperature_" + port_key + ",sensor=ch{:} temp={:}".format(n+1,float(data))) 
        except:
            exception_details = traceback.format_exc()
            log_error(exception_details)
            #lakeshore_port.close()
            time.sleep(1)
            #lakeshore_port.open()
            return
        
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
        #logging.info(latest_status)
    time.sleep(1)
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
        time.sleep(1)
        return

def read_recondenser_controller(port_key):
    port = all_ports[port_key]
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
            # If the controller does not respond within 10 seconds, 
            # send a command to enable monitor mode and break
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

def read_vacuum_pressure(port_key):
    port = all_ports[port_key]
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

def read_gyrotron_lvl(port_key):
    port = all_ports[port_key]
    # First clear the buffer of any data
    port.reset_input_buffer()
    
    # Reads the gyrotron nitrogen liquid levels
    port.write(bytes("MEASure:N2:LEVel?\r", "ASCII"))
    time.sleep(0.5)
    try: 
        data = str(port.readline()).split("\\")
        #print(data)
        # Try to reopen the serial port if something happens 
    except:
        exception_details = traceback.format_exc()
        log_error(exception_details)
        port.close()
        time.sleep(10)
        port.open()
        return
    
    msg = []
    if len(data[0]) > 3:
        N2_lvl = data[0].split('\'')[-1].strip()
        msg.append("AMI_1700,sensor=N2_lvl n2_percent=" + N2_lvl)

    # Reads the gyrotron He liquid levels
    port.write(bytes("MEASure:HE:LEVel?\r", "ASCII"))
    time.sleep(0.5)
    data = str(port.readline()).split("\\")
    print(data)
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
    #print(msg)
    if len(msg) > 0:
        return msg
    else:
        return
    
def read_maxigauge(IP='192.168.130.195'):
    tn = Telnet(IP, 8000, 3)
    data = b''
    msg = []
    for gauge_n in range(1, 7):
        command = bytes('PR' + str(gauge_n) + '\r', 'ASCII')
        tn.write(command)
        time.sleep(0.2)
        data = tn.read_eager()
        
        if data == b'\x06\r\n': #ACQ

            tn.write(b'\x05')   #ENQ
            time.sleep(0.2)
            data = tn.read_eager()
            if not data == b'':
                pressure_str = data.decode("ASCII").strip("\r\n").split(",")[1]
                pressure = float(pressure_str)
                #print(pressure)
                msg.append("MAXIGAUGE_TPG366,sensor=CH_" + str(gauge_n) + " PRESSURE=" + str(pressure))

        else:
            log_error("Maxigauge failed to respond to " + str(command))
            time.sleep(0.2)
    tn.close()
    time.sleep(0.2)
    return msg