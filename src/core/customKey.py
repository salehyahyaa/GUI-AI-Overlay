from pynput import keyboard
import threading


class CustomKeyListener: 
    def __init__(self, trigger_key):
        self.trigger_key = trigger_key
        self.listener = None 

    
    def when_triggerd(self):
        print("Hotkey thread:", threading.current_thread().name)
        self.trigger_key()

    
    def _normalize_key_event(self, func):                        #listens to all keys to detect custom comibnation 
        def wrapper(key): 
            return func(self.listener.canonical(key))            #normalizes (left Ctrl vs right Ctrl, etc.) to betreated the same
        return wrapper 


    def start(self):
        customKey = keyboard.HotKey(                             #some may think of this as the customized hot key
            keyboard.HotKey.parse('<cmd>+<shift>+<space>'),
            self.when_triggerd
        )

        
        self.listener = keyboard.Listener(
            on_press = self._normalize_key_event(customKey.press),              #what you press
            on_release = self._normalize_key_event(customKey.release)           #what you release 
        )
        
        self.listener.start()                                                   #starts listening