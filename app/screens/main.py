from datetime import datetime

import time
import json
import pygame
import numpy as np
import datetime as dt
import subprocess as sub
from datetime import datetime
from pygame.mixer import Sound
from os.path import dirname, join

import paho.mqtt.client as mqtt

from ui import colours, screenPWM
from ui.widgets.background import LcarsBackgroundImage, LcarsImage
from ui.widgets.gifimage import LcarsGifImage
from ui.widgets.lcars_widgets import *
from ui.widgets.screen import LcarsScreen

from datasources.network import get_ip_address_string

def CtoF(tempy):
    """
    Convert Celcius to Fahrenheit
    """
    ft = (float(tempy)*(9./5.) + 32.)
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
        script_dir = dirname(__file__)
        ipath = join(script_dir, '../assets/mainscreen.png')
        all_sprites.add(LcarsBackgroundImage(ipath),
                        layer=0)

        # panel text
        all_sprites.add(LcarsText(colours.BLACK, (15, 44), "LCARS 105"),
                        layer=1)
                        
        all_sprites.add(LcarsText(colours.ORANGE, (0, 135), "HOME AUTOMATION", 2),
                        layer=1)
        all_sprites.add(LcarsBlockMedium(colours.RED_BROWN, (145, 16), "LIGHTS"),
                        layer=1)
        all_sprites.add(LcarsBlockSmall(colours.ORANGE, (211, 16), "CAMERAS"),
                        layer=1)
        all_sprites.add(LcarsBlockLarge(colours.BEIGE, (249, 16), "ENERGY"),
                        layer=1)

        self.ip_address = LcarsText(colours.BLACK, (444, 520),
                                    get_ip_address_string())
        all_sprites.add(self.ip_address, layer=1)

        # info text
        all_sprites.add(LcarsText(colours.WHITE, (192, 174), "EVENT LOG:", 1.5),
                        layer=3)
        all_sprites.add(LcarsText(colours.BLUE, (244, 174), "2 ALARM ZONES TRIGGERED", 1.5),
                        layer=3)
        all_sprites.add(LcarsText(colours.BLUE, (286, 174), "14.3 kWh USED YESTERDAY", 1.5),
                        layer=3)
        all_sprites.add(LcarsText(colours.BLUE, (330, 174), "1.3 Tb DATA USED THIS MONTH", 1.5),
                        layer=3)
        self.info_text = all_sprites.get_sprites_from_layer(3)

        # date display
        self.stardate = LcarsText(colours.BLUE, (12, 380), "STAR DATE 2311.05 17:54:32", 1.5)
        self.lastClockUpdate = 0
        self.whenLastRead = dt.datetime.now()
        all_sprites.add(self.stardate, layer=1)

        # buttons
        all_sprites.add(LcarsButton(colours.RED_BROWN, (6, 662), "LOGOUT", self.logoutHandler),
                        layer=4)
        all_sprites.add(LcarsButton(colours.BEIGE, (107, 127), "SENSORS", self.sensorsHandler),
                        layer=4)
        all_sprites.add(LcarsButton(colours.PURPLE, (107, 262), "GAUGES", self.gaugesHandler),
                        layer=4)
        all_sprites.add(LcarsButton(colours.PEACH, (107, 398), "WEATHER", self.weatherHandler),
                        layer=4)
        all_sprites.add(LcarsButton(colours.PEACH, (108, 536), "HOME", self.homeHandler),
                        layer=4)

        # gadgets
        all_sprites.add(LcarsGifImage("assets/gadgets/fwscan.gif", (277, 556), 100), layer=1)

        self.sensor_gadget = LcarsGifImage("assets/gadgets/lcars_anim2.gif", (235, 150), 100)
        self.sensor_gadget.visible = False
        all_sprites.add(self.sensor_gadget, layer=2)

        self.dashboard = LcarsImage("assets/gadgets/dashboard.png", (187, 232))
        self.dashboard.visible = False
        all_sprites.add(self.dashboard, layer=2)

        self.weather = LcarsImage("assets/weather.jpg", (188, 122))
        self.weather.visible = False
        all_sprites.add(self.weather, layer=2)

        #all_sprites.add(LcarsMoveToMouse(colours.WHITE), layer=1)
        self.beep1 = Sound("assets/audio/panel/201.wav")
        Sound("assets/audio/panel/220.wav").play()

    def update(self, screenSurface, fpsClock):
        if pygame.time.get_ticks() - self.lastClockUpdate > 1000:
            sDateFmt = "%d%m.%y %H:%M:%S"
            sDate = "{}".format(datetime.now().strftime(sDateFmt))
            self.stardate.setText(sDate)
            self.lastClockUpdate = pygame.time.get_ticks()

        LcarsScreen.update(self, screenSurface, fpsClock)

    def handleEvents(self, event, fpsClock):
        if event.type == pygame.MOUSEBUTTONDOWN:
#            self.beep1.play()
            pass

        if event.type == pygame.MOUSEBUTTONUP:
            return False

    def hideInfoText(self):
        if self.info_text[0].visible:
            for sprite in self.info_text:
                sprite.visible = False

    def showInfoText(self):
        for sprite in self.info_text:
            sprite.visible = True

    def gaugesHandler(self, item, event, clock):
        self.hideInfoText()
        self.sensor_gadget.visible = False
        self.dashboard.visible = True
        self.weather.visible = False

    def sensorsHandler(self, item, event, clock):
        self.hideInfoText()
        self.sensor_gadget.visible = True
        self.dashboard.visible = False
        self.weather.visible = False

    def weatherHandler(self, item, event, clock):
        self.hideInfoText()
        self.sensor_gadget.visible = False
        self.dashboard.visible = False
        self.weather.visible = True

    def homeHandler(self, item, event, clock):
        self.showInfoText()
        self.sensor_gadget.visible = False
        self.dashboard.visible = False
        self.weather.visible = False
        
    def logoutHandler(self, item, event, clock):
        from screens.authorize import ScreenAuthorize
        self.loadScreen(ScreenAuthorize())


