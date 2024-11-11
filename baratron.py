import time
import logging
import numpy as np
import redpitaya_scpi as scpi
import matplotlib.pyplot as plot


def read_baratron_rp(IP="rp-f0908c.local"):
    # zero offset with CFS magnets at full field
    #zero_offset = 2.883e-3
    # zero offset with zero field
    zero_offset = -0.89e-3
    
    DEC = 1
    # connect to RP at the provided IP
    rp = scpi.scpi(IP)
    # Reset acquisition params
    rp.tx_txt('ACQ:RST')
    rp.acq_set(DEC, gain=["LV", "HV"])

    rp.tx_txt('ACQ:START')
    rp.tx_txt('ACQ:TRIG NOW')
    
    while 1:
        rp.tx_txt('ACQ:TRIG:FILL?')
        if rp.rx_txt() == '1':
            break
    
    buff = rp.acq_data(1, convert=True)
    average_voltage = np.average(buff)
    int_time = len(buff) / 125e6 * DEC
    rp.tx_txt('ACQ:STOP')

    rp.tx_txt('DIG:PIN:DIR IN,DIO1_P') #RANGE_IDENT
    rp.tx_txt('DIG:PIN:DIR IN,DIO2_P')  #OVERRANGE
    rp.tx_txt('DIG:PIN:DIR OUT,DIO3_P')  #0.1_RANGE
    rp.tx_txt('DIG:PIN:DIR OUT,DIO4_P')  #REMOTE_ZERO
    
    #rp.tx_txt('DIG:PIN DIO3_P,0')
    # check if 0.1 range is active
    rp.tx_txt('DIG:PIN? DIO1_P')
    if rp.rx_txt() == '1':
        pressure = average_voltage / 10 + zero_offset
        full_range = True
    else:
        pressure = average_voltage / 100 + zero_offset
        full_range = False
        
    rp.tx_txt('DIG:PIN? DIO2_P')
    if rp.rx_txt() == '1':
        overrange = True
        print("Baratron is over range!")
    else:
        overrange = False
    """
    print("Average of all samples: {:.3f}".format(average_voltage))
    print("Indicated pressure: {:.3e} Torr".format(pressure))
    
    time_scale = np.linspace(0, int_time, len(buff))
    plot.plot(buff)
    plot.ylabel('Voltage')
    plot.xlabel('Time (s)')
    plot.show()
    """
    rp.tx_txt('ANALOG:PIN? AIN0')
    vs_voltage = float(rp.rx_txt()) * 49.9/2.22
    
    rp.tx_txt('ANALOG:PIN? AIN1')
    ps_voltage = float(rp.rx_txt()) * 49.9/2.22
    
    rp.close()
    
    msg = []
    msg.append("BARATRON_120A,IP=" + IP + " pressure={:.8f}".format(pressure))
    msg.append("BARATRON_120A,IP=" + IP + " over_range=" + str(overrange))
    msg.append("BARATRON_120A,IP=" + IP + " full_range=" + str(full_range))
    msg.append("BARATRON_120A,IP=" + IP + " vs_voltage=" + str(vs_voltage))
    msg.append("BARATRON_120A,IP=" + IP + " ps_voltage=" + str(ps_voltage))
    
    #print(msg)
    return msg

if __name__ == '__main__':
    read_baratron_rp()