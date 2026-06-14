import evdev
from evdev import ecodes
import pygame
import select

DEBUG = False  # Set to True to print touch debug info


class TouchListener:
    def __init__(self, device_path='/dev/input/event0', width=480, height=320):
        self.device_path = device_path
        self.width = width
        self.height = height
        self.device = None
        self.call_count = 0
        
        try:
            self.device = evdev.InputDevice(self.device_path)
        except Exception as e:
            print(f"Could not open touch device {device_path}: {e}")

    def get_events(self):
        events = []
        if not self.device:
            return events
        self.call_count += 1
        try:
            # Use select with a small timeout to reduce spinning
            ready, _, _ = select.select([self.device.fileno()], [], [], 0.001)
            if ready:
                for event in self.device.read():
                    if event.type == ecodes.EV_ABS:
                        if event.code == ecodes.ABS_X:
                            self.last_x = event.value
                        elif event.code == ecodes.ABS_Y:
                            self.last_y = event.value
                    elif event.type == ecodes.EV_KEY:
                        if event.code == ecodes.BTN_TOUCH:
                            # Simple linear mapping: raw 0-4095 -> screen 0-width/height
                            scaled_x = int((self.last_x / 4095.0) * self.width)
                            scaled_y = int((self.last_y / 4095.0) * self.height)
                            if DEBUG:
                                print(f"Touch: raw ({self.last_x}, {self.last_y}) -> screen ({scaled_x}, {scaled_y})")
                            if event.value == 1:  # Press
                                events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (scaled_x, scaled_y), 'button': 1}))
                            elif event.value == 0:  # Release
                                events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (scaled_x, scaled_y), 'button': 1}))
        except Exception as e:
            print(f"Error reading touch events: {e}")
        return events
