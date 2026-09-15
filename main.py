from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.text import LabelBase
from kivy.clock import Clock

FONT_FILE = "NotoKufiArabic-VariableFont_wght.ttf"

try:
    LabelBase.register(
        name="Arabic",
        fn_regular=FONT_FILE
    )
    ARABIC_FONT = "Arabic"
except Exception:
    ARABIC_FONT = "Roboto"


class VoiceControlApp(App):

    REQUEST_CODE = 5001

    def build(self):

        self.result_label = Label(
            text="",
            font_name=ARABIC_FONT,
            font_size=20,
            halign="center",
            valign="middle",
        )

        self.status_label = Label(
            text="اضغط على الزر وتحدث",
            font_name=ARABIC_FONT,
            font_size=20,
            halign="center",
            valign="middle",
        )

        layout = BoxLayout(
            orientation="vertical",
            padding=30,
            spacing=20,
        )

        layout.add_widget(
            Label(
                text="التحكم الصوتي",
                font_name=ARABIC_FONT,
                font_size=28,
                size_hint_y=None,
                height=80,
            )
        )

        layout.add_widget(self.status_label)
        layout.add_widget(self.result_label)

        start_button = Button(
            text="🎤 بدء الاستماع",
            font_name=ARABIC_FONT,
            font_size=22,
            size_hint_y=None,
            height=80,
        )

        start_button.bind(
            on_release=self.start_listening
        )

        layout.add_widget(start_button)

        return layout


    def start_listening(self, *args):

        try:

            from android.permissions import (
                request_permissions,
                Permission
            )

            request_permissions([
                Permission.RECORD_AUDIO
            ])

            self.status_label.text = (
                "جاري فتح التعرف الصوتي..."
            )

            Clock.schedule_once(
                self.open_recognizer,
                1.5
            )

        except Exception as e:

            self.status_label.text = (
                "تعذر طلب صلاحية الميكروفون"
            )

            self.result_label.text = str(e)


    def open_recognizer(self, dt):

        try:

            from android import activity
            from jnius import autoclass

            Intent = autoclass(
                "android.content.Intent"
            )

            RecognizerIntent = autoclass(
                "android.speech.RecognizerIntent"
            )

            intent = Intent(
                RecognizerIntent.ACTION_RECOGNIZE_SPEECH
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE,
                "ar-YE"
            )

            intent
