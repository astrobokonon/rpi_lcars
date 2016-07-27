import subprocess as sub

from ui import screenPWM
from ui.ui import UserInterface
from screens.main import ScreenMain

# global config
UI_PLACEMENT_MODE = True
RESOLUTION = (480, 320)
FPS = 25
DEV_MODE = True


if __name__ == "__main__":
    # Set the screen brightness to midrange to start with
    try:
        screenPWM.screenPWM(1.0, pin=18)
        screenPWM.screenPWM(0.5, pin=18)
#        sub.call(['gpio', '-g', 'pwm', '18', '800'])
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
