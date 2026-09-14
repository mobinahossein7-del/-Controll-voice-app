from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.text import LabelBase
from kivy.clock import Clock

# =========================================================
# الخط العربي
# يجب أن يكون الملف في نفس مجلد main.py
# =========================================================

FONT_FILE = "NotoKufiArabic-VariableFont_wght.ttf"

try:
    LabelBase.register(
        name="Arabic",
        fn_regular=FONT_FILE
    )
    ARABIC_FONT = "Arabic"
except Exception:
    ARABIC_FONT = "Roboto"


# =========================================================
# التطبيق
# =========================================================

class VoiceControlApp(App):

    def build(self):

        self.title = "التحكم الصوتي"

        layout = BoxLayout(
            orientation="vertical",
            padding=30,
            spacing=20
        )

        # العنوان
        self.title_label = Label(
            text="التحكم الصوتي بالإعدادات",
            font_name=ARABIC_FONT,
            font_size=26,
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=80
        )

        layout.add_widget(self.title_label)

        # حالة التطبيق
        self.status_label = Label(
            text="اضغط على زر بدء الاستماع",
            font_name=ARABIC_FONT,
            font_size=20,
            halign="center",
            valign="middle"
        )

        layout.add_widget(self.status_label)

        # النص الذي تم التعرف عليه
        self.result_label = Label(
            text="",
            font_name=ARABIC_FONT,
            font_size=19,
            halign="center",
            valign="middle"
        )

        layout.add_widget(self.result_label)

        # زر الاستماع
        listen_button = Button(
            text="🎤 بدء الاستماع",
            font_name=ARABIC_FONT,
            font_size=22,
            size_hint_y=None,
            height=70
        )

        listen_button.bind(
            on_press=self.start_listening
        )

        layout.add_widget(listen_button)

        # زر الإيقاف
        stop_button = Button(
            text="إيقاف الاستماع",
            font_name=ARABIC_FONT,
            font_size=20,
            size_hint_y=None,
            height=65
        )

        stop_button.bind(
            on_press=self.stop_listening
        )

        layout.add_widget(stop_button)

        # زر المسح
        clear_button = Button(
            text="مسح النص",
            font_name=ARABIC_FONT,
            font_size=20,
            size_hint_y=None,
            height=65
        )

        clear_button.bind(
            on_press=self.clear_text
        )

        layout.add_widget(clear_button)

        return layout


    # =====================================================
    # بدء الاستماع
    # =====================================================

    def start_listening(self, *args):

        self.status_label.text = "جاري الاستماع..."

        self.result_label.text = ""

        try:

            from android.permissions import request_permissions
            from android.permissions import Permission

            request_permissions([
                Permission.RECORD_AUDIO
            ])

        except Exception:
            pass

        try:

            from jnius import autoclass

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            SpeechRecognizer = autoclass(
                "android.speech.SpeechRecognizer"
            )

            RecognizerIntent = autoclass(
                "android.content.Intent"
            )

            Locale = autoclass(
                "java.util.Locale"
            )

            self.SpeechRecognizer = SpeechRecognizer
            self.RecognizerIntent = RecognizerIntent

            activity = PythonActivity.mActivity

            if not SpeechRecognizer.isRecognitionAvailable(activity):

                self.status_label.text = (
                    "التعرف الصوتي غير متوفر على الجهاز"
                )

                return

            self.recognizer = SpeechRecognizer.createSpeechRecognizer(
                activity
            )

            from jnius import PythonJavaClass, java_method


            class RecognitionListener(
                PythonJavaClass
            ):

                __javainterfaces__ = [
                    "android.speech.RecognitionListener"
                ]

                def __init__(self, app):

                    super().__init__()

                    self.app = app


                @java_method("()V")
                def onReadyForSpeech(self, params):
                    pass


                @java_method("()V")
                def onBeginningOfSpeech(self):
                    pass


                @java_method("([B)V")
                def onBufferReceived(self, buffer):
                    pass


                @java_method("()V")
                def onEndOfSpeech(self):

                    self.app.status_label.text = (
                        "انتهى الاستماع"
                    )


                @java_method("(I)V")
                def onError(self, error):

                    self.app.status_label.text = (
                        "حدث خطأ أثناء التعرف الصوتي"
                    )


                @java_method("(Landroid/os/Bundle;)V")
                def onPartialResults(self, results):

                    self.handle_results(results)


                @java_method("(Landroid/os/Bundle;)V")
                def onResults(self, results):

                    self.handle_results(results)


                @java_method("(F)V")
                def onRmsChanged(self, rmsdB):
                    pass


                @java_method("(Landroid/os/Bundle;)V")
                def onEvent(self, eventType, params):
                    pass


                def handle_results(self, results):

                    try:

                        ArrayList = results.getStringArrayList(
                            "results_recognition"
                        )

                        if ArrayList:

                            text = str(
                                ArrayList.get(0)
                            )

                            self.app.process_command(
                                text
                            )

                    except Exception:
                        pass


            self.listener = RecognitionListener(
                self
            )

            self.recognizer.setRecognitionListener(
                self.listener
            )

            intent = RecognizerIntent(
                "android.speech.action.RECOGNIZE_SPEECH"
            )

            intent.putExtra(
                "android.speech.extra.LANGUAGE_MODEL",
                "free_form"
            )

            intent.putExtra(
                "android.speech.extra.LANGUAGE",
                "ar"
            )

            intent.putExtra(
                "android.speech.extra.LANGUAGE_PREFERENCE",
                "ar"
            )

            intent.putExtra(
                "android.speech.extra.PARTIAL_RESULTS",
                True
            )

            self.recognizer.startListening(
                intent
            )

        except Exception as e:

            self.status_label.text = (
                "تعذر تشغيل التعرف الصوتي"
            )

            self.result_label.text = str(e)


    # =====================================================
    # إيقاف الاستماع
    # =====================================================

    def stop_listening(self, *args):

        try:

            if hasattr(self, "recognizer"):

                self.recognizer.stopListening()

                self.status_label.text = (
                    "تم إيقاف الاستماع"
                )

        except Exception:

            self.status_label.text = (
                "تم إيقاف الاستماع"
            )


    # =====================================================
    # معالجة الأمر الصوتي
    # =====================================================

    def process_command(self, text):

        self.result_label.text = text

        self.status_label.text = (
            "تم التعرف على الكلام"
        )

        command = text.lower()

        # أوامر مستقبلية يمكن إضافة وظائفها هنا

        if "واي فاي" in command or "wifi" in command:

            self.status_label.text = (
                "تم التعرف على أمر الواي فاي"
            )

        elif "بلوتوث" in command:

            self.status_label.text = (
                "تم التعرف على أمر البلوتوث"
            )

        elif "صوت" in command:

            self.status_label.text = (
                "تم التعرف على أمر الصوت"
            )

        elif "سطوع" in command:

            self.status_label.text = (
                "تم التعرف على أمر السطوع"
            )


    # =====================================================
    # مسح النص
    # =====================================================

    def clear_text(self, *args):

        self.result_label.text = ""

        self.status_label.text = (
            "تم مسح النص"
        )


# =========================================================
# تشغيل التطبيق
# =========================================================

if __name__ == "__main__":

    VoiceControlApp().run()
