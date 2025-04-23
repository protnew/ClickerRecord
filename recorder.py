import time
import threading
from pynput import mouse, keyboard

class Recorder:
    def __init__(self):
        self.actions = []
        self.start_time = None
        self.recording = False
        self.mouse_listener = None
        self.keyboard_listener = None
        self.callback = None
    
    def start_recording(self, callback):
        """Запускает запись действий пользователя"""
        self.actions = []
        self.callback = callback
        self.start_time = time.time()
        self.recording = True
        
        # Запуск обработчиков событий в отдельных потоках
        self.start_mouse_listener()
        self.start_keyboard_listener()
    
    def stop_recording(self):
        """Останавливает запись действий пользователя"""
        self.recording = False
        
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
            
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
    
    def start_mouse_listener(self):
        """Запускает прослушивание событий мыши"""
        def on_move(x, y):
            if not self.recording:
                return
            
            timestamp = time.time() - self.start_time
            action = {
                'type': 'mouse_move',
                'timestamp': timestamp,
                'x': x,
                'y': y
            }
            
            if self.callback:
                self.callback(action)
        
        def on_click(x, y, button, pressed):
            if not self.recording:
                return
            
            timestamp = time.time() - self.start_time
            action = {
                'type': 'mouse_click',
                'timestamp': timestamp,
                'x': x,
                'y': y,
                'button': str(button),
                'pressed': pressed
            }
            
            if self.callback:
                self.callback(action)
        
        def on_scroll(x, y, dx, dy):
            if not self.recording:
                return
            
            timestamp = time.time() - self.start_time
            action = {
                'type': 'mouse_scroll',
                'timestamp': timestamp,
                'x': x,
                'y': y,
                'dx': dx,
                'dy': dy
            }
            
            if self.callback:
                self.callback(action)
        
        self.mouse_listener = mouse.Listener(
            on_move=on_move,
            on_click=on_click,
            on_scroll=on_scroll
        )
        self.mouse_listener.start()
    
    def start_keyboard_listener(self):
        """Запускает прослушивание событий клавиатуры"""
        def on_press(key):
            if not self.recording:
                return
            
            timestamp = time.time() - self.start_time
            
            try:
                # Для обычных символов
                key_char = key.char
            except AttributeError:
                # Для специальных клавиш (Enter, Shift и т.д.)
                key_char = str(key)
            
            action = {
                'type': 'key_press',
                'timestamp': timestamp,
                'key': key_char
            }
            
            if self.callback:
                self.callback(action)
        
        def on_release(key):
            if not self.recording:
                return
            
            timestamp = time.time() - self.start_time
            
            try:
                key_char = key.char
            except AttributeError:
                key_char = str(key)
            
            action = {
                'type': 'key_release',
                'timestamp': timestamp,
                'key': key_char
            }
            
            if self.callback:
                self.callback(action)
        
        self.keyboard_listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release
        )
        self.keyboard_listener.start() 