import pygame
import time
from pygame.locals import *
from .touch_input import TouchListener


from ui.utils import sound


class UserInterface:
    def __init__(self, screen, resolution=(800,480),
                 ui_placement_mode=False, fps=60, dev_mode=False, audio=True,
                 audio_params=(22050, -8, 1, 1024)):
        # init system
        pygame.display.init()
        pygame.font.init()
        sound.init(audio_params)

        self.screenSurface = pygame.display.set_mode(resolution) #, pygame.FULLSCREEN)
        self.fpsClock = pygame.time.Clock()
        self.fps = fps
        pygame.display.set_caption("LCARS")
        if not dev_mode: 
            # see https://github.com/tobykurien/rpi_lcars/issues/9
            #pygame.mouse.set_visible(False)
            pygame.mouse.set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0))
        
        # set up screen elements
        self.all_sprites = pygame.sprite.LayeredDirty()
        self.all_sprites.UI_PLACEMENT_MODE = ui_placement_mode
    
        self.screen = screen
        self.screen.setup(self.all_sprites)
        self.touch_listener = TouchListener(width=resolution[0], height=resolution[1])
        self.running = True

    def update(self):
        self.screen.pre_update(self.screenSurface, self.fpsClock)
        self.all_sprites.update()
        self.all_sprites.draw(self.screenSurface)
        self.screen.update(self.screenSurface, self.fpsClock)
        pygame.display.update()
    
    def handleEvents(self):
        # Inject touch events into the Pygame event queue
        touch_events = self.touch_listener.get_events()
        for event in touch_events:
            pygame.event.post(event)

        # Debug: print how many times get_events was called this frame
        if self.touch_listener.call_count:
            print(f"Touch listener calls this frame: {self.touch_listener.call_count}")
            self.touch_listener.call_count = 0

        for event in pygame.event.get():
            if (event.type == pygame.QUIT) or \
                (event.type == KEYUP and event.key == K_ESCAPE):
                pygame.quit()
                self.running = False
                return

            for sprite in self.all_sprites.sprites():
                if hasattr(event, "pos"):
                    focussed = sprite.rect.collidepoint(event.pos)
                    if (focussed or sprite.focussed) and sprite.handleEvent(event, self.fpsClock):
                        break

            self.screen.handleEvents(event, self.fpsClock)

            newScreen = self.screen.getNextScreen()
            if (newScreen):
                self.all_sprites.empty()
                newScreen.setup(self.all_sprites)
                self.screen = newScreen
                break
    
    def isRunning(self):
        pygame.display.get_init()
    
    def tick(self):
        frame_start = time.time()
        self.update()
        self.handleEvents()
        self.fpsClock.tick(self.fps)
        frame_time = time.time() - frame_start
        # Debug: print frame timing occasionally
        if not hasattr(self, '_frame_count'):
            self._frame_count = 0
        self._frame_count += 1
        if self._frame_count % 60 == 0:
            print(f"Frame time: {frame_time*1000:.2f} ms (fps ~ {1.0/frame_time if frame_time>0 else 0:.1f})")
