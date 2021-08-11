import time, math
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.ads1x15 import Mode
from adafruit_ads1x15.analog_in import AnalogIn
import board
from busio import I2C
from adafruit_bus_device.i2c_device import I2CDevice
import numpy as np
import curses
from curses import wrapper
from curses.textpad import Textbox, rectangle
import parse

defaultSettings = {"dacA":0, "dacB":0, "dacC":0, "dacD":0, "dacE":0, "dacF":0,
                   "dacG":0, "dacH":0, "adcA":-1, "adcB":-1, "adcC":-1}


channel = 1
addr = 0x72 # specific dac board (configurable by jumpers) , global address (write to all dac boards) is 0x73

bus = I2C(board.SCL, board.SDA)
dacboard = I2CDevice(bus, addr)

writeup = 3 # command to write and update the dac
dacs = [0,1,2,3,4,5,6,7] # each dac has a binary address
all_dacs = 15 # all dacs at once
ads = ADS.ADS1115(bus, address=0x48)
adcA = AnalogIn(ads, ADS.P0)#, ADS.P1)
adcB = AnalogIn(ads, ADS.P2)
adcC = AnalogIn(ads, ADS.P3)
ads.data_rate = 860 # Max rate is 860
ads.mode = Mode.SINGLE
_ = adcA.value
_ = adcB.value
_ = adcC.value

def dac_write(data, command, dac):

    # data should be 2 bytes
    # command should be 1 byte
    # dac should be 1 byte

    if dac == "all":
        dac = 15

    # full command sent to dac is (in binary) ccccaaaa dddddddd dddddddd
    b1 = (command<<4) + dac # first byte is 4 bits command then 4 bits which dac
    b2 = (data & (0xff << 8)) >> 8 # second byte is first byte of data (leftmost set of ds)
    b3 = data & 0xff # third byte is second byte of data (rightmost set of ds)

    #bus.write_i2c_block_data(addr, b1, [b2, b3])
    with dacboard:
        dacboard.write(bytes([b1,b2,b3]))

def do_update_dac(voltage, dac):

    data = voltage / (5 / ((2 ** 16) - 1))
    data = math.ceil(data) if (data > (math.floor(data) + 0.5)) else math.floor(data)

    if data > ((2 ** 16) - 1): data = (2 ** 16) - 1
    if data < 0: data = 0

    try:
        if dac == "all":
            for i in range(8):
                defaultSettings[f"dac{chr(ord('A') + i)}"] = data
        else:
            defaultSettings[f"dac{chr(ord('A') + dac)}"] = data

        dac_write(data, writeup, dac)
    except Exception as e:
        print(e)

def main(stdscr):
    stdscr.clear()
    rectangle(stdscr, 16, 0,19,32)

    editwin = curses.newwin(1,30, 17,1)
    box = Textbox(editwin)
    #stdscr.noecho()
    stdscr.nodelay(1)


    listA = []
    listB = []
    listC = []
    t_update = time.time()
    while True:

        t_curr = time.time()

        listA.append(adcA.voltage)
        listB.append(adcB.voltage)
        listC.append(adcC.voltage)
        # listA.append(np.random.randint(50))
        # listB.append(np.random.randint(50))
        # listC.append(np.random.randint(50))

        c = stdscr.getch()
        if c == ord('q'):
            command = box.edit()
            #stdscr.addstr(20,0,command)
            parsed = parse.parse("{} {}", command)
            do_update_dac(float(parsed[1]), int(parsed[0]))

        if (t_curr - t_update) > 1:
            try:
                defaultSettings['adcA'] = np.median(listA)
                defaultSettings['adcB'] = np.median(listB)
                defaultSettings['adcC'] = np.median(listC)
                listA = []
                listB = []
                listC = []

                for i in range(8):
                    d = "dac" + chr(ord('A') + i)
                    stdscr.addstr(i, 0, f"{d}: {defaultSettings[d]}")

                for i in range(3):
                    d = "adc" + chr(ord('A') + i)
                    stdscr.addstr( i + 8,0, f"{d}: {defaultSettings[d]}")

                stdscr.addstr(12, 0, "Press \"q\" to give a command...")
                stdscr.addstr(13, 0, "dac update command syntax: <dac> <value>")
                stdscr.addstr(14, 0, "eg, to update dacB to 2.3V: 1 2.3")


            except Exception as e:
                print(e)

            t_update = time.time()

        time.sleep(0.01)
        stdscr.refresh()

if __name__ == "__main__":
    wrapper(main)
