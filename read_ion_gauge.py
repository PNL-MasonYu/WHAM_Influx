import time
import logging
import numpy as np
import redpitaya_scpi as scpi
import matplotlib.pyplot as plot


def read_ion_gauge(IP="rp-f09303.local"):
    """
    "rp-f09303.local" is ch02 on diag rack
    "rp-f0be68.local" is ch04 on diag rack
    """
    zero_offset = 0
    # connect to RP at the provided IP
    rp = scpi.scpi(IP)
    #print(rp.get_settings())
    # Reset acquisition params
    rp.tx_txt('ACQ:RST')
    rp.tx_txt('ACQ:DATA:FORMAT ASCII')
    rp.tx_txt('ACQ:DATA:UNITS VOLTS')
    rp.tx_txt('ACQ:DEC 4')
    rp.tx_txt('ACQ:SOUR1:GAIN HV')
    rp.tx_txt('ACQ:SOUR2:GAIN HV')
    rp.tx_txt('ACQ:AVG:CH1 ON')
    rp.tx_txt('ACQ:AVG:CH2 ON')
    
    rp.tx_txt('ACQ:START')
    rp.tx_txt('ACQ:TRIG NOW')
    
    while 1:
        rp.tx_txt('ACQ:TRIG:FILL?')
        if rp.rx_txt() == '1':
            break
    
    rp.tx_txt('ACQ:SOUR1:DATA?')
    buff_string = rp.rx_txt()
    buff_string = buff_string.strip('{}\n\r').replace("  ", "").split(',')
    buff = list(map(float, buff_string))
    average_voltage1 = np.average(buff)

    rp.tx_txt('ACQ:SOUR2:DATA?')
    buff_string = rp.rx_txt()
    buff_string = buff_string.strip('{}\n\r').replace("  ", "").split(',')
    buff = list(map(float, buff_string))
    average_voltage2 = np.average(buff)
    
    #plot.plot(buff)
    #plot.ylabel('Voltage')
    #plot.show()
    
    rp.close()
    
    msg = []
    msg.append("ION_GAUGE,GAUGE="+IP+"_ch1 voltage={:.8f}".format(average_voltage1))
    msg.append("ION_GAUGE,GAUGE="+IP+"_ch2 voltage={:.8f}".format(average_voltage2))
    
    return msg
