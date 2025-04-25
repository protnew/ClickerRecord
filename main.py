import sys
import json
import time
import os
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

# Базовый английский словарь с полным набором ключей
BASE_TRANSLATIONS = {
    'app_title': 'ClickerRecord',
        'start_record': 'Start Recording',
        'stop_record': 'Stop Recording',
        'play': 'Play',
        'stop_play': 'Stop Playback',
        'repeat': 'Repeat Last',
        'save': 'Save Recording',
        'load': 'Load Recording',
        'help': 'Help',
        'settings': 'Settings',
        'language': 'Language',
        'actions_recorded': 'Actions recorded:',
        'file': 'File:',
        'ready': 'Ready',
        'recording': 'Recording...',
        'infinite_repeats': 'Infinite Repeats', # 
        'playing': 'Playing...',
        'no_actions': 'No actions recorded to play.',
        'error': 'Error',
        'repeat_count': 'Repeat count:',
        'schedule': 'Schedule:',
        'once': 'Run once',
        'interval': 'Run every',
        'minutes': 'minutes',
        'seconds': 'seconds', # 
        'at_time': 'Run at',
        'speed': 'Playback speed:',
    'help_title': 'Help - ClickerRecord',
    'help_text': 'ClickerRecord - Help\n\nMain features:\n- Record mouse and keyboard actions.\n- Playback recorded actions.\n- Set repeat count, speed, and schedule.\n- Save and load recordings.\n\nHotkeys:\nF6: Start/Stop recording\nF7: Play\nF8: Repeat last\nEsc: Stop playback\nCtrl+S: Save\nCtrl+O: Load',
        'no_actions_warning': 'No recorded actions to play.',
        'no_actions_to_repeat': 'No recorded actions to repeat.',
        'recording_error_title': 'Recording Error',
        'recording_error_text': 'Failed to start recording: {error}',
        'playback_error_title': 'Playback Error',
        'playback_error_text': 'Failed to start playback: {error}',
        'playback_type_error': 'Argument mismatch when calling Player.play:\n{error}\n\nInterface and player may be out of sync.',
        'playback_stop_error': 'Error while stopping playback.',
        'playback_stopped': 'Playback stopped...',
        'save_error': 'Error saving:',
        'load_error': 'Error loading:',
        'load_file_error': 'Failed to load file:\n{error}',
        'file_not_valid': 'File does not contain a valid list of actions.',
    'help_dialog_title': 'Help - ClickerRecord',
        'close_confirm': 'Are you sure you want to exit?',
        'status_ready': 'Ready',
        'status_recording': 'Recording... ({count})',
        'status_playing': 'Playing... ({progress}%)',
        'status_playing_simple': 'Playing...',
        'status_no_actions': 'No actions recorded',
        'status_saved': 'Recording saved:',
        'status_loaded': 'Recording loaded:',
        'status_error': 'Error:',
        'status_stopped': 'Stopped',
        'status_file': 'File:',
        'status_actions': 'Actions:',
        'dialog_ok': 'OK',
        'dialog_cancel': 'Cancel',
        'dialog_yes': 'Yes',
        'dialog_no': 'No',
        'repeat_last': 'Repeat last',
        'repeat_last_warning': 'Cannot repeat: no actions.',
        'repeat_last_busy': 'Cannot repeat: recording or playback in progress.',
        'save_success': 'Recording saved successfully.',
        'load_success': 'Recording loaded successfully.',
        'file_dialog_save': 'Save recording',
        'file_dialog_load': 'Load recording',
        'file_dialog_filter': 'Clicker files (*.clk);;All files (*)',
        'exit': 'Exit',
        'settings_title': 'Settings',
        'about': 'About',
    'about_text': 'ClickerRecord\nMulti-language mouse and keyboard recorder.\n© 2025',
}

TRANSLATIONS = {
    'en': BASE_TRANSLATIONS,
    'ru': {
        'app_title': 'ClickerRecord',
        'start_record': 'Начать запись',
        'stop_record': 'Остановить запись',
        'play': 'Воспроизвести',
        'stop_play': 'Остановить воспроизведение',
        'repeat': 'Повторить последнее',
        'save': 'Сохранить запись',
        'load': 'Загрузить запись',
        'help': 'Справка',
        'settings': 'Настройки',
        'language': 'Язык',
        'actions_recorded': 'Записано действий:',
        'file': 'Файл:',
        'ready': 'Готово',
        'recording': 'Запись...',
        'infinite_repeats': 'Бесконечные повторы', # <-- Добавлен перевод
        'playing': 'Воспроизведение...',
        'no_actions': 'Нет записанных действий для воспроизведения.',
        'error': 'Ошибка',
        'repeat_count': 'Количество повторений:',
        'schedule': 'Расписание:',
        'once': 'Запустить один раз',
        'interval': 'Запускать каждые',
        'minutes': 'минут',
        'seconds': 'секунд', # <-- Добавлен перевод
        'at_time': 'Запускать в',
        'speed': 'Скорость воспроизведения:',
        'help_title': 'Справка - ClickerRecord',
        'help_text': 'ClickerRecord - Справка\n\nОсновные функции:\n- Запись действий мыши и клавиатуры.\n- Воспроизведение записанных действий.\n- Настройка количества повторений, скорости и расписания.\n- Сохранение и загрузка записей.\n\nГорячие клавиши:\nF6: Начать/Остановить запись\nF7: Воспроизвести\nF8: Повторить последнее\nEsc: Остановить воспроизведение\nCtrl+S: Сохранить\nCtrl+O: Загрузить',
        'no_actions_warning': 'Нет записанных действий для воспроизведения.',
        'no_actions_to_repeat': 'Нет записанных действий для повтора.',
        'recording_error_title': 'Ошибка записи',
        'recording_error_text': 'Не удалось начать запись: {error}',
        'playback_error_title': 'Ошибка воспроизведения',
        'playback_error_text': 'Не удалось начать воспроизведение: {error}',
        'playback_type_error': 'Несоответствие аргументов при вызове Player.play:\n{error}\n\nИнтерфейс и плеер могут быть рассинхронизированы.',
        'playback_stop_error': 'Ошибка при остановке воспроизведения.',
        'playback_stopped': 'Воспроизведение остановлено...',
        'save_error': 'Ошибка сохранения:',
        'load_error': 'Ошибка загрузки:',
        'load_file_error': 'Не удалось загрузить файл:\n{error}',
        'file_not_valid': 'Файл не содержит корректный список действий.',
        'help_dialog_title': 'Справка - ClickerRecord',
        'close_confirm': 'Вы уверены, что хотите выйти?',
        'status_ready': 'Готово',
        'status_recording': 'Запись... ({count})',
        'status_playing': 'Воспроизведение... ({progress}%)',
        'status_playing_simple': 'Воспроизведение...',
        'status_no_actions': 'Нет записанных действий',
        'status_saved': 'Запись сохранена:',
        'status_loaded': 'Запись загружена:',
        'status_error': 'Ошибка:',
        'status_stopped': 'Остановлено',
        'status_file': 'Файл:',
        'status_actions': 'Действия:',
        'dialog_ok': 'OK',
        'dialog_cancel': 'Отмена',
        'dialog_yes': 'Да',
        'dialog_no': 'Нет',
        'repeat_last': 'Повторить последнее',
        'repeat_last_warning': 'Невозможно повторить: нет действий.',
        'repeat_last_busy': 'Невозможно повторить: идет запись или воспроизведение.',
        'save_success': 'Запись успешно сохранена.',
        'load_success': 'Запись успешно загружена.',
        'file_dialog_save': 'Сохранить запись',
        'file_dialog_load': 'Загрузить запись',
        'file_dialog_filter': 'Файлы кликера (*.clk);;Все файлы (*)',
        'exit': 'Выход',
        'settings_title': 'Настройки',
        'about': 'О программе',
        'about_text': 'ClickerRecord\\nМногоязычный регистратор действий мыши и клавиатуры.\\n© 2025',
    },
    'zh': dict(BASE_TRANSLATIONS, **{
        'app_title': 'ClickerRecord',
        'start_record': '开始录制',
        'stop_record': '停止录制',
        'play': '播放',
        'stop_play': '停止播放',
        'repeat': '重复上一次',
        'save': '保存录制',
        'load': '加载录制',
        'help': '帮助',
        'language': '语言',
    }),
    'es': dict(BASE_TRANSLATIONS, **{
        'app_title': 'ClickerRecord',
        'start_record': 'Iniciar grabación',
        'stop_record': 'Detener grabación',
        'play': 'Reproducir',
        'stop_play': 'Detener reproducción',
        'repeat': 'Repetir último',
        'save': 'Guardar grabación',
        'load': 'Cargar grabación',
        'help': 'Ayuda',
        'language': 'Idioma',
    }),
    'fr': dict(BASE_TRANSLATIONS, **{
        'app_title': 'ClickerRecord',
        'start_record': 'Démarrer l\'enregistrement',
        'stop_record': 'Arrêter l\'enregistrement',
        'play': 'Lire',
        'stop_play': 'Arrêter la lecture',
        'repeat': 'Répéter le dernier',
        'save': 'Enregistrer',
        'load': 'Charger',
        'help': 'Aide',
        'language': 'Langue',
    }),
    'de': dict(BASE_TRANSLATIONS, **{
        'app_title': 'ClickerRecord',
        'start_record': 'Aufnahme starten',
        'stop_record': 'Aufnahme stoppen',
        'play': 'Abspielen',
        'stop_play': 'Wiedergabe stoppen',
        'repeat': 'Letztes wiederholen',
        'save': 'Aufnahme speichern',
        'load': 'Aufnahme laden',
        'help': 'Hilfe',
        'settings': 'Einstellungen',
        'language': 'Sprache',
        'actions_recorded': 'Aktionen aufgezeichnet:',
        'file': 'Datei:',
        'ready': 'Bereit',
        'recording': 'Aufnahme...',
        'infinite_repeats': 'Unendliche Wiederholungen', # <-- Добавлен перевод
        'playing': 'Wiedergabe...',
        'no_actions': 'Keine Aktionen zum Abspielen aufgezeichnet.',
        'error': 'Fehler',
        'repeat_count': 'Wiederholungen:',
        'schedule': 'Zeitplan:',
        'once': 'Einmal ausführen',
        'interval': 'Alle',
        'minutes': 'Minuten ausführen',
        'seconds': 'Sekunden ausführen', # <-- Добавлен перевод
        'at_time': 'Ausführen um',
        'speed': 'Wiedergabegeschwindigkeit:',
        'help_title': 'Hilfe - ClickerRecord',
        'help_text': 'ClickerRecord - Hilfe\n\nHauptfunktionen:\n- Maus- und Tastaturaktionen aufzeichnen.\n- Aufgezeichnete Aktionen abspielen.\n- Wiederholungen, Geschwindigkeit und Zeitplan einstellen.\n- Aufnahmen speichern und laden.\n\nTastenkombinationen:\nF6: Aufnahme starten/stoppen\nF7: Abspielen\nF8: Letztes wiederholen\nEsc: Wiedergabe stoppen\nStrg+S: Speichern\nStrg+O: Laden',
        'no_actions_warning': 'Keine Aktionen zum Abspielen.',
        'no_actions_to_repeat': 'Keine Aktionen zum Wiederholen.',
        'recording_error_title': 'Aufnahmefehler',
        'recording_error_text': 'Aufnahme konnte nicht gestartet werden: {error}',
        'playback_error_title': 'Wiedergabefehler',
        'playback_error_text': 'Wiedergabe konnte nicht gestartet werden: {error}',
        'save_error': 'Fehler beim Speichern:',
        'load_error': 'Fehler beim Laden:',
        'close_confirm': 'Möchten Sie wirklich beenden?',
        'status_ready': 'Bereit',
        'status_recording': 'Aufnahme... ({count})',
        'status_playing': 'Wiedergabe... ({progress}%)',
        'status_playing_simple': 'Wiedergabe...',
        'status_no_actions': 'Keine Aktionen aufgezeichnet',
        'dialog_ok': 'OK',
        'dialog_cancel': 'Abbrechen',
        'dialog_yes': 'Ja',
        'dialog_no': 'Nein',
        'exit': 'Beenden',
        'about': 'Über',
        'about_text': 'ClickerRecord\\nMehrsprachiger Maus- und Tastaturrekorder.\\n© 2025'
    }),
    'it': dict(BASE_TRANSLATIONS, **{
        'app_title': 'ClickerRecord',
        'start_record': 'Avvia registrazione',
        'stop_record': 'Ferma registrazione',
        'play': 'Riproduci',
        'stop_play': 'Ferma riproduzione',
        'repeat': 'Ripeti ultimo',
        'save': 'Salva registrazione',
        'load': 'Carica registrazione',
        'help': 'Aiuto',
        'settings': 'Impostazioni',
        'language': 'Lingua',
        'actions_recorded': 'Azioni registrate:',
        'file': 'File:',
        'ready': 'Pronto',
        'recording': 'Registrazione...',
        'infinite_repeats': 'Ripetizioni infinite', # <-- Добавлен перевод
        'playing': 'Riproduzione...',
        'no_actions': 'Nessuna azione registrata da riprodurre.',
        'error': 'Errore',
        'repeat_count': 'Numero di ripetizioni:',
        'schedule': 'Programmazione:',
        'once': 'Esegui una volta',
        'interval': 'Esegui ogni',
        'minutes': 'minuti',
        'seconds': 'secondi', # <-- Добавлен перевод
        'at_time': 'Esegui alle',
        'speed': 'Velocità di riproduzione:',
        'help_title': 'Aiuto - ClickerRecord',
        'help_text': 'ClickerRecord - Aiuto\n\nFunzionalità principali:\n- Registra azioni del mouse e della tastiera.\n- Riproduci azioni registrate.\n- Imposta ripetizioni, velocità e programmazione.\n- Salva e carica registrazioni.\n\nScorciatoie:\nF6: Avvia/Ferma registrazione\nF7: Riproduci\nF8: Ripeti ultimo\nEsc: Ferma riproduzione\nCtrl+S: Salva\nCtrl+O: Carica',
        'no_actions_warning': 'Nessuna azione da riprodurre.',
        'no_actions_to_repeat': 'Nessuna azione da ripetere.',
        'recording_error_title': 'Errore di registrazione',
        'recording_error_text': 'Impossibile avviare la registrazione: {error}',
        'playback_error_title': 'Errore di riproduzione',
        'playback_error_text': 'Impossibile avviare la riproduzione: {error}',
        'save_error': 'Errore di salvataggio:',
        'load_error': 'Errore di caricamento:',
        'close_confirm': 'Sei sicuro di voler uscire?',
        'status_ready': 'Pronto',
        'status_recording': 'Registrazione... ({count})',
        'status_playing': 'Riproduzione... ({progress}%)',
        'status_playing_simple': 'Riproduzione...',
        'status_no_actions': 'Nessuna azione registrata',
        'dialog_ok': 'OK',
        'dialog_cancel': 'Annulla',
        'dialog_yes': 'Sì',
        'dialog_no': 'No',
        'exit': 'Esci',
        'about': 'Informazioni',
        'about_text': 'ClickerRecord\\nRegistratore mouse e tastiera multilingua.\\n© 2025'
    }),
    'ja': dict(BASE_TRANSLATIONS, **{
        'app_title': 'ClickerRecord',
        'start_record': '記録開始',
        'stop_record': '記録停止',
        'play': '再生',
        'stop_play': '再生停止',
        'repeat': '最後を繰り返す',
        'save': '記録を保存',
        'load': '記録を読込',
        'help': 'ヘルプ',
        'settings': '設定',
        'language': '言語',
        'actions_recorded': '記録されたアクション：',
        'file': 'ファイル：',
        'ready': '準備完了',
        'recording': '記録中...',
        'infinite_repeats': '無限繰り返し', # <-- Добавлен перевод
        'playing': '再生中...',
        'no_actions': '再生する記録がありません。',
        'error': 'エラー',
        'repeat_count': '繰り返し回数：',
        'schedule': 'スケジュール：',
        'once': '1回実行',
        'interval': '毎',
        'minutes': '分実行',
        'seconds': '秒実行', # <-- Добавлен перевод
        'at_time': '指定時刻に実行',
        'speed': '再生速度：',
        'help_title': 'ヘルプ - ClickerRecord',
        'help_text': 'ClickerRecord - ヘルプ\n\n主な機能：\n- マウスとキーボードの操作を記録。\n- 記録した操作を再生。\n- 繰り返し回数、速度、スケジュールを設定。\n- 記録の保存と読込。\n\nホットキー：\nF6：記録開始/停止\nF7：再生\nF8：最後を繰り返す\nEsc：再生停止\nCtrl+S：保存\nCtrl+O：読込',
        'no_actions_warning': '再生する操作がありません。',
        'no_actions_to_repeat': '繰り返す操作がありません。',
        'recording_error_title': '記録エラー',
        'recording_error_text': '記録を開始できません：{error}',
        'playback_error_title': '再生エラー',
        'playback_error_text': '再生を開始できません：{error}',
        'save_error': '保存エラー：',
        'load_error': '読込エラー：',
        'close_confirm': '終了してもよろしいですか？',
        'status_ready': '準備完了',
        'status_recording': '記録中... ({count})',
        'status_playing': '再生中... ({progress}%)',
        'status_playing_simple': '再生中...',
        'status_no_actions': '記録された操作はありません',
        'dialog_ok': 'OK',
        'dialog_cancel': 'キャンセル',
        'dialog_yes': 'はい',
        'dialog_no': 'いいえ',
        'exit': '終了',
        'about': 'バージョン情報',
        'about_text': 'ClickerRecord\\n多言語対応マウス・キーボード記録ツール。\n© 2025'
    }),
    'tr': dict(BASE_TRANSLATIONS, **{
        'app_title': 'ClickerRecord',
        'start_record': 'Kayıt Başlat',
        'stop_record': 'Kaydı Durdur',
        'play': 'Oynat',
        'stop_play': 'Oynatmayı Durdur',
        'repeat': 'Son İşlemi Tekrarla',
        'save': 'Kaydı Kaydet',
        'load': 'Kayıt Yükle',
        'help': 'Yardım',
        'settings': 'Ayarlar',
        'language': 'Dil',
        'actions_recorded': 'Kaydedilen işlemler:',
        'file': 'Dosya:',
        'ready': 'Hazır',
        'recording': 'Kaydediyor...',
        'infinite_repeats': 'Sonsuz Tekrar', # <-- Добавлен перевод
        'playing': 'Oynatılıyor...',
        'no_actions': 'Oynatılacak kayıtlı işlem yok.',
        'error': 'Hata',
        'repeat_count': 'Tekrar sayısı:',
        'schedule': 'Zamanlama:',
        'once': 'Bir kez çalıştır',
        'interval': 'Her',
        'minutes': 'dakikada bir çalıştır',
        'seconds': 'sekund', # <-- Добавлен перевод
        'at_time': 'Uruchom o',
        'speed': 'Prędkość odtwarzania:',
        'help_title': 'Yardım - ClickerRecord',
        'help_text': 'ClickerRecord - Yardım\n\nTemel özellikler:\n- Fare ve klavye işlemlerini kaydet.\n- Kaydedilen işlemleri oynat.\n- Tekrar sayısı, hız ve zamanlama ayarla.\n- Kayıtları kaydet ve yükle.\n\nKısayollar:\nF6: Kaydı başlat/durdur\nF7: Oynat\nF8: Son işlemi tekrarla\nEsc: Oynatmayı durdur\nCtrl+S: Kaydet\nCtrl+O: Yükle',
        'no_actions_warning': 'Oynatılacak işlem yok.',
        'no_actions_to_repeat': 'Tekrarlanacak işlem yok.',
        'recording_error_title': 'Kayıt Hatası',
        'recording_error_text': 'Kayıt başlatılamadı: {error}',
        'playback_error_title': 'Oynatma Hatası',
        'playback_error_text': 'Oynatma başlatılamadı: {error}',
        'save_error': 'Kaydetme hatası:',
        'load_error': 'Yükleme hatası:',
        'close_confirm': 'Çıkmak istediğinizden emin misiniz?',
        'status_ready': 'Hazır',
        'status_recording': 'Kaydediyor... ({count})',
        'status_playing': 'Oynatılıyor... ({progress}%)',
        'status_playing_simple': 'Oynatılıyor...',
        'status_no_actions': 'Kayıtlı işlem yok',
        'dialog_ok': 'Tamam',
        'dialog_cancel': 'İptal',
        'dialog_yes': 'Evet',
        'dialog_no': 'Hayır',
        'exit': 'Çıkış',
        'about': 'Hakkında',
        'about_text': 'ClickerRecord\\nÇok dilli fare ve klavye kaydedici.\\n© 2025'
    }),
    'pl': dict(BASE_TRANSLATIONS, **{
        'app_title': 'ClickerRecord',
        'start_record': 'Rozpocznij nagrywanie',
        'stop_record': 'Zatrzymaj nagrywanie',
        'play': 'Odtwórz',
        'stop_play': 'Zatrzymaj odtwarzanie',
        'repeat': 'Powtórz ostatnie',
        'save': 'Zapisz nagranie',
        'load': 'Wczytaj nagranie',
        'help': 'Pomoc',
        'settings': 'Ustawienia',
        'language': 'Język',
        'actions_recorded': 'Zarejestrowane akcje:',
        'file': 'Plik:',
        'ready': 'Gotowy',
        'recording': 'Nagrywanie...',
        'infinite_repeats': 'Nieskończone powtórzenia', # <-- Добавлен перевод
        'playing': 'Odtwarzanie...',
        'no_actions': 'Brak nagranych akcji do odtworzenia.',
        'error': 'Błąd',
        'repeat_count': 'Liczba powtórzeń:',
        'schedule': 'Harmonogram:',
        'once': 'Uruchom raz',
        'interval': 'Uruchamiaj co',
        'minutes': 'minut',
        'seconds': 'sekund', # <-- Добавлен перевод
        'at_time': 'Uruchom o',
        'speed': 'Prędkość odtwarzania:',
        'help_title': 'Pomoc - ClickerRecord',
        'help_text': 'ClickerRecord - Pomoc\n\nGłówne funkcje:\n- Nagrywanie akcji myszy i klawiatury.\n- Odtwarzanie nagranych akcji.\n- Ustawianie powtórzeń, prędkości i harmonogramu.\n- Zapisywanie i wczytywanie nagrań.\n\nSkróty klawiszowe:\nF6: Rozpocznij/Zatrzymaj nagrywanie\nF7: Odtwórz\nF8: Powtórz ostatnie\nEsc: Zatrzymaj odtwarzanie\nCtrl+S: Zapisz\nCtrl+O: Wczytaj',
        'no_actions_warning': 'Brak akcji do odtworzenia.',
        'no_actions_to_repeat': 'Brak akcji do powtórzenia.',
        'recording_error_title': 'Błąd nagrywania',
        'recording_error_text': 'Nie można rozpocząć nagrywania: {error}',
        'playback_error_title': 'Błąd odtwarzania',
        'playback_error_text': 'Nie można rozpocząć odtwarzania: {error}',
        'save_error': 'Błąd zapisu:',
        'load_error': 'Błąd wczytywania:',
        'close_confirm': 'Czy na pewno chcesz wyjść?',
        'status_ready': 'Gotowy',
        'status_recording': 'Nagrywanie... ({count})',
        'status_playing': 'Odtwarzanie... ({progress}%)',
        'status_playing_simple': 'Odtwarzanie...',
        'status_no_actions': 'Brak nagranych akcji',
        'dialog_ok': 'OK',
        'dialog_cancel': 'Anuluj',
        'dialog_yes': 'Tak',
        'dialog_no': 'Nie',
        'exit': 'Wyjście',
        'about': 'O programie',
        'about_text': 'ClickerRecord\\nWielojęzyczny rejestrator myszy i klawiatury.\\n© 2025'
    }),
    'he': dict(BASE_TRANSLATIONS, **{
        'app_title': 'ClickerRecord',
        'start_record': 'התחל הקלטה',
        'stop_record': 'עצור הקלטה',
        'play': 'הפעל',
        'stop_play': 'עצור הפעלה',
        'repeat': 'חזור על אחרון',
        'save': 'שמור הקלטה',
        'load': 'טען הקלטה',
        'help': 'עזרה',
        'settings': 'הגדרות',
        'language': 'שפה',
        'actions_recorded': 'פעולות שהוקלטו:',
        'file': 'קובץ:',
        'ready': 'מוכן',
        'recording': 'מקליט...',
        'infinite_repeats': 'חזרות אינסופיות', # <-- Добавлен перевод
        'playing': 'מפעיל...',
        'no_actions': 'אין פעולות מוקלטות להפעלה.',
        'error': 'שגיאה',
        'repeat_count': 'מספר חזרות:',
        'schedule': 'תזמון:',
        'once': 'הפעל פעם אחת',
        'interval': 'הפעל כל',
        'minutes': 'דקות',
        'seconds': 'שניות', # <-- Добавлен перевод
        'at_time': 'הפעל בשעה',
        'speed': 'מהירות הפעלה:',
        'help_title': 'עזרה - ClickerRecord',
        'help_text': 'ClickerRecord - עזרה\n\nתכונות עיקריות:\n- הקלטת פעולות עכבר ומקלדת.\n- הפעלת פעולות מוקלטות.\n- הגדרת מספר חזרות, מהירות ותזמון.\n- שמירה וטעינה של הקלטות.\n\nקיצורי מקשים:\nF6: התחל/עצור הקלטה\nF7: הפעל\nF8: חזור על אחרון\nEsc: עצור הפעלה\nCtrl+S: שמור\nCtrl+O: טען',
        'no_actions_warning': 'אין פעולות מוקלטות להפעלה.',
        'no_actions_to_repeat': 'אין פעולות מוקלטות לחזרה.',
        'recording_error_title': 'שגיאת הקלטה',
        'recording_error_text': 'כשל בהתחלת ההקלטה: {error}',
        'playback_error_title': 'שגיאת הפעלה',
        'playback_error_text': 'כשל בהתחלת ההפעלה: {error}',
        'playback_type_error': 'חוסר התאמה בארגומנטים בקריאה ל-Player.play:\n{error}\n\nהממשק והנגן עלולים לא להיות מסונכרנים.',
        'playback_stop_error': 'שגיאה בעצירת ההפעלה.',
        'playback_stopped': 'ההפעלה הופסקה...',
        'save_error': 'שגיאה בשמירה:',
        'load_error': 'שגיאה בטעינה:',
        'load_file_error': 'כשל בטעינת הקובץ:\n{error}',
        'file_not_valid': 'הקובץ אינו מכיל רשימת פעולות תקינה.',
        'help_dialog_title': 'עזרה - ClickerRecord',
        'close_confirm': 'האם אתה בטוח שברצונך לצאת?',
        'status_ready': 'מוכן',
        'status_recording': 'מקליט... ({count})',
        'status_playing': 'מפעיל... ({progress}%)',
        'status_playing_simple': 'מפעיל...',
        'status_no_actions': 'אין פעולות מוקלטות',
        'status_saved': 'ההקלטה נשמרה:',
        'status_loaded': 'ההקלטה נטענה:',
        'status_error': 'שגיאה:',
        'status_stopped': 'נעצר',
        'status_file': 'קובץ:',
        'status_actions': 'פעולות:',
        'dialog_ok': 'אישור',
        'dialog_cancel': 'ביטול',
        'dialog_yes': 'כן',
        'dialog_no': 'לא',
        'repeat_last': 'חזור על אחרון',
        'repeat_last_warning': 'לא ניתן לחזור: אין פעולות.',
        'repeat_last_busy': 'לא ניתן לחזור: הקלטה או הפעלה בתהליך.',
        'save_success': 'ההקלטה נשמרה בהצלחה.',
        'load_success': 'ההקלטה נטענה בהצלחה.',
        'file_dialog_save': 'שמור הקלטה',
        'file_dialog_load': 'טען הקלטה',
        'file_dialog_filter': 'קבצי קליקר (*.clk);;כל הקבצים (*)',
        'exit': 'יציאה',
        'settings_title': 'הגדרות',
        'about': 'אודות',
        'about_text': 'ClickerRecord\\nמקליט עכבר ומקלדת רב-לשוני.\\n© 2025'
    })
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
        self.translations = TRANSLATIONS['en'] # Загружаем английские переводы
        
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
        self.load_settings() # Загружаем сохраненные настройки (язык)
        
    def initUI(self):
        self.setWindowTitle(self.translations['app_title'])
        self.setFixedSize(400, 780)
        
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
            self.recorder.start_recording(self.on_action_recorded)
            print("[start_recording] Запись начата.")
            self.updateUIState() # Обновляем интерфейс ПОСЛЕ старта записи
        except Exception as e:
             print(f"[start_recording] Ошибка старта рекордера: {e}")
             QMessageBox.critical(self, "Ошибка записи", f"Не удалось запустить запись: {e}")
             self.recording = False # Сбрасываем флаг, если старт не удался
             self.updateUIState()
    
    def stop_recording(self):
        """Остановка записи"""
        if not self.recording:
            return
            
        try:
            self.recorder.stop()
            self.recording = False
            print(f"[stop_recording] Остановлено. Состояние: recording={self.recording}, playing={self.playing}, actions={len(self.recorded_actions)}")
        except Exception as e:
            print(f"[stop_recording] Ошибка остановки рекордера: {e}")
            self.recording = False # Все равно считаем остановленным
        finally:
            self.updateUIState() # Обновляем интерфейс
            QApplication.processEvents() # Принудительно обрабатываем события
            print("[stop_recording] Вызван updateUIState и processEvents.")
    
    def on_action_recorded(self, action):
        if self.recording: # Доп. проверка на всякий случай
             self.recorded_actions.append(action)
        # Счетчик обновится через update_status
    
    def start_playback(self):
        if not self.recorded_actions:
            QMessageBox.warning(self, self.translations['playback_error_title'], self.translations.get('no_actions_warning', TRANSLATIONS['en']['no_actions_warning']))
            return
        if self.playing or self.recording:
            return

        speed_factor = self.speed_slider.value() / 100.0

        # Определяем режим запуска
        if self.once_radio.isChecked():
            repeat_count = self.repeat_count.value()
            self._start_direct_playback(repeat_count, speed_factor)
        elif self.interval_radio.isChecked():
            interval_seconds = self.interval_value.value()
            is_infinite = self.infinite_repeat_checkbox.isChecked()

            if interval_seconds > 0:
                # Сначала устанавливаем флаги и счетчики
                if is_infinite:
                    self.interval_repeats_left = -1 # Флаг бесконечности
                    print(f"[start_playback] Запуск БЕСКОНЕЧНОГО интервального таймера: каждые {interval_seconds} сек")
                else:
                    self.interval_repeats_left = self.repeat_count.value()
                    if self.interval_repeats_left <= 0:
                        print("[start_playback] Количество повторов <= 0, запуск не требуется.")
                        return # Не запускаем, если повторов 0 или меньше
                    print(f"[start_playback] Запуск интервального таймера: каждые {interval_seconds} сек, повторов: {self.interval_repeats_left}")

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
                 print("[start_playback] Интервал <= 0, интервальный режим не запущен.")
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
            
            print(f"[start_playback] Запуск таймера на время: {target_time.toString('HH:mm')}, через {msecs_to_target / 1000:.1f} сек")
            self.schedule_timer.setSingleShot(True) # Убедимся, что таймер однократный
            self.schedule_timer.start(msecs_to_target)
            self.playing = True # Устанавливаем флаг игры, пока ждем таймер
            self.updateUIState()
            self.statusBar.showMessage(f"Запланировано на {target_time.toString('HH:mm')}")

    def _start_direct_playback(self, repeat_count, speed_factor):
        """Запускает немедленное воспроизведение заданное число раз."""
        print(f"[start_playback] Прямой запуск: повторов={repeat_count}, скорость={speed_factor}")
        self.playing = True
        try:
            self.player.play(
                self.recorded_actions, 
                repeat_count, 
                speed_factor
            )
            self.updateUIState()
        except TypeError as te:
            QMessageBox.critical(self, self.translations['playback_error_title'], self.translations.get('playback_type_error', TRANSLATIONS['en']['playback_type_error']).format(error=te))
            self.playing = False
            self.updateUIState()
        except Exception as e:
            QMessageBox.critical(self, self.translations['playback_error_title'], self.translations.get('playback_error_text', TRANSLATIONS['en']['playback_error_text']).format(error=e))
            self.playing = False
            self.updateUIState()
            
    def _trigger_scheduled_playback(self):
        """Срабатывает по таймеру для 'Run at HH:MM'."""
        print("[schedule_timer] Таймер сработал.")
        if self.playing: # Проверка, что не остановили вручную
             repeat_count = self.repeat_count.value()
             speed_factor = self.speed_slider.value() / 100.0
             # Запускаем однократно, т.к. таймер был SingleShot
             # Флаг self.playing уже True, плеер сам его сбросит по завершению/ошибке
             self._start_direct_playback(repeat_count, speed_factor)
             # Важно: Не сбрасываем self.playing здесь, ждем сигнал от плеера
        else:
             print("[schedule_timer] Воспроизведение было отменено.")
             # Убедимся, что UI обновлен
             self.updateUIState()

    def _trigger_interval_playback(self):
         """Срабатывает по таймеру для 'Run every X seconds'. Запускает ОДИН цикл воспроизведения."""
         if self.playing: # Проверяем, что не было остановки
            is_infinite = (self.interval_repeats_left == -1) # Проверяем флаг бесконечности
            
            # Если режим конечный, проверяем, остались ли еще повторы (перед текущим запуском)
            if not is_infinite and self.interval_repeats_left <= 0:
                 print("[_trigger_interval_playback] Повторы закончились, но таймер сработал? Остановка.")
                 # Не вызываем stop_playback(), чтобы не сбросить плеер, если он еще играет последний раз
                 if self.interval_timer.isActive():
                     self.interval_timer.stop()
                 # Состояние playing сбросится в on_playback_completed
                 return
                 
            speed_factor = self.speed_slider.value() / 100.0
            
            # Уменьшаем счетчик, если режим не бесконечный (делаем это *после* запуска play)
            # current_repeat_num_str = "(бесконечно)" # Для логгирования
            # if not is_infinite:
            #     remaining_before_play = self.interval_repeats_left
            #     # self.interval_repeats_left -= 1 # Уменьшаем ПОСЛЕ play
            #     current_repeat_num_str = f"(осталось {remaining_before_play} до запуска)"
            
            print(f"[_trigger_interval_playback] Запуск воспроизведения 1 раз.")
            
            # Запускаем плеер на repeat_count раз
            try:
                 # Запускаем плеер только на ОДИН раз
                 self.player.play(self.recorded_actions, 1, speed_factor)
                 
                 # Уменьшаем счетчик ПОСЛЕ успешного запуска play, если режим не бесконечный
                 if not is_infinite:
                      self.interval_repeats_left -= 1
                      print(f"[_trigger_interval_playback] Воспроизведение запущено, осталось {self.interval_repeats_left} запусков.")
                 else:
                      print(f"[_trigger_interval_playback] Воспроизведение (бесконечное) запущено.")

            except Exception as e:
                 print(f"[interval_timer] Ошибка при запуске player.play: {e}")
                 QMessageBox.critical(self, self.translations['playback_error_title'], self.translations.get('playback_error_text', TRANSLATIONS['en']['playback_error_text']).format(error=e))
                 self.stop_playback() # Останавливаем всю серию при ошибке
                 return
                 
            # Логика перезапуска таймера перенесена сюда (после успешного play)
            # Если игра все еще активна (не остановили во время play) 
            # и (режим бесконечный ИЛИ остались повторы > 0)
            if self.playing and (is_infinite or self.interval_repeats_left > 0):
                 interval_seconds = self.interval_value.value()
                 # Запускаем таймер только если интервал положительный
                 if interval_seconds > 0:
                      print(f"[_trigger_interval_playback] Планируем следующий запуск через {interval_seconds} сек.")
                      self.interval_timer.start(interval_seconds * 1000)
                 else:
                      print(f"[_trigger_interval_playback] Интервал <= 0, таймер не перезапускается.")
                      # Если интервал 0, а повторы конечные, останавливаем
                      if not is_infinite: 
                           self.stop_playback() 
            else:
                 # Если повторы кончились (или остановили вручную)
                 print("[_trigger_interval_playback] Конечные повторы завершены или остановлено вручную. Таймер не перезапускается.")
                 # Не меняем self.playing здесь, ждем on_playback_completed/error от последнего play

         else:
             print("[_trigger_interval_playback] Воспроизведение было остановлено, таймер не перезапускается.")
             if self.interval_timer.isActive(): # Доп. проверка
                 self.interval_timer.stop()

    def stop_playback(self):
        """Остановка воспроизведения (прямого или по расписанию)"""
        print("[stop_playback] Вызван метод остановки.")

        # Останавливаем таймеры расписания, если они активны
        was_timer_active = False
        if self.schedule_timer.isActive():
            print("[stop_playback] Остановка таймера 'Run at'.")
            self.schedule_timer.stop()
            was_timer_active = True
        if self.interval_timer.isActive():
            print("[stop_playback] Остановка таймера 'Run every'.")
            self.interval_timer.stop()
            was_timer_active = True

        # Сбрасываем счетчик интервальных повторов
        self.interval_repeats_left = 0

        # Останавливаем плеер, если он активен
        player_was_playing = self.player.is_playing # Проверяем фактическое состояние плеера
        if player_was_playing:
            try:
                print("[stop_playback] Запрос на остановку плеера.")
                self.player.stop()
                # Не меняем self.playing здесь, ждем callback
                self.statusBar.showMessage(self.translations.get('playback_stopped', TRANSLATIONS['en']['playback_stopped']))
            except Exception as e:
                print(f"[stop_playback] Ошибка при вызове player.stop(): {e}")
                # Если ошибка при остановке плеера, всё равно сбрасываем состояние GUI
                self.playing = False
                self.updateUIState()
                self.statusBar.showMessage(self.translations.get('playback_stop_error', TRANSLATIONS['en']['playback_stop_error']))
                return # Выходим, чтобы не сбросить флаг еще раз ниже

        # Если был активен таймер, но плеер еще не запущен (ожидание 'Run at' или между интервалами)
        # или если плеер НЕ был активен (например, уже остановился сам),
        # то нужно вручную сбросить флаг playing и обновить UI.
        # Если плеер БЫЛ активен, то сброс флага и обновление UI произойдет в on_playback_completed/error.
        if was_timer_active and not player_was_playing:
             print("[stop_playback] Таймер был остановлен до запуска плеера. Сброс состояния GUI.")
             self.playing = False
             self.updateUIState()
        elif not player_was_playing and self.playing: # Если плеер не играет, но GUI думает, что играет
             print("[stop_playback] Плеер не активен, но флаг GUI был установлен. Сброс состояния GUI.")
             self.playing = False
             self.updateUIState()
        else:
             print("[stop_playback] Либо плеер активен (ждем колбек), либо уже все остановлено.")

         # Убираем ручное управление кнопками - оно теперь в updateUIState
         # self.play_button.setEnabled(True)

    def on_playback_completed(self):
        """Слот, вызываемый сигналом playbackFinished из плеера"""
        print("[on_playback_completed] Слот вызван сигналом.")

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
                 print("[on_playback_completed] Завершение НЕинтервального воспроизведения.")
                 self.playing = False
                 self.updateUIState() # Обновляем интерфейс
                 QApplication.processEvents() # Даем интерфейсу обновиться
                 print("[on_playback_completed] Состояние обновлено.")
             else:
                 print("[on_playback_completed] НЕинтервальное завершение, но self.playing уже был False.")
        else:
             # Это был один из запусков интервального таймера
             print("[on_playback_completed] Завершение одного интервального цикла.")
             # Проверяем, был ли это последний запуск (если режим не бесконечный)
             # Важно: self.interval_repeats_left уже уменьшен в _trigger_interval_playback *перед* этим вызовом
             is_infinite = (self.interval_repeats_left == -1) # Проверяем флаг бесконечности
             if not is_infinite and self.interval_repeats_left <= 0:
                  # Повторы закончились
                  print("[on_playback_completed] Конечные интервальные повторы завершены. Сброс состояния.")
                  if self.playing: # Доп. проверка
                     self.playing = False
                     self.updateUIState()
                     QApplication.processEvents()
                     print("[on_playback_completed] Интервальный режим завершен, состояние обновлено.")
                  else:
                     print("[on_playback_completed] Интервальный режим завершен, но self.playing уже был False.")
             else:
                 # Либо режим бесконечный, либо еще остались повторы - таймер должен был перезапуститься в _trigger_interval_playback
                 print("[on_playback_completed] Интервальный цикл продолжается (или бесконечный). Логика продолжения в _trigger_interval_playback.")
                 # Ничего не делаем здесь, интерфейс остается в состоянии 'Playing...'.

    def on_playback_error(self, error_message):
         """Слот, вызываемый сигналом playbackError из плеера"""
         print(f"[on_playback_error] Слот вызван сигналом: {error_message}")
         
         # При любой ошибке останавливаем все таймеры и сбрасываем состояние
         if self.schedule_timer.isActive():
             self.schedule_timer.stop()
         if self.interval_timer.isActive():
             self.interval_timer.stop()
         # self.interval_repeats_left = 0 # Больше не нужно
            
         if self.playing: # Доп. проверка
              print("[on_playback_error] Ошибка во время воспроизведения. Сброс состояния.")
              self.playing = False
              self.updateUIState()
              QApplication.processEvents()
              QMessageBox.warning(self, self.translations['playback_error_title'], str(error_message))
              self.statusBar.showMessage(f"{self.translations['playback_error_title']}: {error_message}")
              print("[on_playback_error] Состояние обновлено, ошибка показана.")
         else:
              print("[on_playback_error] Состояние playing уже было False.")

    def update_playback_progress(self, current_ms, total_ms):
        """Обновляет статус-бар для отображения прогресса воспроизведения"""
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
        if not self.recorded_actions:
            self.statusBar.showMessage(self.translations.get('status_no_actions', TRANSLATIONS['en']['status_no_actions']))
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, self.translations.get('file_dialog_save', TRANSLATIONS['en']['file_dialog_save']), "", self.translations.get('file_dialog_filter', TRANSLATIONS['en']['file_dialog_filter'])
        )
        
        if file_path:
            try:
                if not file_path.endswith('.clk'):
                    file_path += '.clk'
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.recorded_actions, f)
                
                self.current_file_path = file_path
                file_name = os.path.basename(file_path)
                self.action_count.setText(f"{self.translations['file']} {file_name} ({len(self.recorded_actions)} {self.translations['actions_recorded']})")
                self.statusBar.showMessage(f"{self.translations.get('status_saved', TRANSLATIONS['en']['status_saved'])} {file_path}")
            except Exception as e:
                self.statusBar.showMessage(f"{self.translations.get('save_error', TRANSLATIONS['en']['save_error'])} {str(e)}")
    
    def load_recording(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, self.translations.get('file_dialog_load', TRANSLATIONS['en']['file_dialog_load']), "", self.translations.get('file_dialog_filter', TRANSLATIONS['en']['file_dialog_filter'])
        )
        
        if file_path:
            # Загрузка происходит синхронно, интерфейс может подвиснуть на больших файлах
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    actions = json.load(f)
                    if isinstance(actions, list): # Простая проверка, что это похоже на список действий
                        self.recorded_actions = actions
                        self.current_file_path = file_path
                        print(f"[load_recording] Загружено действий: {len(self.recorded_actions)}")
                        # Обновляем интерфейс ПОСЛЕ успешной загрузки
                        self.updateUIState()
                        # self.action_count.setText(...) # Обновится через update_status
                        # self.statusBar.showMessage(...) # Обновится через update_status
                    else:
                         raise ValueError(self.translations.get('file_not_valid', TRANSLATIONS['en']['file_not_valid']))
            except Exception as e:
                QMessageBox.warning(self, self.translations['load_error'], self.translations.get('load_file_error', TRANSLATIONS['en']['load_file_error']).format(error=str(e)))
                self.statusBar.showMessage(f"{self.translations.get('load_error', TRANSLATIONS['en']['load_error'])} {e}")
                # Сбрасываем состояние, если загрузка не удалась
                # self.recorded_actions = [] # Не очищаем, если была предыдущая запись
                # self.current_file_path = None
                self.updateUIState()
    
    def show_help(self):
        help_text = f"{self.translations.get('help_dialog_title', TRANSLATIONS['en']['help_dialog_title'])}\n\n{self.translations.get('help_text', TRANSLATIONS['en']['help_text'])}"
        QMessageBox.information(self, self.translations.get('help_dialog_title', TRANSLATIONS['en']['help_dialog_title']), help_text)

    def updateUIState(self):
        """Обновляет состояние кнопок и настроек в зависимости от состояния приложения"""
        is_idle = not self.recording and not self.playing
        can_play = is_idle and bool(self.recorded_actions)
        
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
        
        # Настройки - блокируем только интерактивные виджеты из списка
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
        if not self.infinite_repeat_checkbox.isEnabled():
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
        self.save_settings() # Сохраняем настройки перед выходом
        self.gui_update_timer.stop()
        if self.is_recording:
            self.stop_recording()
        reply = QMessageBox.question(self, self.translations.get('exit', TRANSLATIONS['en']['exit']), self.translations.get('close_confirm', TRANSLATIONS['en']['close_confirm']), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def set_language(self, lang_code):
        if lang_code in TRANSLATIONS:
            self.current_language = lang_code
            self.translations = TRANSLATIONS[self.current_language]
            # Обновляем тексты и сохраняем настройки ПОСЛЕ установки языка
            self.updateUITexts()
            self.save_settings() # Сохраняем язык после смены
        else:
            print(f"Warning: Language code \'{lang_code}\' not found in TRANSLATIONS.")

    def updateUITexts(self):
        """Обновляет тексты всех виджетов в соответствии с текущим языком"""
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
        # Обновляем строку состояния, если она не показывает прогресс
        if self.playing:
            self.statusBar.showMessage(f"{self.translations['playing']} ({self.player.get_current_playback_time() // 1000} сек / {self.player.get_total_playback_time() // 1000} сек)")
        else:
            self.statusBar.showMessage("")
        # Обновляем текст чекбокса
        self.infinite_repeat_checkbox.setText(self.translations.get('infinite_repeats', 'Infinite Repeats'))
    
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
            'language': self.current_language # Убеждаемся, что используется правильная переменная
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
        except IOError as e:
            print(f"Error saving settings to {self.config_file}: {e}")

    def load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    lang_code = settings.get('language')
                    if lang_code and lang_code in LANGUAGES:
                        # Просто применяем язык из файла, если он валидный
                        self.set_language(lang_code) 
                    else:
                         print(f"Warning: Invalid or missing language code in {self.config_file}, using default.")

            except (IOError, json.JSONDecodeError) as e:
                print(f"Error loading settings from {self.config_file}: {e}, using default.")
        # Если файла нет или он некорректный, остается английский (установлен в __init__)

def main():
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
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 