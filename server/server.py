from mqtt_client import MQTTClient
import json, sys, time
import datetime as dt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QWidget, QLineEdit, QPushButton, QPlainTextEdit
from PyQt5 import QtWidgets, QtCore, QtGui

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        
        self.defaultSettings = {'user':"dacControl", 'password':'password', 'remoteIP':"192.168.0.103", "remoteUser":"dac"}
        self.dacLabels = ["dacA", "dacB", "dacC", "dacD", "dacE", "dacF", "dacG", "dacH"] # change these to smth more useful
        self.adc_names = ['Phase', 'Power 1', 'Power 2']
        
        self.outFile = f"logs/logs_{dt.datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"

        # main window
        self.setWindowTitle("DAC Command")
        self.setGeometry(100,100,1300,850)
        color = self.palette().color(QtGui.QPalette.Window)  # Get the default window background,
        styles = {"color": "#000", "font-size": "20px"}

        # MQTT label
        self.mqtt_label = QLabel('MQTT:', parent=self)
        self.mqtt_label.move(650,20)
        self.mqtt_label.resize(220,80)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.mqtt_label.setFont(font)
        self.mqtt_label.show()

        # MQTT message box
        self.text = QPlainTextEdit(parent=self)
        self.text.move(650, 90)
        self.text.resize(600,700)
        self.text.show()
        self.text.setReadOnly(True)


        # this doesnt work any other way i tried
        self.button_functions = []
        self.button_functions.append(lambda: self.voltage_send(0))
        self.button_functions.append(lambda: self.voltage_send(1))
        self.button_functions.append(lambda: self.voltage_send(2))
        self.button_functions.append(lambda: self.voltage_send(3))
        self.button_functions.append(lambda: self.voltage_send(4))
        self.button_functions.append(lambda: self.voltage_send(5))
        self.button_functions.append(lambda: self.voltage_send(6))
        self.button_functions.append(lambda: self.voltage_send(7))
        self.button_functions.append(lambda: self.voltage_send("all"))

        # set dac input boxes
        self.dac_send = []
        self.dac_send_btn = []
        for i in range(8):
            self.dac_send.append(QLineEdit(parent=self))
            self.dac_send[i].move(100, 90+i*50)
            self.dac_send[i].resize(60, 50)
            font = QtGui.QFont()
            font.setPointSize(12)
            self.dac_send[i].setFont(font)
            self.dac_send[i].show()
       
            self.dac_send_btn.append(QPushButton(f"Set {self.dacLabels[i]}", parent=self))
            self.dac_send_btn[i].move(170, 90+50*i)
            self.dac_send_btn[i].resize(200, 50)
            font = QtGui.QFont()
            font.setPointSize(10)
            self.dac_send_btn[i].setFont(font)
            self.dac_send_btn[i].show()


            self.dac_send_btn[i].clicked.connect(self.button_functions[i])

        i=8
        self.dac_send.append(QLineEdit(parent=self))
        self.dac_send[i].move(100, 90+10*50)
        self.dac_send[i].resize(60, 50)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.dac_send[i].setFont(font)
        self.dac_send[i].show()
   
        self.dac_send_btn.append(QPushButton(f"Set All", parent=self))
        self.dac_send_btn[i].move(170, 90+50*10)
        self.dac_send_btn[i].resize(200, 50)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.dac_send_btn[i].setFont(font)
        self.dac_send_btn[i].show()


        self.dac_send_btn[i].clicked.connect(self.button_functions[i])

        self.dac_readouts = []
        for i in range(8):
            self.dac_readouts.append(QLineEdit(parent=self))
            self.dac_readouts[i].move(20, 90+i*50)
            self.dac_readouts[i].resize(60, 50)
            font = QtGui.QFont()
            font.setPointSize(12)
            self.dac_readouts[i].setFont(font)
            self.dac_readouts[i].show()
            self.dac_readouts[i].setReadOnly(True)

        self.adc_readouts = []
        self.adc_labels = []
        for i in range(3):
            self.adc_readouts.append(QLineEdit(parent=self))
            self.adc_readouts[i].move(20, 900+i*50)
            self.adc_readouts[i].resize(60, 50)
            font = QtGui.QFont()
            font.setPointSize(12)
            self.adc_readouts[i].setFont(font)
            self.adc_readouts[i].show()
            self.adc_readouts[i].setReadOnly(True)

            self.adc_labels.append(QLabel(self.adc_names[i], parent=self))
            self.adc_labels[i].move(20, 900+i*50)
            self.adc_labels[i].resize(220, 80)
            font = QtGui.QFont()
            font.setPointSize(10)
            self.adc_labels[i].setFont(font)
            self.adc_labels[i].show()

        # command label
        self.command_label = QLabel('Commands:', parent=self)
        self.command_label.move(20, 20)
        self.command_label.resize(220,80)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.command_label.setFont(font)
        self.command_label.show()

        # ack is green when acked, else red
        self.ack_led = QLabel("",parent=self)
        self.ack_led.move(20, 240+10*50)
        self.ack_led.resize(30,30)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.ack_led.setFont(font)
        self.ack_led.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.ack_led.setText("")
        self.ack_led.setPixmap(QtGui.QPixmap("icons/green-led-on.png"))
        self.ack_led.setScaledContents(True)
        self.ack_led.show()

        # ack label
        self.ack_label = QLabel('Command Acked', parent=self)
        self.ack_label.move(60, 230+10*50)
        self.ack_label.resize(400, 50)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.ack_label.setFont(font)
        self.ack_label.show()

        # init mqtt
        self.acked = True
        self.ack_time = time.time()
        self.init_mqtt()
        
        # make sure connected
        # runs a function every time the timer goes off
        self.conn_timer = QtCore.QTimer()
        self.conn_timer.setInterval(10000) # 10s
        self.conn_timer.timeout.connect(self.check_connect)
        self.conn_timer.start()

        
    def check_connect(self):
    
        self.conn = self.client._connected
    
        if not self.conn:
            self.append_line("Disconnected from MQTT!, retrying automatically")
            self.init_mqtt()
            

    # init mqtt, subscribe to relevant feeds
    def init_mqtt(self):
        self.client = MQTTClient(self.defaultSettings["user"], self.defaultSettings["password"], service_host=self.defaultSettings["remoteIP"], secure=False, port=5005)
        self.client.on_message = self.recv
        try:
            self.client.connect()
            self.conn = True
        except:
            self.conn = False
            return -1

        time.sleep(0.5)
        self.client.subscribe("state", feed_user=self.defaultSettings["remoteUser"],qos=1)
        self.client.subscribe("ack", feed_user=self.defaultSettings["remoteUser"],qos=1)
        time.sleep(0.5)

        # this causees a race condition with the textbox that causes a segfault
        # kinda annoying but that's threading for you
        #self.client.loop_background()

        # runs a function every time the timer goes off
        try:
            self.timer.stop()
        except:
            pass

        self.timer = QtCore.QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.poll)
        self.timer.start()

    # run every time we recieve a MQTT message
    def recv(self, client, feed_id, payload):
        self.append_line(f"Got message from {feed_id}")

        # log all mqtt messages
        with open(self.outFile, "a") as logfile:
            now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f") #time.time()
            logfile.write(f"{now}: client: {client} feed id: {feed_id} payload: {payload}")

        # parse acks or update graphs
        if feed_id == "ack" and payload == "ack":
            self.acked = True
            self.ack_time = time.time()
        elif feed_id == "state":
            state = json.loads(payload)

            for i in range(8):
                self.dac_readouts[i].setReadOnly(False)
                voltage = 5*state[f"dac{chr(ord('A')+i)}"] / ((2**16)-1)
                self.dac_readouts[i].setText(f"{voltage:.2f}")
                self.dac_readouts[i].setReadOnly(True)

            for i in range(3):
                self.adc_readouts[i].setReadOnly(False)
                self.adc_readouts[i].setText(f"{voltage:.2f}")
                self.adc_readouts[i].setReadOnly(True)


    # add a new line to the bottom of the textbox
    def append_line(self, line):
        new = '\n' + line
        self.text.insertPlainText(new)
        self.text.moveCursor(self.text.textCursor().Down)#scrolls down

    # polling function run on timer
    def poll(self):
        try:
            # check for mqtt messages
            self.client.loop(timeout_sec=0.1)

            # check that commands are acknowledged
            td = time.time() - self.ack_time
            if not self.acked and td >= 20:
                self.append_line(f"No ack for {td:0.1f} seconds!!")
                self.ack_time = time.time()

            # indicator if command has been acknowledged
            if self.acked:
                self.ack_led.setPixmap(QtGui.QPixmap("icons/green-led-on.png"))
            else:
                self.ack_led.setPixmap(QtGui.QPixmap("icons/red-led-on.png"))
        except KeyboardInterrupt:
            sys.exit(0)
            

    # bound to set temperature button
    def voltage_send(self, dac):
        try:
            if dac == "all":
                voltage = float(self.dac_send[-1].text())
            else:
                voltage = float(self.dac_send[dac].text())

            command = {"command": "writeup", "voltage": voltage, "dac":dac}
            self.client.publish("commands", json.dumps(command))
            self.acked = False
            self.ack_time = time.time()
        except ValueError as e:
            self.append_line("Cannot set voltage: couldnt convert string to float")

# breakpoint function for use with gdb
def bp():
    import os, signal; os.kill(os.getpid(), signal.SIGTRAP)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())
