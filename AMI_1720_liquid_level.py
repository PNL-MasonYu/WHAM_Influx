import serial
import logging
import numpy as np
import time
import traceback

def read_AMI1720_NBI(IP="192.168.130.227"):
    url = "socket://" + IP + ":4196"
    with serial.serial_for_url(url) as ser:
        ser.baudrate = 115200
        ser.parity = serial.PARITY_NONE
        ser.bytesize = serial.EIGHTBITS
        ser.stopbits = serial.STOPBITS_ONE
        ser.timeout = 1
        # Command to set unit to percent
        """
        command_str = "CONFigure:CH1:UNIT 0\r\n"
        command = command_str.encode("ASCII")
        ser.write(command)
        data = str(ser.readline()).strip("\r\n")
        print(data)
        time.sleep(0.1)
        """
        msg = []
        for ch in [1, 2]:
            command_str = f"MEASure:CH{ch}:LEVel?\r\n"
            command = command_str.encode("ASCII")
            ser.write(command)
            time.sleep(0.1)
            try:
                data = str(ser.readline(), encoding="ASCII").strip('\r\n')
                msg.append(f"AMI_1720,sensor=N2_lvl CH{ch}=" + data)
            except:
                exception_details = traceback.format_exc()
                current_time = time.localtime()
                logging.info(time.strftime("%Y %m %d %H:%M:%S", current_time))
                logging.debug([exception_details])
        print(msg)
    return msg

if __name__ == '__main__':
    read_AMI1720_NBI()