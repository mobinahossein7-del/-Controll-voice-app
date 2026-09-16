# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.core.audio import SoundLoader
from kivy.metrics import dp
from kivy.properties import ColorProperty, StringProperty
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen


# =========================================================
# دعم العربية
# =========================================================

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:
    arabic_reshaper = None
    get_display = None


# =========================================================
# Android
# =========================================================

try:
    from android.permissions import Permission, check_permission, request_permissions
    ANDROID = True
except Exception:
    ANDROID = False


try:
    from android import activity
    from jnius import autoclass
    JNIUS = True
except Exception:
    JNIUS = False


# =========================================================
# ملفات التطبيق
# =========================================================

FONT = "NotoKufiArabic-VariableFont_wght.ttf"

BACKGROUND_FILE = "tanjiro_background.jpg"

MUSIC_FILE = "app_music.mp3"

REQUEST_SPEECH = 7001


# =========================================================
# معالجة النص العربي
# =========================================================

def rtl(text):
    text = str(text)

    if (
        arabic_reshaper
        and get_display
        and any("\u0600" <= c <= "\u06ff" for c in text)
    ):
        try:
            return get_display(arabic_reshaper.reshape(text))
        except Exception:
            pass

    return text


def contains_any(text, words):
    return any(word in text for word in words)


# =========================================================
# البطاقات
# =========================================================

class Card(ButtonBehavior, BoxLayout):

    text = StringProperty("")
    icon = StringProperty("")
    subtitle = StringProperty("")

    bg = ColorProperty(
        (0.10, 0.12, 0.16, 1)
    )

    radius = dp(18)

    def __init__(self, **kwargs):

        super().__init__(
            orientation="vertical",
            padding=(dp(14), dp(10)),
            spacing=dp(3),
            **kwargs
        )

        self.size_hint_y = None
        self.height = dp(88)

        self.bind(
            pos=self._draw,
            size=self._draw
        )

        with self.canvas.before:

            self._color = Color(
                *self.bg
            )

            self._rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[self.radius]
            )

        self.icon_label = Label(
            text=self.icon,
            font_size=dp(24),
            size_hint_y=None,
            height=dp(30),
            halign="right",
            font_name=FONT
        )

        self.title_label = Label(
            text=rtl(self.text),
            font_name=FONT,
            font_size=dp(13),
            bold=True,
            halign="right",
            valign="middle"
        )

        self.subtitle_label = Label(
            text=rtl(self.subtitle),
            font_name=FONT,
            font_size=dp(10),
            opacity=0.72,
            halign="right",
            valign="middle"
        )

        self.title_label.bind(
            size=lambda w, _: setattr(
                w,
                "text_size",
                (w.width, None)
            )
        )

        self.subtitle_label.bind(
            size=lambda w, _: setattr(
                w,
                "text_size",
                (w.width, None)
            )
        )

        self.add_widget(
            self.icon_label
        )

        self.add_widget(
            self.title_label
        )

        self.add_widget(
            self.subtitle_label
        )

    def _draw(self, *_):

        if hasattr(self, "_rect"):

            self._rect.pos = self.pos

            self._rect.size = self.size

            self._color.rgba = self.bg


# =========================================================
# زر الميكروفون
# =========================================================

class MicButton(ButtonBehavior, BoxLayout):

    bg = ColorProperty(
        (0.12, 0.48, 0.86, 1)
    )

    active_bg = ColorProperty(
        (0.86, 0.20, 0.25, 1)
    )

    def __init__(self, **kwargs):

        super().__init__(
            orientation="vertical",
            **kwargs
        )

        self.size_hint_y = None

        self.height = dp(150)

        self.padding = dp(10)

        with self.canvas.before:

            self._color = Color(
                *self.bg
            )

            self._ellipse = Ellipse(
                pos=self.pos,
                size=(dp(132), dp(132))
            )

        self.label = Label(
            text=rtl("🎙️\nابدأ التحدث"),
            font_name=FONT,
            font_size=dp(16),
            bold=True,
            halign="center",
            valign="middle"
        )

        self.add_widget(
            self.label
        )

        self.bind(
            pos=self._draw,
            size=self._draw
        )

    def _draw(self, *_):

        d = min(
            self.width - dp(8),
            dp(140)
        )

        self._ellipse.size = (
            d,
            d
        )

        self._ellipse.pos = (
            self.center_x - d / 2,
            self.center_y - d / 2
        )

        self._color.rgba = (
            self.active_bg
            if self.state == "down"
            else self.bg
        )


# =========================================================
# التطبيق
# =========================================================

class VoiceControlApp(App):

    title = "Voice Control"

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        self.language = "ar"

        self.listening = False

        self.bound = False

        self.status = None

        self.result = None

        self.mic = None

        self.search_input = None

        self.settings_content = None

        self.all_setting_cards = []

        self.dark = False

        self.music = None


    # =====================================================
    # خلفية التطبيق
    # =====================================================

    def add_background(self, root):

        try:

            with root.canvas.before:

                Color(
                    1,
                    1,
                    1,
                    0.30
                )

                root._background_rect = RoundedRectangle(
                    source=BACKGROUND_FILE,
                    pos=root.pos,
                    size=root.size,
                    radius=[0]
                )

            root.bind(
                pos=lambda *_: setattr(
                    root._background_rect,
                    "pos",
                    root.pos
                )
            )

            root.bind(
                size=lambda *_: setattr(
                    root._background_rect,
                    "size",
                    root.size
                )
            )

        except Exception as exc:

            print(
                "background:",
                exc
            )


    # =====================================================
    # تشغيل الموسيقى
    # =====================================================

    def start_background_music(self):

        try:

            if self.music:

                self.music.stop()

            self.music = SoundLoader.load(
                MUSIC_FILE
            )

            if self.music:

                self.music.loop = True

                self.music.volume = 0.65

                self.music.play()

        except Exception as exc:

            print(
                "music:",
                exc
            )


    # =====================================================
    # بناء التطبيق
    # =====================================================

    def build(self):

        Window.clearcolor = (
            0.035,
            0.045,
            0.06,
            1
        )

        self.sm = ScreenManager()

        self.sm.add_widget(
            self.home_screen()
        )

        self.sm.add_widget(
            self.settings_screen()
        )

        self.sm.add_widget(
            self.commands_screen()
        )

        self.sm.add_widget(
            self.about_screen()
        )

        # تشغيل الموسيقى تلقائياً بعد فتح التطبيق
        Clock.schedule_once(
            lambda *_:
            self.start_background_music(),
            0.35
        )

        return self.sm


    # =====================================================
    # Label
    # =====================================================

    def label(
        self,
        text,
        size=15,
        bold=False,
        align="right",
        color=None
    ):

        if color is None:

            color = (
                (0.94, 0.96, 0.99, 1)
                if self.dark
                else
                (0.10, 0.12, 0.16, 1)
            )

        w = Label(
            text=rtl(text),
            font_name=FONT,
            font_size=dp(size),
            bold=bold,
            color=color,
            halign=align,
            valign="middle"
        )

        w.bind(
            size=lambda o, _:
            setattr(
                o,
                "text_size",
                (o.width, None)
            )
        )

        return w


    # =====================================================
    # Header
    # =====================================================

    def header(
        self,
        title,
        back=None
    ):

        row = BoxLayout(
            size_hint_y=None,
            height=dp(62),
            spacing=dp(8)
        )

        if back:

            b = Card(
                text=back,
                icon="‹",
                subtitle="",
                height=dp(52)
            )

            b.bind(
                on_release=lambda *_:
                self.goto(back)
            )

            row.add_widget(b)

        row.add_widget(
            self.label(
                title,
                22,
                True,
                "right"
            )
        )

        return row


    # =====================================================
    # الصفحة الرئيسية
    # =====================================================

    def home_screen(self):

        s = Screen(
            name="home"
        )

        root = BoxLayout(
            orientation="vertical",
            padding=dp(14),
            spacing=dp(10)
        )

        root.add_widget(
            self.label(
                "التحكم الصوتي",
                25,
                True,
                "right"
            )
        )

        root.add_widget(
            self.label(
                "تحكم سريع وآمن في إعدادات Android بالصوت",
                12,
                False,
                "right"
            )
        )

        status_card = Card(
            text="الحالة",
            icon="●",
            subtitle="جاهز للاستماع"
        )

        self.status = (
            status_card.subtitle_label
        )

        root.add_widget(
            status_card
        )

        self.result = self.label(
            "لم يتم التعرف على أي كلام بعد.",
            14,
            False,
            "center"
        )

        result_box = BoxLayout(
            size_hint_y=None,
            height=dp(72),
            padding=dp(8)
        )

        result_box.add_widget(
            self.result
        )

        root.add_widget(
            result_box
        )

        self.mic = MicButton()

        self.mic.bind(
            on_release=self.toggle_listening
        )

        root.add_widget(
            self.mic
        )

        quick = GridLayout(
            cols=2,
            spacing=dp(8),
            size_hint_y=None
        )

        quick.bind(
            minimum_height=quick.setter(
                "height"
            )
        )

        for title, icon, sub, action in [

            (
                "الاتصال",
                "📶",
                "Wi-Fi وBluetooth",
                "wifi"
            ),

            (
                "الشاشة",
                "🖥️",
                "السطوع والعرض",
                "display"
            ),

            (
                "البطارية",
                "🔋",
                "الطاقة والخلفية",
                "battery"
            ),

            (
                "الخصوصية",
                "🔐",
                "الأمان والأذونات",
                "privacy"
            ),

        ]:

            c = Card(
                text=title,
                icon=icon,
                subtitle=sub,
                height=dp(96)
            )

            c.bind(
                on_release=
                lambda *_x, a=action:
                self.setting_action(a)
            )

            quick.add_widget(
                c
            )

        root.add_widget(
            quick
        )

        nav = GridLayout(
            cols=4,
            spacing=dp(6),
            size_hint_y=None,
            height=dp(62)
        )

        for text, icon, screen in [

            (
                "الرئيسية",
                "⌂",
                "home"
            ),

            (
                "الإعدادات",
                "⚙",
                "settings"
            ),

            (
                "الأوامر",
                "🎙",
                "commands"
            ),

            (
                "من نحن",
                "ⓘ",
                "about"
            ),

        ]:

            c = Card(
                text=text,
                icon=icon,
                subtitle="",
                height=dp(58)
            )

            c.bind(
                on_release=
                lambda *_x, n=screen:
                self.goto(n)
            )

            nav.add_widget(
                c
            )

        root.add_widget(
            nav
        )

        self.add_background(
            root
        )

        s.add_widget(
            root
        )

        return s


    # =====================================================
    # الإعدادات
    # =====================================================

    def settings_screen(self):

        s = Screen(
            name="settings"
        )

        root = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(8)
        )

        root.add_widget(
            self.header(
                "إعدادات الهاتف"
            )
        )

        self.search_input = TextInput(
            hint_text=rtl(
                "🔎 ابحث في الإعدادات..."
            ),
            font_name=FONT,
            font_size=dp(13),
            multiline=False,
            size_hint_y=None,
            height=dp(48),
            padding=[
                dp(12),
                dp(12)
            ]
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
            padding=dp(4),
            size_hint_y=None
        )

        self.settings_content.bind(
            minimum_height=
            self.settings_content.setter(
                "height"
            )
        )

        self.build_settings()

        scroll.add_widget(
            self.settings_content
        )

        root.add_widget(
            scroll
        )

        self.add_background(
            root
        )

        s.add_widget(
            root
        )

        return s


    # =====================================================
    # بناء قائمة الإعدادات
    # =====================================================

    def build_settings(self):

        sections = [

            (
                "📶 الاتصال والشبكات",

                [
                    (
                        "Wi-Fi",
                        "wifi",
                        "الشبكات اللاسلكية",
                        "📶"
                    ),

                    (
                        "Bluetooth",
                        "bluetooth",
                        "الأجهزة القريبة",
                        "ᛒ"
                    ),

                    (
                        "شبكة الهاتف",
                        "mobile",
                        "الشريحة والشبكة",
                        "📱"
                    ),

                    (
                        "بيانات الهاتف",
                        "data",
                        "استخدام البيانات",
                        "📊"
                    ),

                    (
                        "نقطة الاتصال",
                        "hotspot",
                        "مشاركة الإنترنت",
                        "📡"
                    ),

                    (
                        "VPN",
                        "vpn",
                        "الشبكة الخاصة",
                        "🔒"
                    ),

                    (
                        "NFC",
                        "nfc",
                        "الاتصال قريب المدى",
                        "NFC"
                    )
                ]
            ),

            (
                "🔔 الإشعارات",

                [
                    (
                        "الإشعارات",
                        "notifications",
                        "إعدادات التنبيهات",
                        "🔔"
                    ),

                    (
                        "إشعارات التطبيق",
                        "app_notifications",
                        "هذا التطبيق",
                        "📲"
                    ),

                    (
                        "عدم الإزعاج",
                        "do_not_disturb",
                        "الصوت والتنبيهات",
                        "🔕"
                    ),

                    (
                        "الوصول إلى الإشعارات",
                        "notification_access",
                        "صلاحيات التنبيهات",
                        "👁"
                    )
                ]
            ),

            (
                "🔋 البطارية والخلفية",

                [
                    (
                        "البطارية",
                        "battery",
                        "حالة الطاقة",
                        "🔋"
                    ),

                    (
                        "استخدام البطارية",
                        "battery_usage",
                        "استهلاك التطبيقات",
                        "📊"
                    ),

                    (
                        "توفير الطاقة",
                        "battery_saver",
                        "إطالة عمر البطارية",
                        "⚡"
                    ),

                    (
                        "تحسين البطارية",
                        "battery_optimization",
                        "تحسين التطبيقات",
                        "🛠"
                    )
                ]
            ),

            (
                "🎨 النمط والسمات",

                [
                    (
                        "الوضع الفاتح",
                        "theme_light",
                        "مظهر التطبيق",
                        "☀️"
                    ),

                    (
                        "الوضع الداكن",
                        "theme_dark",
                        "مظهر التطبيق",
                        "🌙"
                    ),

                    (
                        "الوضع التلقائي",
                        "theme_system",
                        "حسب النظام",
                        "◐"
                    )
                ]
            ),

            (
                "🖥️ الشاشة",

                [
                    (
                        "السطوع",
                        "brightness",
                        "السطوع وإذن تعديل النظام",
                        "☀️"
                    ),

                    (
                        "إعدادات العرض",
                        "display",
                        "الشاشة والعرض",
                        "🖥️"
                    )
                ]
            ),

            (
                "🔐 الخصوصية والحماية",

                [
                    (
                        "الخصوصية",
                        "privacy",
                        "إعدادات الخصوصية",
                        "🔐"
                    ),

                    (
                        "الموقع",
                        "location",
                        "خدمات الموقع",
                        "📍"
                    ),

                    (
                        "أذونات التطبيق",
                        "app_permissions",
                        "صلاحيات التطبيق",
                        "🛡"
                    ),

                    (
                        "الأمان",
                        "security",
                        "الحماية وقفل الشاشة",
                        "🛡"
                    )
                ]
            ),

            (
                "🚨 الطوارئ",

                [
                    (
                        "الطوارئ",
                        "emergency",
                        "ميزات الطوارئ",
                        "🚨"
                    )
                ]
            ),

            (
                "👤 الحسابات وGoogle",

                [
                    (
                        "الحسابات",
                        "accounts",
                        "الحسابات والمزامنة",
                        "👤"
                    ),

                    (
                        "Google",
                        "google",
                        "خدمات Google",
                        "G"
                    ),

                    (
                        "النسخ الاحتياطي",
                        "backup",
                        "النسخ والاستعادة",
                        "☁️"
                    )
                ]
            ),

            (
                "📱 التطبيقات",

                [
                    (
                        "جميع التطبيقات",
                        "apps",
                        "إدارة التطبيقات",
                        "📱"
                    ),

                    (
                        "معلومات التطبيق",
                        "app_details",
                        "هذا التطبيق",
                        "ℹ️"
                    ),

                    (
                        "التطبيقات الافتراضية",
                        "default_apps",
                        "التطبيقات الأساسية",
                        "⭐"
                    ),

                    (
                        "الوصول الخاص",
                        "special_access",
                        "صلاحيات خاصة",
                        "🔑"
                    ),

                    (
                        "فوق التطبيقات الأخرى",
                        "overlay",
                        "العرض فوق التطبيقات",
                        "▣"
                    )
                ]
            ),

            (
                "📊 المقاييس والاستخدام",

                [
                    (
                        "استخدام البيانات",
                        "data",
                        "الشبكة",
                        "📊"
                    ),

                    (
                        "التخزين",
                        "storage",
                        "مساحة الهاتف",
                        "💾"
                    ),

                    (
                        "وقت استخدام الجهاز",
                        "digital_wellbeing",
                        "الرفاهية الرقمية",
                        "⏱"
                    )
                ]
            ),

            (
                "⚙️ النظام والميزات المتقدمة",

                [
                    (
                        "تحديث النظام",
                        "system_update",
                        "تحديث البرنامج",
                        "↻"
                    ),

                    (
                        "حول الهاتف",
                        "about_device",
                        "معلومات الجهاز",
                        "ⓘ"
                    ),

                    (
                        "خيارات المطور",
                        "developer",
                        "أدوات المطور",
                        "👨‍💻"
                    ),

                    (
                        "إمكانية الوصول",
                        "accessibility",
                        "ميزات الوصول",
                        "♿"
                    ),

                    (
                        "اللغة والإدخال",
                        "language",
                        "اللغة ولوحة المفاتيح",
                        "文"
                    ),

                    (
                        "التاريخ والوقت",
                        "date",
                        "الوقت والتاريخ",
                        "🕒"
                    ),

                    (
                        "إعادة ضبط الهاتف",
                        "reset",
                        "خيارات إعادة الضبط",
                        "↺"
                    )
                ]
            ),

            (
                "👨‍👩‍👧 التحكم الأبوي",

                [
                    (
                        "التحكم الأبوي",
                        "parental",
                        "إدارة العائلة",
                        "👨‍👩‍👧"
                    ),

                    (
                        "الرفاهية الرقمية",
                        "digital_wellbeing",
                        "وقت الشاشة",
                        "⏱"
                    )
                ]
            ),

            (
                "🎙️ إعدادات التطبيق",

                [
                    (
                        "العربية",
                        "lang_ar",
                        "لغة التعرف الصوتي",
                        "🇸🇦"
                    ),

                    (
                        "English",
                        "lang_en",
                        "Speech recognition",
                        "🇺🇸"
                    ),

                    (
                        "صفحة الأوامر",
                        "commands",
                        "الأوامر المتاحة",
                        "🎙️"
                    ),

                    (
                        "من نحن",
                        "about_app",
                        "المطور والمعلومات",
                        "ⓘ"
                    )
                ]
            )
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

            self.settings_content.add_widget(
                title
            )

            grid = GridLayout(
                cols=2,
                spacing=dp(7),
                size_hint_y=None
            )

            grid.bind(
                minimum_height=
                grid.setter("height")
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
                    on_release=
                    lambda *_x, a=action:
                    self.setting_action(a)
                )

                grid.add_widget(
                    card
                )

                self.all_setting_cards.append(
                    card
                )

            self.settings_content.add_widget(
                grid
            )


    # =====================================================
    # البحث في الإعدادات
    # =====================================================

    def filter_settings(self, *_):

        query = (
            self.search_input.text.strip().lower()
            if self.search_input
            else ""
        )

        for card in self.all_setting_cards:

            card.opacity = (
                1
                if not query
                or query in card.search_text
                else 0
            )

            card.disabled = bool(
                query
                and query not in card.search_text
            )


    # =====================================================
    # صفحة الأوامر
    # =====================================================

    def commands_screen(self):

        s = Screen(
            name="commands"
        )

        root = BoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(10)
        )

        root.add_widget(
            self.header(
                "الأوامر الصوتية"
            )
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
            texture_size=
            lambda w, size:
            setattr(
                w,
                "height",
                size[1] + dp(20)
            )
        )

        scroll.add_widget(
            lab
        )

        root.add_widget(
            scroll
        )

        self.add_background(
            root
        )

        s.add_widget(
            root
        )

        return s


    # =====================================================
    # من نحن
    # =====================================================

    def about_screen(self):

        s = Screen(
            name="about"
        )

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

        self.add_background(
            root
        )

        s.add_widget(
            root
        )

        return s


    # =====================================================
    # زر العودة
    # =====================================================

    def button_back(
        self,
        text,
        target
    ):

        c = Card(
            text=text,
            icon="‹",
            subtitle="",
            height=dp(58)
        )

        c.bind(
            on_release=
            lambda *_:
            self.goto(target)
        )

        return c


    # =====================================================
    # الانتقال بين الصفحات
    # =====================================================

    def goto(self, name):

        if name == "الرئيسية":

            name = "home"

        self.sm.current = name


    # =====================================================
    # اللغة
    # =====================================================

    def set_language(self, lang):

        self.language = lang

        self.set_status(
            "لغة التعرف: العربية"
            if lang == "ar"
            else
            "Recognition language: English"
        )


    # =====================================================
    # الحالة
    # =====================================================

    def set_status(self, text):

        if self.status:

            self.status.text = rtl(
                text
            )


    # =====================================================
    # زر الاستماع
    # =====================================================

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


    # =====================================================
    # إذن الميكروفون
    # =====================================================

    def request_mic(self):

        if ANDROID:

            try:

                if not check_permission(
                    Permission.RECORD_AUDIO
                ):

                    request_permissions(
                        [
                            Permission.RECORD_AUDIO
                        ],
                        lambda *_: None
                    )

                    return False

            except Exception:

                pass

        return True


    # =====================================================
    # عند بدء التطبيق
    # =====================================================

    def on_start(self):

        if (
            ANDROID
            and JNIUS
            and not self.bound
        ):

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


    # =====================================================
    # عند إغلاق التطبيق
    # =====================================================

    def on_stop(self):

        try:

            if self.music:

                self.music.stop()

        except Exception:

            pass

        if (
            ANDROID
            and JNIUS
            and self.bound
        ):

            try:

                activity.unbind(
                    on_activity_result=
                    self.on_activity_result
                )

            except Exception:

                pass

            self.bound = False


    # =====================================================
    # بدء التعرف الصوتي
    # =====================================================

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


    # =====================================================
    # نتيجة التعرف الصوتي
    # =====================================================

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


    # =====================================================
    # معالجة النتيجة
    # =====================================================

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

            self.result.text = rtl(
                text
            )

            self.set_status(
                "✅ تم التعرف على الكلام"
            )

            self.handle_command(
                text
            )

        else:

            self.set_status(
                "لم يتم التعرف على الكلام"
            )


    # =====================================================
    # تطبيع الأوامر
    # =====================================================

    def normalize(self, text):

        t = text.strip().lower()

        for a, b in [
            ("أ", "ا"),
            ("إ", "ا"),
            ("آ", "ا"),
            ("ة", "ه"),
            ("ى", "ي")
        ]:

            t = t.replace(
                a,
                b
            )

        return " ".join(
            t.split()
        )


    # =====================================================
    # تحليل الأوامر الصوتية
    # =====================================================

    def handle_command(self, text):

        t = self.normalize(
            text
        )

        # المساعدة
        if contains_any(
            t,
            [
                "مساعده",
                "الاوامر",
                "help"
            ]
        ):

            self.goto(
                "commands"
            )

            return


        # مسح
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


        # رفع الصوت
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

            self.audio_adjust(
                1
            )

            return


        # خفض الصوت
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

            self.audio_adjust(
                -1
            )

            return


        # كتم الصوت
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


        # السطوع
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

                self.change_brightness(
                    10
                )

                return

            if contains_any(
                t,
                [
                    "اخفض",
                    "نقص",
                    "decrease"
                ]
            ):

                self.change_brightness(
                    -10
                )

                return


        # =================================================
        # الأوامر
        # =================================================

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
            )
        ]


        for words, action in commands:

            if contains_any(
                t,
                words
            ):

                self.setting_action(
                    action
                )

                return


        self.set_status(
            "تعرفت على الكلام، لكن لا يوجد أمر مطابق"
        )


    # =====================================================
    # تنفيذ إعداد
    # =====================================================

    def setting_action(self, action):

        if action == "lang_ar":

            self.set_language(
                "ar"
            )

            return


        if action == "lang_en":

            self.set_language(
                "en-US"
            )

            return


        if action == "about_app":

            self.goto(
                "about"
            )

            return


        if action == "commands":

            self.goto(
                "commands"
            )

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


    # =====================================================
    # فتح إعدادات Android
    # =====================================================

    def open_android_setting(
        self,
        action
    ):

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


    # =====================================================
    # معلومات التطبيق
    # =====================================================

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

            print(
                exc
            )


    # =====================================================
    # إشعارات التطبيق
    # =====================================================

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


    # =====================================================
    # صلاحية تعديل إعدادات النظام
    # =====================================================

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


    # =====================================================
    # رفع وخفض الصوت
    # =====================================================

    def audio_adjust(
        self,
        direction
    ):

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


    # =====================================================
    # كتم الصوت
    # =====================================================

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


    # =====================================================
    # ضبط السطوع
    # =====================================================

    def set_brightness(
        self,
        percent
    ):

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


    # =====================================================
    # تغيير السطوع
    # =====================================================

    def change_brightness(
        self,
        delta
    ):

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
                PythonActivity.mActivity
                .getContentResolver()
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


# =========================================================
# تشغيل البرنامج
# =========================================================

if __name__ == "__main__":

    VoiceControlApp().run()
