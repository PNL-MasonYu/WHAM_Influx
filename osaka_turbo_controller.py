import serial
import logging
import numpy as np
import time
import traceback


def read_osaka_turbo(port='/dev/ttyUSB5'):
    ser = serial.Serial()
    ser.port = port
    # The CC turbo controller does not work at baud rate of 9600 for some reason
    # It was set like this out of the factory
    if port == '/dev/ttyUSB5':
        ser.baudrate = 19200
    else:
        ser.baudrate = 9600
    ser.parity = serial.PARITY_NONE
    ser.bytesize = serial.EIGHTBITS
    ser.stopbits = serial.STOPBITS_ONE
    ser.timeout = 1

    try:
        ser.open()
    except: 
        exception_details = traceback.format_exc()
        current_time = time.localtime()
        logging.info(time.strftime("%Y %m %d %H:%M:%S", current_time))
        logging.debug([exception_details])
        return 
    
    command_str = 'RRS\r'
    command = command_str.encode('ASCII')
    ser.write(command)
    msg = []
    time.sleep(1)
    try:
        serial_input = ser.readline()
        speed = int(serial_input) * 60
        #print(speed)
        msg.append("osaka_turbo,port=" + port + " speed_rpm=" + str(speed))
    except:
        exception_details = traceback.format_exc()
        current_time = time.localtime()
        logging.info(time.strftime("%Y %m %d %H:%M:%S", current_time))
        logging.debug([exception_details])
        time.sleep(1)

    ser.close()

    return msg

if __name__ == '__main__':

    read_osaka_turbo()