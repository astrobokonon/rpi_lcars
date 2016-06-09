from datetime import datetime
import pygame
from pygame.mixer import Sound

from ui import colours
from ui.widgets.background import LcarsBackgroundImage, LcarsImage
from ui.widgets.gifimage import LcarsGifImage
from ui.widgets.lcars_widgets import LcarsText, LcarsButton
from ui.widgets.screen import LcarsScreen
from ui.widgets.sprite import LcarsMoveToMouse

class ScreenMain(LcarsScreen):
    def setup(self, all_sprites):
        all_sprites.add(LcarsBackgroundImage("assets/lcars_screen_1.png"),
                        layer=0)
        
        # panel text
        all_sprites.add(LcarsText(colours.BLACK, (11, 25), "LCARS", size=0.9),
                        layer=1)
        all_sprites.add(LcarsText(colours.ORANGE, (0, 85), "WEATHER", size=2),
                        layer=1)
        all_sprites.add(LcarsText(colours.BLACK, (183, 25), "TEMP", size=0.9),
                        layer=1)
        all_sprites.add(LcarsText(colours.BLACK, (222, 25), "PRESS", size=0.9),
                        layer=1)
        all_sprites.add(LcarsText(colours.BLACK, (372, 25), "HUMI", size=0.9),
                        layer=1)
#        all_sprites.add(LcarsText(colours.BLACK, (444, 612), "192 168 0 3"),
#                        layer=1)

        # info text
        all_sprites.add(LcarsText(colours.WHITE, (130, 100), 
                                  "CURRENT WEATHER:", 1.5), layer=3)
        all_sprites.add(LcarsText(colours.BLUE, (160, 100), 
                                  "TEMPERATURE XX C / XX F", 1.5), layer=3)
        all_sprites.add(LcarsText(colours.BLUE, (190, 100), 
                                  "HUMIDITY XX%", 1.5), layer=3)
        all_sprites.add(LcarsText(colours.BLUE, (220, 100), 
                        "PRESSURE XXXX mB / XX.XX mm Hg", 1.5), layer=3)
        all_sprites.add(LcarsText(colours.BLUE, (250, 100), 
                        "STATION BATTERY X.XXX V", 1.5), layer=3)
        self.info_text = all_sprites.get_sprites_from_layer(3)

        # date display
        self.stardate = LcarsText(colours.BLUE, (12, 250), 
                                  "STAR DATE 2711.05 17:54:32", size=1.35)
        self.lastClockUpdate = 0
        all_sprites.add(self.stardate, layer=1)

        # buttons
        buttonOff = LcarsButton(colours.RED_BROWN, (250, 345), "SCREEN OFF",
                            self.logoutHandler)
        buttrowpos = (75, 75)
        butt1 = LcarsButton(colours.BEIGE, buttrowpos, "CURRENT",
                            self.sensorsHandler)
        butt2 = LcarsButton(colours.PURPLE, 
                            (buttrowpos[0], buttrowpos[1] + butt1.size[0]),
                            "GAUGES", self.gaugesHandler)
        butt3 = LcarsButton(colours.PURPLE, 
                            (buttrowpos[0], 
                             buttrowpos[1] + butt1.size[0] + butt2.size[0]),
                            "WEATHER", self.gaugesHandler)

        all_sprites.add(buttonOff, layer=4)
        all_sprites.add(butt1, layer=4)
        all_sprites.add(butt2, layer=4)
        all_sprites.add(butt3, layer=4)

        # gadgets        
        all_sprites.add(LcarsGifImage("assets/gadgets/fwscan.gif", 
                        (277, 556), 100), layer=1)
        
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
        Sound("assets/audio/panel/220.wav").play()

    def update(self, screenSurface, fpsClock):
        if pygame.time.get_ticks() - self.lastClockUpdate > 1000:
            sDateFmt = "%d%m.%y %H:%M:%S"
            sDate = "STAR DATE {}".format(datetime.now().strftime(sDateFmt))
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

    def hideInfoText(self):
        if self.info_text[0].visible:
            for sprite in self.info_text:
                sprite.visible = False

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
    
    def logoutHandler(self, item, event, clock):
        from screens.authorize import ScreenAuthorize
        self.loadScreen(ScreenAuthorize())
    
    
