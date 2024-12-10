import serial
import logging
import numpy as np
import time
import traceback

def log_error(exception_details):
    current_time = time.localtime()
    logging.info(time.strftime("%Y %m %d %H:%M:%S", current_time))
    logging.debug([exception_details])
    return

def read_lakeshore_temperature(port='/dev/ttyUSB1'):
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = 1200
    ser.parity = serial.PARITY_ODD
    ser.bytesize = serial.SEVENBITS
    ser.stopbits = serial.STOPBITS_ONE
    ser.timeout = 10

    try:
        ser.open()
    except: 
        exception_details = traceback.format_exc()
        log_error(exception_details)
        time.sleep(1)
        return 
    temps = []

    port_key = 'lakeshore_NBI'
    for n in range(1,9):
    
        #ser.reset_output_buffer()
        command_str = 'KRDG? ' + str(n) + '\r\n'
        command = command_str.encode('ASCII')
        ser.write(command)
        
        try:
            serial_input = ser.readline()
            #print(serial_input)
            data = str(serial_input)[2:-5]
            temps.append("temperature_" + port_key + ",sensor=ch{:} temp={:}".format(n,float(data))) 
        except:
            exception_details = traceback.format_exc()
            log_error(exception_details)
            time.sleep(1)
            #lakeshore_port.open()
            return
    #print(temps)
    ser.close()
    time.sleep(0.2)

    return temps

if __name__ == '__main__':

    read_lakeshore_temperature()