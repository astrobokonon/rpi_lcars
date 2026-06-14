import evdev
from evdev import ecodes
import pygame
import pygame


class TouchListener:
    def __init__(self, device_path='/dev/input/event0', width=480, height=320):
        self.device_path = device_path
        self.width = width
        self.height = height
        self.device = None
        
         try:
             self.device = evdev.InputDevice(self.device_path, non_blocking=True)
         except Exception as e:
             print(f"Could not open touch device {device_path}: {e}")

    def get_events(self):
        if not self.device:
            return []

        events = []
        try:
            # Non-blocking read of all available events
            for event in self.device.read():
                if event.type == ecodes.EV_ABS:
                    if event.code == ecodes.ABS_X:
                        self.last_x = event.value
                    elif event.code == ecodes.ABS_Y:
                        self.last_y = event.value
                
                elif event.type == ecodes.EV_KEY:
                    if event.code == ecodes.BTN_TOUCH:
                        # Scale coordinates from 0-4095 to width x height
                        # Assuming 270 rotation: 
                        # Raw X (0-4095) maps to screen Y (inverted)
                        # Raw Y (0-4095) maps to screen X
                        
                        # Basic linear scaling
                        scaled_x = int((self.last_y / 4095.0) * self.width)
                        scaled_y = int((1.0 - (self.last_x / 4095.0)) * self.height)
                        
                        if event.value == 1: # Press
                            events.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (scaled_x, scaled_y), 'button': 1}))
                        elif event.value == 0: # Release
                            events.append(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (scaled_x, scaled_y), 'button': 1}))
        except BlockingIOError:
            # No data available, return empty list
            pass
        except Exception as e:
            # Unexpected error
            print(f"Error reading touch events: {e}")
         
        return events
