import time
import logging
import numpy as np
import redpitaya_scpi as scpi
import matplotlib.pyplot as plot


def read_NBI_gauge_rp(IP="rp-f0bd65.local"):

    zero_offset = 0.0
    sensitivity = 1.0
    # connect to RP at the provided IP
    rp = scpi.scpi(IP, timeout=10)
    #print(rp.get_settings())
    # Reset acquisition params
    rp.tx_txt('ACQ:RST')
    rp.tx_txt('ACQ:DATA:FORMAT ASCII')
    rp.tx_txt('ACQ:DATA:UNITS VOLTS')
    rp.tx_txt('ACQ:DEC 1')
    rp.tx_txt('ACQ:SOUR1:GAIN HV')
    rp.tx_txt('ACQ:SOUR2:GAIN HV')
    #rp.tx_txt('ACQ:AVG:CH1 ON')
    #rp.tx_txt('ACQ:AVG:CH2 ON')
    
    rp.tx_txt('ACQ:START')
    rp.tx_txt('ACQ:TRIG NOW')
    """
    while 1:
        rp.tx_txt('ACQ:TRIG:FILL?')
        if rp.rx_txt() == '1':
            break
    """
    time.sleep(0.5)
    rp.tx_txt('ACQ:SOUR2:DATA?')
    
    buff_string = rp.rx_txt()
    buff_string = buff_string.strip('{}\n\r').replace("  ", "").split(',')
    buff1 = list(map(float, buff_string))
    average_voltage = np.average(buff1)
    log_pressure = np.power(10, average_voltage-11) * sensitivity

    msg = []
    msg.append("ION_GAUGE,GAUGE=NBI_GAUGE voltage_log={:.8f}".format(average_voltage))
    msg.append("ION_GAUGE,GAUGE=NBI_GAUGE pressure_log={:.6e}".format(log_pressure))

    #print("Average of ch1: {:.8f}".format(average_voltage))
    #print("linear pressure : {:.3e}".format(log_pressure))

    rp.tx_txt('ACQ:SOUR1:DATA?')
    buff_string = rp.rx_txt()
    buff_string = buff_string.strip('{}\n\r').replace("  ", "").split(',')
    buff2 = list(map(float, buff_string))
    average_voltage = np.average(buff2)
    linear_pressure = (average_voltage+zero_offset) / 10.0 * (1e-5 - 1e-8)

    msg.append("ION_GAUGE,GAUGE=NBI_GAUGE voltage_linear={:.8f}".format(average_voltage))
    msg.append("ION_GAUGE,GAUGE=NBI_GAUGE pressure_linear={:.6e}".format(linear_pressure))

    #print("Average of ch2: {:.8f}".format(average_voltage))
    #print("linear pressure : {:.3e}".format(linear_pressure))
    """
    print(msg)
    
    plot.plot(buff1, label='buff1')
    plot.plot(buff2, label='buff2')
    plot.ylabel('Voltage')
    plot.legend()
    plot.show()
    """
    rp.close()
    
    return msg

if __name__ == "__main__":
    read_NBI_gauge_rp()