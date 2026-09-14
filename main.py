# ============================================================
# Voice Control - Android
# التحكم الصوتي بالإعدادات
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
    ARABIC_FONT = "Arabic"
except Exception:
    ARABIC_FONT = "Roboto"


# ============================================================
# Android Main Thread
# ============================================================

try:
    from android.runnable import run_on_ui_thread
except Exception:

    def run_on_ui_thread(function):
        return function


# ============================================================
# التطبيق
# ============================================================

class VoiceControlApp(App):

    def build(self):

        self.recognizer = None
        self.listener = None

        layout = BoxLayout(
            orientation="vertical",
            padding=30,
            spacing=20
        )

        # ----------------------------------------------------
        # العنوان
        # ----------------------------------------------------

        self.title_label = Label(
            text="التحكم الصوتي بالإعدادات",
            font_name=ARABIC_FONT,
            font_size=26,
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=90
        )

        layout.add_widget(self.title_label)

        # ----------------------------------------------------
        # الحالة
        # ----------------------------------------------------

        self.status_label = Label(
            text="اضغط على زر بدء الاستماع",
            font_name=ARABIC_FONT,
            font_size=20,
            halign="center",
            valign="middle"
        )

        layout.add_widget(self.status_label)

        # ----------------------------------------------------
        # الكلام الذي تم التعرف عليه
        # ----------------------------------------------------

        self.result_label = Label(
            text="",
            font_name=ARABIC_FONT,
            font_size=19,
            halign="center",
            valign="middle"
        )

        layout.add_widget(self.result_label)

        # ----------------------------------------------------
        # زر بدء الاستماع
        # ----------------------------------------------------

        start_button = Button(
            text="بدء الاستماع",
            font_name=ARABIC_FONT,
            font_size=22,
            size_hint_y=None,
            height=75
        )

        start_button.bind(
            on_release=self.start_listening
        )

        layout.add_widget(start_button)

        # ----------------------------------------------------
        # زر الإيقاف
        # ----------------------------------------------------

        stop_button = Button(
            text="إيقاف الاستماع",
            font_name=ARABIC_FONT,
            font_size=20,
            size_hint_y=None,
            height=65
        )

        stop_button.bind(
            on_release=self.stop_listening
        )

        layout.add_widget(stop_button)

        # ----------------------------------------------------
        # زر المسح
        # ----------------------------------------------------

        clear_button = Button(
            text="مسح النص",
            font_name=ARABIC_FONT,
            font_size=20,
            size_hint_y=None,
            height=65
        )

        clear_button.bind(
            on_release=self.clear_text
        )

        layout.add_widget(clear_button)

        return layout


    # ========================================================
    # تحديث الحالة
    # ========================================================

    def set_status(self, text):

        Clock.schedule_once(
            lambda dt: self._set_status(text),
            0
        )


    def _set_status(self, text):

        self.status_label.text = text


    # ========================================================
    # تحديث النص
    # ========================================================

    def set_result(self, text):

        Clock.schedule_once(
            lambda dt: self._set_result(text),
            0
        )


    def _set_result(self, text):

        self.result_label.text = text


    # ========================================================
    # بدء الاستماع
    # ========================================================

    def start_listening(self, *args):

        self.set_status(
            "جاري طلب صلاحية الميكروفون..."
        )

        try:

            from android.permissions import (
                request_permissions,
                Permission
            )

            request_permissions([
                Permission.RECORD_AUDIO
            ])

            # ننتظر لحظة حتى تظهر/تُعالج نافذة الصلاحية
            Clock.schedule_once(
                self.start_recognition,
                1.0
            )

        except Exception as e:

            self.set_status(
                "تعذر طلب صلاحية الميكروفون"
            )

            self.set_result(
                str(e)
            )


    # ========================================================
    # تشغيل SpeechRecognizer
    #
    # هذه الدالة تعمل على Android Main Thread
    # ========================================================

    @run_on_ui_thread
    def start_recognition(self, *args):

        try:

            from jnius import (
                autoclass,
                PythonJavaClass,
                java_method
            )

            # ------------------------------------------------
            # Android Classes
            # ------------------------------------------------

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

                self.set_status(
                    "التعرف الصوتي غير متوفر على هذا الجهاز"
                )

                return

            # ------------------------------------------------
            # إتلاف أي Recognizer قديم
            # ------------------------------------------------

            self.destroy_recognizer()

            app = self

            # =================================================
            # Recognition Listener
            # =================================================

            class VoiceRecognitionListener(
                PythonJavaClass
            ):

                __javainterfaces__ = [
                    "android.speech.RecognitionListener"
                ]

                # ---------------------------------------------
                # جاهز للاستماع
                # ---------------------------------------------

                @java_method(
                    "(Landroid/os/Bundle;)V"
                )
                def onReadyForSpeech(
                    self,
                    params
                ):

                    app.set_status(
                        "جاهز للاستماع..."
                    )


                # ---------------------------------------------
                # بدأ الكلام
                # ---------------------------------------------

                @java_method("()V")
                def onBeginningOfSpeech(
                    self
                ):

                    app.set_status(
                        "أستمع إليك..."
                    )


                # ---------------------------------------------
                # استقبال البيانات
                # ---------------------------------------------

                @java_method("([B)V")
                def onBufferReceived(
                    self,
                    buffer
                ):

                    pass


                # ---------------------------------------------
                # انتهاء الكلام
                # ---------------------------------------------

                @java_method("()V")
                def onEndOfSpeech(
                    self
                ):

                    app.set_status(
                        "جارٍ معالجة الكلام..."
                    )


                # ---------------------------------------------
                # خطأ
                # ---------------------------------------------

                @java_method("(I)V")
                def onError(
                    self,
                    error
                ):

                    error_messages = {

                        1: "خطأ في الشبكة",

                        2: "الشبكة غير متوفرة",

                        3: "الخادم مشغول",

                        4: "الخدمة غير متاحة",

                        5: "خطأ في التطبيق",

                        6: "لم يبدأ الكلام",

                        7: "لم يتم العثور على كلام",

                        8: "انتهت مهلة التعرف",

                        9: "صلاحية التعرف غير متوفرة"
                    }

                    message = error_messages.get(
                        error,
                        "حدث خطأ في التعرف الصوتي"
                    )

                    app.set_status(
                        message
                    )


                # ---------------------------------------------
                # النتائج الجزئية
                # ---------------------------------------------

                @java_method(
                    "(Landroid/os/Bundle;)V"
                )
                def onPartialResults(
                    self,
                    results
                ):

                    app.read_results(
                        results,
                        False
                    )


                # ---------------------------------------------
                # النتيجة النهائية
                # ---------------------------------------------

                @java_method(
                    "(Landroid/os/Bundle;)V"
                )
                def onResults(
                    self,
                    results
                ):

                    app.read_results(
                        results,
                        True
                    )


                # ---------------------------------------------
                # مستوى الصوت
                # ---------------------------------------------

                @java_method("(F)V")
                def onRmsChanged(
                    self,
                    rmsdB
                ):

                    pass


                # ---------------------------------------------
                # الأحداث
                # ---------------------------------------------

                @java_method(
                    "(ILandroid/os/Bundle;)V"
                )
                def onEvent(
                    self,
                    eventType,
                    params
                ):

                    pass


            # ------------------------------------------------
            # إنشاء Listener
            # ------------------------------------------------

            self.listener = VoiceRecognitionListener()

            # ------------------------------------------------
            # إنشاء SpeechRecognizer
            # ------------------------------------------------

            self.recognizer = (
                SpeechRecognizer.createSpeechRecognizer(
                    activity
                )
            )

            # ------------------------------------------------
            # ربط Listener
            # ------------------------------------------------

            self.recognizer.setRecognitionListener(
                self.listener
            )

            # ------------------------------------------------
            # Intent
            # ------------------------------------------------

            intent = Intent(
                RecognizerIntent.ACTION_RECOGNIZE_SPEECH
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )

            # اللغة العربية
            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE,
                "ar-YE"
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE,
                "ar-YE"
            )

            # النتائج الجزئية
            intent.putExtra(
                RecognizerIntent.EXTRA_PARTIAL_RESULTS,
                True
            )

            # ------------------------------------------------
            # بدء الاستماع
            # ------------------------------------------------

            self.set_status(
                "جاري الاستماع..."
            )

            self.recognizer.startListening(
                intent
            )

        except Exception as e:

            self.set_status(
                "تعذر تشغيل التعرف الصوتي"
            )

            self.set_result(
                str(e)
            )


    # ========================================================
    # قراءة نتائج التعرف الصوتي
    # ========================================================

    def read_results(
        self,
        results,
        final_result=False
    ):

        try:

            if results is None:
                return

            values = results.getStringArrayList(
                "results_recognition"
            )

            if values is None:
                return

            if values.size() == 0:
                return

            text = str(
                values.get(0)
            )

            if not text:
                return

            # عرض الكلام
            self.set_result(
                text
            )

            # ------------------------------------------------
            # نتيجة نهائية
            # ------------------------------------------------

            if final_result:

                self.set_status(
                    "تم التعرف على الأمر"
                )

                Clock.schedule_once(
                    lambda dt: self.process_command(text),
                    0
                )

            # ------------------------------------------------
            # نتيجة جزئية
            # ------------------------------------------------

            else:

                self.set_status(
                    "أستمع: " + text
                )

        except Exception as e:

            self.set_result(
                str(e)
            )


    # ========================================================
    # إيقاف الاستماع
    # ========================================================

    def stop_listening(self, *args):

        self.stop_recognition()


    @run_on_ui_thread
    def stop_recognition(self, *args):

        try:

            self.destroy_recognizer()

            self.set_status(
                "تم إيقاف الاستماع"
            )

        except Exception as e:

            self.set_status(
                "تم إيقاف الاستماع"
            )

            self.set_result(
                str(e)
            )


    # ========================================================
    # تدمير SpeechRecognizer
    #
    # يجب أن يتم على Main Thread
    # ========================================================

    @run_on_ui_thread
    def destroy_recognizer(self):

        if self.recognizer is not None:

            try:
                self.recognizer.stopListening()
            except Exception:
                pass

            try:
                self.recognizer.cancel()
            except Exception:
                pass

            try:
                self.recognizer.destroy()
            except Exception:
                pass

        self.recognizer = None
        self.listener = None


    # ========================================================
    # معالجة الأمر الصوتي
    # ========================================================

    def process_command(self, text):

        command = text.strip().lower()

        # ----------------------------------------------------
        # Wi-Fi
        # ----------------------------------------------------

        if (
            "واي فاي" in command
            or "وايفاي" in command
            or "wifi" in command
            or "wi-fi" in command
        ):

            self.set_status(
                "فتح إعدادات الواي فاي..."
            )

            self.open_settings(
                "android.settings.WIFI_SETTINGS"
            )

            return

        # ----------------------------------------------------
        # Bluetooth
        # ----------------------------------------------------

        if "بلوتوث" in command:

            self.set_status(
                "فتح إعدادات البلوتوث..."
            )

            self.open_settings(
                "android.settings.BLUETOOTH_SETTINGS"
            )

            return

        # ----------------------------------------------------
        # السطوع
        # ----------------------------------------------------

        if (
            "سطوع" in command
            or "إضاءة الشاشة" in command
            or "اضاءة الشاشة" in command
        ):

            self.set_status(
                "فتح إعدادات الشاشة..."
            )

            self.open_settings(
                "android.settings.DISPLAY_SETTINGS"
            )

            return

        # ----------------------------------------------------
        # رفع الصوت
        # ----------------------------------------------------

        if (
            "رفع الصوت" in command
            or "زيادة الصوت" in command
            or "عل الصوت" in command
        ):

            self.change_volume(
                1
            )

            return

        # ----------------------------------------------------
        # خفض الصوت
        # ----------------------------------------------------

        if (
            "خفض الصوت" in command
            or "نقص الصوت" in command
            or "وطي الصوت" in command
        ):

            self.change_volume(
                -1
            )

            return

        # ----------------------------------------------------
        # أمر صوت عام
        # ----------------------------------------------------

        if "صوت" in command:

            self.set_status(
                "تم التعرف على أمر الصوت"
            )

            return

        # ----------------------------------------------------
        # أمر غير معروف
        # ----------------------------------------------------

        self.set_status(
            "تم التعرف على الكلام، لكن الأمر غير معروف"
        )


    # ========================================================
    # فتح إعدادات Android
    # ========================================================

    def open_settings(
        self,
        action
    ):

        self._open_settings(
            action
        )


    @run_on_ui_thread
    def _open_settings(
        self,
        action
    ):

        try:

            from jnius import autoclass

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            Intent = autoclass(
                "android.content.Intent"
            )

            activity = PythonActivity.mActivity

            intent = Intent(
                action
            )

            activity.startActivity(
                intent
            )

        except Exception as e:

            self.set_result(
                str(e)
            )


    # ========================================================
    # تغيير مستوى الصوت
    # ========================================================

    def change_volume(
        self,
        direction
    ):

        self._change_volume(
            direction
        )


    @run_on_ui_thread
    def _change_volume(
        self,
        direction
    ):

        try:

            from jnius import autoclass

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            Context = autoclass(
                "android.content.Context"
            )

            AudioManager = autoclass(
                "android.media.AudioManager"
            )

            activity = PythonActivity.mActivity

            audio_manager = (
                activity.getSystemService(
                    Context.AUDIO_SERVICE
                )
            )

            # ------------------------------------------------
            # رفع الصوت
            # ------------------------------------------------

            if direction > 0:

                audio_manager.adjustVolume(
                    AudioManager.ADJUST_RAISE,
                    AudioManager.FLAG_SHOW_UI
                )

                self.set_status(
                    "تم رفع الصوت"
                )

                return

            # ------------------------------------------------
            # خفض الصوت
            # ------------------------------------------------

            audio_manager.adjustVolume(
                AudioManager.ADJUST_LOWER,
                AudioManager.FLAG_SHOW_UI
            )

            self.set_status(
                "تم خفض الصوت"
            )

        except Exception as e:

            self.set_result(
                str(e)
            )


    # ========================================================
    # مسح النص
    # ========================================================

    def clear_text(
        self,
        *args
    ):

        self.result_label.text = ""

        self.status_label.text = (
            "اضغط على زر بدء الاستماع"
        )


    # ========================================================
    # إغلاق التطبيق
    # ========================================================

    def on_stop(self):

        try:

            if self.recognizer is not None:

                self.stop_recognition()

        except Exception:

            pass


# ============================================================
# تشغيل التطبيق
# ============================================================

if __name__ == "__main__":

    VoiceControlApp().run()
