# %%
import serial
ser_com = serial.Serial()
ser_com.baudrate = 115200
ser_com.port = "COM1"
ser_com.timeout = 3
ser_com.open()
chksum1 = "0000"
chksum2 = "1100"
message_bytes = bytes.fromhex("02 16 10 63 45 4C 07 00 0C 07 0D")
print(ser_com.write(message_bytes))
print(ser_com.readlines())
# %%
