# main.py
# Voice Control - مهند الحمادي

import os
import re
import sys
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.properties import StringProperty, BooleanProperty
from kivy.graphics import Color, RoundedRectangle, Line

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:
    arabic_reshaper = None
    get_display = None

try:
    from jnius import autoclass
    JNIUS = True
except Exception:
    JNIUS = False
    autoclass = None

try:
    from android import activity
    from android.permissions import Permission, check_permission, request_permissions
    ANDROID = True
except Exception:
    activity = None
    Permission = None
    ANDROID = False

REQUEST_SPEECH = 1001

FONT_FILE = "NotoKufiArabic-VariableFont_wght.ttf"


def rtl(text):
    text = str(text)
    if arabic_reshaper and get_display:
        try:
            return get_display(arabic_reshaper.reshape(text))
        except Exception:
            return text
    return text


def contains_any(text, words):
    text = str(text).lower()
    return any(str(word).lower() in text for word in words)


class RoundedBackground:
    pass


class Card(Button):
    icon = StringProperty("")
    subtitle = StringProperty("")

    def __init__(self, text="", icon="", subtitle="", **kwargs):
        self.main_text = text
        self.icon = icon
        self.subtitle = subtitle

        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(92))
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        kwargs.setdefault("border", (0, 0, 0, 0))

        super().__init__(text="", **kwargs)

        self.bind(pos=self._update_graphics, size=self._update_graphics)

        with self.canvas.before:
            self.bg_color = Color(0.075, 0.095, 0.13, 1)
            self.bg = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(14)]
            )

        with self.canvas.after:
            self.line_color = Color(0.18, 0.23, 0.31, 1)
            self.line = Line(
                rounded_rectangle=(
                    self.x,
                    self.y,
                    self.width,
                    self.height,
                    dp(14)
                ),
                width=1
            )

        self.label = Label(
            text=rtl(self._make_text()),
            font_name=FONT_FILE if os.path.exists(FONT_FILE) else "Roboto",
            font_size=dp(13),
            halign="right",
            valign="middle",
            size_hint=(1, 1),
            padding=(dp(10), dp(5))
        )

        self.add_widget(self.label)

    def _make_text(self):
        if self.subtitle:
            return f"{self.icon}  {self.main_text}\n{self.subtitle}"
        return f"{self.icon}  {self.main_text}"

    def _update_graphics(self, *_):
        if hasattr(self, "bg"):
            self.bg.pos = self.pos
            self.bg.size = self.size

        if hasattr(self, "line"):
            self.line.rounded_rectangle = (
                self.x,
                self.y,
                self.width,
                self.height,
                dp(14)
            )


class VoiceButton(Button):
    def __init__(self, **kwargs):
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(170))

        super().__init__(**kwargs)

        with self.canvas.before:
            self.color_bg = Color(0.08, 0.16, 0.25, 1)
            self.rectangle = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(25)]
            )

        self.bind(pos=self._update, size=self._update)

    def _update(self, *_):
        self.rectangle.pos = self.pos
        self.rectangle.size = self.size


class VoiceControlApp(App):

    dark = BooleanProperty(True)
    language = StringProperty("ar")
    listening = BooleanProperty(False)

    def build(self):
        self.title = "Voice Control"

        Window.clearcolor = (0.035, 0.045, 0.06, 1)

        self.sm = ScreenManager()

        self.status = None
        self.result = None
        self.mic = None
        self.search_input = None
        self.settings_content = None
        self.all_setting_cards = []
        self.bound = False

        self.sm.add_widget(self.home_screen())
        self.sm.add_widget(self.settings_screen())
        self.sm.add_widget(self.commands_screen())
        self.sm.add_widget(self.about_screen())

        return self.sm

    # ---------------------------------------------------------
    # أدوات الواجهة
    # ---------------------------------------------------------

    def label(
        self,
        text,
        size=15,
        bold=False,
        halign="right"
    ):
        lab = Label(
            text=rtl(text),
            font_name=FONT_FILE if os.path.exists(FONT_FILE) else "Roboto",
            font_size=dp(size),
            halign=halign,
            valign="middle"
        )

        if bold:
            lab.bold = True

        lab.bind(
            size=lambda instance, value: setattr(
                instance,
                "text_size",
                (instance.width, None)
            )
        )

        return lab

    def header(self, title):
        box = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(65),
            spacing=dp(8)
        )

        back = Button(
            text=rtl("‹"),
            font_name=FONT_FILE if os.path.exists(FONT_FILE) else "Roboto",
            font_size=dp(30),
            size_hint_x=None,
            width=dp(55),
            background_color=(0, 0, 0, 0)
        )

        back.bind(on_release=lambda *_: self.goto("home"))

        title_label = self.label(
            title,
            21,
            True,
            "right"
        )

        box.add_widget(title_label)
        box.add_widget(back)

        return box

    def button_back(self, text, target):
        c = Card(
            text=text,
            icon="‹",
            subtitle="",
            height=dp(58)
        )

        c.bind(
            on_release=lambda *_: self.goto(target)
        )

        return c

    # ---------------------------------------------------------
    # الشاشة الرئيسية
    # ---------------------------------------------------------

    def home_screen(self):
        s = Screen(name="home")

        root = BoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(12)
        )

        top = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(60)
        )

        title = self.label(
            "Voice Control",
            24,
            True,
            "right"
        )

        settings_btn = Button(
            text=rtl("⚙️"),
            font_name=FONT_FILE if os.path.exists(FONT_FILE) else "Roboto",
            font_size=dp(23),
            size_hint_x=None,
            width=dp(60),
            background_color=(0, 0, 0, 0)
        )

        settings_btn.bind(
            on_release=lambda *_: self.goto("settings")
        )

        top.add_widget(title)
        top.add_widget(settings_btn)

        root.add_widget(top)

        root.add_widget(
            self.label(
                "تحكم بهاتفك باستخدام صوتك",
                16,
                False,
                "right"
            )
        )

        self.result = self.label(
            "لم يتم التعرف على أي كلام بعد.",
            16,
            False,
            "center"
        )

        self.result.size_hint_y = None
        self.result.height = dp(100)

        root.add_widget(self.result)

        self.mic = VoiceButton(
            text=rtl("🎙️\nابدأ التحدث"),
            font_name=FONT_FILE if os.path.exists(FONT_FILE) else "Roboto",
            font_size=dp(22)
        )

        self.mic.bind(
            on_release=self.toggle_listening
        )

        root.add_widget(self.mic)

        self.status = self.label(
            "جاهز للاستماع",
            14,
            False,
            "center"
        )

        self.status.size_hint_y = None
        self.status.height = dp(55)

        root.add_widget(self.status)

        commands_btn = Card(
            text="الأوامر الصوتية",
            icon="🎙️",
            subtitle="عرض جميع الأوامر المتاحة",
            height=dp(70)
        )

        commands_btn.bind(
            on_release=lambda *_: self.goto("commands")
        )

        root.add_widget(commands_btn)

        about_btn = Card(
            text="من نحن",
            icon="ⓘ",
            subtitle="معلومات عن التطبيق والمطور",
            height=dp(70)
        )

        about_btn.bind(
            on_release=lambda *_: self.goto("about")
        )

        root.add_widget(about_btn)

        s.add_widget(root)

        return s

    # ---------------------------------------------------------
    # شاشة الإعدادات
    # ---------------------------------------------------------

    def settings_screen(self):
        s = Screen(name="settings")

        root = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(8)
        )

        root.add_widget(
            self.header("إعدادات الهاتف")
        )

        self.search_input = TextInput(
            hint_text=rtl("🔎 ابحث في الإعدادات"),
            font_name=FONT_FILE if os.path.exists(FONT_FILE) else "Roboto",
            font_size=dp(14),
            size_hint_y=None,
            height=dp(50),
            multiline=False,
            halign="right",
            padding=(dp(12), dp(12))
        )

        self.search_input.bind(
            text=self.filter_settings
        )

        root.add_widget(self.search_input)

        scroll = ScrollView(
            do_scroll_x=False
        )

        self.settings_content = GridLayout(
            cols=1,
            spacing=dp(10),
            size_hint_y=None
        )

        self.settings_content.bind(
            minimum_height=self.settings_content.setter("height")
        )

        scroll.add_widget(
            self.settings_content
        )

        root.add_widget(scroll)

        s.add_widget(root)

        Clock.schedule_once(
            lambda *_: self.populate_settings(),
            0
        )

        return s

    def populate_settings(self):
        sections = [
            (
                "📶 الاتصال والشبكات",
                [
                    ("الواي فاي", "wifi", "إعدادات Wi-Fi", "📶"),
                    ("البلوتوث", "bluetooth", "الأجهزة والاتصالات", "🔵"),
                    ("شبكة الهاتف", "mobile", "شبكة الهاتف المحمول", "📱"),
                    ("بيانات الهاتف", "data", "استخدام البيانات", "📊"),
                    ("نقطة الاتصال", "hotspot", "مشاركة الإنترنت", "📡"),
                    ("VPN", "vpn", "الشبكة الخاصة", "🔐"),
                    ("NFC", "nfc", "الاتصال قريب المدى", "📳"),
                ]
            ),
            (
                "🔔 الصوت والإشعارات",
                [
                    ("الإشعارات", "notifications", "إدارة الإشعارات", "🔔"),
                    ("عدم الإزعاج", "do_not_disturb", "الصوت وعدم الإزعاج", "🔕"),
                    ("الوصول إلى الإشعارات", "notification_access", "خدمات الإشعارات", "📢"),
                    ("رفع الصوت", "volume_up", "رفع مستوى الصوت", "🔊"),
                    ("خفض الصوت", "volume_down", "خفض مستوى الصوت", "🔉"),
                    ("كتم الصوت", "volume_mute", "كتم الصوت", "🔇"),
                ]
            ),
            (
                "🔋 البطارية",
                [
                    ("البطارية", "battery", "إعدادات البطارية", "🔋"),
                    ("استخدام البطارية", "battery_usage", "استهلاك التطبيقات", "📈"),
                    ("توفير الطاقة", "battery_saver", "توفير البطارية", "⚡"),
                    ("تحسين البطارية", "battery_optimization", "تحسين التطبيقات", "🔧"),
                ]
            ),
            (
                "📱 الشاشة",
                [
                    ("الشاشة", "display", "إعدادات الشاشة", "📱"),
                    ("السطوع", "brightness", "تعديل سطوع الشاشة", "☀️"),
                    ("شاشة القفل", "lock_screen", "إعدادات شاشة القفل", "🔒"),
                    ("الخلفية", "wallpaper", "خلفية الشاشة", "🖼️"),
                ]
            ),
            (
                "🔐 الخصوصية والحماية",
                [
                    ("الخصوصية", "privacy", "إعدادات الخصوصية", "🛡️"),
                    ("الموقع", "location", "خدمات الموقع", "📍"),
                    ("الحماية", "security", "الأمان", "🔐"),
                    ("الأذونات", "app_permissions", "أذونات التطبيق", "✅"),
                    ("التطبيقات", "apps", "إدارة التطبيقات", "📦"),
                    ("الوصول الخاص", "special_access", "صلاحيات خاصة", "⚙️"),
                    ("الظهور فوق التطبيقات", "overlay", "السماح بالنوافذ العائمة", "🪟"),
                ]
            ),
            (
                "⚙️ النظام والميزات المتقدمة",
                [
                    ("تحديث النظام", "system_update", "تحديث البرنامج", "↻"),
                    ("حول الهاتف", "about_device", "معلومات الجهاز", "ⓘ"),
                    ("خيارات المطور", "developer", "أدوات المطور", "👨‍💻"),
                    ("إمكانية الوصول", "accessibility", "ميزات الوصول", "♿"),
                    ("اللغة والإدخال", "language", "اللغة ولوحة المفاتيح", "文"),
                    ("التاريخ والوقت", "date", "الوقت والتاريخ", "🕒"),
                    ("إعادة ضبط الهاتف", "reset", "خيارات إعادة الضبط", "↺"),
                    ("التطبيقات الافتراضية", "default_apps", "التطبيقات الافتراضية", "📱"),
                ]
            ),
            (
                "👨‍👩‍👧 التحكم الأبوي",
                [
                    ("التحكم الأبوي", "parental", "إدارة العائلة", "👨‍👩‍👧"),
                    ("الرفاهية الرقمية", "digital_wellbeing", "وقت الشاشة", "⏱"),
                ]
            ),
            (
                "🎙️ إعدادات التطبيق",
                [
                    ("العربية", "lang_ar", "لغة التعرف الصوتي", "🇸🇦"),
                    ("English", "lang_en", "Speech recognition", "🇺🇸"),
                    ("صفحة الأوامر", "commands", "الأوامر المتاحة", "🎙️"),
                    ("من نحن", "about_app", "المطور والمعلومات", "ⓘ"),
                ]
            ),
        ]

        self.settings_content.clear_widgets()
        self.all_setting_cards.clear()

        for section, items in sections:

            title = self.label(
                section,
                16,
                True,
                "right"
            )

            title.size_hint_y = None
            title.height = dp(42)

            self.settings_content.add_widget(title)

            grid = GridLayout(
                cols=2,
                spacing=dp(7),
                size_hint_y=None
            )

            grid.bind(
                minimum_height=grid.setter("height")
            )

            for caption, action, sub, icon in items:

                card = Card(
                    text=caption,
                    icon=icon,
                    subtitle=sub,
                    height=dp(92)
                )

                card.action_key = action

                card.search_text = (
                    caption + " " + sub
                ).lower()

                card.bind(
                    on_release=lambda *_x, a=action:
                    self.setting_action(a)
                )

                grid.add_widget(card)

                self.all_setting_cards.append(card)

            self.settings_content.add_widget(grid)

    def filter_settings(self, *_):
        query = (
            self.search_input.text.strip().lower()
            if self.search_input
            else ""
        )

        for card in self.all_setting_cards:

            visible = (
                not query
                or query in card.search_text
            )

            card.opacity = 1 if visible else 0
            card.disabled = not visible

    # ---------------------------------------------------------
    # شاشة الأوامر
    # ---------------------------------------------------------

    def commands_screen(self):
        s = Screen(name="commands")

        root = BoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(10)
        )

        root.add_widget(
            self.header("الأوامر الصوتية")
        )

        scroll = ScrollView(
            do_scroll_x=False
        )

        text = (
            "يمكنك قول:\n\n"

            "• افتح الواي فاي\n"
            "• افتح البلوتوث\n"
            "• افتح شبكة الهاتف\n"
            "• افتح بيانات الهاتف\n"
            "• افتح نقطة الاتصال\n"
            "• افتح VPN\n"
            "• افتح NFC\n"
            "• افتح الإشعارات\n"
            "• افتح عدم الإزعاج\n"
            "• افتح البطارية\n"
            "• افتح توفير الطاقة\n"
            "• افتح الخصوصية\n"
            "• افتح الموقع\n"
            "• افتح الحماية\n"
            "• افتح شاشة القفل\n"
            "• افتح الطوارئ\n"
            "• افتح الحسابات\n"
            "• افتح النسخ الاحتياطي\n"
            "• افتح Google\n"
            "• افتح تحديث النظام\n"
            "• افتح حول الهاتف\n"
            "• افتح خيارات المطور\n"
            "• افتح إمكانية الوصول\n"
            "• افتح التحكم الأبوي\n"
            "• ارفع الصوت\n"
            "• اخفض الصوت\n"
            "• كتم الصوت\n"
            "• اجعل السطوع 50\n\n"

            "English:\n\n"
            "Open Wi-Fi\n"
            "Open Bluetooth\n"
            "Open settings\n"
            "Open privacy\n"
            "Open battery\n"
            "Open developer options\n"
            "Open notifications\n"
            "Open location\n"
            "Open security\n"
        )

        lab = self.label(
            text,
            15,
            False,
            "right"
        )

        lab.size_hint_y = None

        lab.bind(
            texture_size=lambda w, size:
            setattr(
                w,
                "height",
                size[1] + dp(20)
            )
        )

        scroll.add_widget(lab)

        root.add_widget(scroll)

        s.add_widget(root)

        return s

    # ---------------------------------------------------------
    # من نحن
    # ---------------------------------------------------------

    def about_screen(self):
        s = Screen(name="about")

        root = BoxLayout(
            orientation="vertical",
            padding=dp(22),
            spacing=dp(12)
        )

        root.add_widget(
            self.label(
                "من نحن",
                28,
                True,
                "center"
            )
        )

        root.add_widget(
            self.label(
                "Voice Control",
                22,
                True,
                "center"
            )
        )

        root.add_widget(
            self.label(
                "تطبيق للتحكم الصوتي وفتح إعدادات Android بسرعة، مع دعم العربية وEnglish.",
                16,
                False,
                "center"
            )
        )

        root.add_widget(
            self.label(
                "المطور: مهند الحمادي",
                18,
                True,
                "center"
            )
        )

        root.add_widget(
            self.label(
                "واجهة حديثة • أوامر صوتية • إعدادات منظمة",
                13,
                False,
                "center"
            )
        )

        root.add_widget(
            self.button_back(
                "العودة للرئيسية",
                "home"
            )
        )

        s.add_widget(root)

        return s

    # ---------------------------------------------------------
    # التنقل
    # ---------------------------------------------------------

    def goto(self, name):
        if name == "الرئيسية":
            name = "home"

        if self.sm.has_screen(name):
            self.sm.current = name

    # ---------------------------------------------------------
    # اللغة
    # ---------------------------------------------------------

    def set_language(self, lang):
        self.language = lang

        if lang == "ar":
            self.set_status(
                "لغة التعرف: العربية"
            )
        else:
            self.set_status(
                "Recognition language: English"
            )

    # ---------------------------------------------------------
    # حالة التطبيق
    # ---------------------------------------------------------

    def set_status(self, text):
        if self.status:
            self.status.text = rtl(text)

    # ---------------------------------------------------------
    # الاستماع
    # ---------------------------------------------------------

    def toggle_listening(self, *_):

        if self.listening:
            self.listening = False

            self.set_status(
                "تم إيقاف الاستماع"
            )

            self.mic.text = rtl(
                "🎙️\nابدأ التحدث"
            )

            return

        self.start_listening()

    def request_mic(self):

        if ANDROID:

            try:

                if not check_permission(
                    Permission.RECORD_AUDIO
                ):

                    request_permissions(
                        [Permission.RECORD_AUDIO],
                        lambda *_: None
                    )

                    return False

            except Exception:
                pass

        return True

    def on_start(self):

        if ANDROID and JNIUS and not self.bound:

            try:

                activity.bind(
                    on_activity_result=self.on_activity_result
                )

                self.bound = True

            except Exception as exc:
                print(
                    "activity bind:",
                    exc
                )

        self.request_mic()

    def on_stop(self):

        if ANDROID and JNIUS and self.bound:

            try:

                activity.unbind(
                    on_activity_result=self.on_activity_result
                )

            except Exception:
                pass

            self.bound = False

    def start_listening(self):

        if not ANDROID or not JNIUS:

            self.set_status(
                "التعرف الصوتي يعمل داخل APK على Android"
            )

            return

        if not self.request_mic():

            self.set_status(
                "اسمح باستخدام الميكروفون ثم اضغط مرة أخرى"
            )

            return

        try:

            Intent = autoclass(
                "android.content.Intent"
            )

            RI = autoclass(
                "android.speech.RecognizerIntent"
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            intent = Intent(
                RI.ACTION_RECOGNIZE_SPEECH
            )

            intent.putExtra(
                RI.EXTRA_LANGUAGE_MODEL,
                RI.LANGUAGE_MODEL_FREE_FORM
            )

            intent.putExtra(
                RI.EXTRA_LANGUAGE,
                self.language
            )

            intent.putExtra(
                RI.EXTRA_LANGUAGE_PREFERENCE,
                self.language
            )

            intent.putExtra(
                RI.EXTRA_MAX_RESULTS,
                5
            )

            prompt = (
                "تحدث الآن"
                if self.language == "ar"
                else "Speak now"
            )

            intent.putExtra(
                RI.EXTRA_PROMPT,
                prompt
            )

            self.listening = True

            self.mic.text = rtl(
                "⏹️\nجارٍ الاستماع"
            )

            self.set_status(
                "🎙️ استمع الآن..."
            )

            PythonActivity.mActivity.startActivityForResult(
                intent,
                REQUEST_SPEECH
            )

        except Exception as exc:

            self.listening = False

            self.mic.text = rtl(
                "🎙️\nابدأ التحدث"
            )

            self.set_status(
                "تعذر فتح التعرف الصوتي"
            )

            print(
                "speech intent:",
                exc
            )

    def on_activity_result(
        self,
        request_code,
        result_code,
        intent
    ):

        if int(request_code) != REQUEST_SPEECH:
            return

        self.listening = False

        Clock.schedule_once(
            lambda *_:
            self.finish_result(intent),
            0
        )

    def finish_result(self, intent):

        self.mic.text = rtl(
            "🎙️\nابدأ التحدث"
        )

        if not intent:

            self.set_status(
                "لم يتم استلام نتيجة"
            )

            return

        try:

            RI = autoclass(
                "android.speech.RecognizerIntent"
            )

            results = intent.getStringArrayListExtra(
                RI.EXTRA_RESULTS
            )

            text = (
                str(results.get(0))
                if results and results.size()
                else ""
            )

        except Exception as exc:

            print(
                "result:",
                exc
            )

            text = ""

        if text:

            self.result.text = rtl(text)

            self.set_status(
                "✅ تم التعرف على الكلام"
            )

            self.handle_command(text)

        else:

            self.set_status(
                "لم يتم التعرف على الكلام"
            )

    # ---------------------------------------------------------
    # معالجة النص
    # ---------------------------------------------------------

    def normalize(self, text):

        t = text.strip().lower()

        for a, b in [
            ("أ", "ا"),
            ("إ", "ا"),
            ("آ", "ا"),
            ("ة", "ه"),
            ("ى", "ي")
        ]:

            t = t.replace(a, b)

        return " ".join(
            t.split()
        )

    def handle_command(self, text):

        t = self.normalize(text)

        if contains_any(
            t,
            [
                "مساعده",
                "الاوامر",
                "الاوامر",
                "help"
            ]
        ):

            self.goto("commands")
            return

        if contains_any(
            t,
            [
                "امسح",
                "مسح",
                "clear"
            ]
        ):

            self.result.text = rtl(
                "لم يتم التعرف على أي كلام بعد."
            )

            self.set_status(
                "جاهز للاستماع"
            )

            return

        if contains_any(
            t,
            [
                "ارفع الصوت",
                "علي الصوت",
                "زيد الصوت",
                "زود الصوت",
                "increase volume",
                "volume up"
            ]
        ):

            self.audio_adjust(1)
            return

        if contains_any(
            t,
            [
                "اخفض الصوت",
                "وطي الصوت",
                "نقص الصوت",
                "خفض الصوت",
                "انقص الصوت",
                "decrease volume",
                "volume down"
            ]
        ):

            self.audio_adjust(-1)
            return

        if contains_any(
            t,
            [
                "كتم الصوت",
                "اكتم الصوت",
                "صامت",
                "mute"
            ]
        ):

            self.audio_mute()
            return

        if contains_any(
            t,
            [
                "السطوع",
                "اضاءه الشاشه",
                "اضاءة الشاشه",
                "brightness"
            ]
        ):

            match = re.search(
                r"(\d{1,3})",
                t
            )

            if match:

                self.set_brightness(
                    int(match.group(1))
                )

                return

            if contains_any(
                t,
                [
                    "ارفع",
                    "زيد",
                    "increase"
                ]
            ):

                self.change_brightness(10)
                return

            if contains_any(
                t,
                [
                    "اخفض",
                    "نقص",
                    "decrease"
                ]
            ):

                self.change_brightness(-10)
                return

        commands = [

            (
                [
                    "واي فاي",
                    "wifi",
                    "الواي فاي",
                    "شبكه الواي فاي",
                    "open wifi"
                ],
                "wifi"
            ),

            (
                [
                    "بلوتوث",
                    "bluetooth",
                    "open bluetooth"
                ],
                "bluetooth"
            ),

            (
                [
                    "شبكه الهاتف",
                    "mobile network"
                ],
                "mobile"
            ),

            (
                [
                    "بيانات الهاتف",
                    "data usage",
                    "استخدام البيانات"
                ],
                "data"
            ),

            (
                [
                    "نقطه الاتصال",
                    "مشاركه الانترنت",
                    "مشاركة الانترنت",
                    "hotspot",
                    "tether"
                ],
                "hotspot"
            ),

            (
                ["vpn"],
                "vpn"
            ),

            (
                ["nfc"],
                "nfc"
            ),

            (
                [
                    "الاشعارات",
                    "الاشعارات",
                    "notifications"
                ],
                "notifications"
            ),

            (
                [
                    "عدم الازعاج",
                    "عدم الازعاج",
                    "do not disturb"
                ],
                "do_not_disturb"
            ),

            (
                [
                    "البطاريه",
                    "البطارية",
                    "battery"
                ],
                "battery"
            ),

            (
                [
                    "توفير الطاقه",
                    "توفير الطاقة",
                    "battery saver"
                ],
                "battery_saver"
            ),

            (
                [
                    "تحسين البطاريه",
                    "تحسين البطارية",
                    "battery optimization"
                ],
                "battery_optimization"
            ),

            (
                [
                    "شاشه القفل",
                    "شاشة القفل",
                    "lock screen"
                ],
                "lock_screen"
            ),

            (
                [
                    "الخصوصيه",
                    "الخصوصية",
                    "privacy"
                ],
                "privacy"
            ),

            (
                [
                    "الموقع",
                    "location"
                ],
                "location"
            ),

            (
                [
                    "الحمايه",
                    "الحماية",
                    "الامن",
                    "الأمن",
                    "security"
                ],
                "security"
            ),

            (
                [
                    "الطوارئ",
                    "emergency"
                ],
                "emergency"
            ),

            (
                [
                    "الحسابات",
                    "accounts"
                ],
                "accounts"
            ),

            (
                [
                    "النسخ الاحتياطي",
                    "backup"
                ],
                "backup"
            ),

            (
                [
                    "google"
                ],
                "google"
            ),

            (
                [
                    "تحديث البرنامج",
                    "تحديث النظام",
                    "software update",
                    "system update"
                ],
                "system_update"
            ),

            (
                [
                    "حول الهاتف",
                    "معلومات الهاتف",
                    "about phone"
                ],
                "about_device"
            ),

            (
                [
                    "خيارات المطور",
                    "developer options"
                ],
                "developer"
            ),

            (
                [
                    "التحكم الابوي",
                    "التحكم الأبوي",
                    "parental controls"
                ],
                "parental"
            ),

            (
                [
                    "امكانيه الوصول",
                    "إمكانية الوصول",
                    "accessibility"
                ],
                "accessibility"
            ),

            (
                [
                    "التطبيقات",
                    "apps"
                ],
                "apps"
            ),

            (
                [
                    "اعدادات الهاتف",
                    "إعدادات الهاتف",
                    "افتح الاعدادات",
                    "افتح الإعدادات",
                    "open settings"
                ],
                "settings"
            ),
        ]

        for words, action in commands:

            if contains_any(
                t,
                words
            ):

                self.setting_action(action)
                return

        self.set_status(
            "تعرفت على الكلام، لكن لا يوجد أمر مطابق"
        )

    # ---------------------------------------------------------
    # أوامر الإعدادات
    # ---------------------------------------------------------

    def setting_action(self, action):

        if action == "lang_ar":

            self.set_language("ar")
            return

        if action == "lang_en":

            self.set_language("en-US")
            return

        if action == "about_app":

            self.goto("about")
            return

        if action == "commands":

            self.goto("commands")
            return

        if action == "theme_light":

            self.dark = False

            Window.clearcolor = (
                0.96,
                0.97,
                0.98,
                1
            )

            self.set_status(
                "تم اختيار الوضع الفاتح"
            )

            return

        if action == "theme_dark":

            self.dark = True

            Window.clearcolor = (
                0.035,
                0.045,
                0.06,
                1
            )

            self.set_status(
                "تم اختيار الوضع الداكن"
            )

            return

        if action == "theme_system":

            self.set_status(
                "الوضع التلقائي يعتمد على إعداد النظام"
            )

            return

        if action == "brightness":

            self.open_write_settings()
            return

        if action == "app_details":

            self.open_app_details()
            return

        if action == "app_notifications":

            self.open_app_notifications()
            return

        if action == "volume_up":

            self.audio_adjust(1)
            return

        if action == "volume_down":

            self.audio_adjust(-1)
            return

        if action == "volume_mute":

            self.audio_mute()
            return

        actions = {

            "settings":
                "android.settings.SETTINGS",

            "wifi":
                "android.settings.WIFI_SETTINGS",

            "bluetooth":
                "android.settings.BLUETOOTH_SETTINGS",

            "mobile":
                "android.settings.NETWORK_OPERATOR_SETTINGS",

            "data":
                "android.settings.DATA_USAGE_SETTINGS",

            "hotspot":
                "android.settings.TETHER_SETTINGS",

            "vpn":
                "android.settings.VPN_SETTINGS",

            "nfc":
                "android.settings.NFC_SETTINGS",

            "notifications":
                "android.settings.NOTIFICATION_SETTINGS",

            "do_not_disturb":
                "android.settings.SOUND_SETTINGS",

            "notification_access":
                "android.settings.ACTION_NOTIFICATION_LISTENER_SETTINGS",

            "battery":
                "android.settings.BATTERY_SETTINGS",

            "battery_usage":
                "android.settings.BATTERY_SETTINGS",

            "battery_saver":
                "android.settings.BATTERY_SAVER_SETTINGS",

            "battery_optimization":
                "android.settings.IGNORE_BATTERY_OPTIMIZATION_SETTINGS",

            "apps":
                "android.settings.APPLICATION_SETTINGS",

            "display":
                "android.settings.DISPLAY_SETTINGS",

            "privacy":
                "android.settings.PRIVACY_SETTINGS",

            "location":
                "android.settings.LOCATION_SOURCE_SETTINGS",

            "security":
                "android.settings.SECURITY_SETTINGS",

            "lock_screen":
                "android.settings.SECURITY_SETTINGS",

            "emergency":
                "android.settings.SAFETY_CENTER_SETTINGS",

            "accounts":
                "android.settings.SYNC_SETTINGS",

            "google":
                "android.settings.GOOGLE_SETTINGS",

            "backup":
                "android.settings.BACKUP_SETTINGS",

            "storage":
                "android.settings.INTERNAL_STORAGE_SETTINGS",

            "digital_wellbeing":
                "android.settings.DIGITAL_WELLBEING_SETTINGS",

            "developer":
                "android.settings.APPLICATION_DEVELOPMENT_SETTINGS",

            "accessibility":
                "android.settings.ACCESSIBILITY_SETTINGS",

            "language":
                "android.settings.LOCALE_SETTINGS",

            "date":
                "android.settings.DATE_SETTINGS",

            "system_update":
                "android.settings.SYSTEM_UPDATE_SETTINGS",

            "about_device":
                "android.settings.DEVICE_INFO_SETTINGS",

            "default_apps":
                "android.settings.MANAGE_DEFAULT_APPS_SETTINGS",

            "special_access":
                "android.settings.MANAGE_UNKNOWN_APP_SOURCES",

            "overlay":
                "android.settings.action.MANAGE_OVERLAY_PERMISSION",

            "parental":
                "android.settings.FAMILY_CENTER",

            "reset":
                "android.settings.MASTER_CLEAR",

            "wallpaper":
                "android.intent.action.SET_WALLPAPER",

            "app_permissions":
                "android.settings.APPLICATION_DETAILS_SETTINGS",
        }

        self.open_android_setting(
            actions.get(
                action,
                "android.settings.SETTINGS"
            )
        )

    # ---------------------------------------------------------
    # فتح إعدادات Android
    # ---------------------------------------------------------

    def open_android_setting(self, action):

        if not ANDROID or not JNIUS:

            self.set_status(
                "هذه الصفحة متاحة داخل APK على Android"
            )

            return

        try:

            Intent = autoclass(
                "android.content.Intent"
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            try:

                PythonActivity.mActivity.startActivity(
                    Intent(action)
                )

            except Exception:

                PythonActivity.mActivity.startActivity(
                    Intent(
                        "android.settings.SETTINGS"
                    )
                )

        except Exception as exc:

            print(
                "settings:",
                action,
                exc
            )

            self.set_status(
                "تعذر فتح صفحة الإعدادات"
            )

    # ---------------------------------------------------------
    # معلومات التطبيق
    # ---------------------------------------------------------

    def open_app_details(self):

        if not ANDROID or not JNIUS:
            return

        try:

            Intent = autoclass(
                "android.content.Intent"
            )

            Uri = autoclass(
                "android.net.Uri"
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            intent = Intent(
                "android.settings.APPLICATION_DETAILS_SETTINGS"
            )

            intent.setData(
                Uri.parse(
                    "package:"
                    + str(
                        PythonActivity.mActivity.getPackageName()
                    )
                )
            )

            PythonActivity.mActivity.startActivity(
                intent
            )

        except Exception as exc:

            print(exc)

    def open_app_notifications(self):

        if not ANDROID or not JNIUS:
            return

        try:

            Intent = autoclass(
                "android.content.Intent"
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            intent = Intent(
                "android.settings.APP_NOTIFICATION_SETTINGS"
            )

            intent.putExtra(
                "android.provider.extra.APP_PACKAGE",
                str(
                    PythonActivity.mActivity.getPackageName()
                )
            )

            PythonActivity.mActivity.startActivity(
                intent
            )

        except Exception:

            self.open_android_setting(
                "android.settings.NOTIFICATION_SETTINGS"
            )

    # ---------------------------------------------------------
    # WRITE_SETTINGS
    # ---------------------------------------------------------

    def open_write_settings(self):

        if not ANDROID or not JNIUS:

            self.set_status(
                "هذه الميزة تعمل داخل Android"
            )

            return

        try:

            Settings = autoclass(
                "android.provider.Settings"
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            if not Settings.System.canWrite(
                PythonActivity.mActivity
            ):

                Intent = autoclass(
                    "android.content.Intent"
                )

                Uri = autoclass(
                    "android.net.Uri"
                )

                intent = Intent(
                    "android.settings.action.MANAGE_WRITE_SETTINGS"
                )

                intent.setData(
                    Uri.parse(
                        "package:"
                        + str(
                            PythonActivity.mActivity.getPackageName()
                        )
                    )
                )

                PythonActivity.mActivity.startActivity(
                    intent
                )

            else:

                self.set_status(
                    "صلاحية تعديل إعدادات النظام متاحة"
                )

        except Exception as exc:

            print(
                "write settings:",
                exc
            )

    # ---------------------------------------------------------
    # الصوت
    # ---------------------------------------------------------

    def audio_adjust(self, direction):

        if not ANDROID or not JNIUS:
            return

        try:

            Context = autoclass(
                "android.content.Context"
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            audio = (
                PythonActivity.mActivity.getSystemService(
                    Context.AUDIO_SERVICE
                )
            )

            if direction > 0:
                adjustment = 1
            else:
                adjustment = -1

            audio.adjustStreamVolume(
                3,
                adjustment,
                0
            )

            if direction > 0:

                self.set_status(
                    "تم رفع الصوت"
                )

            else:

                self.set_status(
                    "تم خفض الصوت"
                )

        except Exception as exc:

            print(
                "audio:",
                exc
            )

    def audio_mute(self):

        if not ANDROID or not JNIUS:
            return

        try:

            Context = autoclass(
                "android.content.Context"
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            audio = (
                PythonActivity.mActivity.getSystemService(
                    Context.AUDIO_SERVICE
                )
            )

            audio.adjustStreamVolume(
                3,
                101,
                0
            )

            self.set_status(
                "تم كتم الصوت"
            )

        except Exception as exc:

            print(
                "mute:",
                exc
            )

    # ---------------------------------------------------------
    # السطوع
    # ---------------------------------------------------------

    def set_brightness(self, percent):

        percent = max(
            0,
            min(
                100,
                int(percent)
            )
        )

        if not ANDROID or not JNIUS:
            return

        try:

            Settings = autoclass(
                "android.provider.Settings"
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            if not Settings.System.canWrite(
                PythonActivity.mActivity
            ):

                self.open_write_settings()

                self.set_status(
                    "اسمح للتطبيق بتعديل إعدادات النظام ثم أعد الأمر"
                )

                return

            value = int(
                percent * 255 / 100
            )

            Settings.System.putInt(
                PythonActivity.mActivity.getContentResolver(),
                Settings.System.SCREEN_BRIGHTNESS,
                value
            )

            self.set_status(
                f"تم ضبط السطوع على {percent}%"
            )

        except Exception as exc:

            print(
                "brightness:",
                exc
            )

    def change_brightness(self, delta):

        if not ANDROID or not JNIUS:
            return

        try:

            Settings = autoclass(
                "android.provider.Settings"
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            resolver = (
                PythonActivity.mActivity.getContentResolver()
            )

            if not Settings.System.canWrite(
                PythonActivity.mActivity
            ):

                self.open_write_settings()

                return

            current = Settings.System.getInt(
                resolver,
                Settings.System.SCREEN_BRIGHTNESS
            )

            new_value = max(
                0,
                min(
                    255,
                    current
                    + int(
                        255 * delta / 100
                    )
                )
            )

            Settings.System.putInt(
                resolver,
                Settings.System.SCREEN_BRIGHTNESS,
                new_value
            )

            self.set_status(
                "تم تغيير السطوع"
            )

        except Exception as exc:

            print(
                "brightness change:",
                exc
            )


if __name__ == "__main__":
    VoiceControlApp().run()
