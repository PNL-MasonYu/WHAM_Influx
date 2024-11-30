# Modbus communication with Diris A-10 power line monitor
# Installed on the SEC Cryopump as of 11-29-24
# --------------------------------------------------------------------------- #
# import the various client implementations
# --------------------------------------------------------------------------- #
import pymodbus.client as ModbusClient
from pymodbus import (
    ExceptionResponse,
    Framer,
    ModbusException,
    pymodbus_apply_logging_config,
)
import serial


def read_diris(port="COM2"):
    """Run sync client."""
    
    def u32_to_int(registers):
        # big endian conversion
        return int(registers[0]*65535+registers[1])
        
    def s32_to_int(registers):
        if registers[0] > 32767: #negative number
            return int(-(registers[0]-32767)*32767+registers[1])
        else:
            return int((registers[0])*32767+registers[1])
    # activate debugging
    #pymodbus_apply_logging_config("DEBUG")

    client = ModbusClient.ModbusSerialClient(
        port,
        framer=Framer.RTU,
        timeout=3,
        retries=3,
        retry_on_empty=True,
        strict=False,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        #broadcast_enable=True,
        #handle_local_echo=False,
    )
    
    def read_address(address, num_bytes):
        try:
            data = client.read_holding_registers(address, num_bytes, slave=5)
        except ModbusException as exc:
            print(f"Received ModbusException({exc}) from library")
            return
        if data.isError():
            print(f"Received Modbus library error({data})")
            return
        if isinstance(data, ExceptionResponse):
            print(f"Received Modbus library exception ({data})")
        return data.registers
    if client.is_socket_open():
    #if serial.Serial(port).is_open:
        print("port is open, closing port " + port)
        client.socket.close()
        
    if not client.connected:
        client.connect()
    msg = []
    hour = u32_to_int(read_address(50512, 2))/100
    phase_volt_12 = u32_to_int(read_address(50514, 2))/100
    phase_volt_23 = u32_to_int(read_address(50516, 2))/100
    phase_volt_31 = u32_to_int(read_address(50518, 2))/100
    
    msg.append("Diris_"+port+",sensor=hour hr={:.3f}".format(hour))
    msg.append("Diris_"+port+",sensor=phase_volt_12 V={:.3f}".format(phase_volt_12))
    msg.append("Diris_"+port+",sensor=phase_volt_23 V={:.3f}".format(phase_volt_23))
    msg.append("Diris_"+port+",sensor=phase_volt_31 V={:.3f}".format(phase_volt_31))
    
    phase_volt_1 = u32_to_int(read_address(50520, 2))/100
    phase_volt_2 = u32_to_int(read_address(50522, 2))/100
    phase_volt_3 = u32_to_int(read_address(50524, 2))/100
    
    msg.append("Diris_"+port+",sensor=phase_volt_1 V={:.3f}".format(phase_volt_1))
    msg.append("Diris_"+port+",sensor=phase_volt_2 V={:.3f}".format(phase_volt_2))
    msg.append("Diris_"+port+",sensor=phase_volt_3 V={:.3f}".format(phase_volt_3))
    
    frequency = u32_to_int(read_address(50526, 2))/100
    
    phase_current_1 = u32_to_int(read_address(50528, 2))/1000
    phase_current_2 = u32_to_int(read_address(50530, 2))/1000
    phase_current_3 = u32_to_int(read_address(50532, 2))/1000
    neutral_current = u32_to_int(read_address(50534, 2))/1000
    
    msg.append("Diris_"+port+",sensor=frequency Hz={:.3f}".format(frequency))
    msg.append("Diris_"+port+",sensor=phase_current_1 A={:.3f}".format(phase_current_1))
    msg.append("Diris_"+port+",sensor=phase_current_2 A={:.3f}".format(phase_current_2))
    msg.append("Diris_"+port+",sensor=phase_current_3 A={:.3f}".format(phase_current_3))
    msg.append("Diris_"+port+",sensor=neutral_current A={:.3f}".format(neutral_current))
    
    active_power = s32_to_int(read_address(50536, 2))/0.1
    reactive_power = s32_to_int(read_address(50538, 2))/0.1
    apparent_power = u32_to_int(read_address(50540, 2))/0.1
    power_factor = s32_to_int(read_address(50542, 2))/1000
    
    msg.append("Diris_"+port+",sensor=active_power W={:.3f}".format(active_power))
    msg.append("Diris_"+port+",sensor=reactive_power W={:.3f}".format(reactive_power))
    msg.append("Diris_"+port+",sensor=apparent_power W={:.3f}".format(apparent_power))
    msg.append("Diris_"+port+",sensor=power_factor power_factor={:.3f}".format(power_factor))
    
    max_avg_1 = u32_to_int(read_address(51070, 2))/1000
    max_avg_2 = u32_to_int(read_address(51072, 2))/1000
    max_avg_3 = u32_to_int(read_address(51074, 2))/1000
    max_avg_n = u32_to_int(read_address(51076, 2))/1000
    
    msg.append("Diris_"+port+",sensor=max_avg_1 current_ratio={:.3f}".format(max_avg_1))
    msg.append("Diris_"+port+",sensor=max_avg_2 current_ratio={:.3f}".format(max_avg_2))
    msg.append("Diris_"+port+",sensor=max_avg_3 current_ratio={:.3f}".format(max_avg_3))
    msg.append("Diris_"+port+",sensor=max_avg_n current_ratio={:.3f}".format(max_avg_n))
    
    client.close()
    return msg

if __name__ == "__main__":
    print(read_diris("COM2"))