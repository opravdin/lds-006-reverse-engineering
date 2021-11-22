from time import sleep
from serial import Serial
import numpy as np
import matplotlib.pyplot as plt
from math import fabs, radians
from joblib import Parallel, delayed

# Filter extraordinary values, set depends on your env
_MAX_DISTANCE_MM = 10000
# Motor speed, 70 +-1 is working best for me, should be finetuned perfectly
# cause <68 and 74> in my case are not working at all
# this constant means PWM value from 0 to 255, compatible with arduino sketch
_MOTOR_START_SPEED = 75 
_MOTOR_TARGET_SPEED = 30500 # not used for now

# Serial settings
_COM_PORT = "COM3"
_BAUDRATE = 115200
_SERIAL_TIMEOUT = 1
_READ_BATCH = 7944 # 360+1 degrees * 22 bytes per package

ser = Serial(_COM_PORT, baudrate=_BAUDRATE, timeout=_SERIAL_TIMEOUT) 

class LidarReader(object):
    def __init__(self, serial: Serial):
        self.serial = serial
        self.work_state = 0
        self.cache = {}
        self.reflects = {}
        self.motor_pwm = 0

        self.speed = 0

    def start(self):
        self.send_motor_state(_MOTOR_START_SPEED)
        sleep(0.25)
        self.send_lidar_init()

    def send_lidar_init(self):
        self.serial.write(b'$')
        return True

    # Do not use it, it's not working good
    def correct_motor_pwm(self, cur_speed: int):
        if cur_speed == 0:
            return
        target = round(30500 / cur_speed * self.motor_pwm)
        print(target)
        self.send_motor_state(target)

    def send_motor_state(self, speed: int):
        if speed < 0:
            speed = 0
        if speed > 255:
            speed = 255
        self.motor_pwm = speed
        msg = speed.to_bytes(1, 'big')
        print("Motor speed is ", speed)
        self.serial.write(b'!' + msg + b'!')
        return True
    
    def wait_read(self):
        packages = 0
        while packages == 0:
            data = self.serial.read(_READ_BATCH)
            readed = len(data)
            i = 0
            while i < readed:
                if data[i] != 0xFA and (data[i] != 0x5A or self.work_state == 2):
                    i+=1
                    continue
                self.work_state = 1 if data[i] == 0x5A else 2
                msgsize = 3 if self.work_state == 1 else 21
                message = data[i+1:i+1+msgsize]
                i+=msgsize
                if (len(message) < msgsize):
                    print(len(message), msgsize, i)
                    continue
                packages += 1
                if self.work_state == 2:
                    self.parse_message(message)
                else:
                    self.parse_init_message(message)
            
        return self.work_state

    def parse_message(self, packet: bytes):
        endian = 'little'
        angle = packet[0]
        speed = int.from_bytes((packet[1:3]), endian)
        if angle == 0xFB:
            # raise Exception("Speed error!")
            print("Speed error! ", speed)
            print(packet.hex(' '))
            # self.correct_motor_pwm(speed)
            return
        else:
            angle = (angle - 0xA0) * 4
        
        # Parsing distances
        relfrects = []
        distances = []
        for i in range(4):
            offset = 7 + i*4
            distance = int.from_bytes((packet[offset:offset+2]), endian, signed=False)
            reflect = int.from_bytes((packet[offset+2:offset+4]), endian, signed=False)
            distances.append(distance)
            relfrects.append(reflect)
        distance = np.median(distances)
        reflect = min(2000, np.median(relfrects))
        if distance > _MAX_DISTANCE_MM:
            if (self.cache.get(angle)):
                self.reflects.pop(angle)
                self.cache.pop(angle)
            return

        print("Speed ", speed, "; angle ", angle, "; distance", distance, "; reflection", reflect)
        self.cache[angle] = distance
        self.reflects[angle] = reflect

    def parse_init_message(self, packet):
        distance = int.from_bytes((packet[2:4]), 'big')
        print("Init, distance ", distance)

    def get_bins(self):
        if (len(self.cache) == 0):
            return [[], []]
        return zip(*self.cache.items())

    def get_reflections(self):
        if (len(self.reflects) == 0):
            return [[], []]
        return zip(*self.reflects.items())


handler = LidarReader(ser)
handler.start()

ax = plt.subplot(1, 1,1, projection='polar')
# bx = plt.subplot(1, 2, 1, projection='polar')
# ax.set_rmax(5000)

while True:
    for speed in range(_MOTOR_START_SPEED - 3, _MOTOR_START_SPEED - 1):
        print(speed)
        for iter in range(10):
            handler.send_motor_state(speed)
            for i in range(1):
                mode = handler.wait_read()
            
            # print("plotting")
            lidar_bins, lidar_field = handler.get_bins()
            reflect_bins, reflect_vals = handler.get_reflections()
            ax.clear() 
            # bx.clear() 
            ax.plot(np.deg2rad(lidar_bins), lidar_field, linestyle="None", marker="o")
            ax.plot(np.deg2rad(reflect_bins), np.multiply(reflect_vals, 5.0), linestyle="None", marker="s")
            plt.draw()
            plt.pause(0.001)
            # input("Press [enter] to continue.")
            plt.ion()
            plt.show()
    # for i in range(80, 255):
    #     handler.send_motor_state(i)
    #     mode = handler.wait_read()
    #     print(i)
    #     sleep(1)
    # print(mode)