# ============================================================
# Voice Control - Simple Version
# نسخة نظيفة لاختبار التعرف الصوتي العربي
# ============================================================

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.text import LabelBase
from kivy.clock import Clock


# ============================================================
# الخط العربي
# ============================================================

FONT_FILE = "NotoKufiArabic-VariableFont_wght.ttf"

try:
    LabelBase.register(
        name="Arabic",
        fn_regular=FONT_FILE
    )
    FONT = "Arabic"
except Exception:
    FONT = "Roboto"


# ============================================================
# التطبيق
# ============================================================

class VoiceControlApp(App):

    def build(self):

        layout = BoxLayout(
            orientation="vertical",
            padding=30,
            spacing=20
        )

        self.status = Label(
            text="التحكم الصوتي\n\nاضغط على الزر وتحدث",
            font_name=FONT,
            font_size=22,
            halign="center",
            valign="middle"
        )

        layout.add_widget(self.status)

        self.result = Label(
            text="",
            font_name=FONT,
            font_size=20,
            halign="center",
            valign="middle"
        )

        layout.add_widget(self.result)

        button = Button(
            text="🎤 ابدأ التحدث",
            font_name=FONT,
            font_size=22,
            size_hint_y=None,
            height=80
        )

        button.bind(
            on_release=self.start_voice
        )

        layout.add_widget(button)

        return layout


    # ========================================================
    # بدء التعرف الصوتي
    # ========================================================

    def start_voice(self, *args):

        self.status.text = "جاري تشغيل الميكروفون..."

        try:

            from android.permissions import (
                request_permissions,
                Permission
            )

            request_permissions([
                Permission.RECORD_AUDIO
            ])

            Clock.schedule_once(
                self.start_recognition,
                1
            )

        except Exception as e:

            self.status.text = "حدث خطأ"

            self.result.text = str(e)


    # ========================================================
    # تشغيل التعرف
    # ========================================================

    def start_recognition(self, dt):

        try:

            from jnius import autoclass

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            SpeechRecognizer = autoclass(
                "android.speech.SpeechRecognizer"
            )

            RecognizerIntent = autoclass(
                "android.speech.RecognizerIntent"
            )

            Intent = autoclass(
                "android.content.Intent"
            )

            activity = PythonActivity.mActivity

            # ------------------------------------------------
            # التحقق من توفر التعرف الصوتي
            # ------------------------------------------------

            if not SpeechRecognizer.isRecognitionAvailable(
                activity
            ):

                self.status.text = (
                    "التعرف الصوتي غير متوفر"
                )

                return

            # ------------------------------------------------
            # إنشاء المستمع
            # ------------------------------------------------

            listener = self.create_listener()

            self.listener = listener

            # ------------------------------------------------
            # إنشاء SpeechRecognizer
            # ------------------------------------------------

            self.recognizer = (
                SpeechRecognizer.createSpeechRecognizer(
                    activity
                )
            )

            self.recognizer.setRecognitionListener(
                self.listener
            )

            # ------------------------------------------------
            # إنشاء Intent
            # ------------------------------------------------

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

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE,
                "ar-YE"
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_PARTIAL_RESULTS,
                True
            )

            # ------------------------------------------------
            # بدء الاستماع
            # ------------------------------------------------

            self.status.text = "🎤 أستمع إليك..."

            self.recognizer.startListening(
                intent
            )

        except Exception as e:

            self.status.text = "تعذر تشغيل الميكروفون"

            self.result.text = str(e)


    # ========================================================
    # إنشاء RecognitionListener
    # ========================================================

    def create_listener(self):

        from jnius import (
            PythonJavaClass,
            java_method
        )

        app = self

        class Listener(
            PythonJavaClass
        ):

            __javainterfaces__ = [
                "android.speech.RecognitionListener"
            ]

            @java_method(
                "(Landroid/os/Bundle;)V"
            )
            def onReadyForSpeech(
                self,
                params
            ):

                Clock.schedule_once(
                    lambda dt: app.set_status(
                        "🎤 جاهز... تحدث الآن"
                    ),
                    0
                )


            @java_method("()V")
            def onBeginningOfSpeech(
                self
            ):

                Clock.schedule_once(
                    lambda dt: app.set_status(
                        "🎤 أستمع إليك..."
                    ),
                    0
                )


            @java_method("()V")
            def onEndOfSpeech(
                self
            ):

                Clock.schedule_once(
                    lambda dt: app.set_status(
                        "جارٍ معالجة الكلام..."
                    ),
                    0
                )


            @java_method(
                "(Landroid/os/Bundle;)V"
            )
            def onResults(
                self,
                results
            ):

                try:

                    values = (
                        results.getStringArrayList(
                            "results_recognition"
                        )
                    )

                    if values is not None:

                        if values.size() > 0:

                            text = str(
                                values.get(0)
                            )

                            Clock.schedule_once(
                                lambda dt: app.show_result(
                                    text
                                ),
                                0
                            )

                except Exception as e:

                    Clock.schedule_once(
                        lambda dt: app.show_result(
                            str(e)
                        ),
                        0
                    )


            @java_method(
                "(Landroid/os/Bundle;)V"
            )
            def onPartialResults(
                self,
                results
            ):

                try:

                    values = (
                        results.getStringArrayList(
                            "results_recognition"
                        )
                    )

                    if values is not None:

                        if values.size() > 0:

                            text = str(
                                values.get(0)
                            )

                            Clock.schedule_once(
                                lambda dt: app.show_partial(
                                    text
                                ),
                                0
                            )

                except Exception:
                    pass


            @java_method("(I)V")
            def onError(
                self,
                error
            ):

                Clock.schedule_once(
                    lambda dt: app.show_error(
                        error
                    ),
                    0
                )


            @java_method("([B)V")
            def onBufferReceived(
                self,
                buffer
            ):

                pass


            @java_method("(F)V")
            def onRmsChanged(
                self,
                rms
            ):

                pass


            @java_method(
                "(ILandroid/os/Bundle;)V"
            )
            def onEvent(
                self,
                event_type,
                params
            ):

                pass

        return Listener()


    # ========================================================
    # عرض النتيجة
    # ========================================================

    def show_result(
        self,
        text
    ):

        self.result.text = (
            "قلت:\n\n" + text
        )

        self.status.text = (
            "تم التعرف على الكلام"
        )


    # ========================================================
    # عرض النتيجة الجزئية
    # ========================================================

    def show_partial(
        self,
        text
    ):

        self.result.text = (
            "أستمع:\n\n" + text
        )


    # ========================================================
    # الأخطاء
    # ========================================================

    def show_error(
        self,
        error
    ):

        messages = {

            1: "خطأ في الشبكة",

            2: "الشبكة غير متوفرة",

            3: "الخادم غير متاح",

            4: "الخدمة غير متاحة",

            5: "خطأ في التطبيق",

            6: "لم يبدأ الكلام",

            7: "لم يتم العثور على كلام",

            8: "انتهت مهلة التعرف",

            9: "صلاحية التعرف غير متوفرة"
        }

        message = messages.get(
            error,
            "خطأ غير معروف: " + str(error)
        )

        self.status.text = message


    # ========================================================
    # تحديث الحالة
    # ========================================================

    def set_status(
        self,
        text
    ):

        self.status.text = text


# ============================================================
# تشغيل التطبيق
# ============================================================

if __name__ == "__main__":

    VoiceControlApp().run()
