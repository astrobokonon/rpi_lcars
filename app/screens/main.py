import time
import pygame
import numpy as np
import subprocess as sub
from datetime import datetime
from pygame.mixer import Sound

import paho.mqtt.client as mqtt

from ui import colours
from ui.widgets.background import LcarsBackgroundImage, LcarsImage
from ui.widgets.gifimage import LcarsGifImage
from ui.widgets.lcars_widgets import LcarsText, LcarsButton
from ui.widgets.screen import LcarsScreen


def CtoF(tempy):
    """
    Convert Celcius to Fahrenheit
    """
    ft = (np.float(tempy)*(9./5.) + 32.)
    return ft


class ScreenMain(LcarsScreen):
    def setup(self, all_sprites):
        # Weather parameters
        self.temperature = -9999
        self.tStr = None
        self.pressure = -9999
        self.pStr = None
        self.humidity = -9999
        self.hStr = None
        self.battery = -9999
        self.load = -9999
        self.pwrStr = None
        self.timestamp = -9999
        self.tsStr = None
        self.displayedValue = "Temp"
        self.paramStr = self.tStr

        # Background image/overall layout
        all_sprites.add(LcarsBackgroundImage("assets/mainscreen.png"),
                        layer=0)

        # Screen brightness we start from
        self.sbrightness = 800
        # Screen control buttons
        buttonBri = LcarsButton((255, 204, 153), (5, 270), "BRIGHTER",
                                self.screenBrighterHandler)
        buttonDim = LcarsButton((255, 153, 102), (5, 375), "DIMMER",
                                self.screenDimmerHandler)
        buttonOff = LcarsButton((204, 102, 102), (50, 320), "SCREEN OFF",
                                self.logoutHandler)
        all_sprites.add(buttonBri, layer=4)
        all_sprites.add(buttonDim, layer=4)
        all_sprites.add(buttonOff, layer=4)

        # Header text
        all_sprites.add(LcarsText((255, 204, 153), (-5, 55),
                                  "WEATHER", size=3), layer=1)

        # date display
        sDateFmt = "%d%m.%y %H:%M:%S"
        sDate = "{}".format(datetime.now().strftime(sDateFmt))
        self.stardate = LcarsText(colours.BLUE, (55, 55),
                                  sDate, size=2.0)
        self.lastClockUpdate = 0
        all_sprites.add(self.stardate, layer=1)

        # Section/Parameter ID Text
        self.sensorTimestampText = LcarsText((0, 0, 0), (104, 304),
                                             "LAST UPDATE: ", 0.60)
        self.sectionText = LcarsText((255, 204, 153), (120, 55),
                                     "TEMPERATURE:", 3.)
        all_sprites.add(self.sensorTimestampText, layer=4)
        all_sprites.add(self.sectionText, layer=4)

        # Section Value Text.  If the temperature isn't nuts, it's probably
        #   a good enough value to display so start with that.
        self.paramValueText = LcarsText(colours.BLUE, (170, -1),
                                        "XX.X C|XX.X F", 4.5)

        all_sprites.add(self.paramValueText, layer=3)
        self.info_text = all_sprites.get_sprites_from_layer(3)

        # buttons
        buttrowpos = (270, 65)
        butt1 = LcarsButton(colours.BEIGE, buttrowpos, "Temperature",
                            self.cTempHandler)
        butt2 = LcarsButton(colours.PURPLE,
                            (buttrowpos[0], buttrowpos[1] + butt1.size[0]),
                            "Pressure", self.cPressHandler)
        butt3 = LcarsButton(colours.PURPLE,
                            (buttrowpos[0],
                             buttrowpos[1] + butt1.size[0] + butt2.size[0]),
                            "Humidity", self.cHumiHandler)
        butt4 = LcarsButton(colours.PURPLE,
                            (buttrowpos[0],
                             buttrowpos[1] + butt1.size[0] + butt2.size[0] + butt3.size[0]),
                            "Power", self.cPowerHandler)

        all_sprites.add(butt1, layer=5)
        all_sprites.add(butt2, layer=5)
        all_sprites.add(butt3, layer=5)
        all_sprites.add(butt4, layer=5)

        # Local (intranet) MQTT server setup; Hopefully we can can start
        #   with the current values already there if all is well with MQTT
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("192.168.1.66", 1883, 60)

        # Non-blocking call that processes network traffic, dispatches
        #   callbacks and handles reconnecting.  Must call client.loop_stop()
        #   when you're done with stuff.
        self.client.loop_start()

        if self.temperature != -9999:
            self.paramStr = self.tStr
            # Note: We need to explicitly update the strings since they're
            #   caught in the time loop and may lay
            self.updateDisplayedSensorStrings()

    def update(self, screenSurface, fpsClock):
        if pygame.time.get_ticks() - self.lastClockUpdate > 1000:
            sDateFmt = "%d%m.%y %H:%M:%S"
            sDate = "{}".format(datetime.now().strftime(sDateFmt))
            self.stardate.setText(sDate)

# Not needed?
            # While we're at it, update the other strings that
            #   could have changed (param value and last update time)
#            self.updateDisplayedSensorStrings()

            self.lastClockUpdate = pygame.time.get_ticks()
        LcarsScreen.update(self, screenSurface, fpsClock)

    def handleEvents(self, event, fpsClock):
        LcarsScreen.handleEvents(self, event, fpsClock)

        if event.type == pygame.MOUSEBUTTONDOWN:
            #self.beep1.play()
            pass

        if event.type == pygame.MOUSEBUTTONUP:
            return False

    def screenBrighterHandler(self, item, event, clock):
        try:
            self.sbrightness += 150
            if self.sbrightness < 10:
                self.sbrightness = 10
            if self.sbrightness > 1023:
                self.sbrightness = 1023
            sub.call(['gpio', '-g', 'pwm', '18', str(self.sbrightness)])
        except OSError:
            pass

    def screenDimmerHandler(self, item, event, clock):
        try:
            self.sbrightness -= 150
            if self.sbrightness < 10:
                self.sbrightness = 10
            if self.sbrightness > 1023:
                self.sbrightness = 1023
            sub.call(['gpio', '-g', 'pwm', '18', str(self.sbrightness)])
        except OSError:
            pass

    def cTempHandler(self, item, event, clock):
        self.sectionText.setText("TEMPERATURE:")
        self.displayedValue = "Temp"
        self.paramStr = self.tStr
        self.updateDisplayedSensorStrings()

    def cPressHandler(self, item, event, clock):
        self.sectionText.setText("PRESSURE:")
        self.displayedValue = "Pre"
        self.paramStr = self.pStr
        self.updateDisplayedSensorStrings()

    def cHumiHandler(self, item, event, clock):
        self.sectionText.setText("HUMIDITY:")
        self.displayedValue = "Humi"
        self.paramStr = self.hStr
        self.updateDisplayedSensorStrings()

    def cPowerHandler(self, item, event, clock):
        self.sectionText.setText("STATION POWER:")
        self.displayedValue = "Powr"
        self.paramStr = self.pwrStr
        self.updateDisplayedSensorStrings()

    def logoutHandler(self, item, event, clock):
        from screens.blanker import ScreenBlanker
        self.client.loop_stop()
        self.client.unsubscribe("station/#")
        self.client.disconnect()

        self.loadScreen(ScreenBlanker())

    def updateDisplayedSensorStrings(self):
        """
        Update the sensor value and associated timestamp when demanded
        """
        self.paramValueText.setText(self.paramStr)
        self.sensorTimestampText.setText(self.tsStr)

    def on_connect(self, client, userdata, flags, rc):
        """
        Callback for when the client receives a CONNACK response from server.
        """
        print("Connected with result code "+str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        #   reconnect then subscriptions will be renewed.
        #   The character '#' is a wildcard meaning all.
        client.subscribe("station/#")

    def on_message(self, client, userdata, msg):
        """
        Callback for when a PUBLISH message is received from the server.
        """
#        print(msg.topic+" "+str(msg.payload))

        if msg.topic.find("temperature") > -1:
            self.temperature = np.float(msg.payload)
            self.tStr = "%02.1f C | %02.1f F" % (self.temperature,
                                                 CtoF(self.temperature))
            if self.displayedValue == "Temp":
                self.paramStr = self.tStr
            print "Update", self.tStr
        if msg.topic.find("pressure") > -1:
            self.pressure = np.float(msg.payload)
            self.pStr = "%04.2f mB" % (self.pressure)
            if self.displayedValue == "Pres":
                self.paramStr = self.pStr
            print "Update", self.pStr
        elif msg.topic.find("humidity") > -1:
            self.humidity = np.float(msg.payload)
            self.hStr = "%03.0f %%" % (self.humidity)
            if self.displayedValue == "Humi":
                self.paramStr = self.hStr
            print "Update", self.hStr
        elif msg.topic.find("battery") > -1:
            self.battery = np.float(msg.payload)
            self.pwrStr = "%01.2f / %01.2f V" % (self.battery, self.load)
            if self.displayedValue == "Powr":
                self.paramStr = self.pwrStr
            print "Update", self.pwrStr
        elif msg.topic.find("load") > -1:
            self.load = np.float(msg.payload)
            self.pwrStr = "%01.2f / %01.2f V" % (self.battery, self.load)
            if self.displayedValue == "Powr":
                self.paramStr = self.pwrStr
            print "Update", self.pwrStr
        elif msg.topic.find("timestamp") > -1:
            sDateFmt = "%d%m.%y %H:%M:%S"
            self.timestamp = np.int(msg.payload)
            self.timestampDT = datetime.fromtimestamp(self.timestamp)
            sDate = "{}".format(self.timestampDT.strftime(sDateFmt))
            self.tsStr = "Last Update: %s" % (sDate)
            print "Update", self.tsStr

        self.updateDisplayedSensorStrings()
