import time
import threading
import ctypes
import win32api
import win32con
from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController
# Импортируем необходимые компоненты Qt для сигналов
from PyQt5.QtCore import QObject, pyqtSignal

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
        self.is_playing = False
        self.total_time = 0
        self.current_time = 0
    
    def play(self, actions, repeat_count=1, speed_factor=1.0): # Убираем on_complete и on_error
        """
        Воспроизводит записанные действия.
        Использует сигналы playbackFinished и playbackError для обратной связи.
        
        :param actions: Список записанных действий
        :param repeat_count: Количество повторений
        :param speed_factor: Коэффициент скорости воспроизведения
        """
        if self.is_playing:
            print("[Player] Воспроизведение уже идет.")
            return
            
        print("[Player] Запуск потока воспроизведения...")
        # Запуск воспроизведения в отдельном потоке
        self.play_thread = threading.Thread(
            target=self._play_thread,
            args=(actions, repeat_count, speed_factor)
        )
        self.play_thread.daemon = True # Поток завершится, если основной поток завершится
        self.play_thread.start()
    
    def _play_thread(self, actions, repeat_count, speed_factor):
        """Внутренний метод для воспроизведения в отдельном потоке"""
        self.is_playing = True
        self.current_time = 0
        self.total_time = self._calculate_total_time(actions, repeat_count, speed_factor)
        error_message = None
        
        try:
            print("[Player] Начало цикла повторений.")
            for repeat_idx in range(repeat_count):
                print(f"[Player] Повторение {repeat_idx + 1}/{repeat_count}")
                # Проверяем, не была ли запрошена остановка воспроизведения
                if not self.is_playing:
                    print("[Player] Остановка обнаружена в начале повторения.")
                    break
                    
                # Воспроизводим действия для текущего повторения
                self._replay_actions(actions, speed_factor)
                
                # Небольшая пауза между повторениями (только если не последний и не остановлено)
                if repeat_idx < repeat_count - 1 and self.is_playing:
                    pause_duration = 0.5 / speed_factor
                    print(f"[Player] Пауза между повторениями: {pause_duration:.2f} сек.")
                    remaining_pause = pause_duration
                    while remaining_pause > 0 and self.is_playing:
                         sleep_time = min(0.1, remaining_pause)
                         time.sleep(sleep_time)
                         remaining_pause -= sleep_time
        except Exception as e:
            error_message = f"Ошибка при воспроизведении: {str(e)}"
            print(f"[Player] {error_message}")
        finally:
            print("[Player] Завершение потока воспроизведения.")
            was_playing = self.is_playing # Запоминаем, был ли флаг установлен до сброса
            self.is_playing = False
            self.current_time = 0 # Сбрасываем время
            self.total_time = 0
            
            # Испускаем сигналы из основного потока GUI (более безопасный способ будет в main.py)
            # Здесь мы просто вызываем их, т.к. прямое испускание из другого потока может быть небезопасно в некоторых случаях
            # Фактическая обработка должна быть в главном потоке через Qt.QueuedConnection
            if error_message:
                print(f"[Player] Испускаем сигнал playbackError: {error_message}")
                try:
                     self.playbackError.emit(error_message)
                except Exception as emit_e:
                     print(f"[Player] Ошибка при emit playbackError: {emit_e}")
            elif was_playing: # Если не было ошибки и воспроизведение не было прервано ДО вызова play
                print("[Player] Испускаем сигнал playbackFinished.")
                try:
                     self.playbackFinished.emit()
                except Exception as emit_e:
                     print(f"[Player] Ошибка при emit playbackFinished: {emit_e}")
            else:
                 print("[Player] Воспроизведение было остановлено до завершения, сигнал Finished не испускается.")

    def _calculate_total_time(self, actions, repeat_count, speed_factor):
         """Примерный расчет общего времени воспроизведения (без пауз между повторениями)"""
         if not actions or speed_factor <= 0:
              return 0
         last_action_time = max(a['timestamp'] for a in actions) if actions else 0
         single_run_time = last_action_time / speed_factor
         # Упрощенный расчет, можно добавить паузы между повторениями, если нужно точнее
         total_time = single_run_time * repeat_count
         return total_time

    def _replay_actions(self, actions, speed_factor):
        """Воспроизведение списка действий с заданной скоростью"""
        if not actions:
            return
            
        # Сортировка действий по времени (важно)
        try:
             sorted_actions = sorted(actions, key=lambda x: x.get('timestamp', 0))
        except Exception as sort_e:
             print(f"[Player] Ошибка сортировки действий: {sort_e}")
             raise ValueError(f"Ошибка в данных действий: {sort_e}")
             
        start_time = time.perf_counter() # Используем более точный таймер
        base_timestamp = sorted_actions[0]['timestamp'] # Время первого действия
        
        for action in sorted_actions:
            # Проверяем, не была ли запрошена остановка воспроизведения
            if not self.is_playing:
                print("[Player] Остановка обнаружена во время replay_actions.")
                break
                
            # Расчет целевого времени выполнения действия от начала воспроизведения
            target_elapsed_time = (action['timestamp'] - base_timestamp) / speed_factor
            current_elapsed_time = time.perf_counter() - start_time
            
            # Расчет необходимой задержки
            delay = target_elapsed_time - current_elapsed_time
            
            # Пауза для соблюдения временных интервалов
            if delay > 0:
                # Разбиваем задержку на маленькие части, чтобы быстрее реагировать на остановку
                remaining_delay = delay
                while remaining_delay > 0.001 and self.is_playing: # Добавим небольшой порог
                    sleep_time = min(0.05, remaining_delay) # Уменьшим шаг для большей отзывчивости
                    time.sleep(sleep_time)
                    remaining_delay -= sleep_time
            
            # Обновляем текущее время для прогресс-бара (даже если была задержка 0)
            self.current_time = current_elapsed_time + max(0, delay)
            try:
                 self.playbackProgress.emit(int(self.current_time * 1000), int(self.total_time * 1000)) # Отправляем в мс
            except Exception as emit_e:
                 print(f"[Player] Ошибка emit playbackProgress: {emit_e}")

            # Если остановка была запрошена во время задержки, прерываем выполнение
            if not self.is_playing:
                print("[Player] Остановка обнаружена после задержки.")
                break
            
            # Выполнение действия в зависимости от типа
            try:
                 self._perform_action(action)
            except Exception as perform_e:
                 print(f"[Player] Ошибка выполнения действия {action}: {perform_e}")
                 # Решаем, стоит ли прерывать воспроизведение при ошибке одного действия
                 # пока продолжаем
            
            # prev_time больше не нужен

    def _perform_action(self, action):
        """Выполнение конкретного действия"""
        action_type = action['type']
        
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
    
    def _parse_mouse_button(self, button_str):
        """Преобразует строковое представление кнопки мыши в объект Button"""
        button_map = {
            'Button.left': Button.left,
            'Button.right': Button.right,
            'Button.middle': Button.middle
        }
        
        return button_map.get(button_str, Button.left)
    
    def _parse_key(self, key_str):
        """Преобразует строковое представление клавиши в объект Key или символ"""
        special_keys = {
            'Key.alt': Key.alt,
            'Key.alt_l': Key.alt_l,
            'Key.alt_r': Key.alt_r,
            'Key.alt_gr': Key.alt_gr,
            'Key.backspace': Key.backspace,
            'Key.caps_lock': Key.caps_lock,
            'Key.cmd': Key.cmd,
            'Key.cmd_l': Key.cmd_l,
            'Key.cmd_r': Key.cmd_r,
            'Key.ctrl': Key.ctrl,
            'Key.ctrl_l': Key.ctrl_l,
            'Key.ctrl_r': Key.ctrl_r,
            'Key.delete': Key.delete,
            'Key.down': Key.down,
            'Key.end': Key.end,
            'Key.enter': Key.enter,
            'Key.esc': Key.esc,
            'Key.f1': Key.f1,
            'Key.f2': Key.f2,
            'Key.f3': Key.f3,
            'Key.f4': Key.f4,
            'Key.f5': Key.f5,
            'Key.f6': Key.f6,
            'Key.f7': Key.f7,
            'Key.f8': Key.f8,
            'Key.f9': Key.f9,
            'Key.f10': Key.f10,
            'Key.f11': Key.f11,
            'Key.f12': Key.f12,
            'Key.home': Key.home,
            'Key.insert': Key.insert,
            'Key.left': Key.left,
            'Key.menu': Key.menu,
            'Key.num_lock': Key.num_lock,
            'Key.page_down': Key.page_down,
            'Key.page_up': Key.page_up,
            'Key.pause': Key.pause,
            'Key.print_screen': Key.print_screen,
            'Key.right': Key.right,
            'Key.scroll_lock': Key.scroll_lock,
            'Key.shift': Key.shift,
            'Key.shift_l': Key.shift_l,
            'Key.shift_r': Key.shift_r,
            'Key.space': Key.space,
            'Key.tab': Key.tab,
            'Key.up': Key.up
        }
        
        if key_str in special_keys:
            return special_keys[key_str]
        elif len(key_str) == 1:
            return key_str
        
        return None
    
    def stop(self):
        """Останавливает воспроизведение"""
        print("[Player] Установка флага is_playing = False")
        self.is_playing = False
        # Это флаг проверяется в циклах, и они будут прерваны при следующей итерации
        
    def get_current_playback_time(self):
        """Возвращает текущее время воспроизведения в секундах"""
        return self.current_time
        
    def get_total_playback_time(self):
        """Возвращает общее расчетное время воспроизведения в секундах"""
        return self.total_time 