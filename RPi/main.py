import smbus as sm
import time
from mqtt_client import MQTTClient

channel = 1
addr = 0x72 # specific dac board (configurable by jumpers) , global address (write to all dac boards) is 0x73

bus = sm.SMBus(channel)

writeup = 3 # command to write and update the dac
dacs = [0,1,2,3,4,5,6,7] # each dac has a binary address
all_dacs = 15 # all dacs at once

defaultSettings = {"user":"dac", "password":"password", "remoteIP":"192.168.0.100", "remoteUser":"dacControl", "mqttDelay":5,"mqttReconn":5, "dacA":0, "dacB":0, "dacC":0, "dacD":0, "dacE":0, "dacF":0, "dacG":0, "dacH":0, "loadLast"=True}

try:
    with open("lastSettings.json", "r") as f:
        defaultSettings = json.load(f)

        if defaultSettings["loadLast"]:
            for i in range(8):
                dac_write(defaultSettings[f"dac{chr(ord('A')+i)}"], writeup, i)  

except:
    pass

def recv(client, feed_id, payload):

    command = json.loads(payload)

    if command["command"] == "writeup":
        voltage = command["voltage"]
        data = voltage/(5/(2**16)-1)
        data = if (data > (math.floor(data) + 0.5)): math.ceil(data) else math.floor(data) 
        
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
        except:
            client.publish("ack", "nack")

        saveSettings()

def saveSettings():

    try:
        with open("lastSettings.json", "w") as f:
            json.dump(f)
    except:
        pass


def dac_write(data, command, dac):

    # data should be 2 bytes
    # command should be 1 byte
    # dac should be 1 byte

    # full command sent to dac is (in binary) ccccaaaa dddddddd dddddddd
    b1 = (command<<4) + dac # first byte is 4 bits command then 4 bits which dac
    b2 = (data & (0xff << 8)) >> 8 # second byte is first byte of data (leftmost set of ds)
    b3 = data & 0xff # third byte is second byte of data (rightmost set of ds)

    bus.write_i2c_block_data(addr, b1, [b2, b3])



# init mqtt
client = MQTTClient(defaultSettings["user"], defaultSettings["password"], service_host=defaultSettings["remoteIP"], secure=False, port=5005)
client.on_recv = recv

try:
    client.connect()
    time.sleep(0.5)
    client.subscribe("commands", feed_user=defaultSettings["remoteUser"])
    time.sleep(0.1)
    conn = True
except:
    conn = False


t_update = time.time()
t_reconn = time.time()
while True:

    t_curr = time.time()

    if conn and (t_curr - t_update)>defaultSettings["mqttDelay"]:
        try:
            client.loop(timeout_sec=0.5)
            client.publish("state", json.dumps(defaultSettings))
            conn = True
        except:
            conn = False

    if not conn and (t_curr - t_reconn)>defaultSettings["mqttReconn"]:
        try:
            client.connect()
            time.sleep(0.5)
            client.subscribe("commands", feed_user=defaultSettings["remoteUser"])
            time.sleep(0.1)
            conn = True
        except:
            conn = False