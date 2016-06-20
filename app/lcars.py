import subprocess as sub

from screens.main import ScreenMain
from ui.ui import UserInterface

# global config
UI_PLACEMENT_MODE = True
RESOLUTION = (480, 320)
FPS = 25
DEV_MODE = True

if __name__ == "__main__":
    # Set the screen brightness to midrange to start with
    try:
        sub.call(['gpio', '-g', 'pwm', '18', '800'])
    except OSError:
        pass

    firstScreen = ScreenMain()
    ui = UserInterface(firstScreen,
                       RESOLUTION,
                       UI_PLACEMENT_MODE,
                       FPS,
                       DEV_MODE)

    while (True):
        ui.tick()
