import pygame
import subprocess as sub

from ui import colours, screenPWM
from ui.widgets.background import LcarsBackgroundImage
from ui.widgets.gifimage import LcarsGifImage
from ui.widgets.lcars_widgets import LcarsText
from ui.widgets.screen import LcarsScreen


class ScreenBlanker(LcarsScreen):
    def setup(self, all_sprites):
        all_sprites.add(LcarsBackgroundImage("assets/blank.png"),
                        layer=0)
        try:
#            sub.call(['gpio', '-g', 'pwm', '18', '0'])
            screenPWM.screenPWM(0., pin=18)
        except OSError:
            pass
        self.attempts = 0
        self.granted = False

    def handleEvents(self, event, fpsClock):
        LcarsScreen.handleEvents(self, event, fpsClock)
        if event.type == pygame.MOUSEBUTTONDOWN:
                try:
#		    sub.call(['gpio', '-g', 'pwm', '18', '1023'])
		    screenPWM.screenPWM(0.5, pin=18)
                except OSError:
                    pass
                from screens.main import ScreenMain
                self.loadScreen(ScreenMain())

        return False
