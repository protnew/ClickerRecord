import time
import threading
import logging # Added
from pynput import mouse, keyboard

logger = logging.getLogger("ClickerRecord") # Get the same logger instance

class Recorder:
    def __init__(self):
        # self.actions = [] # This list is managed by MainWindow via callback
        self.start_time = None
        self.recording = False
        self.mouse_listener = None
        self.keyboard_listener = None
        self.callback = None
        logger.info("Recorder initialized.")
    
    def start_recording(self, callback):
        """Запускает запись действий пользователя"""
        # self.actions = [] # Managed by MainWindow
        self.callback = callback
        self.start_time = time.time()
        self.recording = True
        logger.info("Recording process started.")
        
        # Запуск обработчиков событий в отдельных потоках
        try:
            self.start_mouse_listener()
            self.start_keyboard_listener()
            logger.info("Mouse and keyboard listeners initiated.")
        except Exception as e:
            self.recording = False
            logger.exception("Error starting listeners in start_recording:")
            # Ensure listeners are stopped if partially started
            if self.mouse_listener and self.mouse_listener.is_alive():
                 self.mouse_listener.stop()
                 self.mouse_listener.join()
            if self.keyboard_listener and self.keyboard_listener.is_alive():
                 self.keyboard_listener.stop()
                 self.keyboard_listener.join()
            self.mouse_listener = None
            self.keyboard_listener = None
            raise # Re-raise the exception to be handled by the caller (e.g., MainWindow)

    def stop_recording(self):
        """Останавливает запись действий пользователя"""
        if not self.recording:
            logger.warning("Stop recording called when not recording.")
            return

        self.recording = False
        logger.info("Stopping recording process.")
        
        if self.mouse_listener:
            try:
                self.mouse_listener.stop()
                self.mouse_listener.join() # Wait for the thread to finish
                logger.info("Mouse listener stopped and joined.")
            except Exception as e:
                logger.error(f"Error stopping mouse listener: {e}", exc_info=True)
            finally:
                self.mouse_listener = None
            
        if self.keyboard_listener:
            try:
                self.keyboard_listener.stop()
                self.keyboard_listener.join() # Wait for the thread to finish
                logger.info("Keyboard listener stopped and joined.")
            except Exception as e:
                logger.error(f"Error stopping keyboard listener: {e}", exc_info=True)
            finally:
                self.keyboard_listener = None
        logger.info("Recording process fully stopped.")

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
            logger.debug(f"Mouse move recorded: x={x}, y={y}, t={timestamp:.3f}")
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
            logger.debug(f"Mouse click recorded: x={x}, y={y}, button={button}, pressed={pressed}, t={timestamp:.3f}")
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
            logger.debug(f"Mouse scroll recorded: dx={dx}, dy={dy}, t={timestamp:.3f}")
            if self.callback:
                self.callback(action)
        
        self.mouse_listener = mouse.Listener(
            on_move=on_move,
            on_click=on_click,
            on_scroll=on_scroll
        )
        self.mouse_listener.start()
        logger.info("Mouse listener thread started.")
    
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
            logger.debug(f"Key press recorded: key='{key_char}', t={timestamp:.3f}")
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
            logger.debug(f"Key release recorded: key='{key_char}', t={timestamp:.3f}")
            if self.callback:
                self.callback(action)
        
        self.keyboard_listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release
        )
        self.keyboard_listener.start() 
        logger.info("Keyboard listener thread started.")