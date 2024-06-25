import time
import logging
import numpy as np
import redpitaya_scpi as scpi
import matplotlib.pyplot as plot


def read_baratron_rp(IP="rp-f0908c.local"):
    # connect to RP at the provided IP
    rp = scpi.scpi(IP)
    #print(rp.get_settings())
    # Reset acquisition params
    rp.tx_txt('ACQ:RST')
    rp.tx_txt('ACQ:DATA:FORMAT ASCII')
    rp.tx_txt('ACQ:DATA:UNITS VOLTS')
    rp.tx_txt('ACQ:DEC 8')
    rp.tx_txt('ACQ:SOUR1:GAIN HV')
    rp.tx_txt('ACQ:SOUR2:GAIN HV')
    rp.tx_txt('ACQ:AVG:CH1 ON')
    #print(rp.get_settings())
    
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
    average_voltage = np.average(buff)
    
    rp.tx_txt('DIG:PIN:DIR IN,DIO1_P') #RANGE_IDENT
    rp.tx_txt('DIG:PIN:DIR IN,DIO2_P')  #OVERRANGE
    rp.tx_txt('DIG:PIN:DIR OUT,DIO3_P')  #0.1_RANGE
    rp.tx_txt('DIG:PIN:DIR OUT,DIO4_P')  #REMOTE_ZERO
    
    #rp.tx_txt('DIG:PIN DIO3_P,0')
    # check if 0.1 range is active
    rp.tx_txt('DIG:PIN? DIO1_P')
    if rp.rx_txt() == '1':
        pressure = average_voltage / 100
        full_range = False
    else:
        pressure = average_voltage / 10
        full_range = True
        
    rp.tx_txt('DIG:PIN? DIO2_P')
    if rp.rx_txt() == '1':
        overrange = True
        #print("Baratron is over range!")
    else:
        overrange = False
    
    #print("Average of all samples: {:.3f}".format(average_voltage))
    #print("Indicated pressure: {:.3e} Torr".format(pressure))
    #plot.plot(buff)
    #plot.ylabel('Voltage')
    #plot.show()
    
    rp.tx_txt('ANALOG:PIN? AIN0')
    vs_voltage = float(rp.rx_txt()) * 49.9/2.22
    
    rp.tx_txt('ANALOG:PIN? AIN1')
    ps_voltage = float(rp.rx_txt()) * 49.9/2.22
    
    rp.close()
    
    msg = []
    msg.append("BARATRON_120A,IP=" + IP + " pressure=" + str(pressure))
    msg.append("BARATRON_120A,IP=" + IP + " over_range=" + str(overrange))
    msg.append("BARATRON_120A,IP=" + IP + " full_range=" + str(full_range))
    msg.append("BARATRON_120A,IP=" + IP + " vs_voltage=" + str(vs_voltage))
    msg.append("BARATRON_120A,IP=" + IP + " ps_voltage=" + str(ps_voltage))
    
    time.sleep(0.1)
    return msg

#read_baratron_rp()