import time
import threading
import ctypes
import win32api
import win32con
import logging # Added
from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController
# Импортируем необходимые компоненты Qt для сигналов
from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger("ClickerRecord") # Get the same logger instance

# Класс Player теперь наследует QObject для поддержки сигналов
class Player(QObject):
    # Определяем сигналы
    playbackFinished = pyqtSignal()
    playbackError = pyqtSignal(str)
    # Сигнал для обновления прогресса (опционально, но полезно)
    playbackProgress = pyqtSignal(int, int) # current_time, total_time

    def __init__(self):
        # Важно вызвать конструктор родительского класса QObject
        super().__init__() 
        
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        self.play_thread = None
        self.is_playing = False # Should be the primary flag controlling playback loops
        self._stop_requested = False # Internal flag to signal thread to stop
        self.total_time = 0
        self.current_time = 0
        logger.info("Player initialized.")
    
    def play(self, actions, repeat_count=1, speed_factor=1.0): # Убираем on_complete и on_error
        """
        Воспроизводит записанные действия.
        Использует сигналы playbackFinished и playbackError для обратной связи.
        
        :param actions: Список записанных действий
        :param repeat_count: Количество повторений
        :param speed_factor: Коэффициент скорости воспроизведения
        """
        if self.is_playing: # Check is_playing first
            logger.warning("Play called when playback is already in progress.")
            return # Or emit an error if preferred
            
        logger.info(f"Starting playback thread: repeats={repeat_count}, speed={speed_factor}")
        self._stop_requested = False # Reset stop flag
        self.is_playing = True # Set is_playing before starting the thread

        # Запуск воспроизведения в отдельном потоке
        self.play_thread = threading.Thread(
            target=self._play_thread,
            args=(actions, repeat_count, speed_factor)
        )
        self.play_thread.daemon = True # Поток завершится, если основной поток завершится
        self.play_thread.start()
    
    def _play_thread(self, actions, repeat_count, speed_factor):
        """Внутренний метод для воспроизведения в отдельном потоке"""
        # self.is_playing = True # Moved to play() to set before thread starts
        self.current_time = 0
        self.total_time = self._calculate_total_time(actions, repeat_count, speed_factor)
        error_message = None
        
        try:
            logger.info("Playback thread: Starting repeat loop.")
            for repeat_idx in range(repeat_count):
                logger.info(f"Playback thread: Repeat {repeat_idx + 1}/{repeat_count}")
                # Проверяем, не была ли запрошена остановка воспроизведения
                if self._stop_requested: # Check internal stop flag
                    logger.info("Playback thread: Stop requested at the beginning of a repeat.")
                    break
                    
                # Воспроизводим действия для текущего повторения
                self._replay_actions(actions, speed_factor)
                
                # Небольшая пауза между повторениями (только если не последний и не остановлено)
                if repeat_idx < repeat_count - 1 and not self._stop_requested:
                    pause_duration = 0.5 / speed_factor
                    logger.debug(f"Playback thread: Pausing between repeats for {pause_duration:.2f} sec.")
                    remaining_pause = pause_duration
                    while remaining_pause > 0 and not self._stop_requested:
                         sleep_time = min(0.1, remaining_pause)
                         time.sleep(sleep_time)
                         remaining_pause -= sleep_time
        except Exception as e:
            error_message = f"Ошибка при воспроизведении: {str(e)}"
            logger.exception(f"Playback thread: Exception during playback loop: {error_message}")
        finally:
            logger.info("Playback thread: Finalizing.")
            # was_playing = self.is_playing # is_playing should be set to False by stop() or here
            self.is_playing = False # Ensure is_playing is false on exit
            self.current_time = 0 # Сбрасываем время
            self.total_time = 0
            
            if error_message:
                logger.error(f"Playback thread: Emitting playbackError signal: {error_message}")
                try:
                     self.playbackError.emit(error_message)
                except Exception as emit_e:
                     logger.exception(f"Playback thread: Error emitting playbackError: {emit_e}")
            elif not self._stop_requested: # Only emit finished if not stopped prematurely
                logger.info("Playback thread: Emitting playbackFinished signal.")
                try:
                     self.playbackFinished.emit()
                except Exception as emit_e:
                     logger.exception(f"Playback thread: Error emitting playbackFinished: {emit_e}")
            else:
                 logger.info("Playback thread: Playback was stopped by request, not emitting playbackFinished.")

    def _calculate_total_time(self, actions, repeat_count, speed_factor):
         """Примерный расчет общего времени воспроизведения (без пауз между повторениями)"""
         if not actions or speed_factor <= 0:
              return 0
         last_action_time = max(a['timestamp'] for a in actions) if actions else 0
         single_run_time = last_action_time / speed_factor
         # Упрощенный расчет, можно добавить паузы между повторениями, если нужно точнее
         total_time_approx = single_run_time * repeat_count
         logger.debug(f"Calculated total approximate playback time: {total_time_approx:.2f}s")
         return total_time_approx

    def _replay_actions(self, actions, speed_factor):
        """Воспроизведение списка действий с заданной скоростью"""
        if not actions:
            return
            
        # Сортировка действий по времени (важно)
        try:
             sorted_actions = sorted(actions, key=lambda x: x.get('timestamp', 0))
        except Exception as sort_e:
             logger.error(f"Error sorting actions: {sort_e}", exc_info=True)
             raise ValueError(f"Ошибка в данных действий: {sort_e}")
             
        start_time = time.perf_counter() # Используем более точный таймер
        base_timestamp = sorted_actions[0]['timestamp'] # Время первого действия
        logger.debug(f"Replay actions started. Base timestamp: {base_timestamp:.3f}s")
        
        for idx, action in enumerate(sorted_actions):
            # Проверяем, не была ли запрошена остановка воспроизведения
            if self._stop_requested:
                logger.info("Playback thread: Stop requested during _replay_actions loop.")
                break
                
            # Расчет целевого времени выполнения действия от начала воспроизведения
            target_elapsed_time = (action['timestamp'] - base_timestamp) / speed_factor
            current_elapsed_time = time.perf_counter() - start_time
            
            # Расчет необходимой задержки
            delay = target_elapsed_time - current_elapsed_time
            
            # Пауза для соблюдения временных интервалов
            if delay > 0:
                logger.debug(f"Action {idx}: Delaying for {delay:.4f}s")
                # Разбиваем задержку на маленькие части, чтобы быстрее реагировать на остановку
                remaining_delay = delay
                while remaining_delay > 0.001 and not self._stop_requested: # Добавим небольшой порог
                    sleep_time = min(0.05, remaining_delay) # Уменьшим шаг для большей отзывчивости
                    time.sleep(sleep_time)
                    remaining_delay -= sleep_time
            
            # Обновляем текущее время для прогресс-бара (даже если была задержка 0)
            self.current_time = current_elapsed_time + max(0, delay) # This is elapsed time for this loop
            try:
                 # Send progress relative to the total estimated time for all repeats
                 # This might need adjustment if total_time is for a single run
                 # For now, let's assume total_time is for all runs (as calculated)
                 # and current_time is for the current single run.
                 # A better progress would be (current_repeat * single_run_time + self.current_time)
                 # For simplicity, we emit progress for the current run.
                 self.playbackProgress.emit(int(self.current_time * 1000), int(self._calculate_total_time(actions, 1, speed_factor) * 1000) ) # Send progress for single run
            except Exception as emit_e:
                 logger.exception(f"Playback thread: Error emitting playbackProgress: {emit_e}")

            # Если остановка была запрошена во время задержки, прерываем выполнение
            if self._stop_requested:
                logger.info("Playback thread: Stop requested after delay in _replay_actions.")
                break
            
            # Выполнение действия в зависимости от типа
            try:
                 logger.debug(f"Action {idx}: Performing action: {action}")
                 self._perform_action(action)
            except Exception as perform_e:
                 logger.exception(f"Playback thread: Error performing action {action}: {perform_e}")
                 # Решаем, стоит ли прерывать воспроизведение при ошибке одного действия
                 # пока продолжаем
            
            # prev_time больше не нужен

    def _perform_action(self, action):
        """Выполнение конкретного действия"""
        action_type = action['type']
        logger.debug(f"Performing action type: {action_type}")
        
        if action_type == 'mouse_move':
            self.mouse.position = (action['x'], action['y'])
        
        elif action_type == 'mouse_click':
            x, y = action['x'], action['y']
            button_str = action['button']
            pressed = action['pressed']
            
            # Определение кнопки мыши
            button = self._parse_mouse_button(button_str)
            
            # Установка курсора в нужное положение
            self.mouse.position = (x, y)
            
            if pressed:
                self.mouse.press(button)
            else:
                self.mouse.release(button)
        
        elif action_type == 'mouse_scroll':
            x, y = action['x'], action['y']
            dx, dy = action['dx'], action['dy']
            
            # Установка курсора в нужное положение
            self.mouse.position = (x, y)
            self.mouse.scroll(dx, dy)
        
        elif action_type in ('key_press', 'key_release'):
            key_str = action['key']
            key = self._parse_key(key_str)
            
            if key:
                if action_type == 'key_press':
                    self.keyboard.press(key)
                else:
                    self.keyboard.release(key)
            else:
                logger.warning(f"Could not parse key: '{key_str}' for action: {action}")
    
    def _parse_mouse_button(self, button_str):
        """Преобразует строковое представление кнопки мыши в объект Button"""
        button_map = {
            'Button.left': Button.left,
            'Button.right': Button.right,
            'Button.middle': Button.middle
        }
        parsed_button = button_map.get(button_str)
        if not parsed_button:
            logger.warning(f"Unknown mouse button string: '{button_str}'. Defaulting to Left.")
            return Button.left
        return parsed_button
    
    def _parse_key(self, key_str):
        """Преобразует строковое представление клавиши в объект Key или символ"""
        special_keys = {
            'Key.alt': Key.alt, 'Key.alt_l': Key.alt_l, 'Key.alt_r': Key.alt_r, 'Key.alt_gr': Key.alt_gr,
            'Key.backspace': Key.backspace, 'Key.caps_lock': Key.caps_lock,
            'Key.cmd': Key.cmd, 'Key.cmd_l': Key.cmd_l, 'Key.cmd_r': Key.cmd_r,
            'Key.ctrl': Key.ctrl, 'Key.ctrl_l': Key.ctrl_l, 'Key.ctrl_r': Key.ctrl_r,
            'Key.delete': Key.delete, 'Key.down': Key.down, 'Key.end': Key.end, 'Key.enter': Key.enter,
            'Key.esc': Key.esc,
            'Key.f1': Key.f1, 'Key.f2': Key.f2, 'Key.f3': Key.f3, 'Key.f4': Key.f4,
            'Key.f5': Key.f5, 'Key.f6': Key.f6, 'Key.f7': Key.f7, 'Key.f8': Key.f8,
            'Key.f9': Key.f9, 'Key.f10': Key.f10, 'Key.f11': Key.f11, 'Key.f12': Key.f12,
            'Key.home': Key.home, 'Key.insert': Key.insert, 'Key.left': Key.left, 'Key.menu': Key.menu,
            'Key.num_lock': Key.num_lock, 'Key.page_down': Key.page_down, 'Key.page_up': Key.page_up,
            'Key.pause': Key.pause, 'Key.print_screen': Key.print_screen, 'Key.right': Key.right,
            'Key.scroll_lock': Key.scroll_lock,
            'Key.shift': Key.shift, 'Key.shift_l': Key.shift_l, 'Key.shift_r': Key.shift_r,
            'Key.space': Key.space, 'Key.tab': Key.tab, 'Key.up': Key.up
        }
        
        if key_str in special_keys:
            return special_keys[key_str]
        elif isinstance(key_str, str) and len(key_str) == 1: # Check if it's a single character string
            return key_str
        
        logger.warning(f"Could not parse key string: '{key_str}' to a valid key object or character.")
        return None # Return None if key_str is not recognized
    
    def stop(self):
        """Останавливает воспроизведение"""
        logger.info("Stop requested for playback.")
        self._stop_requested = True # Set internal flag
        if self.play_thread and self.play_thread.is_alive():
            logger.debug("Player stop: Waiting for playback thread to join.")
            self.play_thread.join(timeout=1.0) # Give some time for the thread to stop gracefully
            if self.play_thread.is_alive():
                logger.warning("Player stop: Playback thread did not join in time.")
        self.is_playing = False # Ensure is_playing is set to False
        logger.info("Player stop: Playback should now be stopped.")
        
    def get_current_playback_time(self):
        """Возвращает текущее время воспроизведения в секундах"""
        return self.current_time
        
    def get_total_playback_time(self):
        """Возвращает общее расчетное время воспроизведения в секундах"""
        return self.total_time 