import sys
import os
import tempfile

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QComboBox, QTextEdit, QPushButton, QLabel, QMessageBox)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
import speech_recognition as sr
from deep_translator import GoogleTranslator
from gtts import gTTS
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

class SpeechRecognitionThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, language):
        super().__init__()
        self.language = language

    def run(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Say something!")
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                text = recognizer.recognize_google(audio, language=self.language)
                self.finished.emit(text)
            except sr.WaitTimeoutError:
                self.error.emit("Listening timed out. Please try again.")
            except sr.UnknownValueError:
                self.error.emit("Speech recognition could not understand audio")
            except sr.RequestError as e:
                self.error.emit(f"Could not request results from speech recognition service; {e}")
            except Exception as e:
                self.error.emit(f"An unexpected error occurred: {str(e)}")

class TranslationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Translation App")
        self.setGeometry(100, 100, 600, 400)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QLabel {
                font-size: 16px;
                color: #333;
            }
            QComboBox {
                font-size: 14px;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QTextEdit {
                font-size: 14px;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QPushButton {
                font-size: 14px;
                padding: 8px 15px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Language selection
        lang_layout = QHBoxLayout()
        self.source_lang = QComboBox()
        self.target_lang = QComboBox()
        languages = {
            'English': 'en', 'Spanish': 'es', 'French': 'fr', 'German': 'de',
            'Italian': 'it', 'Portuguese': 'pt', 'Russian': 'ru', 'Japanese': 'ja',
            'Korean': 'ko', 'Chinese': 'zh-CN','Marathi':'mr','Hindi':'hi','Kannada':'kn'
        }
        for lang, code in languages.items():
            self.source_lang.addItem(lang, code)
            self.target_lang.addItem(lang, code)
        self.target_lang.setCurrentIndex(1)  # Set Spanish as default target
        lang_layout.addWidget(QLabel("From:"))
        lang_layout.addWidget(self.source_lang)
        lang_layout.addWidget(QLabel("To:"))
        lang_layout.addWidget(self.target_lang)
        main_layout.addLayout(lang_layout)

        # Text areas
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Recognized speech will appear here...")
        self.input_text.setReadOnly(True)
        main_layout.addWidget(self.input_text)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Translation will appear here...")
        main_layout.addWidget(self.output_text)

        # Speak button
        self.speak_button = QPushButton(QIcon("mic_icon.png"), "Speak")
        self.speak_button.setToolTip("Click and speak")
        main_layout.addWidget(self.speak_button)

        # Connect button to function
        self.speak_button.clicked.connect(self.start_speech_recognition)

        # Set up audio player
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        self.speech_thread = None
        self.temp_audio_file = None

    def start_speech_recognition(self):
        source_lang = self.source_lang.currentData()
        self.speech_thread = SpeechRecognitionThread(source_lang)
        self.speech_thread.finished.connect(self.on_speech_recognized)
        self.speech_thread.error.connect(self.on_speech_error)
        self.speech_thread.start()
        self.speak_button.setEnabled(False)
        self.speak_button.setText("Listening...")

    def on_speech_recognized(self, text):
        self.input_text.setText(text)
        self.speak_button.setEnabled(True)
        self.speak_button.setText("Speak")
        self.translate_text(text)

    def on_speech_error(self, error_message):
        self.speak_button.setEnabled(True)
        self.speak_button.setText("Speak")
        QMessageBox.warning(self, "Speech Recognition Error", error_message)

    def translate_text(self, source_text):
        source_lang = self.source_lang.currentData()
        target_lang = self.target_lang.currentData()

        try:
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            translated_text = translator.translate(source_text)

            self.output_text.setText(translated_text)
            self.generate_and_play_audio(translated_text, target_lang)
        except Exception as e:
            QMessageBox.warning(self, "Translation Error", f"An error occurred during translation: {str(e)}")

    def generate_and_play_audio(self, text, lang):
        try:
            tts = gTTS(text=text, lang=lang)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                tts.save(temp_file.name)
                self.temp_audio_file = temp_file.name

            self.player.setSource(QUrl.fromLocalFile(self.temp_audio_file))
            self.player.play()
        except Exception as e:
            QMessageBox.warning(self, "Audio Generation Error", f"An error occurred while generating audio: {str(e)}")

    def closeEvent(self, event):
        if self.temp_audio_file:
            try:
                os.unlink(self.temp_audio_file)
            except Exception as e:
                print(f"Error deleting temporary file: {str(e)}")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranslationApp()
    window.show()
    sys.exit(app.exec())