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

FONT_FILE = "NotoKufiArabic-Regular.ttf"

try:
    LabelBase.register(name="Arabic", fn_regular=FONT_FILE)
    ARABIC_FONT = "Arabic"
except Exception:
    ARABIC_FONT = "Roboto"

try:
    from android.permissions import Permission, request_permissions
except Exception:
    Permission = None
    request_permissions = None

try:
    from jnius import autoclass, PythonJavaClass, java_method
except Exception:
    autoclass = None
    PythonJavaClass = object

    def java_method(*args, **kwargs):
        def decorator(fn):
            return fn
        return decorator


class SpeechListener(PythonJavaClass):
    __javainterfaces__ = ["android/speech/RecognitionListener"]

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
            5: "خطأ في الصوت.",
            6: "لم يبدأ الكلام.",
            7: "لم يتم العثور على نتيجة.",
            8: "خدمة التعرف مشغولة.",
            9: "صلاحية التعرف الصوتي غير مسموحة.",
        }

        self.app.set_status(
            messages.get(error, f"حدث خطأ في التعرف: {error}")
        )
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


class VoiceControlApp(App):

    title = "التحكم الصوتي"

    recognizer = None
    listener = None
    is_listening = False

    def build(self):

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
        )

        title = Label(
            text="التحكم الصوتي",
            font_name=ARABIC_FONT,
            font_size=dp(25),
            size_hint_y=None,
            height=dp(55),
        )

        root.add_widget(title)

        self.status = Label(
            text="اضغط على زر التحدث ثم قل أمرًا",
            font_name=ARABIC_FONT,
            font_size=dp(17),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(70),
        )

        self.status.bind(size=self._update_text_size)
        root.add_widget(self.status)

        self.result = Label(
            text="لم يتم التعرف على أي أمر بعد.",
            font_name=ARABIC_FONT,
            font_size=dp(18),
            halign="right",
            valign="top",
            size_hint_y=None,
            height=dp(150),
        )

        self.result.bind(
            texture_size=self._update_result_height
        )

        self.result.bind(
            size=self._update_text_size
        )

        scroll = ScrollView(
            size_hint=(1, 1)
        )

        scroll.add_widget(self.result)
        root.add_widget(scroll)

        self.listen_button = Button(
            text="🎙️ بدء الاستماع",
            font_name=ARABIC_FONT,
            font_size=dp(20),
            size_hint_y=None,
            height=dp(58),
        )

        self.listen_button.bind(
            on_release=self.toggle_listening
        )

        root.add_widget(self.listen_button)

        row = BoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(55),
        )

        clear_btn = Button(
            text="مسح",
            font_name=ARABIC_FONT,
            font_size=dp(17),
        )

        clear_btn.bind(
            on_release=lambda *_: self.clear_text()
        )

        help_btn = Button(
            text="الأوامر",
            font_name=ARABIC_FONT,
            font_size=dp(17),
        )

        help_btn.bind(
            on_release=lambda *_: self.show_help()
        )

        row.add_widget(clear_btn)
        row.add_widget(help_btn)

        root.add_widget(row)

        Clock.schedule_once(
            lambda *_: self.prepare_android(),
            0.5
        )

        return root

    def _update_text_size(self, instance, _size):
        instance.text_size = (
            instance.width - dp(10),
            None
        )

    def _update_result_height(self, instance, _size):
        self.result.height = max(
            dp(150),
            instance.texture_size[1] + dp(20)
        )

    def set_status(self, text):
        Clock.schedule_once(
            lambda *_: setattr(
                self.status,
                "text",
                text
            )
        )

    def set_listening(self, value):

        self.is_listening = value

        Clock.schedule_once(
            self._update_button
        )

    def _update_button(self, *_):

        if self.is_listening:
            self.listen_button.text = (
                "⏹️ إيقاف الاستماع"
            )
        else:
            self.listen_button.text = (
                "🎙️ بدء الاستماع"
            )

    def clear_text(self):

        self.result.text = "تم مسح النص."

        self.set_status(
            "جاهز للاستماع."
        )

    def show_help(self):

        self.result.text = (
            "أمثلة على الأوامر:\n\n"

            "• ارفع الصوت\n"
            "• اخفض الصوت\n"
            "• كتم الصوت\n"
            "• الصوت 50 بالمئة\n\n"

            "• سطوع 50 بالمئة\n"
            "• ارفع السطوع\n"
            "• اخفض السطوع\n\n"

            "• شغل الواي فاي\n"
            "• أوقف الواي فاي\n"
            "• افتح إعدادات الواي فاي\n\n"

            "• افتح البلوتوث\n"
            "• افتح الإعدادات\n"
            "• افتح إعدادات الشاشة"
        )

    # ---------------- Android ----------------

    def prepare_android(self):

        if autoclass is None:

            self.set_status(
                "هذا الإصدار يحتاج Android + PyJNIus."
            )

            return

        if Permission is not None:

            try:

                request_permissions(
                    [Permission.RECORD_AUDIO]
                )

            except Exception:
                pass

        try:

            SpeechRecognizer = autoclass(
                "android.speech.SpeechRecognizer"
            )

            activity = autoclass(
                "org.kivy.android.PythonActivity"
            ).mActivity

            if not SpeechRecognizer.isRecognitionAvailable(
                activity
            ):

                self.set_status(
                    "التعرف الصوتي غير متاح على هذا الهاتف."
                )

                return

            self.recognizer = (
                SpeechRecognizer.createSpeechRecognizer(
                    activity
                )
            )

            self.listener = SpeechListener(self)

            self.recognizer.setRecognitionListener(
                self.listener
            )

            self.activity = activity

            self.Intent = autoclass(
                "android.content.Intent"
            )

            self.RecognizerIntent = autoclass(
                "android.speech.RecognizerIntent"
            )

            self.set_status(
                "جاهز. اضغط «بدء الاستماع»."
            )

        except Exception as exc:

            self.set_status(
                f"تعذر تجهيز التعرف الصوتي: {exc}"
            )

    def toggle_listening(self, *_):

        if self.is_listening:
            self.stop_listening()
        else:
            self.start_listening()

    def start_listening(self):

        if self.recognizer is None:

            self.prepare_android()

            if self.recognizer is None:
                return

        try:

            intent = self.Intent(
                self.RecognizerIntent.ACTION_RECOGNIZE_SPEECH
            )

            intent.putExtra(
                self.RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                self.RecognizerIntent.LANGUAGE_MODEL_FREE_FORM,
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

            self.set_listening(True)

            self.set_status(
                "🎙️ استمع الآن..."
            )

        except Exception as exc:

            self.set_status(
                f"تعذر بدء الاستماع: {exc}"
            )

            self.set_listening(False)

    def stop_listening(self):

        try:

            if self.recognizer is not None:
                self.recognizer.stopListening()

        except Exception:
            pass

        self.set_listening(False)

        self.set_status(
            "تم إيقاف الاستماع."
        )

    def _bundle_text(self, bundle):

        if bundle is None:
            return ""

        try:

            texts = bundle.getStringArrayList(
                self.RecognizerIntent.EXTRA_RESULTS
            )

            if texts is None:
                return ""

            return " / ".join(
                str(x) for x in texts[:5]
            )

        except Exception:

            return ""

    def handle_partial_results(self, bundle):

        text = self._bundle_text(bundle)

        if text:

            self.result.text = (
                f"أسمع: {text}"
            )

    def handle_speech_results(self, bundle):

        text = self._bundle_text(bundle)

        if not text:

            self.set_status(
                "لم يتم التعرف على الكلام."
            )

            return

        self.result.text = (
            f"الأمر: {text}"
        )

        first = text.split(
            " / "
        )[0].strip()

        self.execute_command(
            first
        )

    # ---------------- Settings ----------------

    def open_settings(self, action):

        try:

            intent = self.Intent(
                action
            )

            self.activity.startActivity(
                intent
            )

            return True

        except Exception as exc:

            self.set_status(
                f"تعذر فتح الإعدادات: {exc}"
            )

            return False

    def adjust_volume(self, direction):

        try:

            AudioManager = autoclass(
                "android.media.AudioManager"
            )

            Context = autoclass(
                "android.content.Context"
            )

            audio = self.activity.getSystemService(
                Context.AUDIO_SERVICE
            )

            if direction == "up":

                audio.adjustStreamVolume(
                    AudioManager.STREAM_MUSIC,
                    AudioManager.ADJUST_RAISE,
                    AudioManager.FLAG_SHOW_UI,
                )

                self.set_status(
                    "تم رفع صوت الوسائط."
                )

            elif direction == "down":

                audio.adjustStreamVolume(
                    AudioManager.STREAM_MUSIC,
                    AudioManager.ADJUST_LOWER,
                    AudioManager.FLAG_SHOW_UI,
                )

                self.set_status(
                    "تم خفض صوت الوسائط."
                )

            elif direction == "mute":

                audio.adjustStreamVolume(
                    AudioManager.STREAM_MUSIC,
                    AudioManager.ADJUST_MUTE,
                    AudioManager.FLAG_SHOW_UI,
                )

                self.set_status(
                    "تم كتم صوت الوسائط."
                )

            return True

        except Exception as exc:

            self.set_status(
                f"تعذر التحكم بالصوت: {exc}"
            )

            return False

    def set_volume_percent(self, percent):

        try:

            percent = max(
                0,
                min(100, int(percent))
            )

            AudioManager = autoclass(
                "android.media.AudioManager"
            )

            Context = autoclass(
                "android.content.Context"
            )

            audio = self.activity.getSystemService(
                Context.AUDIO_SERVICE
            )

            maximum = audio.getStreamMaxVolume(
                AudioManager.STREAM_MUSIC
            )

            value = round(
                maximum * percent / 100.0
            )

            audio.setStreamVolume(
                AudioManager.STREAM_MUSIC,
                value,
                AudioManager.FLAG_SHOW_UI,
            )

            self.set_status(
                f"تم ضبط صوت الوسائط على {percent}٪."
            )

            return True

        except Exception as exc:

            self.set_status(
                f"تعذر ضبط الصوت: {exc}"
            )

            return False

    def _open_write_settings(self):

        try:

            Settings = autoclass(
                "android.provider.Settings"
            )

            if Settings.System.canWrite(
                self.activity
            ):

                return True

            intent = self.Intent(
                Settings.ACTION_MANAGE_WRITE_SETTINGS
            )

            Uri = autoclass(
                "android.net.Uri"
            )

            intent.setData(
                Uri.parse(
                    "package:" +
                    self.activity.getPackageName()
                )
            )

            self.activity.startActivity(
                intent
            )

            self.set_status(
                "اسمح للتطبيق بتعديل إعدادات النظام، ثم أعد أمر السطوع."
            )

            return False

        except Exception as exc:

            self.set_status(
                f"تعذر طلب صلاحية السطوع: {exc}"
            )

            return False

    def set_brightness_percent(self, percent):

        try:

            percent = max(
                1,
                min(100, int(percent))
            )

            if not self._open_write_settings():
                return False

            Settings = autoclass(
                "android.provider.Settings"
            )

            value = round(
                255 * percent / 100.0
            )

            Settings.System.putInt(
                self.activity.getContentResolver(),
                Settings.System.SCREEN_BRIGHTNESS,
                value,
            )

            self.set_status(
                f"تم ضبط السطوع على {percent}٪."
            )

            return True

        except Exception as exc:

            self.set_status(
                f"تعذر ضبط السطوع: {exc}"
            )

            return False

    def open_wifi(self):

        return self.open_settings(
            "android.settings.WIFI_SETTINGS"
        )

    def open_bluetooth(self):

        return self.open_settings(
            "android.settings.BLUETOOTH_SETTINGS"
        )

    def open_display(self):

        return self.open_settings(
            "android.settings.DISPLAY_SETTINGS"
        )

    def open_general_settings(self):

        return self.open_settings(
            "android.settings.SETTINGS"
        )

    # ---------------- Commands ----------------

    def execute_command(self, command):

        c = command.strip().lower()

        normalized = (
            c.replace("أ", "ا")
             .replace("إ", "ا")
             .replace("آ", "ا")
        )

        # Wi-Fi settings
        if (
            "اعدادات الواي فاي" in normalized
            or "اعدادات wifi" in normalized
        ):

            self.open_wifi()
            return

        # Bluetooth settings
        if "اعدادات البلوتوث" in normalized:

            self.open_bluetooth()
            return

        # Display settings
        if (
            "اعدادات الشاشه" in normalized
            or "اعدادات الشاشة" in c
        ):

            self.open_display()
            return

        # General settings
        if (
            "افتح الاعدادات" in normalized
            or "افتح الإعدادات" in c
        ):

            self.open_general_settings()
            return

        # Wi-Fi
        if (
            "واي فاي" in normalized
            or "wifi" in normalized
        ):

            self.open_wifi()

            self.set_status(
                "فتحت إعدادات Wi-Fi لتشغيلها أو إيقافها."
            )

            return

        # Bluetooth
        if (
            "بلوتوث" in normalized
            or "bluetooth" in normalized
        ):

            self.open_bluetooth()

            self.set_status(
                "فتحت إعدادات Bluetooth."
            )

            return

        # Mute
        if (
            "كتم الصوت" in normalized
            or normalized == "اكتم"
        ):

            self.adjust_volume(
                "mute"
            )

            return

        # Volume percentage
        m = re.search(
            r"(?:صوت|مستوى الصوت)\s*(\d{1,3})"
            r"\s*(?:بالمئة|بالمائة|٪|%)?",
            normalized
        )

        if m:

            self.set_volume_percent(
                m.group(1)
            )

            return

        # Increase volume
        if any(
            x in normalized
            for x in [
                "ارفع الصوت",
                "علي الصوت",
                "اعلى الصوت",
            ]
        ):

            self.adjust_volume(
                "up"
            )

            return

        # Decrease volume
        if any(
            x in normalized
            for x in [
                "اخفض الصوت",
                "وطي الصوت",
                "خفض الصوت",
            ]
        ):

            self.adjust_volume(
                "down"
            )

            return

        # Brightness percentage
        m = re.search(
            r"(?:سطوع|اضاءة|إضاءة)\s*(\d{1,3})"
            r"\s*(?:بالمئة|بالمائة|٪|%)?",
            c
        )

        if m:

            self.set_brightness_percent(
                m.group(1)
            )

            return

        # Increase brightness
        if any(
            x in normalized
            for x in [
                "ارفع السطوع",
                "زود السطوع",
                "ارفع الاضاءة",
                "ارفع الاضاءه",
            ]
        ):

            self.set_brightness_percent(
                100
            )

            return

        # Decrease brightness
        if any(
            x in normalized
            for x in [
                "اخفض السطوع",
                "قلل السطوع",
                "اخفض الاضاءة",
                "اخفض الاضاءه",
            ]
        ):

            self.set_brightness_percent(
                20
            )

            return

        self.set_status(
            "لم أجد أمرًا مطابقًا. اضغط «الأوامر» لرؤية الأمثلة."
        )


if __name__ == "__main__":
    VoiceControlApp().run()
