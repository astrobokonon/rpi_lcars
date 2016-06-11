import pygame
import subprocess as sub
from datetime import datetime
from pygame.mixer import Sound

from ui import colours
from ui.widgets.background import LcarsBackgroundImage, LcarsImage
from ui.widgets.gifimage import LcarsGifImage
from ui.widgets.lcars_widgets import LcarsText, LcarsButton
from ui.widgets.screen import LcarsScreen


class ScreenMain(LcarsScreen):
    def setup(self, all_sprites):
        all_sprites.add(LcarsBackgroundImage("assets/mainscreen.png"),
                        layer=0)

        # Header text
        all_sprites.add(LcarsText((255, 204, 153), (-5, 55),
                                  "WEATHER", size=3), layer=1)

        # Screen brightness
        self.sbrightness = 500

        # date display
        sDateFmt = "%d%m.%y %H:%M:%S"
        sDate = "{}".format(datetime.now().strftime(sDateFmt))
        self.stardate = LcarsText(colours.BLUE, (55, 55),
                                  sDate, size=2.0)
        self.lastClockUpdate = 0
        all_sprites.add(self.stardate, layer=1)

        buttonBri = LcarsButton((255, 204, 153), (5, 270), "BRIGHTER",
                                self.screenBrighterHandler)
        buttonDim = LcarsButton((255, 153, 102), (5, 375), "DIMMER",
                                self.screenDimmerHandler)
        buttonOff = LcarsButton((204, 102, 102), (50, 320), "SCREEN OFF",
                                self.logoutHandler)

        all_sprites.add(buttonBri, layer=4)
        all_sprites.add(buttonDim, layer=4)
        all_sprites.add(buttonOff, layer=4)

#        all_sprites.add(LcarsText(colours.BLACK, (183, 25), "TEMP", size=0.9),
#                        layer=1)
#        all_sprites.add(LcarsText(colours.BLACK, (222, 25), "PRESS", size=0.9),
#                        layer=1)
#        all_sprites.add(LcarsText(colours.BLACK, (372, 25), "HUMI", size=0.9),
#                        layer=1)
#        all_sprites.add(LcarsText(colours.BLACK, (444, 612), "192 168 0 3"),
#                        layer=1)

        # Section/Parameter ID Text
        self.sectionText = LcarsText((255, 204, 153), (120, 55),
                                     "TEMPERATURE:", 3.)
        all_sprites.add(self.sectionText, layer=4)

        # Section Value Text
        self.paramValueText = LcarsText(colours.BLUE, (170, -1),
                                        "XX C / XX F", 4.5)
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

        # gadgets
#        all_sprites.add(LcarsGifImage("assets/gadgets/fwscan.gif",
#                        (277, 556), 100), layer=1)
        self.sensor_gadget = LcarsGifImage("assets/gadgets/lcars_anim2.gif",
                                           (235, 150), 100)
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
#        Sound("assets/audio/panel/220.wav").play()

    def update(self, screenSurface, fpsClock):
        if pygame.time.get_ticks() - self.lastClockUpdate > 1000:
            sDateFmt = "%d%m.%y %H:%M:%S"
            sDate = "{}".format(datetime.now().strftime(sDateFmt))
            self.stardate.setText(sDate)
            self.lastClockUpdate = pygame.time.get_ticks()
        LcarsScreen.update(self, screenSurface, fpsClock)

    def handleEvents(self, event, fpsClock):
        LcarsScreen.handleEvents(self, event, fpsClock)

        if event.type == pygame.MOUSEBUTTONDOWN:
            #self.beep1.play()
            pass

        if event.type == pygame.MOUSEBUTTONUP:
            return False

#    def hideInfoText(self):
#        if self.info_text[0].visible:
#            for sprite in self.info_text:
#                sprite.visible = False

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
        self.paramValueText.setText("XX C / XX F")

    def cPressHandler(self, item, event, clock):
        self.sectionText.setText("PRESSURE:")
        self.paramValueText.setText("XXXX mB / XX.XX mmHg")

    def cHumiHandler(self, item, event, clock):
        self.sectionText.setText("HUMIDITY:")
        self.paramValueText.setText("XX %")

    def cPowerHandler(self, item, event, clock):
        self.sectionText.setText("STATION POWER:")
        self.paramValueText.setText("X.XXX / X.XXX V")

    def logoutHandler(self, item, event, clock):
        from screens.blanker import ScreenBlanker
        self.loadScreen(ScreenBlanker())

