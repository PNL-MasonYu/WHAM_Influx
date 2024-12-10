import logging
import numpy as np
import time
import traceback

from telnetlib import Telnet

def telnet_client(host: str, port: int, command:str):
    tn = Telnet(host, port, timeout=3)
    #print(f"connected to ({host}, {port})")
    command = bytes(command, "ASCII")
    tn.write(command)
    time.sleep(1)
    data = tn.read_eager()
    output = data.decode('ascii').strip()
    tn.close()
    time.sleep(1)
    return output

def read_AMI_Telnet(IP="192.168.130.200"):
    LN2_lvl = telnet_client(IP, 7180, "MEASure:N2:LEVel?\r")
    HE_lvl = telnet_client(IP, 7180, "MEASure:HE:LEVel?\r")
    IP_digit = IP.split(".")[-1]
    msg = []
    msg.append("AMI_1700_"+IP_digit+",sensor=N2_lvl n2_percent=" + LN2_lvl)
    msg.append("AMI_1700_"+IP_digit+",sensor=HE_lvl he_percent=" + HE_lvl)
    time.sleep(1.0)
    #print(msg)
    return msg

if __name__ == "__main__":
    print(read_AMI_Telnet())