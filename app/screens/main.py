import time
import pygame
import numpy as np
import datetime as dt
import subprocess as sub
from datetime import datetime
from pygame.mixer import Sound

import paho.mqtt.client as mqtt

from ui import colours, screenPWM
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
        self.timestampDT = dt.datetime.now()
        self.beatWarningTime = 10.*60.
        self.runningCam = False

        self.cmdCamGo = ['sudo', '-H', '-u', 'pi',
                         'adafruit-io', 'camera', 'start',
                         '-f', 'camera_feed', '-m', 'false',
                         '-r', '5', '-v', 'false']
        self.cmdCamStop = ['sudo', '-H', '-u', 'pi',
                           'adafruit-io', 'camera', 'stop']

        # Background image/overall layout
        all_sprites.add(LcarsBackgroundImage("assets/mainscreen.png"),
                        layer=0)

        # Screen brightness we start from
        self.sbrightness = 0.5
        # Need this to not crash the auto brightness
        #  button, so choose a default that's easily elimated
        #  from any logging activity just in case
        self.lux = 86.75309

        # Screen control buttons
        buttonBri = LcarsButton((255, 204, 153), (5, 270), "BRIGHTER",
                                self.screenBrighterHandler)
        buttonDim = LcarsButton((255, 153, 102), (5, 375), "DIMMER",
                                self.screenDimmerHandler)
        buttonOff = LcarsButton((204, 102, 102), (50, 270), "OFF",
                                self.logoutHandler)

        # Add this one to self to make it easily changed elsewhere
        self.buttonAuto = LcarsButton(colours.BLUE, (50, 375), "AUTO",
                                      self.autoBrightHandler)
        all_sprites.add(buttonBri, layer=4)
        all_sprites.add(buttonDim, layer=4)
        all_sprites.add(buttonOff, layer=4)
        all_sprites.add(self.buttonAuto, layer=4)

        # Header text
        all_sprites.add(LcarsText((255, 204, 153), (-5, 55),
                                  "WEATHER", size=3), layer=1)

        # date display
        sDateFmt = "%d%m.%y %H:%M:%S"
        sDate = "{}".format(datetime.now().strftime(sDateFmt))
        self.stardate = LcarsText(colours.BLUE, (55, 55),
                                  sDate, size=2.0)
        self.lastClockUpdate = 0
        self.whenLastRead = dt.datetime.now()
        all_sprites.add(self.stardate, layer=1)

        # Section/Parameter ID Text
        self.sensorTimestampText = LcarsText((0, 0, 0), (95, 275),
                                             "LAST UPDATE: ", 1.0)
#        self.sectionText = LcarsText((255, 204, 153), (120, 55),
#                                     "TEMPERATURE:", 3.)
        all_sprites.add(self.sensorTimestampText, layer=4)
#        all_sprites.add(self.sectionText, layer=4)

        # Section Value Text.  If the temperature isn't nuts, it's probably
        #   a good enough value to display so start with that.
        self.paramValueText = LcarsText((255, 204, 153), (170, -1),
                                        "XX.X C|XX.X F", 4.5)

        all_sprites.add(self.paramValueText, layer=3)
        self.info_text = all_sprites.get_sprites_from_layer(3)

        # buttons
        # (Bottom)
        #buttrowpos = (270, 65)
        # (Top)
        buttrowpos = (125, 55)
        self.butt1 = LcarsButton(colours.PURPLE, buttrowpos, "Temperature",
                                 self.cTempHandler)
        self.butt2 = LcarsButton(colours.PURPLE,
                                 (buttrowpos[0],
                                  buttrowpos[1] + self.butt1.size[0]),
                                 "Pressure", self.cPressHandler)
        self.butt3 = LcarsButton(colours.PURPLE,
                                 (buttrowpos[0],
                                  buttrowpos[1] + self.butt1.size[0] +
                                  self.butt2.size[0]),
                                 "Humidity", self.cHumiHandler)
        self.butt4 = LcarsButton(colours.PURPLE,
                                 (buttrowpos[0],
                                  buttrowpos[1] + self.butt1.size[0] +
                                  self.butt2.size[0] + self.butt3.size[0]),
                                 "Power", self.cPowerHandler)

        all_sprites.add(self.butt1, layer=5)
        all_sprites.add(self.butt2, layer=5)
        all_sprites.add(self.butt3, layer=5)
        all_sprites.add(self.butt4, layer=5)

        campos = (270, 320)
        self.buttcam = LcarsButton((204, 102, 102), campos, "KITTY CAM",
                                   self.camHandler)
        all_sprites.add(self.buttcam, layer=4)

        # Local (intranet) MQTT server setup; Hopefully we can can start
        #   with the current values already there if all is well with MQTT
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost", 1883, 60)

        # Non-blocking call that processes network traffic, dispatches
        #   callbacks and handles reconnecting.  Must call client.loop_stop()
        #   when you're done with stuff.
        self.client.loop_start()

        if self.temperature != -9999:
            self.paramStr = self.tStr
            # Note: We need to explicitly update the strings since they're
            #   caught in the time loop and may lag
            self.updateDisplayedSensorStrings()

        # Highlight the default choice so we know where we are and trigger
        self.butt1.changeColor(colours.WHITE)
        self.butt2.changeColor(self.butt2.inactiveColor)
        self.butt3.changeColor(self.butt3.inactiveColor)
        self.butt4.changeColor(self.butt4.inactiveColor)

        # Automatically control screen brightness at start?
        self.autosbrightness = True
        self.buttonAuto.changeColor(colours.WHITE)
      

    def update(self, screenSurface, fpsClock):
        if pygame.time.get_ticks() - self.lastClockUpdate > 1000:
            sDateFmt = "%d%m.%y %H:%M:%S"
            sDate = "{}".format(datetime.now().strftime(sDateFmt))
            self.stardate.setText(sDate)
            self.lastClockUpdate = pygame.time.get_ticks()

        LcarsScreen.update(self, screenSurface, fpsClock)

        # Update the heartbeat indicator(s)
        self.beatCounterDT = (dt.datetime.now() - self.timestampDT)
        self.beatCounter = self.beatCounterDT.total_seconds()
        # Heartbeat bar for whether we read the timestamp remotely correctly
        if self.beatCounter > self.beatWarningTime:
            self.beatColor = (255, 0, 0)
        else:
            self.beatColor = (0, 255, 0)

        # Changing text color depending on time of last good (outdoor) read
        if ((dt.datetime.now() - self.whenLastRead).total_seconds()) > self.beatWarningTime*2.:
            # Warning text color
            self.paramValueText.changeColour((204, 102, 102))
        else:
            # Normal text color
            self.paramValueText.changeColour((255, 204, 153))
        self.curHeartbeat(screenSurface)

    def handleEvents(self, event, fpsClock):
        LcarsScreen.handleEvents(self, event, fpsClock)

        if event.type == pygame.MOUSEBUTTONDOWN:
#            self.beep1.play()
            pass

        if event.type == pygame.MOUSEBUTTONUP:
            return False

    def autoBrightHandler(self, item, event, clock):
        if self.autosbrightness is True:
            self.autosbrightness = False
            self.buttonAuto.changeColor(colours.BLUE)
        else:
            self.autosbrightness = True
            self.buttonAuto.changeColor(colours.WHITE)
            try:
                # First read/scale the last value from the sensor
                self.theLuxRanger()
                print "setting to %f" % (self.sbrightness)
                self.screenBrightAbsolute()
            except:
                # If we're here, something went wrong
                #   but I don't know what to say yet
                print "Whoops"
                pass

    def camHandler(self, item, event, clock):
        try:
            if self.runningCam is False:
                self.runningCam = True
                sub.call(self.cmdCamGo)
            else:
                self.runningCam = False
                sub.call(self.cmdCamStop)
        except OSError:
            pass

    def screenBrightAbsolute(self):
        try:
            screenPWM.screenPWM(self.sbrightness, pin=18)
        except OSError:
            print "Failure to set screen brightness to %f" % \
                (self.sbrightness)
            self.autosbrightness = False

    def screenBrighterHandler(self, item, event, clock):
        try:
            self.sbrightness += 0.1
            if self.sbrightness < 0.1:
                self.sbrightness = 0.1
            if self.sbrightness > 1.0:
                self.sbrightness = 1.0
            screenPWM.screenPWM(self.sbrightness, pin=18)
        except OSError:
            pass

    def screenDimmerHandler(self, item, event, clock):
        try:
            self.sbrightness -= 0.1
            if self.sbrightness < 0.1:
                self.sbrightness = 0.1
            if self.sbrightness > 1.0:
                self.sbrightness = 1.0
            screenPWM.screenPWM(self.sbrightness, pin=18)
        except OSError:
            pass

    def cTempHandler(self, item, event, clock):
        self.displayedValue = "Temp"
        self.paramStr = self.tStr
        self.updateDisplayedSensorStrings()
        self.butt1.changeColor(colours.WHITE)
        self.butt2.changeColor(self.butt2.inactiveColor)
        self.butt3.changeColor(self.butt3.inactiveColor)
        self.butt4.changeColor(self.butt4.inactiveColor)

    def cPressHandler(self, item, event, clock):
        self.displayedValue = "Pre"
        self.paramStr = self.pStr
        self.updateDisplayedSensorStrings()
        self.butt1.changeColor(self.butt1.inactiveColor)
        self.butt2.changeColor(colours.WHITE)
        self.butt3.changeColor(self.butt3.inactiveColor)
        self.butt4.changeColor(self.butt4.inactiveColor)

    def cHumiHandler(self, item, event, clock):
        self.displayedValue = "Humi"
        self.paramStr = self.hStr
        self.updateDisplayedSensorStrings()
        self.butt1.changeColor(self.butt1.inactiveColor)
        self.butt2.changeColor(self.butt2.inactiveColor)
        self.butt3.changeColor(colours.WHITE)
        self.butt4.changeColor(self.butt4.inactiveColor)

    def cPowerHandler(self, item, event, clock):
        self.displayedValue = "Powr"
        self.paramStr = self.pwrStr
        self.updateDisplayedSensorStrings()
        self.butt1.changeColor(self.butt1.inactiveColor)
        self.butt2.changeColor(self.butt2.inactiveColor)
        self.butt3.changeColor(self.butt3.inactiveColor)
        self.butt4.changeColor(colours.WHITE)

    def logoutHandler(self, item, event, clock):
        from screens.blanker import ScreenBlanker
        self.client.loop_stop()
        self.client.unsubscribe("Ostation/#")
        self.client.unsubscribe("Istation/#")
        self.client.disconnect()

        self.loadScreen(ScreenBlanker())

    def updateDisplayedSensorStrings(self):
        """
        Update the sensor value and associated timestamp when demanded
        """
        self.paramValueText.setText(self.paramStr)
        self.sensorTimestampText.setText(self.tsStr)

    def curHeartbeat(self, screenSurface):
        pygame.draw.rect(screenSurface, self.beatColor, (211, 98.5, 235, 14.5), 0)

    def on_connect(self, client, userdata, flags, rc):
        """
        Callback for when the client receives a CONNACK response from server.
        """
        print("Connected with result code "+str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        #   reconnect then subscriptions will be renewed.
        #   The character '#' is a wildcard meaning all.
        client.subscribe("Ostation/#")
        client.subscribe("Istation/lux")

    def on_message(self, client, userdata, msg):
        """
        Callback for when a PUBLISH message is received from the server.
        """

        if msg.topic.find("temperature") > -1:
            self.temperature = np.float(msg.payload)
            self.tStr = "%02.1f C | %02.1f F" % (self.temperature,
                                                 CtoF(self.temperature))
            if self.displayedValue == "Temp":
                self.paramStr = self.tStr
            print "Update", self.tStr
            self.whenLastRead = dt.datetime.now()
        if msg.topic.find("pressure") > -1:
            self.pressure = np.float(msg.payload)
            self.pStr = "%04.2f mB" % (self.pressure)
            if self.displayedValue == "Pres":
                self.paramStr = self.pStr
            print "Update", self.pStr
            self.whenLastRead = dt.datetime.now()
        elif msg.topic.find("humidity") > -1:
            self.humidity = np.float(msg.payload)
            self.hStr = "%03.0f %%" % (self.humidity)
            if self.displayedValue == "Humi":
                self.paramStr = self.hStr
            print "Update", self.hStr
            self.whenLastRead = dt.datetime.now()
        elif msg.topic.find("battery") > -1:
            self.battery = np.float(msg.payload)
            self.pwrStr = "%01.2f / %01.2f V" % (self.battery, self.load)
            if self.displayedValue == "Powr":
                self.paramStr = self.pwrStr
            print "Update", self.pwrStr
            self.whenLastRead = dt.datetime.now()
        elif msg.topic.find("load") > -1:
            self.load = np.float(msg.payload)
            self.pwrStr = "%01.2f / %01.2f V" % (self.battery, self.load)
            if self.displayedValue == "Powr":
                self.paramStr = self.pwrStr
            print "Update", self.pwrStr
            self.whenLastRead = dt.datetime.now()
        elif msg.topic.find("timestamp") > -1:
            sDateFmt = "%d%m.%y %H:%M:%S"
            self.timestamp = np.int(msg.payload)
            self.timestampDT = datetime.fromtimestamp(self.timestamp)
            sDate = "{}".format(self.timestampDT.strftime(sDateFmt))
            self.tsStr = "Last Update: %s" % (sDate)
            print "Update", self.tsStr
        elif msg.topic.find("lux") > -1:
            self.lux = np.float(msg.payload)
            if self.autosbrightness is True:
                self.theLuxRanger()
                self.screenBrightAbsolute()

        self.updateDisplayedSensorStrings()

    def theLuxRanger(self):
        # Turn the lux into a brightness value
        #   >  xr == full brightness
        #   <  mr == min brightness
        # Screen range - 1.0 to 0.1 inclusive
        mr = 3.
        xr = 100.
        if self.lux >= xr:
            self.sbrightness = 1.0
        elif self.lux < xr and self.lux >= mr:
            self.sbrightness = ((self.lux - mr)*(1.0 - 0.2)/(xr - mr)) + 0.2
            self.sbrightness = np.round(self.sbrightness, 3)
        else:
            self.sbrightness = 0.05

        print "Lux: ", self.lux, self.sbrightness

