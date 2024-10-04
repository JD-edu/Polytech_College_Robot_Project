import serial
import time

seq = serial.Serial(
        baudrate=115200,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=1
)

seq.port = "COM48"
seq.open()

while True:
    if seq.isOpen() == True:
        seq.write("10<10>1*\n".encode())
        time.sleep(1)
        if seq.inWaiting():      
            packets = seq.readline()
            print(packets)