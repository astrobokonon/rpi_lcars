import time
import pygame
import numpy as np
import datetime as dt
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
        self.timestampDT = dt.datetime.now()
        self.beatWarningTime = 10.*60.
        self.runningCam = False
        self.cmdCamGo = ['sudo', '-H', '-u', 'pi',
                         'adafruit-io', 'camera', 'start',
                         '-f', 'camera_feed', '-m', 'false',
                         '-r', '5', '-v', 'true']
        self.cmdCamStop = ['sudo', '-H', '-u', 'pi',
                           'adafruit-io', 'camera', 'stop']

        # Background image/overall layout
        all_sprites.add(LcarsBackgroundImage("assets/camscreen.png"),
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
                                  "CAMERA", size=3), layer=1)

        # date display
        sDateFmt = "%d%m.%y %H:%M:%S"
        sDate = "{}".format(datetime.now().strftime(sDateFmt))
        self.stardate = LcarsText(colours.BLUE, (55, 55),
                                  sDate, size=2.0)
        self.lastClockUpdate = 0
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
                                        "CAMERA: STOPPED", 4.5)

        all_sprites.add(self.paramValueText, layer=3)
        self.info_text = all_sprites.get_sprites_from_layer(3)

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
#        print self.beatCounter, self.beatWarningTime
        if self.beatCounter > self.beatWarningTime:
            self.beatColor = (255, 0, 0)
        else:
            self.beatColor = (0, 255, 0)
        self.curHeartbeat(screenSurface)

    def handleEvents(self, event, fpsClock):
        LcarsScreen.handleEvents(self, event, fpsClock)

        if event.type == pygame.MOUSEBUTTONDOWN:
#            self.beep1.play()
            pass

        if event.type == pygame.MOUSEBUTTONUP:
            return False

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

    def logoutHandler(self, item, event, clock):
        from screens.blanker import ScreenBlanker
        self.client.loop_stop()
        self.client.unsubscribe("station/#")
        self.client.disconnect()

        self.loadScreen(ScreenBlanker())

    def curHeartbeat(self, screenSurface):
        pygame.draw.rect(screenSurface, self.beatColor, (211, 100, 50, 12), 0)

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

        if msg.topic.find("camera") > -1:
            print "Update", self.pStr
