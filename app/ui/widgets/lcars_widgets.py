import pygame
from pygame.font import Font
from pygame.locals import *
from pygame.mixer import Sound
from os.path import dirname, join

from ui.widgets.sprite import LcarsWidget
from ui import colours


class LcarsElbow(LcarsWidget):
    """The LCARS corner elbow - not currently used"""

    STYLE_BOTTOM_LEFT = 0
    STYLE_TOP_LEFT = 1
    STYLE_BOTTOM_RIGHT = 2
    STYLE_TOP_RIGHT = 3

    def __init__(self, colour, style, pos):
        script_dir = dirname(__file__)
        ipath = join(script_dir, '../../assets/elbow.png')
        image = pygame.image.load(ipath).convert()
        if (style == LcarsElbow.STYLE_BOTTOM_LEFT):
            image = pygame.transform.flip(image, False, True)
        elif (style == LcarsElbow.STYLE_BOTTOM_RIGHT):
            image = pygame.transform.rotate(image, 180)
        elif (style == LcarsElbow.STYLE_TOP_RIGHT):
            image = pygame.transform.flip(image, True, False)

        self.image = image
        size = (image.get_rect().width, image.get_rect().height)
        LcarsWidget.__init__(self, colour, pos, size)
        self.applyColour(colour)


class LcarsTab(LcarsWidget):
    STYLE_LEFT = 1
    STYLE_RIGHT = 2

    def __init__(self, colour, style, pos):
        script_dir = dirname(__file__)
        ipath = join(script_dir, '../../assets/tab.png')
        image = pygame.image.load(ipath).convert()
        if (style == LcarsTab.STYLE_RIGHT):
            image = pygame.transform.flip(image, False, True)

        size = (image.get_rect().width, image.get_rect().height)
        LcarsWidget.__init__(self, colour, pos, size)
        self.image = image
        self.applyColour(colour)


class LcarsButton(LcarsWidget):
    def __init__(self, colour, pos, text, handler=None):
        self.handler = handler
        script_dir = dirname(__file__)
        ipath = join(script_dir, '../../assets/betterbutton.png')
        image = pygame.image.load(ipath).convert()
        size = (image.get_rect().width, image.get_rect().height)
        ipath = join(script_dir, '../../assets/swiss911.ttf')
        font = Font(ipath, 19)
        textImage = font.render(text, False, colours.BLACK)
        image.blit(textImage,
                   (image.get_rect().width - textImage.get_rect().width - 10,
                    image.get_rect().height - textImage.get_rect().height - 5))

        self.image = image
        self.colour = colour
        self.size = size
        LcarsWidget.__init__(self, colour, pos, size)
        self.applyColour(colour)
        self.highlighted = False
#        self.beep = Sound("assets/audio/panel/202.wav")
        self.inactiveColor = colour

    def changeColor(self, color):
        self.applyColour(color)

    def handleEvent(self, event, clock):
        handled = False

        if (event.type == MOUSEBUTTONDOWN and
           self.rect.collidepoint(event.pos)):
            self.applyColour(colours.WHITE)
            self.highlighted = True
            # NOTE: Should put the sounds behind a global/config param
#            self.beep.play()
            handled = True

        if (event.type == MOUSEBUTTONUP and self.highlighted):
            self.applyColour(self.colour)
            if self.handler:
                self.handler(self, event, clock)
                handled = True

        LcarsWidget.handleEvent(self, event, clock)
        return handled


class LcarsText(LcarsWidget):
    def __init__(self, colour, pos, message, size=1.0,
                 background=None, resolution=(480, 320)):
        self.colour = colour
        self.message = message
        self.background = background
        script_dir = dirname(__file__)
        ipath = join(script_dir, '../../assets/swiss911.ttf')
        self.font = Font(ipath, int(19.0 * size))

        self.renderText(message)
        # center the text if needed
        if (pos[1] < 0):
            # Screen specific magic number below! 240 = half width
            pos = (pos[0], resolution[0]/2 - self.image.get_rect().width/2)

        LcarsWidget.__init__(self, colour, pos, None)

    def renderText(self, message):
        if (self.background is None):
            self.image = self.font.render(message, True, self.colour)
        else:
            self.image = self.font.render(message, True,
                                          self.colour, self.background)

    def setText(self, newText):
        self.message = newText
        self.renderText(newText)

    def changeColour(self, colour):
        self.colour = colour
        self.renderText(self.message)


class LcarsBlockLarge(LcarsWidget):
    def __init__(self, colour, pos):
        size = (100, 70)
        LcarsWidget.__init__(self, colour, pos, size)


class LcarsBlockSmall(LcarsWidget):
    def __init__(self, colour, pos):
        size = (100, 20)
        LcarsWidget.__init__(self, colour, pos, size)


class LcarsTabBlock(LcarsWidget):
    def __init__(self, colour, pos):
        size = (160, 45)
        LcarsWidget.__init__(self, colour, pos, size)
