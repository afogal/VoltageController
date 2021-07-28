import smbus as sm
import time, json, math
from mqtt_client import MQTTClient
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.ads1x15 import Mode
from adafruit_ads1x15.analog_in import AnalogIn
import board
from busio import I2C
from adafruit_bus_device.i2c_device import I2CDevice

channel = 1
addr = 0x72 # specific dac board (configurable by jumpers) , global address (write to all dac boards) is 0x73

#bus = sm.SMBus(channel)
bus = I2C(board.SCL, board.SDA)
dac = I2CDevice(bus, addr)

writeup = 3 # command to write and update the dac
dacs = [0,1,2,3,4,5,6,7] # each dac has a binary address
all_dacs = 15 # all dacs at once
ads = ADS.ADS1115(bus, address=0x48)
adcA = AnalogIn(ads, ADS.P0, ADS.P1)
adcB = AnalogIn(ads, ADS.P2)
adcC = AnalogIn(ads, ADS.P3)
ads.data_rate = 860 # Max rate is 860
_ = adcA.value
_ = adcB.value
_ = adcC.value


defaultSettings = {"user":"dac", "password":"password", "remoteIP":"192.168.0.103", "remoteUser":"dacControl",
                   "mqttDelay":5,"mqttReconn":5, "dacA":0, "dacB":0, "dacC":0, "dacD":0, "dacE":0, "dacF":0,
                   "dacG":0, "dacH":0, "loadLast":True, "adcA":-1, "adcB":-1, "adcC":-1}

# we dont worry about having negative values or loading old values for the adc stuff because it will read before
#     sending every time, so we will only ever report real values.

try:
    with open("lastSettings.json", "r") as f:
        defaultSettings = json.load(f)

        if defaultSettings["loadLast"]:
            for i in range(8):
                dac_write(defaultSettings[f"dac{chr(ord('A')+i)}"], writeup, i)  

except:
    pass


def recv(client, feed_id, payload):

    print(payload)
    command = json.loads(payload)

    if command["command"] == "writeup":
        voltage = command["voltage"]
        data = voltage/(5/((2**16)-1))
        data = math.ceil(data) if (data > (math.floor(data) + 0.5)) else math.floor(data) 

        if data > ((2**16)-1): data = (2**16)-1
        if data < 0: data=0

        if (not command["dac"] in dacs) or command["dac"] == "all":
            client.publish("ack", "nack")

        try:
            dac_write(data, writeup, command["dac"])

            if command["dac"] == "all":
                for i in range(8):
                    defaultSettings[f"dac{chr(ord('A')+i)}"] = data
            else:
                defaultSettings[f"dac{chr(ord('A')+command['dac'])}"] = data


            client.publish("ack", "ack")
        except Exception as e:
            print(e)
            client.publish("ack", "nack")

        saveSettings()

def saveSettings():

    try:
        with open("lastSettings.json", "w") as f:
            json.dump(defaultSettings, f)
    except Exception as e:
        print(e)
        pass


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
    with dac as device:
        device.write(bytes([b1,b2,b3]))



# init mqtt
client = MQTTClient(defaultSettings["user"], defaultSettings["password"], service_host=defaultSettings["remoteIP"], secure=False, port=5005)
client.on_message = recv

try:
    client.connect()
    time.sleep(0.5)
    client.subscribe("commands", feed_user=defaultSettings["remoteUser"], qos=1)
    time.sleep(0.1)
    conn = True
except:
    conn = False


t_update = time.time()
t_reconn = time.time()
gain = 2/3
while True:

    t_curr = time.time()

    if conn and (t_curr - t_update)>defaultSettings["mqttDelay"]:
        try:
            client.loop(timeout_sec=1)
            defaultSettings['adcA'] = adcA.voltage
            defaultSettings['adcB'] = adcB.voltage
            defaultSettings['adcC'] = adcC.voltage
            print(defaultSettings['adcA'],defaultSettings['adcB'],defaultSettings['adcC'])
            client.publish("state", json.dumps(defaultSettings))
            conn = True
        except Exception as e:
            print(e)
            conn = False
        
        t_update = time.time()

    if not conn and (t_curr - t_reconn)>defaultSettings["mqttReconn"]:
        try:
            client.connect()
            time.sleep(0.5)
            client.subscribe("commands", feed_user=defaultSettings["remoteUser"], qos=1)
            time.sleep(0.1)
            conn = True
        except Exception as e:
            print(e)
            conn = False

        t_reconn = time.time()

    time.sleep(0.01)
