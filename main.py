from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.text import LabelBase
from kivy.clock import Clock
from kivy.utils import platform


FONT_FILE = "NotoKufiArabic-VariableFont_wght.ttf"


# =========================
# الخط العربي
# =========================

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


    # =========================
    # طلب صلاحية الميكروفون
    # =========================

    def start_listening(self, *args):

        if platform != "android":

            self.status_label.text = (
                "هذه الخاصية تعمل على Android فقط"
            )

            return

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
                1.0
            )

        except Exception as e:

            self.status_label.text = (
                "تعذر طلب صلاحية الميكروفون"
            )

            self.result_label.text = str(e)


    # =========================
    # فتح التعرف الصوتي
    # =========================

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

            # تسجيل استقبال النتيجة
            activity.bind(
                on_activity_result=self.on_activity_result
            )

            # الحصول على Activity الحالية
            current_activity = PythonActivity.mActivity

            # فتح واجهة التعرف الصوتي
            current_activity.startActivityForResult(
                intent,
                self.REQUEST_CODE
            )

            self.status_label.text = (
                "🎤 تحدث الآن..."
            )

        except Exception as e:

            self.status_label.text = (
                "تعذر فتح التعرف الصوتي"
            )

            self.result_label.text = str(e)


    # =========================
    # استقبال نتيجة الكلام
    # =========================

    def on_activity_result(
        self,
        request_code,
        result_code,
        intent
    ):

        try:

            if request_code != self.REQUEST_CODE:
                return

            from android import activity

            # إلغاء التسجيل بعد وصول النتيجة
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

            text = str(
                results.get(0)
            )

            self.result_label.text = (
                "قلت:\n\n" + text
            )

            self.status_label.text = (
                "تم التعرف على الكلام"
            )

        except Exception as e:

            self.status_label.text = (
                "حدث خطأ في النتيجة"
            )

            self.result_label.text = str(e)


# =========================
# تشغيل التطبيق
# =========================

if __name__ == "__main__":
    VoiceControlApp().run()
