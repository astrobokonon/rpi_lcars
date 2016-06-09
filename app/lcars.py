from screens.authorize import ScreenAuthorize
from screens.main import ScreenMain
from ui.ui import UserInterface

# global config
UI_PLACEMENT_MODE = True
RESOLUTION = (480, 320)
FPS = 60
DEV_MODE = True

if __name__ == "__main__":
#    firstScreen = ScreenAuthorize()
    firstScreen = ScreenMain()
    ui = UserInterface(firstScreen, RESOLUTION, UI_PLACEMENT_MODE, FPS, DEV_MODE)

    while (True):
        ui.tick()
