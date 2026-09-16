# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.core.audio import SoundLoader
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


# ============================================================
# OPTIONAL ARABIC SUPPORT
# ============================================================

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:
    arabic_reshaper = None
    get_display = None


# ============================================================
# ANDROID SUPPORT
# ============================================================

try:
    from android.permissions import (
        Permission,
        check_permission,
        request_permissions,
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


# ============================================================
# APPLICATION CONSTANTS
# ============================================================

FONT = "NotoKufiArabic-VariableFont_wght.ttf"
BACKGROUND_FILE = "tanjiro_background.jpg"
MUSIC_FILE = "app_music.mp3"

REQUEST_SPEECH = 7001

APP_TITLE = "Voice Control"
APP_VERSION = "1.0.0"
DEVELOPER = "mohaned adel alhmadi"


# ============================================================
# TEXT HELPERS
# ============================================================

def rtl(text):
    """
    Prepare Arabic text for Kivy.

    The application interface is English-only,
    but Arabic is retained for speech recognition
    results and Arabic command processing.
    """
    text = str(text)

    if not text:
        return text

    if (
        arabic_reshaper
        and get_display
        and any("\u0600" <= char <= "\u06ff" for char in text)
    ):
        try:
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped, base_dir="R")
        except Exception:
            try:
                return get_display(
                    arabic_reshaper.reshape(text)
                )
            except Exception:
                return text

    return text


def contains_any(text, words):
    """Return True if any word exists in text."""
    return any(word in text for word in words)


# ============================================================
# LABEL
# ============================================================

def make_label(
    text,
    font_size=15,
    bold=False,
    halign="center",
    valign="middle",
    color=(0.94, 0.96, 0.99, 1),
    **kwargs,
):
    """
    General-purpose label.

    The interface itself uses English text.
    Arabic-capable font is retained for recognition results.
    """
    label = Label(
        text=str(text),
        font_name=FONT,
        font_size=dp(font_size),
        bold=bold,
        halign=halign,
        valign=valign,
        color=color,
        **kwargs,
    )

    label.bind(
        size=lambda widget, size: setattr(
            widget,
            "text_size",
            (widget.width, None),
        )
    )

    return label


def make_arabic_label(
    text,
    font_size=15,
    bold=False,
    halign="right",
    color=(0.94, 0.96, 0.99, 1),
    **kwargs,
):
    """Create a label capable of displaying Arabic correctly."""

    label = Label(
        text=rtl(text),
        font_name=FONT,
        font_size=dp(font_size),
        bold=bold,
        halign=halign,
        valign="middle",
        color=color,
        **kwargs,
    )

    label.bind(
        size=lambda widget, size: setattr(
            widget,
            "text_size",
            (widget.width, None),
        )
    )

    return label


# ============================================================
# CARD
# ============================================================

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
            padding=(
                dp(14),
                dp(8),
            ),
            spacing=dp(2),
            **kwargs,
        )

        self.size_hint_y = None

        if "height" not in kwargs:
            self.height = dp(88)

        with self.canvas.before:

            self._color = Color(
                *self.bg
            )

            self._rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[
                    self.radius
                ],
            )

        self.icon_label = make_label(
            self.icon,
            font_size=22,
            bold=True,
            size_hint_y=None,
            height=dp(28),
        )

        self.title_label = make_label(
            self.text,
            font_size=13,
            bold=True,
        )

        self.subtitle_label = make_label(
            self.subtitle,
            font_size=9,
            color=(
                0.70,
                0.73,
                0.78,
                1,
            ),
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

        self.bind(
            pos=self._draw,
            size=self._draw,
        )

    def _draw(self, *_):

        if hasattr(self, "_rect"):

            self._rect.pos = self.pos
            self._rect.size = self.size
            self._color.rgba = self.bg


# ============================================================
# MICROPHONE BUTTON
# ============================================================

class MicButton(ButtonBehavior, BoxLayout):

    normal_bg = ColorProperty(
        (0.12, 0.48, 0.86, 1)
    )

    active_bg = ColorProperty(
        (0.86, 0.20, 0.25, 1)
    )

    def __init__(self, **kwargs):

        super().__init__(
            orientation="vertical",
            **kwargs,
        )

        self.size_hint_y = None
        self.height = dp(150)

        self.padding = dp(10)

        with self.canvas.before:

            self._color = Color(
                *self.normal_bg
            )

            self._ellipse = Ellipse(
                pos=self.pos,
                size=(
                    dp(132),
                    dp(132),
                ),
            )

        self.label = make_label(
            "MIC",
            font_size=18,
            bold=True,
            halign="center",
        )

        self.add_widget(self.label)

        self.bind(
            pos=self._draw,
            size=self._draw,
            state=self._draw,
        )

    def _draw(self, *_):

        diameter = min(
            max(self.width - dp(8), dp(60)),
            dp(140),
        )

        self._ellipse.size = (
            diameter,
            diameter,
        )

        self._ellipse.pos = (
            self.center_x - diameter / 2,
            self.center_y - diameter / 2,
        )

        if self.state == "down":

            self._color.rgba = (
                self.active_bg
            )

        else:

            self._color.rgba = (
                self.normal_bg
            )


# ============================================================
# MAIN APPLICATION
# ============================================================

class VoiceControlApp(App):

    title = APP_TITLE

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

        # Arabic recognition only.
        self.language = "ar"

        self.listening = False
        self.bound = False

        self.status = None
        self.result = None
        self.mic = None

        self.search_input = None
        self.settings_content = None

        self.all_setting_cards = []

        self.music = None

        self.dark = True

    # ========================================================
    # BUILD
    # ========================================================

    def build(self):

        try:

            LabelBase.register(
                name="NotoKufiArabic",
                fn_regular=FONT,
            )

        except Exception as exc:

            print(
                "Font registration error:",
                exc,
            )

        Window.clearcolor = (
            0.035,
            0.045,
            0.06,
            1,
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

        Clock.schedule_once(
            lambda *_:
            self.start_background_music(),
            0.5,
        )

        return self.sm

    # ========================================================
    # MUSIC
    # ========================================================

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

            else:

                print(
                    "Music file not found or cannot be loaded:",
                    MUSIC_FILE,
                )

        except Exception as exc:

            print(
                "Music error:",
                exc,
            )

    # ========================================================
    # STATUS
    # ========================================================

    def set_status(self, text):

        if self.status:

            self.status.text = str(text)

    # ========================================================
    # HOME SCREEN
    # ========================================================

    def home_screen(self):

        screen = Screen(
            name="home"
        )

        root = BoxLayout(
            orientation="vertical",
            padding=dp(14),
            spacing=dp(10),
        )

        root.add_widget(
            make_label(
                "Voice Control",
                font_size=25,
                bold=True,
            )
        )

        root.add_widget(
            make_label(
                "Control Android settings using Arabic voice commands.",
                font_size=11,
            )
        )

        status_card = Card(
            text="Status",
            icon="●",
            subtitle="Ready",
            height=dp(88),
        )

        self.status = (
            status_card.subtitle_label
        )

        root.add_widget(
            status_card
        )

        self.result = make_arabic_label(
            "لم يتم التعرف على أي كلام بعد.",
            font_size=14,
            halign="center",
        )

        result_box = BoxLayout(
            size_hint_y=None,
            height=dp(72),
            padding=dp(8),
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
            size_hint_y=None,
        )

        quick.bind(
            minimum_height=quick.setter(
                "height"
            )
        )

        quick_items = [

            (
                "Network",
                "WIFI",
                "Wi-Fi and Bluetooth",
                "wifi",
            ),

            (
                "Display",
                "DISPLAY",
                "Brightness and display",
                "display",
            ),

            (
                "Battery",
                "BAT",
                "Power settings",
                "battery",
            ),

            (
                "Privacy",
                "PRIV",
                "Security and permissions",
                "privacy",
            ),
        ]

        for title, icon, subtitle, action in quick_items:

            card = Card(
                text=title,
                icon=icon,
                subtitle=subtitle,
                height=dp(96),
            )

            card.bind(
                on_release=lambda *_,
                action=action:
                self.setting_action(action)
            )

            quick.add_widget(card)

        root.add_widget(
            quick
        )

        nav = GridLayout(
            cols=4,
            spacing=dp(6),
            size_hint_y=None,
            height=dp(62),
        )

        nav_items = [

            (
                "Home",
                "⌂",
                "home",
            ),

            (
                "Settings",
                "⚙",
                "settings",
            ),

            (
                "Commands",
                "MIC",
                "commands",
            ),

            (
                "About",
                "INFO",
                "about",
            ),
        ]

        for text, icon, target in nav_items:

            card = Card(
                text=text,
                icon=icon,
                subtitle="",
                height=dp(58),
            )

            card.bind(
                on_release=lambda *_,
                target=target:
                self.goto(target)
            )

            nav.add_widget(card)

        root.add_widget(
            nav
        )

        self.add_background(root)

        screen.add_widget(
            root
        )

        return screen

    # ========================================================
    # SETTINGS SCREEN
    # ========================================================

    def settings_screen(self):

        screen = Screen(
            name="settings"
        )

        root = BoxLayout(
            orientation="vertical",
            padding=dp(12),
            spacing=dp(8),
        )

        root.add_widget(
            self.header(
                "Phone Settings",
                "home",
            )
        )

        self.search_input = TextInput(
            hint_text="Search settings...",
            font_name=FONT,
            font_size=dp(13),
            multiline=False,
            size_hint_y=None,
            height=dp(48),
            padding=[
                dp(12),
                dp(12),
            ],
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
            size_hint_y=None,
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

        self.add_background(root)

        screen.add_widget(
            root
        )

        return screen

    # ========================================================
    # SETTINGS LIST
    # ========================================================

    def build_settings(self):

        sections = [

            (
                "NETWORK",
                [

                    (
                        "Wi-Fi",
                        "wifi",
                        "Wireless networks",
                        "WIFI",
                    ),

                    (
                        "Bluetooth",
                        "bluetooth",
                        "Connected devices",
                        "BT",
                    ),

                    (
                        "Mobile Network",
                        "mobile",
                        "SIM and mobile network",
                        "APP",
                    ),

                    (
                        "Mobile Data",
                        "data",
                        "Data usage",
                        "DATA",
                    ),

                    (
                        "Hotspot",
                        "hotspot",
                        "Internet sharing",
                        "HOT",
                    ),

                    (
                        "VPN",
                        "vpn",
                        "Private network",
                        "VPN",
                    ),

                    (
                        "NFC",
                        "nfc",
                        "Near-field communication",
                        "NFC",
                    ),
                ],
            ),

            (
                "NOTIFICATIONS",
                [

                    (
                        "Notifications",
                        "notifications",
                        "Notification settings",
                        "NOTIFY",
                    ),

                    (
                        "App Notifications",
                        "app_notifications",
                        "This application",
                        "APP",
                    ),

                    (
                        "Do Not Disturb",
                        "do_not_disturb",
                        "Sound and notifications",
                        "DND",
                    ),

                    (
                        "Notification Access",
                        "notification_access",
                        "Notification permissions",
                        "ACCESS",
                    ),
                ],
            ),

            (
                "BATTERY",
                [

                    (
                        "Battery",
                        "battery",
                        "Battery status",
                        "BAT",
                    ),

                    (
                        "Battery Usage",
                        "battery_usage",
                        "Application usage",
                        "DATA",
                    ),

                    (
                        "Battery Saver",
                        "battery_saver",
                        "Extend battery life",
                        "POWER",
                    ),

                    (
                        "Battery Optimization",
                        "battery_optimization",
                        "Optimize applications",
                        "OPT",
                    ),
                ],
            ),

            (
                "DISPLAY",
                [

                    (
                        "Brightness",
                        "brightness",
                        "Screen brightness",
                        "SUN",
                    ),

                    (
                        "Display Settings",
                        "display",
                        "Screen and display",
                        "DISPLAY",
                    ),

                    (
                        "Light Theme",
                        "theme_light",
                        "Application appearance",
                        "SUN",
                    ),

                    (
                        "Dark Theme",
                        "theme_dark",
                        "Application appearance",
                        "DARK",
                    ),
                ],
            ),

            (
                "PRIVACY AND SECURITY",
                [

                    (
                        "Privacy",
                        "privacy",
                        "Privacy settings",
                        "PRIV",
                    ),

                    (
                        "Location",
                        "location",
                        "Location services",
                        "LOC",
                    ),

                    (
                        "App Permissions",
                        "app_permissions",
                        "Application permissions",
                        "SEC",
                    ),

                    (
                        "Security",
                        "security",
                        "Security settings",
                        "SEC",
                    ),

                    (
                        "Lock Screen",
                        "lock_screen",
                        "Lock screen security",
                        "LOCK",
                    ),
                ],
            ),

            (
                "SYSTEM",
                [

                    (
                        "System Update",
                        "system_update",
                        "Software update",
                        "UPDATE",
                    ),

                    (
                        "About Phone",
                        "about_device",
                        "Device information",
                        "INFO",
                    ),

                    (
                        "Developer Options",
                        "developer",
                        "Developer tools",
                        "DEV",
                    ),

                    (
                        "Accessibility",
                        "accessibility",
                        "Accessibility features",
                        "ACCESS",
                    ),

                    (
                        "Language and Input",
                        "language",
                        "Language and keyboard",
                        "LANG",
                    ),

                    (
                        "Date and Time",
                        "date",
                        "Time and date",
                        "TIME",
                    ),

                    (
                        "Reset Options",
                        "reset",
                        "Reset settings",
                        "RESET",
                    ),
                ],
            ),

            (
                "ACCOUNTS AND GOOGLE",
                [

                    (
                        "Accounts",
                        "accounts",
                        "Accounts and sync",
                        "ACCOUNT",
                    ),

                    (
                        "Google",
                        "google",
                        "Google services",
                        "G",
                    ),

                    (
                        "Backup",
                        "backup",
                        "Backup and restore",
                        "BACKUP",
                    ),
                ],
            ),

            (
                "APPLICATIONS",
                [

                    (
                        "All Apps",
                        "apps",
                        "Manage applications",
                        "APP",
                    ),

                    (
                        "App Information",
                        "app_details",
                        "This application",
                        "INFO",
                    ),

                    (
                        "Default Apps",
                        "default_apps",
                        "Default applications",
                        "DEFAULT",
                    ),

                    (
                        "Special Access",
                        "special_access",
                        "Special permissions",
                        "KEY",
                    ),

                    (
                        "Display Over Other Apps",
                        "overlay",
                        "Overlay permissions",
                        "OVERLAY",
                    ),
                ],
            ),

            (
                "USAGE AND STORAGE",
                [

                    (
                        "Data Usage",
                        "data",
                        "Network usage",
                        "DATA",
                    ),

                    (
                        "Storage",
                        "storage",
                        "Internal storage",
                        "STORAGE",
                    ),

                    (
                        "Digital Wellbeing",
                        "digital_wellbeing",
                        "Screen time",
                        "TIME",
                    ),
                ],
            ),

            (
                "APP",
                [

                    (
                        "Arabic Speech Recognition",
                        "speech_ar",
                        "Recognition language: Arabic",
                        "AR",
                    ),

                    (
                        "Commands",
                        "commands",
                        "Available voice commands",
                        "MIC",
                    ),

                    (
                        "About",
                        "about_app",
                        "Developer and application information",
                        "INFO",
                    ),
                ],
            ),
        ]

        self.settings_content.clear_widgets()

        self.all_setting_cards.clear()

        for section, items in sections:

            title = make_label(
                section,
                font_size=16,
                bold=True,
                halign="left",
            )

            title.size_hint_y = None
            title.height = dp(42)

            self.settings_content.add_widget(
                title
            )

            grid = GridLayout(
                cols=2,
                spacing=dp(7),
                size_hint_y=None,
            )

            grid.bind(
                minimum_height=
                grid.setter("height")
            )

            for (
                caption,
                action,
                subtitle,
                icon,
            ) in items:

                card = Card(
                    text=caption,
                    icon=icon,
                    subtitle=subtitle,
                    height=dp(92),
                )

                card.action_key = action

                card.search_text = (
                    caption
                    + " "
                    + subtitle
                ).lower()

                card.bind(
                    on_release=lambda *_,
                    action=action:
                    self.setting_action(action)
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

    # ========================================================
    # SEARCH
    # ========================================================

    def filter_settings(self, *_):

        query = ""

        if self.search_input:

            query = (
                self.search_input.text
                .strip()
                .lower()
            )

        for card in self.all_setting_cards:

            visible = (
                not query
                or query in card.search_text
            )

            card.opacity = (
                1 if visible else 0
            )

            card.disabled = (
                not visible
            )

    # ========================================================
    # COMMANDS SCREEN
    # ========================================================

    def commands_screen(self):

        screen = Screen(
            name="commands"
        )

        root = BoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(10),
        )

        root.add_widget(
            self.header(
                "Voice Commands",
                "home",
            )
        )

        scroll = ScrollView(
            do_scroll_x=False
        )

        commands_text = (
            "Arabic voice commands\n\n"

            "Open Wi-Fi:\n"
            "افتح الواي فاي\n\n"

            "Open Bluetooth:\n"
            "افتح البلوتوث\n\n"

            "Open mobile network:\n"
            "افتح شبكة الهاتف\n\n"

            "Open mobile data:\n"
            "افتح بيانات الهاتف\n\n"

            "Open hotspot:\n"
            "افتح نقطة الاتصال\n\n"

            "Open VPN:\n"
            "افتح vpn\n\n"

            "Open notifications:\n"
            "افتح الإشعارات\n\n"

            "Open Do Not Disturb:\n"
            "افتح عدم الإزعاج\n\n"

            "Open battery:\n"
            "افتح البطارية\n\n"

            "Open battery saver:\n"
            "افتح توفير الطاقة\n\n"

            "Open privacy:\n"
            "افتح الخصوصية\n\n"

            "Open location:\n"
            "افتح الموقع\n\n"

            "Open security:\n"
            "افتح الحماية\n\n"

            "Open accounts:\n"
            "افتح الحسابات\n\n"

            "Open backup:\n"
            "افتح النسخ الاحتياطي\n\n"

            "Open Google:\n"
            "افتح Google\n\n"

            "Open system update:\n"
            "افتح تحديث النظام\n\n"

            "Open about phone:\n"
            "افتح حول الهاتف\n\n"

            "Open developer options:\n"
            "افتح خيارات المطور\n\n"

            "Increase volume:\n"
            "ارفع الصوت\n\n"

            "Decrease volume:\n"
            "اخفض الصوت\n\n"

            "Mute volume:\n"
            "كتم الصوت\n\n"

            "Set brightness:\n"
            "اجعل السطوع 50\n\n"

            "Increase brightness:\n"
            "ارفع السطوع\n\n"

            "Decrease brightness:\n"
            "اخفض السطوع\n\n"

            "Clear result:\n"
            "امسح النتيجة\n\n"

            "Show commands:\n"
            "اعرض الأوامر"
        )

        label = make_arabic_label(
            commands_text,
            font_size=14,
            halign="right",
        )

        label.size_hint_y = None

        label.bind(
            texture_size=lambda widget, size:
            setattr(
                widget,
                "height",
                size[1] + dp(30),
            )
        )

        scroll.add_widget(
            label
        )

        root.add_widget(
            scroll
        )

        self.add_background(root)

        screen.add_widget(
            root
        )

        return screen

    # ========================================================
    # ABOUT
    # ========================================================

    def about_screen(self):

        screen = Screen(
            name="about"
        )

        root = BoxLayout(
            orientation="vertical",
            padding=dp(22),
            spacing=dp(12),
        )

        root.add_widget(
            make_label(
                "About",
                font_size=28,
                bold=True,
            )
        )

        root.add_widget(
            make_label(
                "Voice Control",
                font_size=22,
                bold=True,
            )
        )

        root.add_widget(
            make_label(
                "An Android voice-control application "
                "for opening system settings using Arabic voice commands.",
                font_size=14,
            )
        )

        root.add_widget(
            make_label(
                "Developer",
                font_size=13,
                bold=True,
            )
        )

        root.add_widget(
            make_label(
                DEVELOPER,
                font_size=17,
                bold=True,
            )
        )

        root.add_widget(
            make_label(
                "Version 1.0.0",
                font_size=13,
            )
        )

        root.add_widget(
            make_label(
                "English interface • Arabic speech recognition",
                font_size=12,
            )
        )

        root.add_widget(
            self.button_back(
                "Back to Home",
                "home",
            )
        )

        self.add_background(root)

        screen.add_widget(
            root
        )

        return screen

    # ========================================================
    # HEADER
    # ========================================================

    def header(
        self,
        title,
        back_target=None,
    ):

        row = BoxLayout(
            size_hint_y=None,
            height=dp(62),
            spacing=dp(8),
        )

        if back_target:

            back = Card(
                text="Back",
                icon="<",
                subtitle="",
                height=dp(52),
                size_hint_x=None,
                width=dp(105),
            )

            back.bind(
                on_release=lambda *_:
                self.goto(back_target)
            )

            row.add_widget(
                back
            )

        row.add_widget(
            make_label(
                title,
                font_size=22,
                bold=True,
                halign="left",
            )
        )

        return row

    # ========================================================
    # BACK BUTTON
    # ========================================================

    def button_back(
        self,
        text,
        target,
    ):

        button = Card(
            text=text,
            icon="<",
            subtitle="",
            height=dp(58),
        )

        button.bind(
            on_release=lambda *_:
            self.goto(target)
        )

        return button

    # ========================================================
    # BACKGROUND
    # ========================================================

    def add_background(self, root):

        try:

            with root.canvas.before:

                root._bg_color = Color(
                    1,
                    1,
                    1,
                    0.20,
                )

                root._bg_rect = RoundedRectangle(
                    source=BACKGROUND_FILE,
                    pos=root.pos,
                    size=root.size,
                )

            root.bind(
                pos=lambda *_:
                setattr(
                    root._bg_rect,
                    "pos",
                    root.pos,
                )
            )

            root.bind(
                size=lambda *_:
                setattr(
                    root._bg_rect,
                    "size",
                    root.size,
                )
            )

        except Exception as exc:

            print(
                "Background error:",
                exc,
            )

    # ========================================================
    # NAVIGATION
    # ========================================================

    def goto(self, name):

        if name == "Home":
            name = "home"

        if name == "Settings":
            name = "settings"

        if name == "Commands":
            name = "commands"

        if name == "About":
            name = "about"

        if hasattr(self, "sm"):

            try:

                self.sm.current = name

            except Exception as exc:

                print(
                    "Navigation error:",
                    exc,
                )

    # ========================================================
    # ANDROID PERMISSION
    # ========================================================

    def request_mic(self):

        if not ANDROID:

            return True

        try:

            permission = Permission.RECORD_AUDIO

            if check_permission(permission):

                return True

            request_permissions(
                [permission],
                self.on_permission_result,
            )

            return False

        except Exception as exc:

            print(
                "Microphone permission error:",
                exc,
            )

            return True

    def on_permission_result(
        self,
        permissions,
        results,
    ):

        try:

            granted = all(
                bool(result)
                for result in results
            )

            if granted:

                self.set_status(
                    "Microphone permission granted"
                )

            else:

                self.set_status(
                    "Microphone permission denied"
                )

        except Exception:

            pass

    # ========================================================
    # APP START
    # ========================================================

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
                    "Activity bind error:",
                    exc,
                )

        self.request_mic()

    # ========================================================
    # APP STOP
    # ========================================================

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

    # ========================================================
    # LISTENING
    # ========================================================

    def toggle_listening(self, *_):

        if self.listening:

            self.stop_listening()

        else:

            self.start_listening()

    def stop_listening(self):

        self.listening = False

        if self.mic:

            self.mic.label.text = "MIC"

        self.set_status(
            "Ready"
        )

    # ========================================================
    # START SPEECH RECOGNITION
    # ========================================================

    def start_listening(self):

        if not ANDROID or not JNIUS:

            self.set_status(
                "Speech recognition is available in the Android APK."
            )

            return

        if not self.request_mic():

            self.set_status(
                "Allow microphone permission, then press MIC again."
            )

            return

        try:

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
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM,
            )

            # Arabic recognition ONLY.
            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE,
                "ar",
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE,
                "ar",
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_ONLY_RETURN_LANGUAGE_PREFERENCE,
                "ar",
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_MAX_RESULTS,
                5,
            )

            intent.putExtra(
                RecognizerIntent.EXTRA_PROMPT,
                "تحدث الآن",
            )

            self.listening = True

            if self.mic:

                self.mic.label.text = "STOP"

            self.set_status(
                "Listening..."
            )

            PythonActivity.mActivity.startActivityForResult(
                intent,
                REQUEST_SPEECH,
            )

        except Exception as exc:

            self.listening = False

            if self.mic:

                self.mic.label.text = "MIC"

            self.set_status(
                "Could not start speech recognition."
            )

            print(
                "Speech intent error:",
                exc,
            )

    # ========================================================
    # ACTIVITY RESULT
    # ========================================================

    def on_activity_result(
        self,
        request_code,
        result_code,
        intent,
    ):

        try:

            if int(request_code) != REQUEST_SPEECH:

                return

        except Exception:

            return

        self.listening = False

        Clock.schedule_once(
            lambda *_:
            self.finish_result(intent),
            0,
        )

    # ========================================================
    # SPEECH RESULT
    # ========================================================

    def finish_result(self, intent):

        if self.mic:

            self.mic.label.text = "MIC"

        if not intent:

            self.set_status(
                "No speech result received."
            )

            return

        try:

            RecognizerIntent = autoclass(
                "android.speech.RecognizerIntent"
            )

            results = (
                intent.getStringArrayListExtra(
                    RecognizerIntent.EXTRA_RESULTS
                )
            )

            text = ""

            if results and results.size():

                text = str(
                    results.get(0)
                )

        except Exception as exc:

            print(
                "Speech result error:",
                exc,
            )

            text = ""

        if text:

            self.result.text = rtl(
                text
            )

            self.set_status(
                "Speech recognized"
            )

            self.handle_command(
                text
            )

        else:

            self.set_status(
                "No speech recognized."
            )

    # ========================================================
    # NORMALIZE ARABIC COMMAND
    # ========================================================

    def normalize(self, text):

        text = str(text)

        text = (
            text
            .strip()
            .lower()
        )

        replacements = [

            (
                "أ",
                "ا",
            ),

            (
                "إ",
                "ا",
            ),

            (
                "آ",
                "ا",
            ),

            (
                "ة",
                "ه",
            ),

            (
                "ى",
                "ي",
            ),
        ]

        for old, new in replacements:

            text = text.replace(
                old,
                new,
            )

        return " ".join(
            text.split()
        )

    # ========================================================
    # HANDLE VOICE COMMAND
    # ========================================================

    def handle_command(self, text):

        command = self.normalize(
            text
        )

        # ----------------------------------------------------
        # HELP
        # ----------------------------------------------------

        if contains_any(
            command,
            [
                "مساعده",
                "الاوامر",
                "اعرض الاوامر",
            ],
        ):

            self.goto(
                "commands"
            )

            return

        # ----------------------------------------------------
        # CLEAR
        # ----------------------------------------------------

        if contains_any(
            command,
            [
                "امسح",
                "مسح",
                "امسح النتيجه",
                "امسح النتيجة",
            ],
        ):

            if self.result:

                self.result.text = rtl(
                    "لم يتم التعرف على أي كلام بعد."
                )

            self.set_status(
                "Ready"
            )

            return

        # ----------------------------------------------------
        # VOLUME UP
        # ----------------------------------------------------

        if contains_any(
            command,
            [
                "ارفع الصوت",
                "علي الصوت",
                "زيد الصوت",
                "زود الصوت",
                "ارفع مستوى الصوت",
            ],
        ):

            self.audio_adjust(
                1
            )

            return

        # ----------------------------------------------------
        # VOLUME DOWN
        # ----------------------------------------------------

        if contains_any(
            command,
            [
                "اخفض الصوت",
                "وطي الصوت",
                "نقص الصوت",
                "خفض الصوت",
                "انقص الصوت",
                "خفض مستوى الصوت",
            ],
        ):

            self.audio_adjust(
                -1
            )

            return

        # ----------------------------------------------------
        # MUTE
        # ----------------------------------------------------

        if contains_any(
            command,
            [
                "كتم الصوت",
                "اكتم الصوت",
                "صامت",
                "كتم",
            ],
        ):

            self.audio_mute()

            return

        # ----------------------------------------------------
        # BRIGHTNESS
        # ----------------------------------------------------

        if contains_any(
            command,
            [
                "السطوع",
                "اضاءه الشاشه",
                "سطوع الشاشه",
            ],
        ):

            import re

            match = re.search(
                r"(\d{1,3})",
                command,
            )

            if match:

                self.set_brightness(
                    int(match.group(1))
                )

                return

            if contains_any(
                command,
                [
                    "ارفع",
                    "زيد",
                ],
            ):

                self.change_brightness(
                    10
                )

                return

            if contains_any(
                command,
                [
                    "اخفض",
                    "نقص",
                    "خفض",
                ],
            ):

                self.change_brightness(
                    -10
                )

                return

        # ----------------------------------------------------
        # SETTINGS COMMANDS
        # ----------------------------------------------------

        commands = [

            (
                [
                    "واي فاي",
                    "الواي فاي",
                    "شبكه الواي فاي",
                ],
                "wifi",
            ),

            (
                [
                    "بلوتوث",
                ],
                "bluetooth",
            ),

            (
                [
                    "شبكه الهاتف",
                    "شبكه الجوال",
                ],
                "mobile",
            ),

            (
                [
                    "بيانات الهاتف",
                    "استخدام البيانات",
                ],
                "data",
            ),

            (
                [
                    "نقطه الاتصال",
                    "مشاركه الانترنت",
                    "مشاركة الانترنت",
                ],
                "hotspot",
            ),

            (
                [
                    "vpn",
                ],
                "vpn",
            ),

            (
                [
                    "nfc",
                ],
                "nfc",
            ),

            (
                [
                    "الاشعارات",
                    "اشعارات",
                ],
                "notifications",
            ),

            (
                [
                    "عدم الازعاج",
                ],
                "do_not_disturb",
            ),

            (
                [
                    "البطاريه",
                ],
                "battery",
            ),

            (
                [
                    "توفير الطاقه",
                ],
                "battery_saver",
            ),

            (
                [
                    "تحسين البطاريه",
                ],
                "battery_optimization",
            ),

            (
                [
                    "الخصوصيه",
                ],
                "privacy",
            ),

            (
                [
                    "الموقع",
                ],
                "location",
            ),

            (
                [
                    "الحمايه",
                    "الامن",
                ],
                "security",
            ),

            (
                [
                    "شاشه القفل",
                ],
                "lock_screen",
            ),

            (
                [
                    "الطوارئ",
                ],
                "emergency",
            ),

            (
                [
                    "الحسابات",
                ],
                "accounts",
            ),

            (
                [
                    "النسخ الاحتياطي",
                ],
                "backup",
            ),

            (
                [
                    "جوجل",
                    "google",
                ],
                "google",
            ),

            (
                [
                    "تحديث النظام",
                    "تحديث البرنامج",
                ],
                "system_update",
            ),

            (
                [
                    "حول الهاتف",
                    "معلومات الهاتف",
                ],
                "about_device",
            ),

            (
                [
                    "خيارات المطور",
                ],
                "developer",
            ),

            (
                [
                    "امكانيه الوصول",
                ],
                "accessibility",
            ),

            (
                [
                    "التطبيقات",
                    "جميع التطبيقات",
                ],
                "apps",
            ),

            (
                [
                    "اعدادات الهاتف",
                    "افتح الاعدادات",
                ],
                "settings",
            ),

            (
                [
                    "التخزين",
                ],
                "storage",
            ),

            (
                [
                    "الرفاهيه الرقميه",
                ],
                "digital_wellbeing",
            ),
        ]

        for words, action in commands:

            if contains_any(
                command,
                words,
            ):

                self.setting_action(
                    action
                )

                return

        self.set_status(
            "Command not recognized."
        )

    # ========================================================
    # SETTING ACTION
    # ========================================================

    def setting_action(self, action):

        # ----------------------------------------------------
        # APP PAGES
        # ----------------------------------------------------

        if action == "commands":

            self.goto(
                "commands"
            )

            return

        if action == "about_app":

            self.goto(
                "about"
            )

            return

        if action == "speech_ar":

            self.language = "ar"

            self.set_status(
                "Arabic speech recognition enabled."
            )

            return

        # ----------------------------------------------------
        # THEMES
        # ----------------------------------------------------

        if action == "theme_light":

            self.dark = False

            Window.clearcolor = (
                0.96,
                0.97,
                0.98,
                1,
            )

            self.set_status(
                "Light theme selected."
            )

            return

        if action == "theme_dark":

            self.dark = True

            Window.clearcolor = (
                0.035,
                0.045,
                0.06,
                1,
            )

            self.set_status(
                "Dark theme selected."
            )

            return

        # ----------------------------------------------------
        # SPECIAL APP SETTINGS
        # ----------------------------------------------------

        if action == "brightness":

            self.open_write_settings()

            return

        if action == "app_details":

            self.open_app_details()

            return

        if action == "app_notifications":

            self.open_app_notifications()

            return

        # ----------------------------------------------------
        # ANDROID SETTINGS
        # ----------------------------------------------------

        actions = {

            "settings":
                "android.settings.SETTINGS",

            "wifi":
                "android.settings.WIFI_SETTINGS",

            "bluetooth":
                "android.settings.BLUETOOTH_SETTINGS",

            "mobile":
                "android.settings.WIRELESS_SETTINGS",

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
                "android.settings.ZEN_MODE_PRIORITY_SETTINGS",

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
        }

        # ----------------------------------------------------
        # RESET
        # ----------------------------------------------------
        #
        # IMPORTANT:
        # Do NOT use MASTER_CLEAR.
        # That could represent a destructive factory reset.
        #

        if action == "reset":

            self.open_android_setting(
                "android.settings.SETTINGS"
            )

            self.set_status(
                "Reset options are available in Android Settings."
            )

            return

        self.open_android_setting(
            actions.get(
                action,
                "android.settings.SETTINGS",
            )
        )

    # ========================================================
    # OPEN ANDROID SETTING
    # ========================================================

    def open_android_setting(self, action):

        if not ANDROID or not JNIUS:

            self.set_status(
                "This feature is available in the Android APK."
            )

            return

        try:

            Intent = autoclass(
                "android.content.Intent"
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            activity_instance = (
                PythonActivity.mActivity
            )

            try:

                intent = Intent(
                    action
                )

                package_manager = (
                    activity_instance.getPackageManager()
                )

                resolved = (
                    intent.resolveActivity(
                        package_manager
                    )
                )

                if resolved:

                    activity_instance.startActivity(
                        intent
                    )

                else:

                    activity_instance.startActivity(
                        Intent(
                            "android.settings.SETTINGS"
                        )
                    )

            except Exception as exc:

                print(
                    "Specific setting unavailable:",
                    action,
                    exc,
                )

                activity_instance.startActivity(
                    Intent(
                        "android.settings.SETTINGS"
                    )
                )

        except Exception as exc:

            print(
                "Android settings error:",
                action,
                exc,
            )

            self.set_status(
                "Could not open Android Settings."
            )

    # ========================================================
    # APP DETAILS
    # ========================================================

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

            package_name = str(
                PythonActivity.mActivity.getPackageName()
            )

            intent = Intent(
                "android.settings.APPLICATION_DETAILS_SETTINGS"
            )

            intent.setData(
                Uri.parse(
                    "package:" + package_name
                )
            )

            PythonActivity.mActivity.startActivity(
                intent
            )

        except Exception as exc:

            print(
                "App details error:",
                exc,
            )

    # ========================================================
    # APP NOTIFICATIONS
    # ========================================================

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

            package_name = str(
                PythonActivity.mActivity.getPackageName()
            )

            intent = Intent(
                "android.settings.APP_NOTIFICATION_SETTINGS"
            )

            intent.putExtra(
                "android.provider.extra.APP_PACKAGE",
                package_name,
            )

            PythonActivity.mActivity.startActivity(
                intent
            )

        except Exception as exc:

            print(
                "App notification settings error:",
                exc,
            )

            self.open_android_setting(
                "android.settings.NOTIFICATION_SETTINGS"
            )

    # ========================================================
    # WRITE SETTINGS PERMISSION
    # ========================================================

    def open_write_settings(self):

        if not ANDROID or not JNIUS:

            self.set_status(
                "This feature works inside Android."
            )

            return

        try:

            Settings = autoclass(
                "android.provider.Settings"
            )

            Intent = autoclass(
                "android.content.Intent"
            )

            Uri = autoclass(
                "android.net.Uri"
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            activity_instance = (
                PythonActivity.mActivity
            )

            if not Settings.System.canWrite(
                activity_instance
            ):

                intent = Intent(
                    "android.settings.action.MANAGE_WRITE_SETTINGS"
                )

                intent.setData(
                    Uri.parse(
                        "package:"
                        + str(
                            activity_instance.getPackageName()
                        )
                    )
                )

                activity_instance.startActivity(
                    intent
                )

            else:

                self.set_status(
                    "System settings permission is available."
                )

        except Exception as exc:

            print(
                "Write settings error:",
                exc,
            )

            self.set_status(
                "Could not open system settings permission."
            )

    # ========================================================
    # AUDIO
    # ========================================================

    def audio_adjust(self, direction):

        if not ANDROID or not JNIUS:

            self.set_status(
                "Volume control is available in Android APK."
            )

            return

        try:

            Context = autoclass(
                "android.content.Context"
            )

            AudioManager = autoclass(
                "android.media.AudioManager"
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            audio = (
                PythonActivity.mActivity.getSystemService(
                    Context.AUDIO_SERVICE
                )
            )

            stream_music = (
                AudioManager.STREAM_MUSIC
            )

            if direction > 0:

                adjustment = (
                    AudioManager.ADJUST_RAISE
                )

                status = (
                    "Volume increased."
                )

            else:

                adjustment = (
                    AudioManager.ADJUST_LOWER
                )

                status = (
                    "Volume decreased."
                )

            audio.adjustStreamVolume(
                stream_music,
                adjustment,
                AudioManager.FLAG_SHOW_UI,
            )

            self.set_status(
                status
            )

        except Exception as exc:

            print(
                "Audio error:",
                exc,
            )

            self.set_status(
                "Could not change volume."
            )

    # ========================================================
    # MUTE
    # ========================================================

    def audio_mute(self):

        if not ANDROID or not JNIUS:

            self.set_status(
                "Mute is available in Android APK."
            )

            return

        try:

            Context = autoclass(
                "android.content.Context"
            )

            AudioManager = autoclass(
                "android.media.AudioManager"
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
                AudioManager.STREAM_MUSIC,
                AudioManager.ADJUST_MUTE,
                AudioManager.FLAG_SHOW_UI,
            )

            self.set_status(
                "Volume muted."
            )

        except Exception as exc:

            print(
                "Mute error:",
                exc,
            )

            self.set_status(
                "Could not mute volume."
            )

    # ========================================================
    # BRIGHTNESS
    # ========================================================

    def set_brightness(self, percent):

        percent = max(
            0,
            min(
                100,
                int(percent),
            ),
        )

        if not ANDROID or not JNIUS:

            self.set_status(
                "Brightness control is available in Android APK."
            )

            return

        try:

            Settings = autoclass(
                "android.provider.Settings"
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            activity_instance = (
                PythonActivity.mActivity
            )

            if not Settings.System.canWrite(
                activity_instance
            ):

                self.open_write_settings()

                self.set_status(
                    "Allow system settings permission, then try again."
                )

                return

            resolver = (
                activity_instance.getContentResolver()
            )

            # Force manual brightness mode.
            try:

                Settings.System.putInt(
                    resolver,
                    Settings.System.SCREEN_BRIGHTNESS_MODE,
                    Settings.System.SCREEN_BRIGHTNESS_MODE_MANUAL,
                )

            except Exception:

                pass

            value = int(
                percent * 255 / 100
            )

            Settings.System.putInt(
                resolver,
                Settings.System.SCREEN_BRIGHTNESS,
                value,
            )

            self.set_status(
                f"Brightness set to {percent}%."
            )

        except Exception as exc:

            print(
                "Brightness error:",
                exc,
            )

            self.set_status(
                "Could not change brightness."
            )

    # ========================================================
    # CHANGE BRIGHTNESS
    # ========================================================

    def change_brightness(self, delta):

        if not ANDROID or not JNIUS:

            self.set_status(
                "Brightness control is available in Android APK."
            )

            return

        try:

            Settings = autoclass(
                "android.provider.Settings"
            )

            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            activity_instance = (
                PythonActivity.mActivity
            )

            resolver = (
                activity_instance.getContentResolver()
            )

            if not Settings.System.canWrite(
                activity_instance
            ):

                self.open_write_settings()

                self.set_status(
                    "Allow system settings permission, then try again."
                )

                return

            # Force manual mode.
            try:

                Settings.System.putInt(
                    resolver,
                    Settings.System.SCREEN_BRIGHTNESS_MODE,
                    Settings.System.SCREEN_BRIGHTNESS_MODE_MANUAL,
                )

            except Exception:

                pass

            current = Settings.System.getInt(
                resolver,
                Settings.System.SCREEN_BRIGHTNESS,
            )

            amount = int(
                255 * delta / 100
            )

            new_value = max(
                0,
                min(
                    255,
                    current + amount,
                ),
            )

            Settings.System.putInt(
                resolver,
                Settings.System.SCREEN_BRIGHTNESS,
                new_value,
            )

            self.set_status(
                "Brightness changed."
            )

        except Exception as exc:

            print(
                "Brightness change error:",
                exc,
            )

            self.set_status(
                "Could not change brightness."
            )


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":

    VoiceControlApp().run()
