from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.text import LabelBase
from kivy.clock import Clock
from kivy.utils import platform


# ============================================================
# إعداد الخط العربي
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


class VoiceControlApp(App):

    REQUEST_CODE = 5001

    def build(self):

        self.listening = False

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

        title = Label(
            text="التحكم الصوتي",
            font_name=ARABIC_FONT,
            font_size=28,
            size_hint_y=None,
            height=80,
        )

        layout.add_widget(title)
        layout.add_widget(self.status_label)
        layout.add_widget(self.result_label)

        self.start_button = Button(
            text="🎤 بدء الاستماع",
            font_name=ARABIC_FONT,
            font_size=22,
            size_hint_y=None,
            height=80,
        )

        self.start_button.bind(
            on_release=self.start_listening
        )

        layout.add_widget(self.start_button)

        return layout


    # ========================================================
    # بدء الاستماع
    # ========================================================

    def start_listening(self, *args):

        if platform != "android":

            self.status_label.text = (
                "هذه الخاصية تعمل على Android فقط"
            )

            return

        if self.listening:

            return

        try:

            from android.permissions import (
                request_permissions,
                Permission
            )

            self.listening = True

            self.start_button.text = "🎤 جاري الاستماع..."

            self.status_label.text = (
                "جاري فتح التعرف الصوتي..."
            )

            request_permissions([
                Permission.RECORD_AUDIO
            ])

            Clock.schedule_once(
                self.open_recognizer,
                1.0
            )

        except Exception as e:

            self.listening = False

            self.start_button.text = (
                "🎤 بدء الاستماع"
            )

            self.status_label.text = (
                "تعذر طلب صلاحية الميكروفون"
            )

            self.result_label.text = str(e)


    # ========================================================
    # فتح التعرف الصوتي
    # ========================================================

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

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            intent = Intent(
                RecognizerIntent.ACTION_RECOGNIZE_SPEECH
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )

            # العربية
            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE,
                "ar-YE"
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE,
                "ar-YE"
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_PROMPT,
                "تحدث الآن"
            )

            # طلب نتائج متعددة لزيادة فرصة التعرف الصحيح
            intent.putExtra(
                RecognizerIntent.EXTRA_MAX_RESULTS,
                5
            )

            # تسجيل استقبال النتيجة
            activity.bind(
                on_activity_result=self.on_activity_result
            )

            current_activity = (
                PythonActivity.mActivity
            )

            current_activity.startActivityForResult(
                intent,
                self.REQUEST_CODE
            )

            self.status_label.text = (
                "🎤 تحدث الآن..."
            )

        except Exception as e:

            self.listening = False

            self.start_button.text = (
                "🎤 بدء الاستماع"
            )

            self.status_label.text = (
                "تعذر فتح التعرف الصوتي"
            )

            self.result_label.text = str(e)


    # ========================================================
    # استقبال نتيجة التعرف
    # ========================================================

    def on_activity_result(
        self,
        request_code,
        result_code,
        intent
    ):

        try:

            if request_code != self.REQUEST_CODE:
                return

            # نعيد الحالة إلى الطبيعي
            self.listening = False

            self.start_button.text = (
                "🎤 بدء الاستماع"
            )

            from android import activity

            # إلغاء callback
            try:

                activity.unbind(
                    on_activity_result=self.on_activity_result
                )

            except Exception:
                pass

            if intent is None:

                self.status_label.text = (
                    "لم يتم الحصول على نتيجة"
                )

                return

            from jnius import autoclass

            RecognizerIntent = autoclass(
                "android.speech.RecognizerIntent"
            )

            results = (
                intent.getStringArrayListExtra(
                    RecognizerIntent.EXTRA_RESULTS
                )
            )

            if results is None:

                self.status_label.text = (
                    "لم يتم التعرف على الكلام"
                )

                return

            if results.size() == 0:

                self.status_label.text = (
                    "لم يتم التعرف على الكلام"
                )

                return

            # النتيجة الأولى هي الأكثر احتمالًا
            text = str(
                results.get(0)
            ).strip()

            if not text:

                self.status_label.text = (
                    "لم يتم التعرف على الكلام"
                )

                return

            self.result_label.text = (
                "قلت:\n\n" + text
            )

            self.status_label.text = (
                "جاري تنفيذ الأمر..."
            )

            # تنفيذ الأمر في دورة Kivy الرئيسية
            Clock.schedule_once(
                lambda dt: self.execute_command(text),
                0
            )

        except Exception as e:

            self.listening = False

            self.start_button.text = (
                "🎤 بدء الاستماع"
            )

            self.status_label.text = (
                "حدث خطأ في النتيجة"
            )

            self.result_label.text = str(e)


    # ========================================================
    # تنظيف النص العربي
    # ========================================================

    def normalize_text(self, text):

        text = text.strip().lower()

        replacements = {
            "أ": "ا",
            "إ": "ا",
            "آ": "ا",
            "ة": "ه",
            "ى": "ي",
        }

        for old, new in replacements.items():

            text = text.replace(
                old,
                new
            )

        return text


    # ========================================================
    # تنفيذ الأوامر
    # ========================================================

    def execute_command(self, original_text):

        text = self.normalize_text(
            original_text
        )

        try:

            # ----------------------------------------------
            # رفع الصوت
            # ----------------------------------------------

            if (
                "ارفع الصوت" in text
                or "علي الصوت" in text
                or "ارفع مستوى الصوت" in text
                or "زيد الصوت" in text
                or "زود الصوت" in text
            ):

                self.change_volume(
                    "up"
                )

                return


            # ----------------------------------------------
            # خفض الصوت
            # ----------------------------------------------

            if (
                "اخفض الصوت" in text
                or "وطي الصوت" in text
                or "نقص الصوت" in text
                or "خفض الصوت" in text
                or "انقص الصوت" in text
            ):

                self.change_volume(
                    "down"
                )

                return


            # ----------------------------------------------
            # كتم الصوت
            # ----------------------------------------------

            if (
                "كتم الصوت" in text
                or "اكتم الصوت" in text
                or "صامت" in text
                or "اسكت الصوت" in text
            ):

                self.change_volume(
                    "mute"
                )

                return


            # ----------------------------------------------
            # فتح Wi-Fi
            # ----------------------------------------------

            if (
                "واي فاي" in text
                or "واي فاي" in text
                or "wifi" in text
                or "الواي فاي" in text
                or "شبكه الواي فاي" in text
            ):

                self.open_settings(
                    "wifi"
                )

                return


            # ----------------------------------------------
            # فتح Bluetooth
            # ----------------------------------------------

            if (
                "بلوتوث" in text
                or "البلوتوث" in text
                or "bluetooth" in text
            ):

                self.open_settings(
                    "bluetooth"
                )

                return


            # ----------------------------------------------
            # فتح الإعدادات
            # ----------------------------------------------

            if (
                "افتح الاعدادات" in text
                or "فتح الاعدادات" in text
                or "الاعدادات" in text
                or "اعدادات الهاتف" in text
                or "اعدادات الجهاز" in text
            ):

                self.open_settings(
                    "settings"
                )

                return


            # ----------------------------------------------
            # أوامر السطوع
            # ----------------------------------------------

            if (
                "السطوع" in text
                or "الشاشه" in text
                or "اضاءه الشاشه" in text
                or "اضاءه" in text
            ):

                self.handle_brightness(
                    text
                )

                return


            # ----------------------------------------------
            # أمر غير معروف
            # ----------------------------------------------

            self.status_label.text = (
                "لم أفهم الأمر"
            )

            self.result_label.text = (
                "قلت:\n\n"
                + original_text
                + "\n\n"
                + "جرّب: ارفع الصوت"
            )

        except Exception as e:

            self.status_label.text = (
                "حدث خطأ أثناء تنفيذ الأمر"
            )

            self.result_label.text = (
                original_text
                + "\n\n"
                + str(e)
            )


    # ========================================================
    # التحكم في الصوت
    # ========================================================

    def change_volume(self, action):

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

            activity = (
                PythonActivity.mActivity
            )

            audio_manager = (
                activity.getSystemService(
                    Context.AUDIO_SERVICE
                )
            )

            if action == "up":

                audio_manager.adjustStreamVolume(
                    AudioManager.STREAM_MUSIC,
                    AudioManager.ADJUST_RAISE,
                    AudioManager.FLAG_SHOW_UI
                )

                self.status_label.text = (
                    "🔊 تم رفع الصوت"
                )

            elif action == "down":

                audio_manager.adjustStreamVolume(
                    AudioManager.STREAM_MUSIC,
                    AudioManager.ADJUST_LOWER,
                    AudioManager.FLAG_SHOW_UI
                )

                self.status_label.text = (
                    "🔉 تم خفض الصوت"
                )

            elif action == "mute":

                audio_manager.adjustStreamVolume(
                    AudioManager.STREAM_MUSIC,
                    AudioManager.ADJUST_MUTE,
                    AudioManager.FLAG_SHOW_UI
                )

                self.status_label.text = (
                    "🔇 تم كتم الصوت"
                )

        except Exception as e:

            self.status_label.text = (
                "تعذر التحكم في الصوت"
            )

            self.result_label.text = str(e)


    # ========================================================
    # فتح إعدادات Android
    # ========================================================

    def open_settings(self, setting):

        try:

            from jnius import autoclass

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            Intent = autoclass(
                "android.content.Intent"
            )

            Settings = autoclass(
                "android.provider.Settings"
            )

            activity = (
                PythonActivity.mActivity
            )

            if setting == "wifi":

                action = (
                    Settings.ACTION_WIFI_SETTINGS
                )

                message = (
                    "📶 تم فتح إعدادات Wi-Fi"
                )

            elif setting == "bluetooth":

                action = (
                    Settings.ACTION_BLUETOOTH_SETTINGS
                )

                message = (
                    "🟦 تم فتح إعدادات Bluetooth"
                )

            else:

                action = (
                    Settings.ACTION_SETTINGS
                )

                message = (
                    "⚙️ تم فتح إعدادات الهاتف"
                )

            intent = Intent(
                action
            )

            activity.startActivity(
                intent
            )

            self.status_label.text = message

        except Exception as e:

            self.status_label.text = (
                "تعذر فتح الإعدادات"
            )

            self.result_label.text = str(e)


    # ========================================================
    # التحكم في السطوع
    # ========================================================

    def handle_brightness(self, text):

        import re

        # البحث عن رقم في الأمر
        numbers = re.findall(
            r"\d+",
            text
        )

        if numbers:

            value = int(
                numbers[0]
            )

            # حصر القيمة بين 0 و100
            value = max(
                0,
                min(
                    100,
                    value
                )
            )

            self.set_brightness(
                value
            )

            return

        # لا يوجد رقم
        self.open_display_settings()


    # ========================================================
    # ضبط السطوع
    # ========================================================

    def set_brightness(self, percent):

        try:

            from jnius import autoclass

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            Settings = autoclass(
                "android.provider.Settings"
            )

            activity = (
                PythonActivity.mActivity
            )

            # التأكد من صلاحية تعديل إعدادات النظام
            if not Settings.System.canWrite(
                activity
            ):

                self.status_label.text = (
                    "يجب السماح للتطبيق بتعديل السطوع"
                )

                self.open_write_settings()

                return

            # تحويل النسبة 0-100 إلى نطاق Android 0-255
            brightness = int(
                percent * 255 / 100
            )

            resolver = (
                activity.getContentResolver()
            )

            Settings.System.putInt(
                resolver,
                Settings.System.SCREEN_BRIGHTNESS,
                brightness
            )

            self.status_label.text = (
                "☀️ تم ضبط السطوع إلى "
                + str(percent)
                + "%"
            )

        except Exception as e:

            self.status_label.text = (
                "تعذر ضبط السطوع"
            )

            self.result_label.text = str(e)


    # ========================================================
    # طلب صلاحية تعديل إعدادات النظام
    # ========================================================

    def open_write_settings(self):

        try:

            from jnius import autoclass

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            Intent = autoclass(
                "android.content.Intent"
            )

            Settings = autoclass(
                "android.provider.Settings"
            )

            Uri = autoclass(
                "android.net.Uri"
            )

            activity = (
                PythonActivity.mActivity
            )

            package_name = (
                activity.getPackageName()
            )

            intent = Intent(
                Settings.ACTION_MANAGE_WRITE_SETTINGS
            )

            intent.setData(
                Uri.parse(
                    "package:" + package_name
                )
            )

            activity.startActivity(
                intent
            )

        except Exception as e:

            self.status_label.text = (
                "تعذر فتح صلاحية السطوع"
            )

            self.result_label.text = str(e)


    # ========================================================
    # فتح إعدادات الشاشة
    # ========================================================

    def open_display_settings(self):

        try:

            from jnius import autoclass

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            Intent = autoclass(
                "android.content.Intent"
            )

            Settings = autoclass(
                "android.provider.Settings"
            )

            activity = (
                PythonActivity.mActivity
            )

            intent = Intent(
                Settings.ACTION_DISPLAY_SETTINGS
            )

            activity.startActivity(
                intent
            )

            self.status_label.text = (
                "☀️ تم فتح إعدادات الشاشة"
            )

        except Exception as e:

            self.status_label.text = (
                "تعذر فتح إعدادات الشاشة"
            )

            self.result_label.text = str(e)


# ============================================================
# تشغيل التطبيق
# ============================================================

if __name__ == "__main__":
    VoiceControlApp().run()
