import time
import logging
from srsinst.rga import RGA100

def read_SRS_RGA(port='/dev/ttyUSB0'):
    # initialize client with non-default noise floor setting
    RGA = RGA100('serial', port, 28800)    
    # check filament status and turn it on if necessary
    RGA.filament.turn_on(target_emission_current=1.0)
    # read partial pressures of air constituent
    MASSES = {
        18: "H2O",
        28: "N2",
        32: "O2",
        40: "Ar",
        43: "Acetone",
        31: "Alcohol",
        2: "H2",
        4: "D2",
        44: "CO2"
    }

    if port == '/dev/ttyUSB3':
        location = "_SEC"
    else:
        location = ""

    msg = []
    a, b, c = RGA.ionizer.get_parameters()
    msg.append("RGA_100"+location+",sensor=ionizer electron_energy=" + str(a))
    msg.append("RGA_100"+location+",sensor=ionizer ion_energy=" + str(b))
    msg.append("RGA_100"+location+",sensor=ionizer focus_voltage=" + str(c))
    msg.append("RGA_100"+location+",sensor=ionizer current=" + str(RGA.ionizer.emission_current))
    
    msg.append("RGA_100"+location+",sensor=total_pressure PRESSURE=" + str(RGA.pressure.get_total_pressure_in_torr()))
    
    for m, i in MASSES.items():
        ion_current = RGA.scan.get_single_mass_scan(m)
        pressure = ion_current * RGA.pressure.get_partial_pressure_sensitivity_in_torr()
        msg.append("RGA_100"+location+",sensor=" + i + " PRESSURE=" + str(pressure))
        time.sleep(1)
    
    current_minute = time.strftime("%M", time.localtime())
    # Do a full mass scan on the hour
    if current_minute == "00":
    #if True:
        logging.info("Starting full RGA spectrum scan at: "  + time.strftime("%a %b %d %H:%M:%S %Y", time.localtime()))
        # Set scan parameters
        RGA.scan.initial_mass = 1
        RGA.scan.final_mass = 100
        RGA.scan.scan_speed = 3
        RGA.scan.resolution = 10  # steps_per_amu

        # Get scan parameters
        mi, mf, nf, sa = RGA.scan.get_parameters()
        msg.append("RGA_100"+location+",sensor=scan_param scan_speed=" + str(nf))
        msg.append("RGA_100"+location+",sensor=scan_param steps_per_amu=" + str(sa))
        
        analog_spectrum  = RGA.scan.get_analog_scan()
        spectrum_in_torr = RGA.scan.get_partial_pressure_corrected_spectrum(analog_spectrum)
        # Get the matching mass axis with the spectrum
        analog_mass_axis = RGA.scan.get_mass_axis(True)  # is it for analog scan? No.
        for i in range(len(analog_mass_axis)):
            mass = "%05.1f" % analog_mass_axis[i]
            pressure_in_torr = str(spectrum_in_torr[i])
            msg.append("RGA_100"+location+",amu=" + mass + " pressure=" + pressure_in_torr)
        logging.info("Ending full RGA spectrum scan at: "  + time.strftime("%a %b %d %H:%M:%S %Y", time.localtime()))
        #print(msg)

    RGA.disconnect()

    return msg

def reset_RGA(port='/dev/ttyUSB0'):
    RGA = RGA100('serial', port, 28800)    
    print(RGA.reset())
    RGA.filament.turn_off()
    RGA.disconnect()
    return 0

def degas_RGA(port='/dev/ttyUSB0'):
    
    RGA = RGA100('serial', port, 28800)    
    print('starting degas')
    RGA.filament.start_degas(3)
    RGA.filament.turn_off()
    RGA.disconnect()
    return 0

if __name__ == '__main__':

    #reset_RGA()
    #degas_RGA()
    print(read_SRS_RGA(port='/dev/ttyUSB3'))