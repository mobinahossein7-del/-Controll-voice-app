# -*- coding: utf-8 -*-

from __future__ import annotations

import re

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView


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
# Android permissions
# ============================================================

try:
    from android.permissions import (
        Permission,
        check_permission,
        request_permissions,
    )
except Exception:
    Permission = None
    check_permission = None
    request_permissions = None


# ============================================================
# PyJNIus
# ============================================================

try:
    from jnius import (
        autoclass,
        PythonJavaClass,
        java_method,
    )
except Exception:
    autoclass = None
    PythonJavaClass = object

    def java_method(*args, **kwargs):
        def decorator(function):
            return function
        return decorator


# ============================================================
# Speech Recognition Listener
# ============================================================

class SpeechListener(PythonJavaClass):

    __javainterfaces__ = [
        "android/speech/RecognitionListener"
    ]

    def __init__(self, app):
        super().__init__()
        self.app = app

    @java_method("(Landroid/os/Bundle;)V")
    def onReadyForSpeech(self, params):
        self.app.set_status("🎙️ استمع الآن...")

    @java_method("()V")
    def onBeginningOfSpeech(self):
        self.app.set_status("🎙️ أستمع إلى كلامك...")

    @java_method("(F)V")
    def onRmsChanged(self, rmsdB):
        pass

    @java_method("([B)V")
    def onBufferReceived(self, buffer):
        pass

    @java_method("()V")
    def onEndOfSpeech(self):
        self.app.set_status("⏳ جارٍ تحليل الأمر...")

    @java_method("(I)V")
    def onError(self, error):

        messages = {
            1: "لم أفهم الكلام، حاول مرة أخرى.",
            2: "تعذر الاتصال بخدمة التعرف الصوتي.",
            3: "انتهى وقت التعرف الصوتي.",
            4: "خدمة التعرف الصوتي غير متاحة.",
            5: "حدث خطأ في الصوت.",
            6: "لم يبدأ الكلام.",
            7: "لم يتم العثور على نتيجة.",
            8: "خدمة التعرف مشغولة.",
            9: "صلاحية التعرف الصوتي غير مسموحة.",
        }

        message = messages.get(
            error,
            f"حدث خطأ في التعرف الصوتي: {error}"
        )

        self.app.set_status(message)
        self.app.set_listening(False)

    @java_method("(Landroid/os/Bundle;)V")
    def onResults(self, results):
        self.app.handle_speech_results(results)
        self.app.set_listening(False)

    @java_method("(Landroid/os/Bundle;)V")
    def onPartialResults(self, results):
        self.app.handle_partial_results(results)

    @java_method("(ILandroid/os/Bundle;)V")
    def onEvent(self, eventType, params):
        pass


# ============================================================
# التطبيق
# ============================================================

class VoiceControlApp(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.recognizer = None
        self.listener = None
        self.activity = None

        self.is_listening = False

        self.Intent = None
        self.RecognizerIntent = None

        self.AudioManager = None
        self.Settings = None

    # --------------------------------------------------------
    # بناء الواجهة
    # --------------------------------------------------------

    def build(self):

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12)
        )

        # العنوان
        title = Label(
            text="التحكم الصوتي",
            font_name=ARABIC_FONT,
            font_size=dp(27),
            size_hint_y=None,
            height=dp(60),
            halign="center",
            valign="middle"
        )

        title.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        root.add_widget(title)

        # الحالة
        self.status_label = Label(
            text="اضغط على زر التحدث",
            font_name=ARABIC_FONT,
            font_size=dp(18),
            size_hint_y=None,
            height=dp(55),
            halign="center",
            valign="middle"
        )

        self.status_label.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        root.add_widget(self.status_label)

        # النص المتعرف عليه
        self.result_label = Label(
            text="لم يتم التعرف على أي أمر بعد",
            font_name=ARABIC_FONT,
            font_size=dp(17),
            size_hint_y=None,
            height=dp(100),
            halign="center",
            valign="middle"
        )

        self.result_label.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        root.add_widget(self.result_label)

        # زر التحدث
        self.listen_button = Button(
            text="🎙️ بدء الاستماع",
            font_name=ARABIC_FONT,
            font_size=dp(20),
            size_hint_y=None,
            height=dp(65)
        )

        self.listen_button.bind(
            on_release=self.toggle_listening
        )

        root.add_widget(self.listen_button)

        # ScrollView للأوامر
        scroll = ScrollView(
            size_hint=(1, 1)
        )

        commands = Label(
            text=(
                "الأوامر المتاحة:\n\n"

                "🔊 ارفع الصوت\n"
                "🔉 اخفض الصوت\n"
                "🔇 كتم الصوت\n\n"

                "💡 ارفع السطوع\n"
                "💡 اخفض السطوع\n\n"

                "📶 افتح إعدادات الواي فاي\n"
                "🔵 افتح إعدادات البلوتوث\n"
                "📱 افتح إعدادات الشاشة\n"
                "⚙️ افتح الإعدادات\n"
            ),
            font_name=ARABIC_FONT,
            font_size=dp(16),
            size_hint_y=None,
            halign="right",
            valign="top"
        )

        commands.bind(
            texture_size=lambda instance, value:
            setattr(instance, "height", value[1] + dp(20))
        )

        commands.bind(
            width=lambda instance, value:
            setattr(instance, "text_size", (value, None))
        )

        scroll.add_widget(commands)
        root.add_widget(scroll)

        # الأزرار السفلية
        bottom = BoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(55)
        )

        help_button = Button(
            text="المساعدة",
            font_name=ARABIC_FONT,
            font_size=dp(16)
        )

        clear_button = Button(
            text="مسح",
            font_name=ARABIC_FONT,
            font_size=dp(16)
        )

        help_button.bind(
            on_release=lambda *_:
            self.show_help()
        )

        clear_button.bind(
            on_release=lambda *_:
            self.clear_result()
        )

        bottom.add_widget(help_button)
        bottom.add_widget(clear_button)

        root.add_widget(bottom)

        # تجهيز Android
        Clock.schedule_once(
            lambda dt: self.setup_android(),
            0.5
        )

        return root

    # --------------------------------------------------------
    # Android
    # --------------------------------------------------------

    def setup_android(self):

        if autoclass is None:
            self.set_status(
                "بيئة Android غير متاحة."
            )
            return

        try:

            self.SpeechRecognizer = autoclass(
                "android.speech.SpeechRecognizer"
            )

            Context = autoclass(
                "android.content.Context"
            )

            self.activity = autoclass(
                "org.kivy.android.PythonActivity"
            ).mActivity

            if not self.SpeechRecognizer.isRecognitionAvailable(
                self.activity
            ):
                self.set_status(
                    "التعرف الصوتي غير متاح على هذا الهاتف."
                )
                return

            self.Intent = autoclass(
                "android.content.Intent"
            )

            self.RecognizerIntent = autoclass(
                "android.speech.RecognizerIntent"
            )

            self.AudioManager = autoclass(
                "android.media.AudioManager"
            )

            self.Settings = autoclass(
                "android.provider.Settings"
            )

            self.recognizer = (
                self.SpeechRecognizer
                .createSpeechRecognizer(
                    self.activity
                )
            )

            self.listener = SpeechListener(self)

            self.recognizer.setRecognitionListener(
                self.listener
            )

            self.request_microphone_permission()

        except Exception as e:

            self.set_status(
                f"خطأ في تجهيز Android: {e}"
            )

    # --------------------------------------------------------
    # صلاحية الميكروفون
    # --------------------------------------------------------

    def request_microphone_permission(self):

        if Permission is None:
            return

        try:

            permission = Permission.RECORD_AUDIO

            if check_permission is not None:

                if not check_permission(permission):

                    request_permissions(
                        [permission],
                        self.permission_callback
                    )

        except Exception as e:

            self.set_status(
                f"تعذر طلب صلاحية الميكروفون: {e}"
            )

    def permission_callback(
        self,
        permissions,
        grant_results
    ):
        Clock.schedule_once(
            lambda dt:
            self.set_status(
                "يمكنك الآن الضغط على بدء الاستماع."
            ),
            0
        )

    # --------------------------------------------------------
    # بدء / إيقاف الاستماع
    # --------------------------------------------------------

    def toggle_listening(self, *_):

        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()

    def start_listening(self):

        if self.recognizer is None:

            self.set_status(
                "التعرف الصوتي غير جاهز."
            )
            return

        try:

            self.is_listening = True

            self.listen_button.text = (
                "⏹️ إيقاف الاستماع"
            )

            self.set_status(
                "🎙️ جارٍ تشغيل الميكروفون..."
            )

            intent = self.Intent(
                self.RecognizerIntent.ACTION_RECOGNIZE_SPEECH
            )

            intent.putExtra(
                self.RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                self.RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )

            intent.putExtra(
                self.RecognizerIntent.EXTRA_LANGUAGE,
                "ar"
            )

            intent.putExtra(
                self.RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE,
                "ar"
            )

            intent.putExtra(
                self.RecognizerIntent.EXTRA_PARTIAL_RESULTS,
                True
            )

            intent.putExtra(
                self.RecognizerIntent.EXTRA_MAX_RESULTS,
                5
            )

            self.recognizer.startListening(
                intent
            )

        except Exception as e:

            self.is_listening = False

            self.listen_button.text = (
                "🎙️ بدء الاستماع"
            )

            self.set_status(
                f"خطأ في بدء الاستماع: {e}"
            )

    def stop_listening(self):

        try:

            if self.recognizer:
                self.recognizer.stopListening()

        except Exception:
            pass

        self.set_listening(False)

        self.set_status(
            "تم إيقاف الاستماع."
        )

    # --------------------------------------------------------
    # النتائج
    # --------------------------------------------------------

    def get_results_from_bundle(self, results):

        try:

            matches = results.getStringArrayList(
                self.RecognizerIntent.EXTRA_RESULTS
            )

            if matches is None:
                return []

            return [
                str(matches.get(i))
                for i in range(matches.size())
            ]

        except Exception:
            return []

    def handle_partial_results(self, results):

        try:

            matches = self.get_results_from_bundle(
                results
            )

            if matches:

                self.result_label.text = (
                    "🎙️ " + matches[0]
                )

        except Exception:
            pass

    def handle_speech_results(self, results):

        try:

            matches = self.get_results_from_bundle(
                results
            )

            if not matches:

                self.set_status(
                    "لم يتم التعرف على الكلام."
                )

                return

            text = matches[0]

            self.result_label.text = (
                "🗣️ " + text
            )

            self.execute_command(
                text
            )

        except Exception as e:

            self.set_status(
                f"خطأ في معالجة الكلام: {e}"
            )

    # --------------------------------------------------------
    # تنظيف النص
    # --------------------------------------------------------

    def normalize_text(self, text):

        text = text.lower().strip()

        text = text.replace(
            "أ", "ا"
        ).replace(
            "إ", "ا"
        ).replace(
            "آ", "ا"
        )

        text = re.sub(
            r"[ًٌٍَُِّْـ]",
            "",
            text
        )

        return text

    # --------------------------------------------------------
    # تنفيذ الأوامر
    # --------------------------------------------------------

    def execute_command(self, text):

        original = text
        text = self.normalize_text(text)

        # -----------------------------
        # الصوت
        # -----------------------------

        if (
            "ارفع الصوت" in text
            or "علي الصوت" in text
            or "رفع الصوت" in text
            or "زد الصوت" in text
        ):

            self.volume_up()

            self.set_status(
                "🔊 تم رفع الصوت."
            )

            return

        if (
            "اخفض الصوت" in text
            or "نزل الصوت" in text
            or "خفض الصوت" in text
            or "قلل الصوت" in text
        ):

            self.volume_down()

            self.set_status(
                "🔉 تم خفض الصوت."
            )

            return

        if (
            "كتم الصوت" in text
            or "اكتم الصوت" in text
            or "صامت" in text
        ):

            self.volume_mute()

            self.set_status(
                "🔇 تم كتم الصوت."
            )

            return

        # -----------------------------
        # السطوع
        # -----------------------------

        if (
            "ارفع السطوع" in text
            or "علي السطوع" in text
            or "زد السطوع" in text
        ):

            self.brightness_up()

            return

        if (
            "اخفض السطوع" in text
            or "خفض السطوع" in text
            or "قلل السطوع" in text
        ):

            self.brightness_down()

            return

        # -----------------------------
        # Wi-Fi
        # -----------------------------

        if (
            "واي فاي" in text
            or "وايفاي" in text
            or "wifi" in text
        ):

            self.open_wifi_settings()

            return

        # -----------------------------
        # Bluetooth
        # -----------------------------

        if (
            "بلوتوث" in text
            or "bluetooth" in text
        ):

            self.open_bluetooth_settings()

            return

        # -----------------------------
        # الشاشة
        # -----------------------------

        if (
            "اعدادات الشاشة" in text
            or "الشاشة" in text
        ):

            self.open_display_settings()

            return

        # -----------------------------
        # الإعدادات العامة
        # -----------------------------

        if (
            "افتح الاعدادات" in text
            or "اعدادات الهاتف" in text
            or "اعدادات الجهاز" in text
        ):

            self.open_general_settings()

            return

        self.set_status(
            f"لم أتعرف على الأمر: {original}"
        )

    # ========================================================
    # الصوت
    # ========================================================

    def get_audio_manager(self):

        return self.activity.getSystemService(
            self.AudioManager.AUDIO_SERVICE
        )

    def volume_up(self):

        try:

            manager = self.get_audio_manager()

            manager.adjustStreamVolume(
                self.AudioManager.STREAM_MUSIC,
                self.AudioManager.ADJUST_RAISE,
                0
            )

        except Exception as e:

            self.set_status(
                f"تعذر رفع الصوت: {e}"
            )

    def volume_down(self):

        try:

            manager = self.get_audio_manager()

            manager.adjustStreamVolume(
                self.AudioManager.STREAM_MUSIC,
                self.AudioManager.ADJUST_LOWER,
                0
            )

        except Exception as e:

            self.set_status(
                f"تعذر خفض الصوت: {e}"
            )

    def volume_mute(self):

        try:

            manager = self.get_audio_manager()

            manager.adjustStreamVolume(
                self.AudioManager.STREAM_MUSIC,
                self.AudioManager.ADJUST_MUTE,
                0
            )

        except Exception as e:

            self.set_status(
                f"تعذر كتم الصوت: {e}"
            )

    # ========================================================
    # السطوع
    # ========================================================

    def brightness_up(self):

        try:

            SettingsSystem = self.Settings.System

            if not SettingsSystem.canWrite(
                self.activity
            ):

                self.set_status(
                    "اسمح للتطبيق بتعديل إعدادات النظام أولاً."
                )

                intent = self.Intent(
                    self.Settings.ACTION_MANAGE_WRITE_SETTINGS
                )

                self.activity.startActivity(intent)

                return

            current = SettingsSystem.getInt(
                self.activity.getContentResolver(),
                SettingsSystem.SCREEN_BRIGHTNESS
            )

            value = min(
                255,
                current + 30
            )

            SettingsSystem.putInt(
                self.activity.getContentResolver(),
                SettingsSystem.SCREEN_BRIGHTNESS,
                value
            )

            self.set_status(
                "💡 تم رفع السطوع."
            )

        except Exception as e:

            self.set_status(
                f"تعذر تغيير السطوع: {e}"
            )

    def brightness_down(self):

        try:

            SettingsSystem = self.Settings.System

            if not SettingsSystem.canWrite(
                self.activity
            ):

                self.set_status(
                    "اسمح للتطبيق بتعديل إعدادات النظام أولاً."
                )

                intent = self.Intent(
                    self.Settings.ACTION_MANAGE_WRITE_SETTINGS
                )

                self.activity.startActivity(intent)

                return

            current = SettingsSystem.getInt(
                self.activity.getContentResolver(),
                SettingsSystem.SCREEN_BRIGHTNESS
            )

            value = max(
                1,
                current - 30
            )

            SettingsSystem.putInt(
                self.activity.getContentResolver(),
                SettingsSystem.SCREEN_BRIGHTNESS,
                value
            )

            self.set_status(
                "💡 تم خفض السطوع."
            )

        except Exception as e:

            self.set_status(
                f"تعذر تغيير السطوع: {e}"
            )

    # ========================================================
    # فتح إعدادات Android
    # ========================================================

    def open_wifi_settings(self):

        try:

            intent = self.Intent(
                "android.settings.WIFI_SETTINGS"
            )

            self.activity.startActivity(intent)

            self.set_status(
                "📶 تم فتح إعدادات Wi-Fi."
            )

        except Exception as e:

            self.set_status(
                f"تعذر فتح Wi-Fi: {e}"
            )

    def open_bluetooth_settings(self):

        try:

            intent = self.Intent(
                "android.settings.BLUETOOTH_SETTINGS"
            )

            self.activity.startActivity(intent)

            self.set_status(
                "🔵 تم فتح إعدادات Bluetooth."
            )

        except Exception as e:

            self.set_status(
                f"تعذر فتح Bluetooth: {e}"
            )

    def open_display_settings(self):

        try:

            intent = self.Intent(
                "android.settings.DISPLAY_SETTINGS"
            )

            self.activity.startActivity(intent)

            self.set_status(
                "📱 تم فتح إعدادات الشاشة."
            )

        except Exception as e:

            self.set_status(
                f"تعذر فتح إعدادات الشاشة: {e}"
            )

    def open_general_settings(self):

        try:

            intent = self.Intent(
                "android.settings.SETTINGS"
            )

            self.activity.startActivity(intent)

            self.set_status(
                "⚙️ تم فتح إعدادات الهاتف."
            )

        except Exception as e:

            self.set_status(
                f"تعذر فتح الإعدادات: {e}"
            )

    # ========================================================
    # أدوات الواجهة
    # ========================================================

    def set_status(self, text):

        def update(_dt):

            if hasattr(
                self,
                "status_label"
            ):
                self.status_label.text = text

        Clock.schedule_once(
            update,
            0
        )

    def set_listening(self, value):

        self.is_listening = value

        def update(_dt):

            if hasattr(
                self,
                "listen_button"
            ):

                self.listen_button.text = (
                    "⏹️ إيقاف الاستماع"
                    if value
                    else
                    "🎙️ بدء الاستماع"
                )

        Clock.schedule_once(
            update,
            0
        )

    def clear_result(self):

        self.result_label.text = (
            "لم يتم التعرف على أي أمر بعد"
        )

        self.set_status(
            "جاهز للاستماع."
        )

    def show_help(self):

        self.result_label.text = (
            "مثال:\n"
            "ارفع الصوت\n"
            "اخفض الصوت\n"
            "كتم الصوت\n"
            "ارفع السطوع\n"
            "اخفض السطوع\n"
            "افتح الواي فاي\n"
            "افتح البلوتوث\n"
            "افتح إعدادات الشاشة\n"
            "افتح الإعدادات"
        )

        self.set_status(
            "🎙️ قل أحد الأوامر السابقة."
        )


# ============================================================
# تشغيل التطبيق
# ============================================================

if __name__ == "__main__":
    VoiceControlApp().run()
