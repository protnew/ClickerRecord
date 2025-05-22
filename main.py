import sys
import json
import time
import os
import logging # <-- Added
from datetime import datetime, timedelta
from PyQt5.QtCore import Qt, QTimer, QTime, QObject, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon, QFont, QKeySequence
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, QSpinBox, 
                            QRadioButton, QSlider, QFileDialog, QStatusBar, QWidget, 
                            QVBoxLayout, QHBoxLayout, QTimeEdit, QButtonGroup, QLineEdit,
                            QShortcut, QMessageBox, QGridLayout, QFrame, QDialog, QListWidget, 
                            QListWidgetItem, QCheckBox)
from recorder import Recorder
from player import Player
import locale
import threading # <-- Добавлено

# --- Logging Setup ---
logger = logging.getLogger("ClickerRecord") # Use a specific name for the logger
logger.setLevel(logging.DEBUG) 
# Create file handler
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'clickerrecord.log')
fh = logging.FileHandler(log_file_path, encoding='utf-8')
fh.setLevel(logging.DEBUG)
# Create formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s')
fh.setFormatter(formatter)
# Add the handlers to the logger
logger.addHandler(fh)
# --- End Logging Setup ---

# All comments below this line are in English
# Button styles for different states
STYLE_BUTTON_NORMAL = "background-color: {bg_color}; color: white; border-radius: 5px; padding: 5px;"
STYLE_BUTTON_DISABLED = "background-color: #CCCCCC; color: #666666; border-radius: 5px; padding: 5px;"
STYLE_BUTTON_PRESSED = "background-color: {press_color}; color: white; border-radius: 5px; padding: 5px; border: 2px solid #FFFFFF;"
STYLE_BUTTON_ACTIVE = "background-color: {active_color}; color: white; border-radius: 5px; padding: 5px; font-weight: bold;"

STYLE_SAVE_LOAD_NORMAL = "background-color: #E0E0E0; border: 1px solid #BDBDBD; border-radius: 5px; padding: 5px;"
STYLE_SAVE_LOAD_PRESSED = "background-color: #BDBDBD; border: 1px solid #9E9E9E; border-radius: 5px; padding: 5px;"
STYLE_SAVE_LOAD_DISABLED = "background-color: #F5F5F5; color: #BDBDBD; border: 1px solid #E0E0E0; border-radius: 5px; padding: 5px;"

STYLE_HELP_NORMAL = "background-color: #F0F0F0; border: 1px solid #CCCCCC; border-radius: 5px; padding: 3px;"
STYLE_HELP_PRESSED = "background-color: #D0D0D0; border: 1px solid #BDBDBD; border-radius: 5px; padding: 3px;"

# --- Мультиязычность ---
LANGUAGES = {
    'en': 'English',
    'ru': 'Русский',
    'de': 'Deutsch',
    'fr': 'Français',
    'es': 'Español',
    'it': 'Italiano',
    'zh': '中文',
    'ja': '日本語',
    'tr': 'Türkçe',
    'pl': 'Polski',
    'he': 'עברית',
}

# Функция определения системного языка
def detect_system_language():
    """Определяет язык системы и возвращает код языка."""
    lang, _ = locale.getdefaultlocale()
    if lang:
        code = lang.split('_')[0]
        if code in LANGUAGES:
            return code
    return 'en'

# Специфично для Windows, устанавливаем атрибуты High DPI перед созданием QApplication
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Устанавливаем английский по умолчанию
        self.current_language = 'en'
        self.translations = load_translations(self.current_language) # Загружаем английские переводы
        
        self.recorder = Recorder()
        self.player = Player()
        self.recording = False
        self.playing = False
        self.recorded_actions = []
        self.current_file_path = None  # Путь к текущему файлу записи
        self.settings = QSettings("ClickerRecord", "UserSettings")
        
        # Таймеры для расписания
        self.schedule_timer = QTimer(self)
        self.schedule_timer.setSingleShot(True) # По умолчанию однократный
        self.schedule_timer.timeout.connect(self._trigger_scheduled_playback)
        
        self.interval_timer = QTimer(self)
        self.interval_timer.timeout.connect(self._trigger_interval_playback)
        self.interval_repeats_left = 0 # Счетчик оставшихся повторов для интервального таймера (небесконечного)
        
        self.initUI()
        self.connectSignals()
        self.setupShortcuts()
        self.updateUIState() # Начальное состояние интерфейса
        logger.info("MainWindow UI initialized, attempting to load settings.")
        self.load_settings() # Загружаем сохраненные настройки (язык)
        logger.info("Settings loaded and applied.")
        
    def initUI(self):
        logger.debug("Initializing UI elements.")
        self.setWindowTitle(self.translations['app_title'])
        # Increased height to accommodate the action list
        self.setFixedSize(400, 900) 
        
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Шрифты
        title_font = QFont("Arial", 12, QFont.Bold)
        normal_font = QFont("Arial", 10)
        small_font = QFont("Arial", 8)
        status_font = QFont("Arial", 10)
        
        # Заголовок приложения
        self.header_label = QLabel(self.translations['app_title'])
        self.header_label.setFont(title_font)
        self.header_label.setAlignment(Qt.AlignCenter)
        self.header_label.setWordWrap(True)
        main_layout.addWidget(self.header_label)
        
        # Верхние кнопки в сетке
        button_grid = QGridLayout()
        button_grid.setSpacing(25)  # Увеличиваем расстояние между кнопками
        button_grid.setContentsMargins(10, 10, 10, 10)  # Добавляем отступы внутри сетки
        
        # Ряд 1: Запись
        record_layout = QHBoxLayout()
        record_layout.setSpacing(10)
        
        # Кнопка Начать запись + подпись
        start_record_vlayout = QVBoxLayout()
        self.record_button = QPushButton(self.translations['start_record'])
        self.record_button.setFont(normal_font)
        self.record_button.setFixedHeight(40)
        self.record_button.setStyleSheet(
            f"QPushButton {{ {STYLE_BUTTON_NORMAL.format(bg_color='#00CC00')} }}"
            f"QPushButton:pressed {{ {STYLE_BUTTON_PRESSED.format(press_color='#009900')} }}"
            f"QPushButton:disabled {{ {STYLE_BUTTON_DISABLED} }}"
        )
        start_record_vlayout.addWidget(self.record_button)
        self.record_shortcut_label = QLabel("F6")
        self.record_shortcut_label.setFont(small_font)
        self.record_shortcut_label.setAlignment(Qt.AlignCenter)
        start_record_vlayout.addWidget(self.record_shortcut_label)
        record_layout.addLayout(start_record_vlayout)
        
        # Кнопка Остановить запись + подпись
        stop_record_vlayout = QVBoxLayout()
        self.stop_record_button = QPushButton(self.translations['stop_record'])
        self.stop_record_button.setFont(normal_font)
        self.stop_record_button.setFixedHeight(40)
        self.stop_record_button.setStyleSheet(
            f"QPushButton {{ {STYLE_BUTTON_NORMAL.format(bg_color='#FF3333')} }}"
            f"QPushButton:pressed {{ {STYLE_BUTTON_PRESSED.format(press_color='#CC0000')} }}"
            f"QPushButton:disabled {{ {STYLE_BUTTON_DISABLED} }}"
        )
        self.stop_record_button.setEnabled(False)
        stop_record_vlayout.addWidget(self.stop_record_button)
        self.stop_record_shortcut_label = QLabel("F6")
        self.stop_record_shortcut_label.setFont(small_font)
        self.stop_record_shortcut_label.setAlignment(Qt.AlignCenter)
        stop_record_vlayout.addWidget(self.stop_record_shortcut_label)
        record_layout.addLayout(stop_record_vlayout)
        
        main_layout.addLayout(record_layout)
        
        # Ряд 2: Воспроизведение
        play_layout = QHBoxLayout()
        play_layout.setSpacing(10)
        
        # Кнопка Воспроизвести + подпись
        start_play_vlayout = QVBoxLayout()
        self.play_button = QPushButton(self.translations['play'])
        self.play_button.setFont(normal_font)
        self.play_button.setFixedHeight(40)
        self.play_button.setStyleSheet(
             f"QPushButton {{ {STYLE_BUTTON_NORMAL.format(bg_color='#0066CC')} }}"
             f"QPushButton:pressed {{ {STYLE_BUTTON_PRESSED.format(press_color='#004C99')} }}"
             f"QPushButton:disabled {{ {STYLE_BUTTON_DISABLED} }}"
        )
        start_play_vlayout.addWidget(self.play_button)
        self.play_shortcut_label = QLabel("F7")
        self.play_shortcut_label.setFont(small_font)
        self.play_shortcut_label.setAlignment(Qt.AlignCenter)
        start_play_vlayout.addWidget(self.play_shortcut_label)
        play_layout.addLayout(start_play_vlayout)
        
        # Кнопка Остановить воспроизведение + подпись
        stop_play_vlayout = QVBoxLayout()
        self.stop_play_button = QPushButton(self.translations['stop_play'])
        self.stop_play_button.setFont(normal_font)
        self.stop_play_button.setFixedHeight(40)
        self.stop_play_button.setStyleSheet(
             f"QPushButton {{ {STYLE_BUTTON_NORMAL.format(bg_color='#FF9900')} }}"
             f"QPushButton:pressed {{ {STYLE_BUTTON_PRESSED.format(press_color='#CC6600')} }}"
             f"QPushButton:disabled {{ {STYLE_BUTTON_DISABLED} }}"
        )
        self.stop_play_button.setEnabled(False)
        stop_play_vlayout.addWidget(self.stop_play_button)
        self.stop_play_shortcut_label = QLabel("Esc")
        self.stop_play_shortcut_label.setFont(small_font)
        self.stop_play_shortcut_label.setAlignment(Qt.AlignCenter)
        stop_play_vlayout.addWidget(self.stop_play_shortcut_label)
        play_layout.addLayout(stop_play_vlayout)
        
        main_layout.addLayout(play_layout)
        
        # Ряд 3: Язык (бывший Повтор)
        language_vlayout = QVBoxLayout()
        self.repeat_button = QPushButton(self.translations['language'])
        self.repeat_button.setFont(normal_font)
        self.repeat_button.setFixedHeight(40)
        self.repeat_button.setStyleSheet(
             f"QPushButton {{ {STYLE_BUTTON_NORMAL.format(bg_color='#9966CC')} }}"
             f"QPushButton:pressed {{ {STYLE_BUTTON_PRESSED.format(press_color='#663399')} }}"
             f"QPushButton:disabled {{ {STYLE_BUTTON_DISABLED} }}"
        )
        language_vlayout.addWidget(self.repeat_button)
        self.language_shortcut_label = QLabel("F8")
        self.language_shortcut_label.setFont(small_font)
        self.language_shortcut_label.setAlignment(Qt.AlignCenter)
        language_vlayout.addWidget(self.language_shortcut_label)
        
        main_layout.addLayout(language_vlayout)
        
        # --- Разделитель --- 
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # --- Настройки --- 
        
        # Список ТОЛЬКО интерактивных виджетов для блокировки
        self.settings_widgets = [] 
        
        repeat_setup_layout = QHBoxLayout()
        self.repeat_label = QLabel(self.translations['repeat_count'])
        self.repeat_label.setFont(normal_font)
        self.repeat_count = QSpinBox()
        self.repeat_count.setFont(normal_font)
        self.repeat_count.setRange(1, 1000)
        self.repeat_count.setValue(1)
        self.repeat_count.setFixedWidth(80)
        repeat_setup_layout.addWidget(self.repeat_label)
        repeat_setup_layout.addStretch()
        self.infinite_repeat_checkbox = QCheckBox(self.translations.get('infinite_repeats', 'Infinite Repeats'))
        self.infinite_repeat_checkbox.setFont(normal_font)
        self.infinite_repeat_checkbox.setChecked(False)
        repeat_setup_layout.addWidget(self.infinite_repeat_checkbox)
        repeat_setup_layout.addWidget(self.repeat_count)
        main_layout.addLayout(repeat_setup_layout)
        self.settings_widgets.append(self.repeat_count) # Добавляем только SpinBox
        self.settings_widgets.append(self.infinite_repeat_checkbox) # Добавляем чекбокс в список управляемых
        
        schedule_group_layout = QVBoxLayout()
        schedule_group_layout.setSpacing(5)
        self.schedule_label = QLabel(self.translations['schedule'])
        self.schedule_label.setFont(normal_font)
        schedule_group_layout.addWidget(self.schedule_label)
        # self.settings_widgets.append(schedule_label) # Не добавляем Label
        
        self.schedule_group = QButtonGroup(self)
        self.once_radio = QRadioButton(self.translations['once'])
        self.once_radio.setFont(normal_font)
        self.once_radio.setChecked(True)
        self.schedule_group.addButton(self.once_radio)
        schedule_group_layout.addWidget(self.once_radio)
        self.settings_widgets.append(self.once_radio) # Добавляем RadioButton
        
        interval_layout = QHBoxLayout()
        self.interval_radio = QRadioButton(self.translations['interval'])
        self.interval_radio.setFont(normal_font)
        self.schedule_group.addButton(self.interval_radio)
        self.interval_value = QSpinBox()
        self.interval_value.setRange(1, 3600 * 24) # От 1 секунды до 24 часов
        self.interval_value.setValue(5)
        self.interval_value.setFixedWidth(60)
        self.interval_value.setFont(normal_font)
        self.interval_label = QLabel(self.translations['seconds']) # <-- Изменено на seconds
        self.interval_label.setFont(normal_font)
        interval_layout.addWidget(self.interval_radio)
        interval_layout.addWidget(self.interval_value)
        interval_layout.addWidget(self.interval_label)
        interval_layout.addStretch()
        schedule_group_layout.addLayout(interval_layout)
        self.settings_widgets.append(self.interval_radio) # Добавляем RadioButton
        self.settings_widgets.append(self.interval_value) # Добавляем SpinBox
        # self.settings_widgets.extend([self.interval_radio, self.interval_value, interval_label]) # Не добавляем Label
        
        time_layout = QHBoxLayout()
        self.time_radio = QRadioButton(self.translations['at_time'])
        self.time_radio.setFont(normal_font)
        # Убираем self.time_radio.setChecked(True) # Пусть "once" будет по умолчанию
        self.schedule_group.addButton(self.time_radio)
        self.time_value = QTimeEdit()
        self.time_value.setDisplayFormat("HH:mm")
        self.time_value.setTime(QTime.currentTime().addSecs(300))
        self.time_value.setFixedWidth(80)
        self.time_value.setFont(normal_font)
        time_layout.addWidget(self.time_radio)
        time_layout.addWidget(self.time_value)
        time_layout.addStretch()
        schedule_group_layout.addLayout(time_layout)
        main_layout.addLayout(schedule_group_layout)
        self.settings_widgets.append(self.time_radio) # Добавляем RadioButton
        self.settings_widgets.append(self.time_value) # Добавляем TimeEdit
        # self.settings_widgets.extend([self.time_radio, self.time_value])
        
        speed_layout = QVBoxLayout()
        self.speed_label = QLabel(self.translations['speed'])
        self.speed_label.setFont(normal_font)
        speed_layout.addWidget(self.speed_label)
        # self.settings_widgets.append(speed_label) # Не добавляем Label
        
        speed_slider_layout = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 500)
        self.speed_slider.setValue(100)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(50)
        self.speed_value = QLabel("1.00x")
        self.speed_value.setFont(normal_font)
        self.speed_value.setFixedWidth(50)
        self.speed_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        speed_slider_layout.addWidget(self.speed_slider)
        speed_slider_layout.addWidget(self.speed_value)
        speed_layout.addLayout(speed_slider_layout)
        main_layout.addLayout(speed_layout)
        self.settings_widgets.append(self.speed_slider) # Добавляем Slider
        # self.settings_widgets.extend([self.speed_slider, self.speed_value]) # Не добавляем Label

        # --- Action List Section ---
        self.actions_list_label = QLabel(self.translations.get("recorded_actions_label", "Recorded Actions:"))
        self.actions_list_label.setFont(normal_font)
        main_layout.addWidget(self.actions_list_label)

        self.actions_list_widget = QListWidget()
        self.actions_list_widget.setFont(small_font) # Use small_font for list items
        self.actions_list_widget.setFixedHeight(150) # Adjust height as needed
        main_layout.addWidget(self.actions_list_widget)
        self.settings_widgets.append(self.actions_list_widget) # Disable list during record/play

        self.delete_action_button = QPushButton(self.translations.get("delete_selected_action_button", "Delete Selected Action"))
        self.delete_action_button.setFont(normal_font)
        self.delete_action_button.setFixedHeight(30)
        self.delete_action_button.setStyleSheet(
            f"QPushButton {{ {STYLE_BUTTON_NORMAL.format(bg_color='#FF6347')} }}" # Tomato color
            f"QPushButton:pressed {{ {STYLE_BUTTON_PRESSED.format(press_color='#E5533D')} }}"
            f"QPushButton:disabled {{ {STYLE_BUTTON_DISABLED} }}"
        )
        self.delete_action_button.setEnabled(False) # Initially disabled
        main_layout.addWidget(self.delete_action_button)
        # self.settings_widgets.append(self.delete_action_button) # This button is managed by selection state too

        # --- End Action List Section ---

        # Создаем статус бар без кнопки Language
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Создаем счетчик действий
        self.action_count = QLabel()
        self.action_count.setFont(QFont("Arial", 10))
        self.statusBar.addWidget(self.action_count)
        
        # --- Нижние кнопки --- 
        
        # Кнопки сохранения и загрузки
        save_load_layout = QHBoxLayout()
        save_load_layout.setSpacing(10)
        
        # Кнопка сохранения + подпись
        save_vlayout = QVBoxLayout()
        self.save_button = QPushButton(self.translations['save'])
        self.save_button.setFont(normal_font)
        self.save_button.setFixedHeight(35)
        # Возвращаем стиль для кнопки
        self.save_button.setStyleSheet(
            f"QPushButton {{ {STYLE_SAVE_LOAD_NORMAL} }}"
            f"QPushButton:pressed {{ {STYLE_SAVE_LOAD_PRESSED} }}"
            f"QPushButton:disabled {{ {STYLE_SAVE_LOAD_DISABLED} }}"
        )
        save_vlayout.addWidget(self.save_button)
        self.save_shortcut_label = QLabel("Ctrl+S")
        self.save_shortcut_label.setFont(small_font)
        self.save_shortcut_label.setAlignment(Qt.AlignCenter)
        save_vlayout.addWidget(self.save_shortcut_label)
        save_load_layout.addLayout(save_vlayout)
        
        # Кнопка загрузки + подпись
        load_vlayout = QVBoxLayout()
        self.load_button = QPushButton(self.translations['load'])
        self.load_button.setFont(normal_font)
        self.load_button.setFixedHeight(35)
        # Возвращаем стиль для кнопки
        self.load_button.setStyleSheet(
            f"QPushButton {{ {STYLE_SAVE_LOAD_NORMAL} }}"
            f"QPushButton:pressed {{ {STYLE_SAVE_LOAD_PRESSED} }}"
            f"QPushButton:disabled {{ {STYLE_SAVE_LOAD_DISABLED} }}"
        )
        load_vlayout.addWidget(self.load_button)
        self.load_shortcut_label = QLabel("Ctrl+O")
        self.load_shortcut_label.setFont(small_font)
        self.load_shortcut_label.setAlignment(Qt.AlignCenter)
        load_vlayout.addWidget(self.load_shortcut_label)
        save_load_layout.addLayout(load_vlayout)
        
        main_layout.addLayout(save_load_layout)
        
        # Кнопка справки
        help_layout = QHBoxLayout()
        self.help_button = QPushButton(self.translations['help'])
        self.help_button.setFont(normal_font)
        self.help_button.setFixedHeight(30)
        self.help_button.setStyleSheet(
            f"QPushButton {{ {STYLE_HELP_NORMAL} }}"
            f"QPushButton:pressed {{ {STYLE_HELP_PRESSED} }}"
        )
        help_layout.addStretch()
        help_layout.addWidget(self.help_button)
        help_layout.addStretch()
        main_layout.addLayout(help_layout)
        
        # Статусная строка
        self.statusBar.setFont(status_font)
        self.statusBar.showMessage(self.translations['ready'])
        
        # Таймер для обновления статус-бара (более частый)
        self.gui_update_timer = QTimer(self)
        self.gui_update_timer.timeout.connect(self.update_status)
        self.gui_update_timer.start(100) # Обновление статуса 10 раз в секунду
        
        self.updateUITexts()
    
    def connectSignals(self):
        self.record_button.clicked.connect(self.start_recording)
        self.stop_record_button.clicked.connect(self.stop_recording)
        self.play_button.clicked.connect(self.start_playback)
        self.stop_play_button.clicked.connect(self.stop_playback)
        self.repeat_button.clicked.connect(self.show_language_dialog)
        self.save_button.clicked.connect(self.save_recording)
        self.load_button.clicked.connect(self.load_recording)
        self.help_button.clicked.connect(self.show_help)
        
        self.speed_slider.valueChanged.connect(self.update_speed_label)
        
        # Подключение к сигналам плеера
        # Используем Qt.QueuedConnection для потокобезопасности!
        self.player.playbackFinished.connect(self.on_playback_completed, Qt.QueuedConnection)
        self.player.playbackError.connect(self.on_playback_error, Qt.QueuedConnection)
        self.player.playbackProgress.connect(self.update_playback_progress, Qt.QueuedConnection)
        
        self.actions_list_widget.currentItemChanged.connect(self.updateUIState)
        self.delete_action_button.clicked.connect(self.delete_selected_action)


    def setupShortcuts(self):
        """Настройка горячих клавиш"""
        # F6 - начать/остановить запись
        self.record_shortcut = QShortcut(QKeySequence("F6"), self)
        self.record_shortcut.activated.connect(self.toggle_recording)
        
        # F7 - воспроизвести
        self.play_shortcut = QShortcut(QKeySequence("F7"), self)
        self.play_shortcut.activated.connect(self.start_playback)
        
        # Esc - остановить воспроизведение
        self.stop_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.stop_shortcut.activated.connect(self.stop_playback)
        
        # F8 - повторить последнее
        self.repeat_shortcut = QShortcut(QKeySequence("F8"), self)
        self.repeat_shortcut.activated.connect(self.show_language_dialog)
        
        # Ctrl+S - сохранить запись
        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self.save_recording)
        
        # Ctrl+O - загрузить запись
        self.load_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        self.load_shortcut.activated.connect(self.load_recording)
    
    def toggle_recording(self):
        """Переключение между записью и остановкой по горячей клавише F6"""
        if self.recording:
            self.stop_recording()
        elif not self.playing: # Добавим проверку, чтобы не начать запись во время игры
            self.start_recording()
    
    def start_recording(self):
        """Начало записи"""
        if self.recording or self.playing: # Не начинаем, если уже записываем или играем
            return
            
        self.recording = True
        self.recorded_actions = []
        self.current_file_path = None
        # action_count обновится через update_status
        
        # Убираем ручное управление кнопками
        # self.record_button.setEnabled(False)
        # self.stop_record_button.setEnabled(True)
        
        # self.statusBar.showMessage("Запись...") # Обновится через update_status
        
        # Запускаем запись
        try:
            self.recorded_actions = [] # Clear previous actions
            self.actions_list_widget.clear() # Clear display list
            self.current_file_path = None # Reset file path
            self.recorder.start_recording(self.on_action_recorded)
            logger.info("Recording started via UI.")
            self.updateUIState() # Обновляем интерфейс ПОСЛЕ старта записи
        except Exception as e:
            logger.error(f"Error starting recorder: {e}", exc_info=True)
            QMessageBox.critical(self, self.translations['recording_error_title'], self.translations.get('recording_error_text', self.translations['recording_error_text']).format(error=e))
            self.recording = False # Сбрасываем флаг, если старт не удался
            self.updateUIState()
    
    def stop_recording(self):
        """Остановка записи"""
        if not self.recording:
            return
        logger.info("Attempting to stop recording via UI.")
        try:
            self.recorder.stop()
            self.recording = False
            logger.info(f"Recording stopped. State: recording={self.recording}, playing={self.playing}, actions={len(self.recorded_actions)}")
        except Exception as e:
            logger.error(f"Error stopping recorder: {e}", exc_info=True)
            self.recording = False # Все равно считаем остановленным
        finally:
            self.updateUIState() # Обновляем интерфейс
            QApplication.processEvents() # Принудительно обрабатываем события
            logger.debug("stop_recording: Called updateUIState and processEvents.")
    
    def on_action_recorded(self, action):
        if self.recording: # Доп. проверка на всякий случай
            self.recorded_actions.append(action)
            display_text = self._format_action_for_display(action)
            self.actions_list_widget.addItem(display_text)
            logger.debug(f"Action recorded and added to list: {display_text}, total actions: {len(self.recorded_actions)}")
        # Счетчик обновится через update_status
    
    def start_playback(self):
        logger.info("Attempting to start playback.")
        if not self.recorded_actions:
            warning_msg = self.translations.get('no_actions_warning', self.translations['no_actions_warning'])
            logger.warning(f"Playback start denied: {warning_msg}")
            QMessageBox.warning(self, self.translations['playback_error_title'], warning_msg)
            return
        if self.playing or self.recording:
            logger.warning("Playback start denied: Already playing or recording.")
            return

        speed_factor = self.speed_slider.value() / 100.0
        logger.debug(f"Playback speed factor: {speed_factor}")

        # Определяем режим запуска
        if self.once_radio.isChecked():
            repeat_count = self.repeat_count.value()
            logger.info(f"Starting direct playback: repeats={repeat_count}")
            self._start_direct_playback(repeat_count, speed_factor)
        elif self.interval_radio.isChecked():
            interval_seconds = self.interval_value.value()
            is_infinite = self.infinite_repeat_checkbox.isChecked()
            logger.info(f"Starting interval playback: interval_seconds={interval_seconds}, infinite={is_infinite}")

            if interval_seconds > 0:
                # Сначала устанавливаем флаги и счетчики
                if is_infinite:
                    self.interval_repeats_left = -1 # Флаг бесконечности
                    logger.debug(f"Starting INFINITE interval timer: every {interval_seconds} sec")
                else:
                    self.interval_repeats_left = self.repeat_count.value()
                    if self.interval_repeats_left <= 0:
                        logger.warning("Interval playback: Repeat count <= 0, no playback started.")
                        return # Не запускаем, если повторов 0 или меньше
                    logger.debug(f"Starting interval timer: every {interval_seconds} sec, repeats: {self.interval_repeats_left}")

                # Ставим self.playing = True и обновляем UI ПЕРЕД первым запуском
                self.playing = True # Устанавливаем флаг игры
                self.updateUIState()

                # Запускаем первый раз немедленно
                self._trigger_interval_playback() # Этот вызов запустит плеер и, если нужно, перезапустит таймер

                # --- УДАЛЕНО: Логика перезапуска таймера теперь полностью в _trigger_interval_playback ---
                # if self.playing and (is_infinite or self.interval_repeats_left > 0):
                #      self.interval_timer.start(interval_seconds * 1000)
                # --- КОНЕЦ УДАЛЕНИЯ ---
            else:
                 logger.warning("Interval playback: Interval <= 0, interval mode not started.")
                 # Если интервал 0, то играть не начинаем
                 return

            # --- ПЕРЕМЕЩЕНО ВЫШЕ: Установка playing и updateUIState перед первым запуском ---
            # self.playing = True # Устанавливаем флаг игры
            # self.updateUIState()
            # --- КОНЕЦ ПЕРЕМЕЩЕНИЯ ---
        elif self.time_radio.isChecked():
            target_time = self.time_value.time()
            current_time = QTime.currentTime()
            msecs_to_target = current_time.msecsTo(target_time)

            if msecs_to_target < 0: # Если время уже прошло сегодня, планируем на завтра
                msecs_to_target += 24 * 60 * 60 * 1000 
            
            logger.info(f"Scheduling playback at: {target_time.toString('HH:mm')}, in {msecs_to_target / 1000:.1f} sec")
            self.schedule_timer.setSingleShot(True) # Убедимся, что таймер однократный
            self.schedule_timer.start(msecs_to_target)
            self.playing = True # Устанавливаем флаг игры, пока ждем таймер
            self.updateUIState()
            self.statusBar.showMessage(f"{self.translations['schedule']} {target_time.toString('HH:mm')}")

    def _start_direct_playback(self, repeat_count, speed_factor):
        """Запускает немедленное воспроизведение заданное число раз."""
        logger.debug(f"Direct playback initiated: repeats={repeat_count}, speed={speed_factor}")
        self.playing = True
        try:
            self.player.play(
                self.recorded_actions, 
                repeat_count, 
                speed_factor
            )
            self.updateUIState()
        except TypeError as te:
            error_msg = self.translations.get('playback_type_error', self.translations['playback_type_error']).format(error=te)
            logger.error(f"Playback TypeError: {error_msg}", exc_info=True)
            QMessageBox.critical(self, self.translations['playback_error_title'], error_msg)
            self.playing = False
            self.updateUIState()
        except Exception as e:
            error_msg = self.translations.get('playback_error_text', self.translations['playback_error_text']).format(error=e)
            logger.error(f"Playback Exception: {error_msg}", exc_info=True)
            QMessageBox.critical(self, self.translations['playback_error_title'], error_msg)
            self.playing = False
            self.updateUIState()
            
    def _trigger_scheduled_playback(self):
        """Срабатывает по таймеру для 'Run at HH:MM'."""
        logger.info("Scheduled playback timer triggered.")
        if self.playing: # Проверка, что не остановили вручную
             repeat_count = self.repeat_count.value()
             speed_factor = self.speed_slider.value() / 100.0
             logger.debug(f"Executing scheduled playback: repeats={repeat_count}, speed={speed_factor}")
             # Запускаем однократно, т.к. таймер был SingleShot
             # Флаг self.playing уже True, плеер сам его сбросит по завершению/ошибке
             self._start_direct_playback(repeat_count, speed_factor)
             # Важно: Не сбрасываем self.playing здесь, ждем сигнал от плеера
        else:
             logger.info("Scheduled playback was cancelled before execution.")
             # Убедимся, что UI обновлен
             self.updateUIState()

    def _trigger_interval_playback(self):
         """Срабатывает по таймеру для 'Run every X seconds'. Запускает ОДИН цикл воспроизведения."""
         logger.debug("Interval playback timer triggered.")
         if self.playing: # Проверяем, что не было остановки
            is_infinite = (self.interval_repeats_left == -1) # Проверяем флаг бесконечности
            
            # Если режим конечный, проверяем, остались ли еще повторы (перед текущим запуском)
            if not is_infinite and self.interval_repeats_left <= 0:
                 logger.info("Interval playback: Repeats ended, but timer triggered? Stopping.")
                 # Не вызываем stop_playback(), чтобы не сбросить плеер, если он еще играет последний раз
                 if self.interval_timer.isActive():
                     self.interval_timer.stop()
                 # Состояние playing сбросится в on_playback_completed
                 return
                 
            speed_factor = self.speed_slider.value() / 100.0
            logger.debug(f"Executing interval cycle: speed={speed_factor}, infinite={is_infinite}, repeats_left_before_play={self.interval_repeats_left}")
            
            # Запускаем плеер на repeat_count раз
            try:
                 # Запускаем плеер только на ОДИН раз
                 self.player.play(self.recorded_actions, 1, speed_factor)
                 
                 # Уменьшаем счетчик ПОСЛЕ успешного запуска play, если режим не бесконечный
                 if not is_infinite:
                      self.interval_repeats_left -= 1
                      logger.debug(f"Interval playback cycle started, repeats left: {self.interval_repeats_left}")
                 else:
                      logger.debug("Infinite interval playback cycle started.")

            except Exception as e:
                 error_msg = self.translations.get('playback_error_text', self.translations['playback_error_text']).format(error=e)
                 logger.error(f"Error during interval player.play: {error_msg}", exc_info=True)
                 QMessageBox.critical(self, self.translations['playback_error_title'], error_msg)
                 self.stop_playback() # Останавливаем всю серию при ошибке
                 return
                 
            # Логика перезапуска таймера перенесена сюда (после успешного play)
            # Если игра все еще активна (не остановили во время play) 
            # и (режим бесконечный ИЛИ остались повторы > 0)
            if self.playing and (is_infinite or self.interval_repeats_left > 0):
                 interval_seconds = self.interval_value.value()
                 # Запускаем таймер только если интервал положительный
                 if interval_seconds > 0:
                      logger.debug(f"Scheduling next interval run in {interval_seconds} sec.")
                      self.interval_timer.start(interval_seconds * 1000)
                 else:
                      logger.warning("Interval playback: Interval <= 0, timer not restarting.")
                      # Если интервал 0, а повторы конечные, останавливаем
                      if not is_infinite: 
                           self.stop_playback() 
            else:
                 # Если повторы кончились (или остановили вручную)
                 logger.info("Interval playback: Finite repeats completed or manually stopped. Timer not restarting.")
                 # Не меняем self.playing здесь, ждем on_playback_completed/error от последнего play

         else:
             logger.info("Interval playback: Playback was stopped, timer not restarting.")
             if self.interval_timer.isActive(): # Доп. проверка
                 self.interval_timer.stop()

    def stop_playback(self):
        """Остановка воспроизведения (прямого или по расписанию)"""
        logger.info("Stop playback called.")

        # Останавливаем таймеры расписания, если они активны
        was_timer_active = False
        if self.schedule_timer.isActive():
            logger.debug("Stopping 'Run at' schedule timer.")
            self.schedule_timer.stop()
            was_timer_active = True
        if self.interval_timer.isActive():
            logger.debug("Stopping 'Run every' interval timer.")
            self.interval_timer.stop()
            was_timer_active = True

        # Сбрасываем счетчик интервальных повторов
        self.interval_repeats_left = 0

        # Останавливаем плеер, если он активен
        player_was_playing = self.player.is_playing # Проверяем фактическое состояние плеера
        if player_was_playing:
            try:
                logger.info("Requesting player stop.")
                self.player.stop()
                # Не меняем self.playing здесь, ждем callback
                self.statusBar.showMessage(self.translations.get('playback_stopped', self.translations['playback_stopped']))
            except Exception as e:
                logger.error(f"Error calling player.stop(): {e}", exc_info=True)
                # Если ошибка при остановке плеера, всё равно сбрасываем состояние GUI
                self.playing = False
                self.updateUIState()
                self.statusBar.showMessage(self.translations.get('playback_stop_error', self.translations['playback_stop_error']))
                return # Выходим, чтобы не сбросить флаг еще раз ниже

        # Если был активен таймер, но плеер еще не запущен (ожидание 'Run at' или между интервалами)
        # или если плеер НЕ был активен (например, уже остановился сам),
        # то нужно вручную сбросить флаг playing и обновить UI.
        # Если плеер БЫЛ активен, то сброс флага и обновление UI произойдет в on_playback_completed/error.
        if was_timer_active and not player_was_playing:
             logger.debug("Timer was stopped before player started. Resetting GUI state.")
             self.playing = False
             self.updateUIState()
        elif not player_was_playing and self.playing: # Если плеер не играет, но GUI думает, что играет
             logger.debug("Player not active, but GUI flag was set. Resetting GUI state.")
             self.playing = False
             self.updateUIState()
        else:
             logger.debug("Player is active (waiting for callback) or already stopped.")

         # Убираем ручное управление кнопками - оно теперь в updateUIState
         # self.play_button.setEnabled(True)

    def on_playback_completed(self):
        """Слот, вызываемый сигналом playbackFinished из плеера"""
        logger.info("Playback completed signal received.")

        # В режиме интервала:
        # - Плеер завершил ОДИН цикл (из 1 повтора).
        # - Флаг self.playing остается True.
        # - Таймер был перезапущен (или должен быть перезапущен) в _trigger_interval_playback.
        # - Остановка происходит ТОЛЬКО через stop_playback() или по завершению счетчика в _trigger_interval_playback.
        # Поэтому здесь не нужно менять self.playing или останавливать таймер.

        # Если это НЕ интервальный режим (был прямой запуск или 'Run at'):
        # Проверяем, был ли режим интервальным, посмотрев на радио-кнопку (более надежно, чем timer.isActive())
        is_interval_radio_checked = self.interval_radio.isChecked()

        if not is_interval_radio_checked:
             # Это был прямой запуск или 'Run at', и он завершился.
             if self.playing: # Дополнительная проверка, что мы действительно считали себя играющими
                 logger.info("Non-interval playback finished. Resetting state.")
                 self.playing = False
                 self.updateUIState() # Обновляем интерфейс
                 QApplication.processEvents() # Даем интерфейсу обновиться
                 logger.debug("Non-interval playback state updated.")
             else:
                 logger.warning("Non-interval playback finished, but self.playing was already False.")
        else:
             # Это был один из запусков интервального таймера
             logger.debug("Interval playback cycle finished.")
             # Проверяем, был ли это последний запуск (если режим не бесконечный)
             # Важно: self.interval_repeats_left уже уменьшен в _trigger_interval_playback *перед* этим вызовом
             is_infinite = (self.interval_repeats_left == -1) # Проверяем флаг бесконечности
             if not is_infinite and self.interval_repeats_left <= 0:
                  # Повторы закончились
                  logger.info("Finite interval repeats completed. Resetting state.")
                  if self.playing: # Доп. проверка
                     self.playing = False
                     self.updateUIState()
                     QApplication.processEvents()
                     logger.debug("Finite interval playback state updated.")
                  else:
                     logger.warning("Finite interval repeats completed, but self.playing was already False.")
             else:
                 # Либо режим бесконечный, либо еще остались повторы - таймер должен был перезапуститься в _trigger_interval_playback
                 logger.debug("Interval cycle continues (or infinite). Logic in _trigger_interval_playback.")
                 # Ничего не делаем здесь, интерфейс остается в состоянии 'Playing...'.

    def on_playback_error(self, error_message):
         """Слот, вызываемый сигналом playbackError из плеера"""
         logger.error(f"Playback error signal received: {error_message}")
         
         # При любой ошибке останавливаем все таймеры и сбрасываем состояние
         if self.schedule_timer.isActive():
             self.schedule_timer.stop()
             logger.debug("Scheduled timer stopped due to playback error.")
         if self.interval_timer.isActive():
             self.interval_timer.stop()
             logger.debug("Interval timer stopped due to playback error.")
         # self.interval_repeats_left = 0 # Больше не нужно
            
         if self.playing: # Доп. проверка
              logger.info("Error during playback. Resetting state.")
              self.playing = False
              self.updateUIState()
              QApplication.processEvents()
              QMessageBox.warning(self, self.translations['playback_error_title'], str(error_message))
              self.statusBar.showMessage(f"{self.translations['playback_error_title']}: {error_message}")
              logger.debug("Playback error state updated, error message shown.")
         else:
              logger.warning("Playback error, but self.playing was already False.")

    def update_playback_progress(self, current_ms, total_ms):
        """Обновляет статус-бар для отображения прогресса воспроизведения"""
        logger.debug(f"Updating playback progress: {current_ms}ms / {total_ms}ms")
        if self.playing and total_ms > 0:
            progress_percent = int((current_ms / total_ms) * 100)
            # Показываем прогресс только если он валидный
            if 0 <= progress_percent <= 100:
                 self.statusBar.showMessage(f"Воспроизведение... ({progress_percent}%)")
            else: # Если расчет странный, показываем просто статус
                 self.statusBar.showMessage(f"Воспроизведение...")
        elif self.playing:
             self.statusBar.showMessage(f"Воспроизведение... (расчет времени)")
    
    def check_schedule(self):
        # Этот метод больше не нужен, логика в start_playback
        pass 
    
    def update_speed_label(self, value):
        speed = value / 100.0
        self.speed_value.setText(f"{speed:.2f}x")
    
    def save_recording(self):
        logger.info("Save recording called.")
        if not self.recorded_actions:
            no_actions_msg = self.translations.get('status_no_actions', self.translations['status_no_actions'])
            logger.warning(f"Save denied: {no_actions_msg}")
            self.statusBar.showMessage(no_actions_msg)
            return
        
        dialog_title = self.translations.get('file_dialog_save', self.translations['file_dialog_save'])
        dialog_filter = self.translations.get('file_dialog_filter', self.translations['file_dialog_filter'])
        file_path, _ = QFileDialog.getSaveFileName(self, dialog_title, "", dialog_filter)
        
        if file_path:
            logger.info(f"Attempting to save recording to: {file_path}")
            try:
                if not file_path.endswith('.clk'):
                    file_path += '.clk'
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.recorded_actions, f)
                
                self.current_file_path = file_path
                file_name = os.path.basename(file_path)
                self.action_count.setText(f"{self.translations['file']} {file_name} ({len(self.recorded_actions)} {self.translations['actions_recorded']})")
                status_msg = f"{self.translations.get('status_saved', self.translations['status_saved'])} {file_path}"
                self.statusBar.showMessage(status_msg)
                logger.info(f"Recording saved successfully to {file_path}")
            except Exception as e:
                error_msg = f"{self.translations.get('save_error', self.translations['save_error'])} {str(e)}"
                self.statusBar.showMessage(error_msg)
                logger.error(f"Error saving recording to {file_path}: {e}", exc_info=True)
    
    def load_recording(self):
        logger.info("Load recording called.")
        dialog_title = self.translations.get('file_dialog_load', self.translations['file_dialog_load'])
        dialog_filter = self.translations.get('file_dialog_filter', self.translations['file_dialog_filter'])
        file_path, _ = QFileDialog.getOpenFileName(self, dialog_title, "", dialog_filter)
        
        if file_path:
            logger.info(f"Attempting to load recording from: {file_path}")
            # Загрузка происходит синхронно, интерфейс может подвиснуть на больших файлах
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    actions = json.load(f)
                if isinstance(actions, list): # Простая проверка, что это похоже на список действий
                    self.recorded_actions = actions
                    self.current_file_path = file_path
                    self.actions_list_widget.clear() # Clear previous items
                    for act in self.recorded_actions:
                        self.actions_list_widget.addItem(self._format_action_for_display(act))
                    logger.info(f"Recording loaded successfully from {file_path}. Actions: {len(self.recorded_actions)}")
                        # Обновляем интерфейс ПОСЛЕ успешной загрузки
                    self.updateUIState()
                        # self.action_count.setText(...) # Обновится через update_status
                        # self.statusBar.showMessage(...) # Обновится через update_status
                else:
                    error_msg = self.translations.get('file_not_valid', self.translations['file_not_valid'])
                    logger.error(f"Failed to load {file_path}: {error_msg}")
                    raise ValueError(error_msg)
            except Exception as e:
                load_error_title = self.translations['load_error']
                load_error_text = self.translations.get('load_file_error', self.translations['load_file_error']).format(error=str(e))
                logger.error(f"Error loading recording from {file_path}: {e}", exc_info=True)
                QMessageBox.warning(self, load_error_title, load_error_text)
                self.statusBar.showMessage(f"{self.translations.get('load_error', self.translations['load_error'])} {e}")
            # Сбрасываем состояние, если загрузка не удалась
            # self.recorded_actions = [] # Не очищаем, если была предыдущая запись
            # self.current_file_path = None
                self.updateUIState() # Ensure UI is updated even on failure
    
    def show_help(self):
        logger.info("Showing help dialog.")
        help_title = self.translations.get('help_dialog_title', self.translations['help_dialog_title'])
        help_text_key = self.translations.get('help_text', self.translations['help_text']) 
        help_text_content = f"{help_title}\n\n{help_text_key}" # Ensure title is part of the content for QMessageBox
        QMessageBox.information(self, help_title, help_text_content)

    def updateUIState(self):
        """Обновляет состояние кнопок и настроек в зависимости от состояния приложения"""
        logger.debug(f"Updating UI state: recording={self.recording}, playing={self.playing}, actions_count={len(self.recorded_actions)}, list_selection={self.actions_list_widget.currentRow()}")
        is_idle = not self.recording and not self.playing
        can_play = is_idle and bool(self.recorded_actions)
        action_selected = self.actions_list_widget.currentRow() >= 0
        
        # Кнопки записи
        self.record_button.setEnabled(is_idle)
        self.stop_record_button.setEnabled(self.recording)
        
        # Кнопки воспроизведения
        self.play_button.setEnabled(can_play)
        self.stop_play_button.setEnabled(self.playing)
        
        # Кнопка Language всегда активна
        self.repeat_button.setEnabled(True)
        
        # Кнопки сохранения/загрузки
        self.save_button.setEnabled(is_idle and bool(self.recorded_actions))
        self.load_button.setEnabled(is_idle)

        # Кнопка удаления действия
        self.delete_action_button.setEnabled(is_idle and action_selected and bool(self.recorded_actions))
        
        # Настройки - блокируем только интерактивные виджеты из списка
        # self.actions_list_widget is in settings_widgets, so it's disabled during record/play
        for widget in self.settings_widgets:
            widget.setEnabled(is_idle)
            
        # Стили активных кнопок (если нужно)
        # Можно добавить сюда изменение стилей для record_button/play_button, если они активны
        # Например, изменить текст или фон
        if self.recording:
             self.record_button.setStyleSheet(f"QPushButton {{ {STYLE_BUTTON_ACTIVE.format(active_color='#009900')} }}")
             self.record_button.setText(self.translations['recording'])
        else:
             self.record_button.setStyleSheet(
                 f"QPushButton {{ {STYLE_BUTTON_NORMAL.format(bg_color='#00CC00')} }}"
                 f"QPushButton:pressed {{ {STYLE_BUTTON_PRESSED.format(press_color='#009900')} }}"
                 f"QPushButton:disabled {{ {STYLE_BUTTON_DISABLED} }}"
             )
             self.record_button.setText(self.translations['start_record'])

        if self.playing:
             self.play_button.setStyleSheet(f"QPushButton {{ {STYLE_BUTTON_ACTIVE.format(active_color='#004C99')} }}")
             self.play_button.setText(self.translations['playing'])
        else:
             self.play_button.setStyleSheet(
                 f"QPushButton {{ {STYLE_BUTTON_NORMAL.format(bg_color='#0066CC')} }}"
                 f"QPushButton:pressed {{ {STYLE_BUTTON_PRESSED.format(press_color='#004C99')} }}"
                 f"QPushButton:disabled {{ {STYLE_BUTTON_DISABLED} }}"
             )
             self.play_button.setText(self.translations['play'])

        # Дополнительная логика для чекбокса и счетчика повторов
        # Чекбокс "Бесконечные" активен только если выбран режим "Run every"
        self.infinite_repeat_checkbox.setEnabled(is_idle and self.interval_radio.isChecked())
        # Если чекбокс не активен, снимаем галку
        if not self.infinite_repeat_checkbox.isEnabled(): # This check might be redundant if is_idle is false
            self.infinite_repeat_checkbox.setChecked(False)
            
        # Счетчик повторов активен если:
        # 1. Режим "Run once" или "Run at"
        # 2. Режим "Run every" И НЕ выбран чекбокс "Бесконечные"
        repeats_enabled = is_idle and (
            self.once_radio.isChecked() or \
            self.time_radio.isChecked() or \
            (self.interval_radio.isChecked() and not self.infinite_repeat_checkbox.isChecked())
        )
        self.repeat_count.setEnabled(repeats_enabled)
        self.repeat_label.setEnabled(repeats_enabled) # Также активируем/деактивируем метку

    def update_status(self):
        """Обновляет строку состояния и счетчик действий"""
        if self.recording:
            self.statusBar.showMessage(f"{self.translations['recording']} ({len(self.recorded_actions)})")
            # Обновляем счетчик действий только во время записи
            self.action_count.setText(f"{self.translations['actions_recorded']} {len(self.recorded_actions)}")
        elif self.playing:
            current_time = self.player.get_current_playback_time()
            total_time = self.player.get_total_playback_time()
            if total_time > 0:
                 progress = int((current_time / total_time) * 100)
                 self.statusBar.showMessage(f"{self.translations['playing']} ({progress}%)")
            else:
                 self.statusBar.showMessage(self.translations['playing'])
        else:
            self.statusBar.showMessage("") # <--- Убрано 'Ready'
            # Обновляем счетчик действий, если не записываем и не воспроизводим
            file_info = f" ({os.path.basename(self.current_file_path)})" if self.current_file_path else ""
            self.action_count.setText(f"{self.translations['actions_recorded']} {len(self.recorded_actions)}{file_info}")

    def closeEvent(self, event):
        logger.info("Close event triggered.")
        self.save_settings() # Сохраняем настройки перед выходом
        self.gui_update_timer.stop()
        # if self.is_recording: # AttributeError: 'MainWindow' object has no attribute 'is_recording'
        #     self.stop_recording()
        if self.recording: # Check recording attribute instead
            logger.info("Stopping recording due to close event.")
            self.stop_recording()
        
        exit_title = self.translations.get('exit', self.translations['exit'])
        exit_confirm_msg = self.translations.get('close_confirm', self.translations['close_confirm'])
        reply = QMessageBox.question(self, exit_title, exit_confirm_msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            logger.info("User confirmed exit. Accepting close event.")
            event.accept()
        else:
            logger.info("User cancelled exit. Ignoring close event.")
            event.ignore()

    def set_language(self, lang_code):
        if lang_code in LANGUAGES:  # Check against LANGUAGES, not the removed TRANSLATIONS
            self.current_language = lang_code
            logger.info(f"Setting language to: {lang_code}")
            self.translations = load_translations(self.current_language)
            # Обновляем тексты и сохраняем настройки ПОСЛЕ установки языка
            self.updateUITexts()
            self.save_settings() # Сохраняем язык после смены
        else:
            logger.warning(f"Language code \'{lang_code}\' not found in LANGUAGES.")

    def updateUITexts(self):
        """Обновляет тексты всех виджетов в соответствии с текущим языком"""
        logger.debug("Updating UI texts for current language.")
        self.setWindowTitle(self.translations['app_title'])
        self.record_button.setText(self.translations['start_record'])
        self.stop_record_button.setText(self.translations['stop_record'])
        self.play_button.setText(self.translations['play'])
        self.stop_play_button.setText(self.translations['stop_play'])
        self.repeat_button.setText(self.translations['language'])
        self.save_button.setText(self.translations['save'])
        self.load_button.setText(self.translations['load'])
        self.help_button.setText(self.translations['help'])
        self.action_count.setText(f"{self.translations['actions_recorded']} {len(self.recorded_actions)}")
        self.repeat_label.setText(self.translations['repeat_count'])
        self.schedule_label.setText(self.translations['schedule'])
        self.once_radio.setText(self.translations['once'])
        self.interval_radio.setText(self.translations['interval'])
        self.interval_label.setText(self.translations['seconds']) # <-- Обновлено на seconds
        self.time_radio.setText(self.translations['at_time'])
        self.speed_label.setText(self.translations['speed'])
        
        # Update new UI elements
        self.actions_list_label.setText(self.translations.get("recorded_actions_label", "Recorded Actions:"))
        self.delete_action_button.setText(self.translations.get("delete_selected_action_button", "Delete Selected Action"))

        # Обновляем строку состояния, если она не показывает прогресс
        if self.playing:
            self.statusBar.showMessage(f"{self.translations['playing']} ({self.player.get_current_playback_time() // 1000} сек / {self.player.get_total_playback_time() // 1000} сек)")
        else:
            # Show 'Ready' or other relevant status if not playing/recording
            if not self.recording:
                 self.statusBar.showMessage(self.translations.get('status_ready', "Ready"))

        # Обновляем текст чекбокса
        self.infinite_repeat_checkbox.setText(self.translations.get('infinite_repeats', self.translations['infinite_repeats'])) # Fallback to self.translations
    
    def _format_action_for_display(self, action):
        """Formats an action dictionary into a human-readable string for the QListWidget."""
        action_type = action.get('type', 'unknown')
        timestamp = action.get('timestamp', 0) # Timestamp from action, not live time.time()

        if action_type == 'mouse_move':
            return f"Mouse Move: ({action.get('x')}, {action.get('y')}) @ {timestamp:.2f}s"
        elif action_type == 'mouse_click':
            state = "Press" if action.get('pressed', False) else "Release"
            button = action.get('button', 'N/A').replace("Button.", "")
            return f"{state} {button}: ({action.get('x')}, {action.get('y')}) @ {timestamp:.2f}s"
        elif action_type == 'mouse_scroll':
            return f"Mouse Scroll: (dx={action.get('dx')}, dy={action.get('dy')}) at ({action.get('x')}, {action.get('y')}) @ {timestamp:.2f}s"
        elif action_type == 'key_press':
            return f"Press Key: '{action.get('key', 'N/A')}' @ {timestamp:.2f}s"
        elif action_type == 'key_release':
            return f"Release Key: '{action.get('key', 'N/A')}' @ {timestamp:.2f}s"
        # Fallback for older action types from previous recorder.py versions if any
        elif action_type == 'click': # From one of the old recorder.py versions
            button = action.get('button', 'N/A').replace("Button.", "")
            return f"Click {button}: ({action.get('x')}, {action.get('y')}) @ {timestamp:.2f}s"
        elif action_type == 'scroll': # From one of the old recorder.py versions
            return f"Scroll: (dx={action.get('dx')}, dy={action.get('dy')}) @ {timestamp:.2f}s"
        elif action_type == 'keypress': # From one of the old recorder.py versions
            return f"KeyPress: '{action.get('key', 'N/A')}' @ {timestamp:.2f}s"
        else:
            return f"Unknown action: {action} @ {timestamp:.2f}s"

    def delete_selected_action(self):
        current_row = self.actions_list_widget.currentRow()
        if current_row >= 0 and current_row < len(self.recorded_actions):
            logger.info(f"Deleting action at index {current_row}")
            del self.recorded_actions[current_row]
            self.actions_list_widget.takeItem(current_row)
            
            # Update status bar
            deleted_msg = self.translations.get('action_deleted_status', "Action deleted.")
            self.statusBar.showMessage(deleted_msg)
            logger.info(deleted_msg)

            self.updateUIState() # Update button states (e.g., save button if list becomes empty)
        else:
            logger.warning("Delete action called but no item selected or index out of bounds.")
            
    def show_language_dialog(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QComboBox, QPushButton, QLabel
        dialog = QDialog(self)
        dialog.setWindowTitle(self.translations['language'])
        layout = QVBoxLayout()
        label = QLabel(self.translations['language'])
        layout.addWidget(label)
        combo = QComboBox()
        for code, name in LANGUAGES.items():
            combo.addItem(name, code)
        combo.setCurrentText(LANGUAGES.get(self.current_language, 'English'))
        layout.addWidget(combo)
        ok_btn = QPushButton('OK')
        layout.addWidget(ok_btn)
        dialog.setLayout(layout)
        def on_ok():
            selected_code = combo.currentData()
            self.set_language(selected_code)
            dialog.accept()
        ok_btn.clicked.connect(on_ok)
        dialog.exec_()
        
    # --- Сохранение/Загрузка Настроек --- 
    
    @property
    def config_file(self):
        # Определяем базовый путь в зависимости от того, запущено ли как скрипт или .exe
        if getattr(sys, 'frozen', False):
            # Запущено как .exe (PyInstaller)
            base_path = os.path.dirname(sys.executable)
        else:
            # Запущено как .py скрипт
            try:
                 base_path = os.path.dirname(os.path.abspath(__file__))
            except NameError:
                 # Резервный вариант для интерактивных сессий
                 base_path = os.getcwd()
        return os.path.join(base_path, "config.json")

    def save_settings(self):
        settings = {
            'language': self.current_language,
            'playback_speed': self.speed_slider.value(),
            'repeat_count': self.repeat_count.value(),
            'infinite_repeat': self.infinite_repeat_checkbox.isChecked()
        }

        if self.once_radio.isChecked():
            settings['schedule_type'] = 'once'
        elif self.interval_radio.isChecked():
            settings['schedule_type'] = 'interval'
            settings['schedule_interval_value'] = self.interval_value.value()
        elif self.time_radio.isChecked():
            settings['schedule_type'] = 'time'
            settings['schedule_time_value'] = self.time_value.time().toString("HH:mm")

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
            logger.info(f"Settings saved to {self.config_file}")
        except IOError as e:
            logger.error(f"Error saving settings to {self.config_file}: {e}", exc_info=True)

    def load_settings(self):
        logger.info(f"Attempting to load settings from {self.config_file}")
        # Default language setting (will be overridden if config file exists and is valid)
        current_lang_code = detect_system_language() # Start with system language
        logger.debug(f"Detected system language: {current_lang_code}")

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                logger.info(f"Successfully loaded settings from {self.config_file}")
                    
                    # Load language first
                lang_code_from_config = settings.get('language')
                if lang_code_from_config and lang_code_from_config in LANGUAGES:
                    logger.debug(f"Language code from config: {lang_code_from_config}")
                    current_lang_code = lang_code_from_config
                else:
                    logger.warning(f"Invalid or missing language code in {self.config_file}, using detected system language '{current_lang_code}'.")
                    
                    # Apply language (this also loads translations)
                self.set_language(current_lang_code) # set_language handles calling load_translations

                    # Load other settings with defaults
                logger.debug("Loading other settings...")
                    self.speed_slider.setValue(settings.get('playback_speed', 100))
                    self.update_speed_label(self.speed_slider.value()) # Update label for speed

                    self.repeat_count.setValue(settings.get('repeat_count', 1))
                    self.infinite_repeat_checkbox.setChecked(settings.get('infinite_repeat', False))

                    schedule_type = settings.get('schedule_type', 'once')
                    if schedule_type == 'interval':
                        self.interval_radio.setChecked(True)
                        self.interval_value.setValue(settings.get('schedule_interval_value', 5))
                    elif schedule_type == 'time':
                        self.time_radio.setChecked(True)
                        time_str = settings.get('schedule_time_value')
                        if time_str:
                            self.time_value.setTime(QTime.fromString(time_str, "HH:mm"))
                        else:
                            self.time_value.setTime(QTime.currentTime().addSecs(300)) # Default if missing
                            logger.debug(f"Schedule time set to default: {self.time_value.time().toString('HH:mm')}")
                    else: # 'once' or default
                        self.once_radio.setChecked(True)
                        logger.debug("Schedule type set to 'once'.")
                logger.info("Finished loading settings from file.")


            except (IOError, json.JSONDecodeError) as e:
                logger.error(f"Error loading settings from {self.config_file}: {e}. Applying defaults.", exc_info=True)
                # Apply default language if file loading failed
                self.set_language(current_lang_code) 
                # Apply default values for other settings
                logger.debug("Applying default values for all settings due to error.")
                self.speed_slider.setValue(100)
                self.update_speed_label(100)
                self.repeat_count.setValue(1)
                self.infinite_repeat_checkbox.setChecked(False)
                self.once_radio.setChecked(True)
                self.interval_value.setValue(5)
                self.time_value.setTime(QTime.currentTime().addSecs(300))
        else:
            # Config file does not exist, apply system/default language and other defaults
            logger.info("Config file not found. Applying system/default language and default settings.")
            self.set_language(current_lang_code) # Apply detected/default language
            self.speed_slider.setValue(100)
            self.update_speed_label(100)
            logger.debug("Playback speed set to default: 100")
            self.repeat_count.setValue(1)
            self.infinite_repeat_checkbox.setChecked(False)
            self.once_radio.setChecked(True)
            self.interval_value.setValue(5)
            self.time_value.setTime(QTime.currentTime().addSecs(300))

        self.updateUIState() # Update UI based on loaded settings
        logger.info("Finished load_settings method.")


def load_translations(lang_code):
    """Loads translations from a JSON file for the given language code."""
    logger.debug(f"Attempting to load translations for language code: {lang_code}")
    base_translations_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "translations", "en.json")
    translations_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "translations", f"{lang_code}.json")

    # Always load English translations first as a base
    try:
        with open(base_translations_path, 'r', encoding='utf-8') as f:
            translations = json.load(f)
        logger.debug(f"Successfully loaded base English translations from {base_translations_path}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.critical(f"Could not load base English translations from {base_translations_path}: {e}", exc_info=True)
        # In a real application, you might want to exit or use hardcoded minimal English strings
        return {} 

    if lang_code == 'en':
        logger.debug("Language code is 'en', returning base English translations.")
        return translations # Already loaded English

    try:
        with open(translations_path, 'r', encoding='utf-8') as f:
            specific_translations = json.load(f)
            translations.update(specific_translations) # Override English with specific language translations
            logger.info(f"Successfully loaded and merged translations for '{lang_code}' from {translations_path}")
    except FileNotFoundError:
        logger.warning(f"Translation file for '{lang_code}' not found at {translations_path}. Falling back to English.")
        # English translations are already loaded, so nothing more to do
    except json.JSONDecodeError as e:
        logger.warning(f"Could not decode translation file for '{lang_code}' from {translations_path}: {e}. Falling back to English.", exc_info=True)
        # English translations are already loaded
    return translations

def main():
    logger.info("Application starting.")
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Современный стиль интерфейса
    
    # Ускорение загрузки за счет отложенной инициализации
    app.setQuitOnLastWindowClosed(True)
    
    # Создаем MainWindow
    window = MainWindow()
    
    # Хотя плеер наследуется от QObject, его можно переместить в главный поток 
    # для более явного управления жизненным циклом (опционально, но иногда помогает)
    # window.player.moveToThread(app.thread()) 
    
    window.show()
    logger.info("Application event loop started.")
    exit_code = app.exec_()
    logger.info(f"Application exiting with code {exit_code}.")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()