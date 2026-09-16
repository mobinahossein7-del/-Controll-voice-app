# -*- coding: utf-8 -*-

import os
import re
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:
    arabic_reshaper = None
    get_display = None

# Android imports
ANDROID = False

try:
    from jnius import autoclass, cast
    from android import activity
    from android.permissions import Permission, check_permission, request_permissions

    ANDROID = True

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Intent = autoclass("android.content.Intent")
    Uri = autoclass("android.net.Uri")
    Settings = autoclass("android.provider.Settings")
    Context = autoclass("android.content.Context")
    AudioManager = autoclass("android.media.AudioManager")
    Build = autoclass("android.os.Build")

except Exception:
    ANDROID = False


# ---------------------------------------------------------
# إعدادات عامة
# ---------------------------------------------------------

APP_TITLE = "Voice Control"
DEVELOPER = "مهند الحمادي"
FONT_FILE = "NotoKufiArabic-VariableFont_wght.ttf"

if os.path.exists(FONT_FILE):
    try:
        LabelBase.register(
            name="NotoKufi",
            fn_regular=FONT_FILE
        )
        DEFAULT_FONT = "NotoKufi"
    except Exception:
        DEFAULT_FONT = "Roboto"
else:
    DEFAULT_FONT = "Roboto"


# ---------------------------------------------------------
# معالجة العربية
# ---------------------------------------------------------

def rtl(text):
    text = str(text)

    if arabic_reshaper is not None and get_display is not None:
        try:
            return get_display(arabic_reshaper.reshape(text))
        except Exception:
            return text

    return text


# ---------------------------------------------------------
# أدوات الواجهة
# ---------------------------------------------------------

def make_label(text, size=16, bold=False, halign="right"):
    label = Label(
        text=rtl(text),
        font_name=DEFAULT_FONT,
        font_size=dp(size),
        halign=halign,
        valign="middle",
        bold=bold,
        color=(0.93, 0.95, 1, 1),
    )
    label.bind(
        size=lambda instance, value: setattr(
            instance, "text_size", (instance.width - dp(12), None)
        )
    )
    return label


class CardButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.font_name = DEFAULT_FONT
        self.font_size = dp(15)
        self.halign = "right"
        self.valign = "middle"
        self.text_size = (None, None)
        self.color = (0.94, 0.96, 1, 1)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0.10, 0.13, 0.19, 1)

        with self.canvas.before:
            self.bg_color = Color(
                0.10, 0.13, 0.19, 1
            )
            self.bg = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(16)]
            )

        self.bind(
            pos=self.update_background,
            size=self.update_background
        )

    def update_background(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size


# ---------------------------------------------------------
# تعريف الإعدادات
# ---------------------------------------------------------

SETTING_DEFS = [

    # الاتصال
    {
        "category": "الاتصال",
        "title": "Wi-Fi",
        "subtitle": "فتح إعدادات Wi-Fi والتحكم بالشبكات",
        "action": "wifi",
        "keywords": "wifi wi-fi واي فاي وايفاي شبكة انترنت"
    },
    {
        "category": "الاتصال",
        "title": "بيانات الهاتف",
        "subtitle": "إعدادات شبكة الهاتف والبيانات",
        "action": "mobile",
        "keywords": "بيانات الهاتف بيانات جوال mobile network"
    },
    {
        "category": "الاتصال",
        "title": "Bluetooth",
        "subtitle": "تشغيل أو إدارة البلوتوث",
        "action": "bluetooth",
        "keywords": "bluetooth بلوتوث"
    },
    {
        "category": "الاتصال",
        "title": "نقطة الاتصال",
        "subtitle": "إعدادات مشاركة الإنترنت",
        "action": "hotspot",
        "keywords": "hotspot نقطة اتصال مشاركة الانترنت"
    },
    {
        "category": "الاتصال",
        "title": "VPN",
        "subtitle": "إدارة اتصالات VPN",
        "action": "vpn",
        "keywords": "vpn في بي ان"
    },
    {
        "category": "الاتصال",
        "title": "وضع الطيران",
        "subtitle": "فتح إعدادات وضع الطيران",
        "action": "airplane",
        "keywords": "airplane طيران وضع الطيران"
    },
    {
        "category": "الاتصال",
        "title": "NFC",
        "subtitle": "إعدادات الاتصال قريب المدى",
        "action": "nfc",
        "keywords": "nfc"
    },

    # الصوت
    {
        "category": "الصوت والإشعارات",
        "title": "الصوت",
        "subtitle": "رفع وخفض مستوى الصوت",
        "action": "sound",
        "keywords": "صوت volume sound"
    },
    {
        "category": "الصوت والإشعارات",
        "title": "عدم الإزعاج",
        "subtitle": "إدارة وضع عدم الإزعاج",
        "action": "dnd",
        "keywords": "عدم الازعاج do not disturb dnd"
    },
    {
        "category": "الصوت والإشعارات",
        "title": "الإشعارات",
        "subtitle": "إعدادات إشعارات التطبيقات",
        "action": "notifications",
        "keywords": "notifications اشعارات إشعارات"
    },
    {
        "category": "الصوت والإشعارات",
        "title": "نغمة الهاتف",
        "subtitle": "اختيار نغمة الرنين",
        "action": "ringtone",
        "keywords": "نغمة رنين ringtone"
    },

    # الشاشة
    {
        "category": "الشاشة",
        "title": "السطوع",
        "subtitle": "تغيير مستوى سطوع الشاشة",
        "action": "brightness",
        "keywords": "سطوع brightness شاشة"
    },
    {
        "category": "الشاشة",
        "title": "الشاشة",
        "subtitle": "إعدادات الشاشة والعرض",
        "action": "display",
        "keywords": "شاشة display عرض"
    },
    {
        "category": "الش
