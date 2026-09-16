# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_OK = True
except Exception:
    arabic_reshaper = None
    get_display = None
    ARABIC_OK = False

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


FONT = "NotoKufiArabic-VariableFont_wght.ttf"
BACKGROUND_FILE = "tanjiro_background.jpg"
MUSIC_FILE = "app_music.mp3"

REQUEST_SPEECH = 7001


# =========================================================
# COLORS
# =========================================================

BG = (0.025, 0.018, 0.025, 1)
PANEL = (0.035, 0.028, 0.045, 0.94)
PANEL_2 = (0.055, 0.025, 0.035, 0.94)

RED = (0.90, 0.055, 0.045, 1)
RED_DARK = (0.38, 0.015, 0.020, 1)

WHITE = (1, 1, 1, 1)
MUTED = (0.76, 0.76, 0.80, 1)


# =========================================================
# ARABIC RTL
# =========================================================

def rtl(text):
    """
    معالجة النص العربي:
    1. تشكيل الحروف.
    2. ترتيب RTL.
    """

    text = str(text)

    if not text:
        return text

    if not ARABIC_OK:
        return text

    if not any("\u0600" <= c <= "\u06ff" for c in text):
        return text

    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


def contains_any(text, words):
    return any(word in text for word in words)


# =========================================================
# ROUNDED PANEL
# =========================================================

class RoundedPanel(BoxLayout):

    def __init__(self, bg=PANEL, radius=dp(16), **kwargs):

        super().__init__(**kwargs)

        self.panel_bg = bg
        self.radius_value = radius

        with self.canvas.before:

            self._panel_color = Color(*bg)

            self._panel_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[radius]
            )

        self.bind(
            pos=self._redraw,
            size=self._redraw
        )

    def _redraw(self, *_):

        self._panel_rect.pos = self.pos
        self._panel_rect.size = self.size


# =========================================================
# SETTING CARD
# =========================================================

class SettingCard(ButtonBehavior, BoxLayout):

    def __init__(
        self,
        title,
        subtitle="",
        icon="",
        action=None,
        accent=RED,
        **kwargs
    ):

        super().__init__(
            orientation="horizontal",
            spacing=dp(10),
            padding=(dp(10), dp(7)),
            **kwargs
        )

        self.size_hint_y = None
        self.height = dp(66)

        self.action_key = action

        self.title_raw = title
        self.subtitle_raw = subtitle

        self.search_text = (
            title + " " + subtitle
        ).lower()

        self.accent = accent
        self._pressed = False

        with self.canvas.before:

            self._bg_color = Color(
                0.025,
                0.022,
                0.032,
                0.94
            )

            self._bg_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(13)]
            )

            self._line_color = Color(*accent)

            self._line = Line(
                rounded_rectangle=(
                    0,
                    0,
                    0,
                    0,
                    dp(13)
                ),
                width=0.8
            )

        self.bind(
            pos=self._draw,
            size=self._draw
        )

        # -------------------------------------------------
        # ICON
        # -------------------------------------------------

        icon_box = BoxLayout(
            size_hint_x=None,
            width=dp(45),
            padding=dp(2)
        )

        with icon_box.canvas.before:

            icon_box._c = Color(*accent)

            icon_box._e = Ellipse(
                size=(dp(38), dp(38)),
                pos=(0, 0)
            )

        icon_box.bind(
            pos=lambda *_: self._place_icon(icon_box)
        )

        self.icon_label = Label(
            text=icon,
            font_name=FONT,
            font_size=dp(15),
            color=WHITE,
            bold=True,
            halign="center",
            valign="middle"
        )

        icon_box.add_widget(self.icon_label)

        # -------------------------------------------------
        # TEXT
        # -------------------------------------------------

        texts = BoxLayout(
            orientation="vertical",
            spacing=dp(1)
        )

        self.title_label = Label(
            text=rtl(title),
            font_name=FONT,
            font_size=dp(12.5),
            color=WHITE,
            bold=True,
            halign="right",
            valign="middle"
        )

        self.subtitle_label = Label(
            text=rtl(subtitle),
            font_name=FONT,
            font_size=dp(9.5),
            color=MUTED,
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

        texts.add_widget(self.title_label)
        texts.add_widget(self.subtitle_label)

        # -------------------------------------------------
        # ARROW
        # -------------------------------------------------

        self.chevron = Label(
            text="›",
            font_name=FONT,
            font_size=dp(24),
            color=WHITE,
            size_hint_x=None,
            width=dp(22),
            halign="center",
            valign="middle"
        )

        self.add_widget(icon_box)
        self.add_widget(texts)
        self.add_widget(self.chevron)

    def _place_icon(self, box):

        box._e.pos = (
            box.x + dp(3),
            box.center_y - dp(19)
        )

        box._e.size = (
            dp(38),
            dp(38)
        )

    def _draw(self, *_):

        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

        self._line.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            dp(13)
        )

    def on_press(self):

        self._pressed = True

        self._bg_color.rgba = (
            0.12,
            0.025,
            0.035,
            0.98
        )

    def on_release(self):

        self._pressed = False

        self._bg_color.rgba = (
            0.025,
            0.022,
            0.032,
            0.94
        )


# =========================================================
# BOTTOM CARD
# =========================================================

class BottomCard(ButtonBehavior, BoxLayout):

    def __init__(
        self,
        title,
        subtitle,
        icon,
        action=None,
        **kwargs
    ):

        super().__init__(
            orientation="horizontal",
            spacing=dp(10),
            padding=(dp(13), dp(8)),
            **kwargs
        )

        self.size_hint_y = None
        self.height = dp(68)

        self.action_key = action

        with self.canvas.before:

            self._color = Color(
                0.025,
                0.018,
                0.025,
                0.96
            )

            self._rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(14)]
            )

            self._border_color = Color(
                RED[0],
                RED[1],
                RED[2],
                0.8
            )

            self._border = Line(
                rounded_rectangle=(
                    0,
                    0,
                    0,
                    0,
                    dp(14)
                ),
                width=0.8
            )

        self.bind(
            pos=self._draw,
            size=self._draw
        )

        self.icon = Label(
            text=icon,
            font_name=FONT,
            font_size=dp(18),
            color=WHITE,
            size_hint_x=None,
            width=dp(34),
            halign="center"
        )

        txt = BoxLayout(
            orientation="vertical"
        )

        self.title_label = Label(
            text=rtl(title),
            font_name=FONT,
            font_size=dp(12.5),
            color=WHITE,
            bold=True,
            halign="right",
            valign="middle"
        )

        self.subtitle_label = Label(
            text=rtl(subtitle),
            font_name=FONT,
            font_size=dp(9.5),
            color=MUTED,
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

        txt.add_widget(self.title_label)
        txt.add_widget(self.subtitle_label)

        self.arrow = Label(
            text="›",
            font_name=FONT,
            font_size=dp(24),
            color=RED,
            size_hint_x=None,
            width=dp(20)
        )

        self.add_widget(self.icon)
        self.add_widget(txt)
        self.add_widget(self.arrow)

    def _draw(self, *_):

        self._rect.pos = self.pos
        self._rect.size = self.size

        self._border.rounded_rectangle = (
            self.x,
            self.y,
            self.width,
            self.height,
            dp(14)
        )


# =========================================================
# MICROPHONE BUTTON
# =========================================================

class MicButton(ButtonBehavior, BoxLayout):

    def __init__(self, **kwargs):

        super().__init__(
            orientation="vertical",
            **kwargs
        )

        self.size_hint_y = None
        self.height = dp(185)

        self.active = False

        with self.canvas.before:

            self._outer = Color(
                0.45,
                0.01,
                0.01,
                0.45
            )

            self._outer_circle = Ellipse(
                size=(dp(148), dp(148))
            )

            self._inner = Color(
                0.72,
                0.02,
                0.02,
                1
            )

            self._inner_circle = Ellipse(
                size=(dp(122), dp(122))
            )

            self._ring = Color(
                1,
                0.18,
                0.12,
                1
            )

            self._line = Line(
                circle=(0, 0, 0),
                width=2.2
            )

        self.label = Label(
            text=rtl("MIC\nابدأ التحدث"),
            font_name=FONT,
            font_size=dp(14),
            color=WHITE,
            bold=True,
            halign="center",
            valign="middle"
        )

        self.add_widget(self.label)

        self.bind(
            pos=self._draw,
            size=self._draw
        )

    def _draw(self, *_):

        d1 = min(
            dp(148),
            self.width - dp(12)
        )

        d2 = d1 - dp(26)

        cx = self.center_x
        cy = self.y + dp(98)

        self._outer_circle.size = (
            d1,
            d1
        )

        self._outer_circle.pos = (
            cx - d1 / 2,
            cy - d1 / 2
        )

        self._inner_circle.size = (
            d2,
            d2
        )

        self._inner_circle.pos = (
            cx - d2 / 2,
            cy - d2 / 2
        )

        self._line.circle = (
            cx,
            cy,
            d2 / 2 + dp(5)
        )

        self.label.pos = (
            self.x,
            self.y - dp(2)
        )

    def on_press(self):

        self._inner.rgba = (
            0.95,
            0.04,
            0.03,
            1
        )

    def on_release(self):

        self._inner.rgba = (
            0.72,
            0.02,
            0.02,
            1
        )


# =========================================================
# MAIN APP
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

        self.dark = True

        self.music = None

    # =====================================================
    # BUILD
    # =====================================================

    def build(self):

        Window.clearcolor = BG

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

        Clock.schedule_once(
            lambda *_: self.start_background_music(),
            0.7
        )

        return self.sm

    # =====================================================
    # LABEL HELPER
    # =====================================================

    def label(
        self,
        text,
        size=15,
        bold=False,
        align="right",
        color=WHITE
    ):

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
            size=lambda o, _: setattr(
                o,
                "text_size",
                (o.width, None)
            )
        )

        return w

    # =====================================================
    # MUSIC
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

                self.set_status(
                    "تم تشغيل الموسيقى"
                )

            else:

                print(
                    "Music file could not be loaded:",
                    MUSIC_FILE
                )

        except Exception as exc:

            print(
                "music:",
                exc
            )

    # =====================================================
    # BACKGROUND
    # =====================================================

    def add_background(
        self,
        root,
        opacity=0.48
    ):

        try:

            with root.canvas.before:

                root._bg_tint = Color(
                    0.18,
                    0.005,
                    0.01,
                    opacity
                )

                root._bg_rect = RoundedRectangle(
                    source=BACKGROUND_FILE,
                    pos=root.pos,
                    size=root.size
                )

                root._dark_overlay = Color(
                    0.01,
                    0.005,
                    0.01,
                    0.32
                )

                root._overlay_rect = RoundedRectangle(
                    pos=root.pos,
                    size=root.size
                )

            root.bind(
                pos=lambda *_: self._update_bg(root),
                size=lambda *_: self._update_bg(root)
            )

        except Exception as exc:

            print(
                "background:",
                exc
            )

    def _update_bg(self, root):

        root._bg_rect.pos = root.pos
        root._bg_rect.size = root.size

        root._overlay_rect.pos = root.pos
        root._overlay_rect.size = root.size

    # =====================================================
    # HOME
    # =====================================================

    def home_screen(self):

        s = Screen(
            name="home"
        )

        root = BoxLayout(
            orientation="vertical",
            padding=(
                dp(14),
                dp(12)
            ),
            spacing=dp(8)
        )

        self.add_background(
            root,
            0.52
        )

        # -------------------------------------------------
        # TOP
        # -------------------------------------------------

        top = BoxLayout(
            size_hint_y=None,
            height=dp(48)
        )

        gear = Label(
            text="⚙",
            font_name=FONT,
            font_size=dp(22),
            color=WHITE,
            size_hint_x=None,
            width=dp(42),
            halign="center"
        )

        gear.bind(
            on_touch_down=lambda *_:
            self.goto("settings")
        )

        top.add_widget(gear)

        top.add_widget(
            BoxLayout()
        )

        root.add_widget(top)

        # -------------------------------------------------
        # TITLES
        # -------------------------------------------------

        root.add_widget(
            self.label(
                "التحكم الصوتي",
                27,
                True,
                "center"
            )
        )

        root.add_widget(
            self.label(
                "Voice Control",
                20,
                True,
                "center"
            )
        )

        root.add_widget(
            self.label(
                "تحكم سريع وآمن في إعدادات Android بالصوت",
                11,
                False,
                "center",
                MUTED
            )
        )

        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        self.result = self.label(
            "لم يتم التعرف على أي كلام بعد.",
            11,
            False,
            "center",
            WHITE
        )

        result_panel = RoundedPanel(
            orientation="vertical",
            size_hint_y=None,
            height=dp(48),
            padding=dp(6),
            bg=(
                0.02,
                0.01,
                0.02,
                0.72
            )
        )

        result_panel.add_widget(
            self.result
        )

        root.add_widget(
            result_panel
        )

        # -------------------------------------------------
        # MICROPHONE
        # -------------------------------------------------

        self.mic = MicButton()

        self.mic.bind(
            on_release=self.toggle_listening
        )

        root.add_widget(
            self.mic
        )

        # -------------------------------------------------
        # STATUS
        # -------------------------------------------------

        self.status = self.label(
            "جاهز للاستماع",
            11,
            False,
            "center",
            WHITE
        )

        root.add_widget(
            self.status
        )

        # -------------------------------------------------
        # BOTTOM BUTTONS
        # -------------------------------------------------

        root.add_widget(
            self.bottom_action(
                "الأوامر الصوتية",
                "عرض جميع أوامر التطبيق",
                "MIC",
                "commands"
            )
        )

        root.add_widget(
            self.bottom_action(
                "من نحن",
                "معلومات عن التطبيق والمطور",
                "INFO",
                "about"
            )
        )

        s.add_widget(root)

        return s

    # =====================================================
    # BOTTOM ACTION
    # =====================================================

    def bottom_action(
        self,
        title,
        subtitle,
        icon,
        target
    ):

        c = BottomCard(
            title,
            subtitle,
            icon,
            action=target
        )

        c.bind(
            on_release=lambda *_:
            self.goto(target)
        )

        return c

    # =====================================================
    # SETTINGS SCREEN
    # =====================================================

    def settings_screen(self):

        s = Screen(
            name="settings"
        )

        root = BoxLayout(
            orientation="vertical",
            padding=(
                dp(10),
                dp(8)
            ),
            spacing=dp(7)
        )

        self.add_background(
            root,
            0.40
        )

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------

        top = BoxLayout(
            size_hint_y=None,
            height=dp(50),
            spacing=dp(5)
        )

        back = Label(
            text="‹",
            font_name=FONT,
            font_size=dp(30),
            color=WHITE,
            size_hint_x=None,
            width=dp(35)
        )

        back.bind(
            on_touch_down=lambda *_:
            self.goto("home")
        )

        top.add_widget(back)

        top.add_widget(
            self.label(
                "إعدادات الهاتف",
                19,
                True,
                "center"
            )
        )

        root.add_widget(top)

        # -------------------------------------------------
        # SEARCH
        # -------------------------------------------------

        self.search_input = TextInput(

            hint_text=rtl(
                "ابحث في الإعدادات..."
            ),

            font_name=FONT,

            font_size=dp(11.5),

            multiline=False,

            size_hint_y=None,

            height=dp(43),

            padding=[
                dp(14),
                dp(10)
            ],

            foreground_color=WHITE,

            hint_text_color=(
                0.65,
                0.65,
                0.70,
                1
            ),

            background_color=(
                0.01,
                0.015,
                0.025,
                0.90
            ),

            cursor_color=RED,

            halign="right"
        )

        self.search_input.bind(
            text=self.filter_settings
        )

        root.add_widget(
            self.search_input
        )

        # -------------------------------------------------
        # SCROLL
        # -------------------------------------------------

        scroll = ScrollView(
            do_scroll_x=False,
            bar_width=dp(3)
        )

        self.settings_content = BoxLayout(
            orientation="vertical",
            spacing=dp(6),
            padding=(
                dp(1),
                dp(3)
            ),
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

        s.add_widget(root)

        return s

    # =====================================================
    # BUILD SETTINGS
    # =====================================================

    def build_settings(self):

        sections = [

            (
                "الاتصال والشبكات",
                [
                    (
                        "الواي فاي",
                        "wifi",
                        "Wi-Fi وWi-Fi Direct",
                        "W"
                    ),
                    (
                        "البلوتوث",
                        "bluetooth",
                        "الأجهزة القريبة",
                        "B"
                    ),
                    (
                        "شبكة الهاتف",
                        "mobile",
                        "شبكة الهاتف المحمول",
                        "M"
                    ),
                    (
                        "بيانات الهاتف",
                        "data",
                        "استخدام البيانات",
                        "D"
                    ),
                    (
                        "نقطة الاتصال",
                        "hotspot",
                        "مشاركة الإنترنت",
                        "H"
                    ),
                    (
                        "VPN",
                        "vpn",
                        "الشبكة الخاصة",
                        "V"
                    ),
                    (
                        "NFC",
                        "nfc",
                        "الاتصال قريب المدى",
                        "N"
                    ),
                ]
            ),

            (
                "الصوت والإشعارات",
                [
                    (
                        "الإشعارات",
                        "notifications",
                        "إدارة الإشعارات",
                        "!"
                    ),
                    (
                        "عدم الإزعاج",
                        "do_not_disturb",
                        "الصوت وعدم الإزعاج",
                        "D"
                    ),
                    (
                        "الوصول إلى الإشعارات",
                        "notification_access",
                        "صلاحيات التنبيهات",
                        "A"
                    ),
                ]
            ),

            (
                "البطارية والخلفية",
                [
                    (
                        "البطارية",
                        "battery",
                        "حالة الطاقة",
                        "B"
                    ),
                    (
                        "استخدام البطارية",
                        "battery_usage",
                        "استهلاك التطبيقات",
                        "U"
                    ),
                    (
                        "توفير الطاقة",
                        "battery_saver",
                        "إطالة عمر البطارية",
                        "P"
                    ),
                    (
                        "تحسين البطارية",
                        "battery_optimization",
                        "تحسين التطبيقات",
                        "O"
                    ),
                ]
            ),

            (
                "الشاشة",
                [
                    (
                        "السطوع",
                        "brightness",
                        "السطوع وإذن تعديل النظام",
                        "S"
                    ),
                    (
                        "إعدادات العرض",
                        "display",
                        "الشاشة والعرض",
                        "D"
                    ),
                ]
            ),

            (
                "الخصوصية والحماية",
                [
                    (
                        "الخصوصية",
                        "privacy",
                        "إعدادات الخصوصية",
                        "P"
                    ),
                    (
                        "الموقع",
                        "location",
                        "خدمات الموقع",
                        "L"
                    ),
                    (
                        "أذونات التطبيق",
                        "app_permissions",
                        "صلاحيات التطبيق",
                        "A"
                    ),
                    (
                        "الأمان",
                        "security",
                        "الحماية وقفل الشاشة",
                        "S"
                    ),
                ]
            ),

            (
                "الحسابات وGoogle",
                [
                    (
                        "الحسابات",
                        "accounts",
                        "الحسابات والمزامنة",
                        "A"
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
                        "B"
                    ),
                ]
            ),

            (
                "التطبيقات",
                [
                    (
                        "جميع التطبيقات",
                        "apps",
                        "إدارة التطبيقات",
                        "A"
                    ),
                    (
                        "معلومات التطبيق",
                        "app_details",
                        "هذا التطبيق",
                        "I"
                    ),
                    (
                        "التطبيقات الافتراضية",
                        "default_apps",
                        "التطبيقات الأساسية",
                        "D"
                    ),
                    (
                        "الوصول الخاص",
                        "special_access",
                        "صلاحيات خاصة",
                        "S"
                    ),
                    (
                        "فوق التطبيقات الأخرى",
                        "overlay",
                        "العرض فوق التطبيقات",
                        "O"
                    ),
                ]
            ),

            (
                "المقاييس والاستخدام",
                [
                    (
                        "استخدام البيانات",
                        "data",
                        "الشبكة",
                        "D"
                    ),
                    (
                        "التخزين",
                        "storage",
                        "مساحة الهاتف",
                        "T"
                    ),
                    (
                        "وقت استخدام الجهاز",
                        "digital_wellbeing",
                        "الرفاهية الرقمية",
                        "T"
                    ),
                ]
            ),

            (
                "النظام والميزات المتقدمة",
                [
                    (
                        "تحديث النظام",
                        "system_update",
                        "تحديث البرنامج",
                        "U"
                    ),
                    (
                        "حول الهاتف",
                        "about_device",
                        "معلومات الجهاز",
                        "I"
                    ),
                    (
                        "خيارات المطور",
                        "developer",
                        "أدوات المطور",
                        "D"
                    ),
                    (
                        "إمكانية الوصول",
                        "accessibility",
                        "ميزات الوصول",
                        "A"
                    ),
                    (
                        "اللغة والإدخال",
                        "language",
                        "اللغة ولوحة المفاتيح",
                        "L"
                    ),
                    (
                        "التاريخ والوقت",
                        "date",
                        "الوقت والتاريخ",
                        "T"
                    ),
                    (
                        "إعادة ضبط الهاتف",
                        "reset",
                        "خيارات إعادة الضبط",
                        "R"
                    ),
                ]
            ),

            (
                "إعدادات التطبيق",
                [
                    (
                        "العربية",
                        "lang_ar",
                        "لغة التعرف الصوتي",
                        "AR"
                    ),
                    (
                        "English",
                        "lang_en",
                        "Speech recognition",
                        "EN"
                    ),
                    (
                        "صفحة الأوامر",
                        "commands",
                        "الأوامر المتاحة",
                        "MIC"
                    ),
                    (
                        "من نحن",
                        "about_app",
                        "المطور والمعلومات",
                        "INFO"
                    ),
                ]
            ),
        ]

        self.settings_content.clear_widgets()

        self.all_setting_cards.clear()

        for section, items in sections:

            title = self.label(
                section,
                14,
                True,
                "right",
                WHITE
            )

            title.size_hint_y = None

            title.height = dp(34)

            self.settings_content.add_widget(
                title
            )

            for caption, action, sub, icon in items:

                card = SettingCard(
                    caption,
                    sub,
                    icon,
                    action=action,
                    accent=RED,
                    size_hint_x=1
                )

                card.bind(
                    on_release=
                    lambda *_x, a=action:
                    self.setting_action(a)
                )

                self.settings_content.add_widget(
                    card
                )

                self.all_setting_cards.append(
                    card
                )

    # =====================================================
    # FILTER SETTINGS
    # =====================================================

    def filter_settings(self, *_):

        query = (
            self.search_input.text.strip().lower()
            if self.search_input
            else ""
        )

        for card in self.all_setting_cards:

            show = (
                not query
            ) or (
                query in card.search_text
            )

            card.opacity = (
                1 if show else 0
            )

            card.disabled = not show

    # =====================================================
    # COMMANDS SCREEN
    # =====================================================

    def commands_screen(self):

        s = Screen(
            name="commands"
        )

        root = BoxLayout(
            orientation="vertical",
            padding=(
                dp(12),
                dp(8)
            ),
            spacing=dp(7)
        )

        self.add_background(
            root,
            0.44
        )

        top = BoxLayout(
            size_hint_y=None,
            height=dp(50)
        )

        back = Label(
            text="‹",
            font_name=FONT,
            font_size=dp(30),
            color=WHITE,
            size_hint_x=None,
            width=dp(35)
        )

        back.bind(
            on_touch_down=lambda *_:
            self.goto("home")
        )

        top.add_widget(back)

        top.add_widget(
            self.label(
                "الأوامر الصوتية",
                19,
                True,
                "center"
            )
        )

        root.add_widget(top)

        panel = RoundedPanel(
            orientation="vertical",
            padding=(
                dp(18),
                dp(14)
            ),
            spacing=dp(7),
            bg=(
                0.02,
                0.012,
                0.028,
                0.93
            ),
            size_hint_y=None
        )

        panel.bind(
            minimum_height=
            panel.setter("height")
        )

        intro = self.label(
            "يمكنك قول:",
            14,
            True,
            "right"
        )

        intro.size_hint_y = None
        intro.height = dp(35)

        panel.add_widget(
            intro
        )

        commands = [

            "افتح الواي فاي",
            "افتح البلوتوث",
            "افتح شبكة الهاتف",
            "افتح نقطة الاتصال",
            "افتح الإشعارات",
            "افتح البطارية",
            "افتح الخصوصية",
            "افتح الموقع",
            "افتح الحماية",
            "افتح شاشة القفل",
            "افتح الطوارئ",
            "افتح الحسابات",
            "افتح النسخ الاحتياطي",
            "افتح Google",
            "افتح تحديث النظام",
            "افتح حول الهاتف",
            "افتح خيارات المطور",
            "ارفع الصوت",
            "اخفض الصوت",
            "كتم الصوت",
            "اجعل السطوع 50",
        ]

        for cmd in commands:

            row = self.label(
                "• " + cmd,
                11,
                False,
                "right",
                WHITE
            )

            row.size_hint_y = None
            row.height = dp(27)

            panel.add_widget(row)

        eng = self.label(
            "English:\n"
            "Open Wi-Fi\n"
            "Open Bluetooth\n"
            "Open settings\n"
            "Open battery\n"
            "Open location\n"
            "Open security",
            10.5,
            False,
            "left",
            MUTED
        )

        eng.size_hint_y = None
        eng.height = dp(170)

        panel.add_widget(eng)

        scroll = ScrollView(
            do_scroll_x=False,
            bar_width=dp(3)
        )

        scroll.add_widget(panel)

        root.add_widget(scroll)

        s.add_widget(root)

        return s

    # =====================================================
    # ABOUT SCREEN
    # =====================================================

    def about_screen(self):

        s = Screen(
            name="about"
        )

        root = BoxLayout(
            orientation="vertical",
            padding=(
                dp(18),
                dp(10)
            ),
            spacing=dp(8)
        )

        self.add_background(
            root,
            0.54
        )

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------

        top = BoxLayout(
            size_hint_y=None,
            height=dp(50)
        )

        back = Label(
            text="‹",
            font_name=FONT,
            font_size=dp(30),
            color=WHITE,
            size_hint_x=None,
            width=dp(35)
        )

        back.bind(
            on_touch_down=lambda *_:
            self.goto("home")
        )

        top.add_widget(back)

        top.add_widget(
            self.label(
                "من نحن",
                19,
                True,
                "center",
                WHITE
            )
        )

        root.add_widget(top)

        root.add_widget(
            BoxLayout(
                size_hint_y=None,
                height=dp(18)
            )
        )

        # -------------------------------------------------
        # APP NAME
        # -------------------------------------------------

        root.add_widget(
            self.label(
                "Voice Control",
                25,
                True,
                "center",
                WHITE
            )
        )

        # -------------------------------------------------
        # DESCRIPTION
        # -------------------------------------------------

        root.add_widget(
            self.label(
                "تطبيق للتحكم الصوتي وفتح إعدادات Android بسرعة،\n"
                "مع دعم العربية وEnglish.",
                12,
                False,
                "center",
                WHITE
            )
        )

        # -------------------------------------------------
        # INFORMATION CARD
        # -------------------------------------------------

        info = RoundedPanel(
            orientation="vertical",
            padding=(
                dp(16),
                dp(10)
            ),
            spacing=dp(3),
            size_hint_y=None,
            height=dp(120),
            bg=(
                0.015,
                0.01,
                0.025,
                0.88
            )
        )

        info.add_widget(
            self.label(
                "المطور",
                10,
                False,
                "right",
                WHITE
            )
        )

        info.add_widget(
            self.label(
                "مهند الحمادي",
                15,
                True,
                "right",
                WHITE
            )
        )

        info.add_widget(
            self.label(
                "الإصدار",
                10,
                False,
                "right",
                WHITE
            )
        )

        info.add_widget(
            self.label(
                "1.0.0",
                12,
                True,
                "right",
                WHITE
            )
        )

        root.add_widget(info)

        # -------------------------------------------------
        # FOOTER
        # -------------------------------------------------

        root.add_widget(
            self.label(
                "واجهة حديثة • أوامر صوتية • إعدادات منظمة",
                10.5,
                False,
                "center",
                WHITE
            )
        )

        root.add_widget(
            BoxLayout()
        )

        root.add_widget(
            self.bottom_action(
                "العودة للرئيسية",
                "",
                "‹",
                "home"
            )
        )

        s.add_widget(root)

        return s

    # =====================================================
    # NAVIGATION
    # =====================================================

    def goto(self, name):

        mapping = {
            "الرئيسية": "home",
            "الإعدادات": "settings"
        }

        self.sm.current = mapping.get(
            name,
            name
        )

    # =====================================================
    # LANGUAGE
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
    # STATUS
    # =====================================================

    def set_status(self, text):

        if self.status:

            self.status.text = rtl(
                text
            )

    # =====================================================
    # LISTENING
    # =====================================================

    def toggle_listening(self, *_):

        if self.listening:

            self.listening = False

            self.set_status(
                "تم إيقاف الاستماع"
            )

            self.mic.label.text = rtl(
                "MIC\nابدأ التحدث"
            )

            return

        self.start_listening()

    # =====================================================
    # MICROPHONE PERMISSION
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
    # START
    # =====================================================

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

    # =====================================================
    # STOP
    # =====================================================

    def on_stop(self):

        try:

            if self.music:

                self.music.stop()

        except Exception:

            pass

        if ANDROID and JNIUS and self.bound:

            try:

                activity.unbind(
                    on_activity_result=
                    self.on_activity_result
                )

            except Exception:

                pass

            self.bound = False

    # =====================================================
    # START LISTENING
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
                "⏹\nجارٍ الاستماع"
            )

            self.set_status(
                "استمع الآن..."
            )

            PythonActivity.mActivity.startActivityForResult(
                intent,
                REQUEST_SPEECH
            )

        except Exception as exc:

            self.listening = False

            self.mic.label.text = rtl(
                "MIC\nابدأ التحدث"
            )

            self.set_status(
                "تعذر فتح التعرف الصوتي"
            )

            print(
                "speech intent:",
                exc
            )

    # =====================================================
    # ACTIVITY RESULT
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
    # SPEECH RESULT
    # =====================================================

    def finish_result(self, intent):

        self.mic.label.text = rtl(
            "MIC\nابدأ التحدث"
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
                "تم التعرف على الكلام"
            )

            self.handle_command(
                text
            )

        else:

            self.set_status(
                "لم يتم التعرف على الكلام"
            )

    # =====================================================
    # NORMALIZE COMMAND
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
    # HANDLE COMMAND
    # =====================================================

    def handle_command(self, text):

        t = self.normalize(text)

        # -------------------------------------------------
        # HELP
        # -------------------------------------------------

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

        # -------------------------------------------------
        # CLEAR
        # -------------------------------------------------

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

        # -------------------------------------------------
        # VOLUME UP
        # -------------------------------------------------

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

        # -------------------------------------------------
        # VOLUME DOWN
        # -------------------------------------------------

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

        # -------------------------------------------------
        # MUTE
        # -------------------------------------------------

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

        # -------------------------------------------------
        # BRIGHTNESS
        # -------------------------------------------------

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

        # -------------------------------------------------
        # SETTINGS COMMANDS
        # -------------------------------------------------

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
    # SETTING ACTION
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

            return

        if action == "theme_dark":

            self.dark = True

            return

        if action == "theme_system":

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
    # OPEN ANDROID SETTING
    # =====================================================

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

    # =====================================================
    # APP DETAILS
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
    # APP NOTIFICATIONS
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
    # WRITE SYSTEM SETTINGS
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
    # AUDIO UP / DOWN
    # =====================================================

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

    # =====================================================
    # MUTE
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
    # SET BRIGHTNESS
    # =====================================================

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

    # =====================================================
    # CHANGE BRIGHTNESS
    # =====================================================

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
# RUN
# =========================================================

if __name__ == "__main__":

    VoiceControlApp().run()
