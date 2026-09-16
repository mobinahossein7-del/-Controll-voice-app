# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import ColorProperty, StringProperty
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:
    arabic_reshaper = None
    get_display = None

try:
    from android.permissions import (
        Permission,
        check_permission,
        request_permissions
    )
    ANDROID = True
except Exception:
    ANDROID = False

try:
    from android import activity
    from jnius import autoclass
    JNIUS = True
except Exception:
    JNIUS = False


FONT = "NotoKufiArabic-VariableFont_wght.ttf"
REQUEST_SPEECH = 7001


def rtl(text):
    text = str(text)
    if arabic_reshaper and get_display:
        try:
            return get_display(arabic_reshaper.reshape(text))
        except Exception:
            return text
    return text


def contains_any(text, words):
    return any(word.lower() in text for word in words)


class Card(ButtonBehavior, BoxLayout):
    text = StringProperty("")
    subtitle = StringProperty("")
    icon = StringProperty("")
    background_color = ColorProperty((0.10, 0.13, 0.18, 1))

    def __init__(self, **kwargs):
        super().__init__(
            orientation="horizontal",
            padding=[dp(12), dp(8)],
            spacing=dp(10),
            size_hint_y=None,
            **kwargs
        )

        with self.canvas.before:
            self.bg_color = Color(*self.background_color)
            self.bg = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(16)]
            )

        self.bind(
            pos=self._update_bg,
            size=self._update_bg,
            background_color=self._update_color
        )

        icon_box = BoxLayout(
            orientation="vertical",
            size_hint_x=None,
            width=dp(48)
        )

        self.icon_label = Label(
            text=self.icon,
            font_name=FONT,
            font_size=22,
            halign="center",
            valign="middle"
        )
        self.icon_label.bind(
            size=lambda w, s: setattr(w, "text_size", s)
        )

        icon_box.add_widget(self.icon_label)

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(2)
        )

        self.title_label = Label(
            text=rtl(self.text),
            font_name=FONT,
            font_size=14,
            bold=True,
            halign="right",
            valign="middle",
            color=(1, 1, 1, 1)
        )
        self.title_label.bind(
            size=lambda w, s: setattr(w, "text_size", s)
        )

        self.subtitle_label = Label(
            text=rtl(self.subtitle),
            font_name=FONT,
            font_size=10,
            halign="right",
            valign="middle",
            color=(0.65, 0.70, 0.78, 1)
        )
        self.subtitle_label.bind(
            size=lambda w, s: setattr(w, "text_size", s)
        )

        content.add_widget(self.title_label)
        content.add_widget(self.subtitle_label)

        self.add_widget(icon_box)
        self.add_widget(content)

    def _update_bg(self, *_):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def _update_color(self, *_):
        self.bg_color.rgb = self.background_color[:3]
        self.bg_color.a = self.background_color[3]


class MicButton(ButtonBehavior, BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            size_hint=(None, None),
            size=(dp(150), dp(150)),
            padding=dp(10),
            **kwargs
        )

        with self.canvas.before:
            self.color = Color(0.12, 0.55, 0.95, 1)
            self.circle = Ellipse(
                pos=self.pos,
                size=self.size
            )

        self.bind(pos=self._update, size=self._update)

        self.label = Label(
            text=rtl("🎙️\nابدأ التحدث"),
            font_name=FONT,
            font_size=15,
            bold=True,
            halign="center",
            valign="middle",
            color=(1, 1, 1, 1)
        )
        self.label.bind(
            size=lambda w, s: setattr(w, "text_size", s)
        )

        self.add_widget(self.label)

    def _update(self, *_):
        self.circle.pos = self.pos
        self.circle.size = self.size


class VoiceControlApp(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.sm = None
        self.status = None
        self.result = None
        self.mic = None
        self.search_input = None
        self.settings_content = None
        self.all_setting_cards = []

        self.language = "ar"
        self.listening = False
        self.bound = False
        self.dark = True

    def build(self):
        Window.clearcolor = (0.035, 0.045, 0.06, 1)

        self.sm = ScreenManager()

        self.sm.add_widget(self.home_screen())
        self.sm.add_widget(self.settings_screen())
        self.sm.add_widget(self.commands_screen())
        self.sm.add_widget(self.about_screen())

        return self.sm

    def label(self, text, size=14, bold=False, halign="right"):
        lab = Label(
            text=rtl(text),
            font_name=FONT,
            font_size=size,
            bold=bold,
            halign=halign,
            valign="middle",
            color=(0.94, 0.96, 1, 1)
        )
        lab.bind(
            size=lambda w, s: setattr(w, "text_size", s)
        )
        return lab

    def header(self, title):
        box = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(60),
            spacing=dp(8)
        )

        title_label = self.label(
            title,
            22,
            True,
            "right"
        )

        home = Card(
            text="الرئيسية",
            icon="⌂",
            subtitle="",
            height=dp(48)
        )
        home.size_hint_x = None
        home.width = dp(115)
        home.bind(
            on_release=lambda *_: self.goto("home")
        )

        box.add_widget(title_label)
        box.add_widget(home)

        return box

    def bottom_nav(self):
        nav = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(62),
            spacing=dp(6)
        )

        home = Card(
            text="الرئيسية",
            icon="⌂",
            subtitle="",
            height=dp(58)
        )

        settings = Card(
            text="الإعدادات",
            icon="⚙",
            subtitle="",
            height=dp(58)
        )

        commands = Card(
            text="الأوامر",
            icon="🎙",
            subtitle="",
            height=dp(58)
        )

        about = Card(
            text="من نحن",
            icon="ⓘ",
            subtitle="",
            height=dp(58)
        )

        home.bind(on_release=lambda *_: self.goto("home"))
        settings.bind(on_release=lambda *_: self.goto("settings"))
        commands.bind(on_release=lambda *_: self.goto("commands"))
        about.bind(on_release=lambda *_: self.goto("about"))

        nav.add_widget(home)
        nav.add_widget(settings)
        nav.add_widget(commands)
        nav.add_widget(about)

        return nav

    def home_screen(self):
        s = Screen(name="home")

        root = BoxLayout(
            orientation="vertical",
            padding=dp(14),
            spacing=dp(10)
        )

        title = self.label(
            "Voice Control",
            27,
            True,
            "center"
        )
        title.size_hint_y = None
        title.height = dp(55)

        subtitle = self.label(
            "التحكم بالصوت وإعدادات Android",
            13,
            False,
            "center"
        )
        subtitle.size_hint_y = None
        subtitle.height = dp(35)

        status_card = Card(
            text="الحالة",
            icon="●",
            subtitle="جاهز للاستماع",
            height=dp(75)
        )

        self.status = status_card.subtitle_label

        root.add_widget(title)
        root.add_widget(subtitle)
        root.add_widget(status_card)

        result_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(82),
            padding=dp(10)
        )

        self.result = self.label(
            "لم يتم التعرف على أي كلام بعد.",
            14,
            False,
            "center"
        )

        result_box.add_widget(self.result)
        root.add_widget(result_box)

        mic_area = BoxLayout(
            orientation="vertical",
            padding=dp(8)
        )

        self.mic = MicButton()
        self.mic.bind(
            on_release=self.toggle_listening
        )

        mic_area.add_widget(
            self.mic
        )

        root.add_widget(mic_area)

        quick_title = self.label(
            "الوصول السريع",
            16,
            True,
            "right"
        )
        quick_title.size_hint_y = None
        quick_title.height = dp(35)

        root.add_widget(quick_title)

        quick_scroll = ScrollView(
            do_scroll_x=False
        )

        quick_grid = GridLayout(
            cols=2,
            spacing=dp(7),
            size_hint_y=None
        )
        quick_grid.bind(
            minimum_height=quick_grid.setter("height")
        )

        quick_items = [
            ("Wi-Fi", "wifi", "فتح إعدادات Wi-Fi", "📶"),
            ("Bluetooth", "bluetooth", "فتح البلوتوث", "🔵"),
            ("الشاشة", "display", "إعدادات الشاشة", "📱"),
            ("البطارية", "battery", "إعدادات البطارية", "🔋"),
            ("الخصوصية", "privacy", "إعدادات الخصوصية", "🔒"),
            ("الموقع", "location", "إعدادات الموقع", "📍"),
        ]

        for caption, action, sub, icon in quick_items:
            card = Card(
                text=caption,
                icon=icon,
                subtitle=sub,
                height=dp(82)
            )
            card.bind(
                on_release=lambda *_,
                a=action: self.setting_action(a)
            )
            quick_grid.add_widget(card)

        quick_scroll.add_widget(quick_grid)
        root.add_widget(quick_scroll)

        root.add_widget(self.bottom_nav())

        s.add_widget(root)

        return s

    def settings_screen(self):
        s = Screen(name="settings")

        root = BoxLayout(
            orientation="vertical",
            padding=dp(14),
            spacing=dp(8)
        )

        root.add_widget(
            self.header("إعدادات التطبيق والهاتف")
        )

        self.search_input = TextInput(
            hint_text=rtl("ابحث عن إعداد..."),
            font_name=FONT,
            font_size=13,
            multiline=False,
            size_hint_y=None,
            height=dp(48),
            padding=[dp(12), dp(10)],
            background_normal="",
            background_active="",
            background_color=(0.09, 0.11, 0.15, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.2, 0.65, 1, 1)
        )

        self.search_input.bind(
            text=self.filter_settings
        )

        root.add_widget(
            self.search_input
        )

        scroll = ScrollView(
            do_scroll_x=False
        )

        self.settings_content = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None
        )

        self.settings_content.bind(
            minimum_height=self.settings_content.setter("height")
        )

        self.all_setting_cards = []

        sections = [
            (
                "الاتصال والشبكات",
                [
                    ("Wi-Fi", "wifi", "إعدادات الشبكة اللاسلكية", "📶"),
                    ("Bluetooth", "bluetooth", "إعدادات البلوتوث", "🔵"),
                    ("شبكة الهاتف", "mobile", "الشبكات الخلوية", "📡"),
                    ("استخدام البيانات", "data", "استهلاك بيانات الهاتف", "📊"),
                    ("نقطة الاتصال", "hotspot", "مشاركة الإنترنت", "🌐"),
                    ("VPN", "vpn", "الشبكات الخاصة الافتراضية", "🔐"),
                    ("NFC", "nfc", "الاتصال قريب المدى", "📳"),
                ]
            ),
            (
                "الصوت والإشعارات",
                [
                    ("الإشعارات", "notifications", "إعدادات الإشعارات", "🔔"),
                    ("عدم الإزعاج", "do_not_disturb", "الصوت وعدم الإزعاج", "🔕"),
                    ("الوصول إلى الإشعارات", "notification_access", "صلاحيات قراءة الإشعارات", "📩"),
                    ("رفع الصوت", "volume_up", "زيادة مستوى الصوت", "🔊"),
                    ("خفض الصوت", "volume_down", "تقليل مستوى الصوت", "🔉"),
                    ("كتم الصوت", "mute", "الوضع الصامت", "🔇"),
                ]
            ),
            (
                "الشاشة والطاقة",
                [
                    ("الشاشة", "display", "إعدادات الشاشة", "📱"),
                    ("السطوع", "brightness", "صلاحية تعديل السطوع", "☀️"),
                    ("البطارية", "battery", "معلومات البطارية", "🔋"),
                    ("استخدام البطارية", "battery_usage", "استهلاك الطاقة", "⚡"),
                    ("توفير الطاقة", "battery_saver", "وضع توفير البطارية", "🔋"),
                    ("تحسين البطارية", "battery_optimization", "تحسين التطبيقات", "⚙️"),
                ]
            ),
            (
                "الخصوصية والأمان",
                [
                    ("الخصوصية", "privacy", "إعدادات الخصوصية", "🛡️"),
                    ("الموقع", "location", "خدمات الموقع", "📍"),
                    ("الحماية والأمان", "security", "إعدادات الأمان", "🔒"),
                    ("شاشة القفل", "lock_screen", "الحماية والقفل", "🔐"),
                    ("الطوارئ", "emergency", "معلومات وخدمات الطوارئ", "🚨"),
                ]
            ),
            (
                "النظام",
                [
                    ("الحسابات", "accounts", "الحسابات والمزامنة", "👤"),
                    ("Google", "google", "إعدادات Google", "G"),
                    ("النسخ الاحتياطي", "backup", "النسخ الاحتياطي والاستعادة", "💾"),
                    ("التخزين", "storage", "مساحة التخزين", "💿"),
                    ("الرفاهية الرقمية", "digital_wellbeing", "إدارة وقت استخدام الهاتف", "⏱️"),
                    ("خيارات المطور", "developer", "خيارات المطور", "🧰"),
                    ("إمكانية الوصول", "accessibility", "خدمات إمكانية الوصول", "♿"),
                    ("اللغة", "language", "اللغات والإدخال", "🌐"),
                    ("التاريخ والوقت", "date", "إعدادات التاريخ والوقت", "🕒"),
                    ("تحديث النظام", "system_update", "تحديث Android", "⬆️"),
                    ("حول الهاتف", "about_device", "معلومات الجهاز", "ℹ️"),
                ]
            ),
            (
                "التطبيقات",
                [
                    ("التطبيقات", "apps", "إدارة التطبيقات", "▦"),
                    ("التطبيقات الافتراضية", "default_apps", "اختيار التطبيقات الافتراضية", "⭐"),
                    ("صلاحيات التطبيقات", "app_permissions", "إدارة صلاحيات التطبيقات", "🔑"),
                    ("الوصول الخاص", "special_access", "صلاحيات الوصول الخاص", "⚙️"),
                    ("الظهور فوق التطبيقات", "overlay", "صلاحية النوافذ العائمة", "🪟"),
                    ("إشعارات التطبيق", "app_notifications", "إشعارات Voice Control", "🔔"),
                    ("معلومات التطبيق", "app_details", "تفاصيل Voice Control", "📦"),
                ]
            ),
            (
                "التطبيق",
                [
                    ("العربية", "lang_ar", "لغة التعرف الصوتي العربية", "ع"),
                    ("English", "lang_en", "English speech recognition", "E"),
                    ("الوضع الفاتح", "theme_light", "واجهة فاتحة", "☀️"),
                    ("الوضع الداكن", "theme_dark", "واجهة داكنة", "🌙"),
                    ("الوضع التلقائي", "theme_system", "حسب إعداد النظام", "🔄"),
                    ("الأوامر الصوتية", "commands", "عرض الأوامر المتاحة", "🎙️"),
                    ("من نحن", "about_app", "معلومات التطبيق والمطور", "ⓘ"),
                ]
            ),
        ]

        for section_title, items in sections:
            title = self.label(
                section_title,
                17,
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
                    on_release=lambda *_x,
                    a=action: self.setting_action(a)
                )

                grid.add_widget(card)
                self.all_setting_cards.append(card)

            self.settings_content.add_widget(grid)

        scroll.add_widget(
            self.settings_content
        )

        root.add_widget(scroll)
        root.add_widget(self.bottom_nav())

        s.add_widget(root)

        return s

    def filter_settings(self, *_):
        query = (
            self.search_input.text.strip().lower()
            if self.search_input
            else ""
        )

        for card in self.all_setting_cards:
            card.opacity = (
                1
                if not query or query in card.search_text
                else 0
            )

            card.disabled = bool(
                query and query not in card.search_text
            )

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
            "• افتح نقطة الاتصال\n"
            "• افتح الإشعارات\n"
            "• افتح البطارية\n"
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
            "• افتح التحكم الأبوي\n"
            "• ارفع الصوت\n"
            "• اخفض الصوت\n"
            "• كتم الصوت\n"
            "• اجعل السطوع 50\n\n"
            "English:\n"
            "Open Wi-Fi\n"
            "Open Bluetooth\n"
            "Open settings\n"
            "Open privacy\n"
            "Open battery\n"
            "Open developer options"
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
            setattr(w, "height", size[1] + dp(20))
        )

        scroll.add_widget(lab)

        root.add_widget(scroll)

        root.add_widget(self.bottom_nav())

        s.add_widget(root)

        return s

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

        root.add_widget(
            self.bottom_nav()
        )

        s.add_widget(root)

        return s

    def button_back(self, text, target):
        c = Card(
            text=text,
            icon="‹",
            subtitle="",
            height=dp(58)
        )

        c.bind(
            on_release=lambda *_:
            self.goto(target)
        )

        return c

    def goto(self, name):
        if name == "الرئيسية":
            name = "home"

        self.sm.current = name

    def set_language(self, lang):
        self.language = lang

        self.set_status(
            "لغة التعرف: العربية"
            if lang == "ar"
            else
            "Recognition language: English"
        )

    def set_status(self, text):
        if self.status:
            self.status.text = rtl(text)

    def toggle_listening(self, *_):
        if self.listening:
            self.listening = False

            self.set_status(
                "تم إيقاف الاستماع"
            )

            self.mic.label.text = rtl(
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
                    on_activity_result=
                    self.on_activity_result
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
                    on_activity_result=
                    self.on_activity_result
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

            intent.putExtra(
                RI.EXTRA_PROMPT,
                "تحدث الآن"
                if self.language == "ar"
                else
                "Speak now"
            )

            self.listening = True

            self.mic.label.text = rtl(
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

            self.mic.label.text = rtl(
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
        self.mic.label.text = rtl(
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

        return " ".join(t.split())

    def handle_command(self, text):
        t = self.normalize(text)

        if contains_any(
            t,
            [
                "مساعده",
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
                "brightness"
            ]
        ):
            import re

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
                    "hotspot",
                    "tether"
                ],
                "hotspot"
            ),

            (
                [
                    "vpn"
                ],
                "vpn"
            ),

            (
                [
                    "nfc"
                ],
                "nfc"
            ),

            (
                [
                    "الاشعارات",
                    "notifications"
                ],
                "notifications"
            ),

            (
                [
                    "عدم الازعاج",
                    "do not disturb"
                ],
                "do_not_disturb"
            ),

            (
                [
                    "البطاريه",
                    "battery"
                ],
                "battery"
            ),

            (
                [
                    "توفير الطاقه",
                    "battery saver"
                ],
                "battery_saver"
            ),

            (
                [
                    "تحسين البطاريه",
                    "battery optimization"
                ],
                "battery_optimization"
            ),

            (
                [
                    "شاشه القفل",
                    "lock screen"
                ],
                "lock_screen"
            ),

            (
                [
                    "الخصوصيه",
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
                    "الامن",
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
                    "parental controls"
                ],
                "parental"
            ),

            (
                [
                    "امكانيه الوصول",
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
                    "افتح الاعدادات",
                    "open settings"
                ],
                "settings"
            ),
        ]

        for words, action in commands:
            if contains_any(t, words):
                self.setting_action(action)
                return

        self.set_status(
            "تعرفت على الكلام، لكن لا يوجد أمر مطابق"
        )

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

        if action == "mute":
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

            "app_permissions":
                "android.settings.APPLICATION_DETAILS_SETTINGS",
        }

        self.open_android_setting(
            actions.get(
                action,
                "android.settings.SETTINGS"
            )
        )

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

            audio = PythonActivity.mActivity.getSystemService(
                Context.AUDIO_SERVICE
            )

            audio.adjustStreamVolume(
                3,
                1 if direction > 0 else -1,
                0
            )

            self.set_status(
                "تم رفع الصوت"
                if direction > 0
                else
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

            audio = PythonActivity.mActivity.getSystemService(
                Context.AUDIO_SERVICE
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

    def set_brightness(self, percent):
        percent = max(
            0,
            min(100, int(percent))
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

            resolver = PythonActivity.mActivity.getContentResolver()

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
                    + int(255 * delta / 100)
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
