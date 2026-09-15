# -*- coding: utf-8 -*-

import os
import re
import unicodedata

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
from kivy.uix.popup import Popup

import arabic_reshaper
from bidi.algorithm import get_display


# ============================================================
# الخط
# ============================================================

FONT = "NotoKufiArabic-VariableFont_wght.ttf"


# ============================================================
# Android
# ============================================================

ANDROID = False

try:
    from android import activity
    from android.permissions import request_permissions, Permission
    from jnius import autoclass
    ANDROID = True
except Exception:
    ANDROID = False


if ANDROID:
    Intent = autoclass("android.content.Intent")
    Uri = autoclass("android.net.Uri")
    Settings = autoclass("android.provider.Settings")
    AudioManager = autoclass("android.media.AudioManager")
    PythonActivity = autoclass("org.kivy.android.PythonActivity")


# ============================================================
# RTL
# ============================================================

def rtl(text):
    text = str(text)

    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


def normalize_arabic(text):
    text = str(text).strip().lower()

    # إزالة التشكيل
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )

    text = text.replace("أ", "ا")
    text = text.replace("إ", "ا")
    text = text.replace("آ", "ا")
    text = text.replace("ٱ", "ا")
    text = text.replace("ـ", "")

    return text


def arabic_digits_to_ascii(text):
    result = ""

    for c in str(text):
        try:
            result += str(unicodedata.digit(c))
        except Exception:
            result += c

    return result


# ============================================================
# الألوان
# ============================================================

LIGHT_BG = (0.96, 0.97, 0.99, 1)
DARK_BG = (0.055, 0.065, 0.09, 1)

LIGHT_TEXT = (0.08, 0.09, 0.12, 1)
DARK_TEXT = (0.94, 0.95, 0.98, 1)

BUTTON_LIGHT = (0.88, 0.91, 0.96, 1)
BUTTON_DARK = (0.13, 0.15, 0.20, 1)


# ============================================================
# أدوات Android
# ============================================================

class AndroidController:

    @staticmethod
    def context():
        if not ANDROID:
            return None

        return PythonActivity.mActivity

    @staticmethod
    def start_action(action, fallback=None):
        if not ANDROID:
            return False

        ctx = AndroidController.context()

        if ctx is None:
            return False

        try:
            intent = Intent(action)
            ctx.startActivity(intent)
            return True

        except Exception:
            if fallback:
                try:
                    intent = Intent(fallback)
                    ctx.startActivity(intent)
                    return True
                except Exception:
                    pass

        return False

    @staticmethod
    def start_panel(panel_action, fallback):
        return AndroidController.start_action(
            panel_action,
            fallback
        )

    @staticmethod
    def app_details():
        if not ANDROID:
            return False

        try:
            ctx = AndroidController.context()
            package_name = ctx.getPackageName()

            intent = Intent(
                Settings.ACTION_APPLICATION_DETAILS_SETTINGS
            )

            intent.setData(
                Uri.parse("package:" + package_name)
            )

            ctx.startActivity(intent)
            return True

        except Exception:
            return False

    @staticmethod
    def app_notifications():
        if not ANDROID:
            return False

        try:
            ctx = AndroidController.context()
            package_name = ctx.getPackageName()

            intent = Intent(
                "android.settings.APP_NOTIFICATION_SETTINGS"
            )

            intent.putExtra(
                "android.provider.extra.APP_PACKAGE",
                package_name
            )

            ctx.startActivity(intent)
            return True

        except Exception:
            return AndroidController.start_action(
                "android.settings.NOTIFICATION_SETTINGS"
            )

    @staticmethod
    def write_settings_page():
        if not ANDROID:
            return False

        try:
            ctx = AndroidController.context()
            package_name = ctx.getPackageName()

            intent = Intent(
                "android.settings.action.MANAGE_WRITE_SETTINGS"
            )

            intent.setData(
                Uri.parse("package:" + package_name)
            )

            ctx.startActivity(intent)
            return True

        except Exception:
            return AndroidController.start_action(
                "android.settings.SETTINGS"
            )

    @staticmethod
    def can_write_settings():
        if not ANDROID:
            return False

        try:
            return bool(
                Settings.System.canWrite(
                    AndroidController.context()
                )
            )
        except Exception:
            return False

    # --------------------------------------------------------
    # الصوت
    # --------------------------------------------------------

    @staticmethod
    def volume_up():
        if not ANDROID:
            return False

        try:
            ctx = AndroidController.context()
            audio = ctx.getSystemService("audio")

            audio.adjustStreamVolume(
                AudioManager.STREAM_MUSIC,
                AudioManager.ADJUST_RAISE,
                0
            )

            return True

        except Exception:
            return False

    @staticmethod
    def volume_down():
        if not ANDROID:
            return False

        try:
            ctx = AndroidController.context()
            audio = ctx.getSystemService("audio")

            audio.adjustStreamVolume(
                AudioManager.STREAM_MUSIC,
                AudioManager.ADJUST_LOWER,
                0
            )

            return True

        except Exception:
            return False

    @staticmethod
    def volume_mute():
        if not ANDROID:
            return False

        try:
            ctx = AndroidController.context()
            audio = ctx.getSystemService("audio")

            audio.adjustStreamVolume(
                AudioManager.STREAM_MUSIC,
                AudioManager.ADJUST_MUTE,
                0
            )

            return True

        except Exception:
            try:
                audio.setStreamVolume(
                    AudioManager.STREAM_MUSIC,
                    0,
                    0
                )
                return True
            except Exception:
                return False

    # --------------------------------------------------------
    # السطوع
    # --------------------------------------------------------

    @staticmethod
    def set_brightness(percent):
        if not ANDROID:
            return False

        if not AndroidController.can_write_settings():
            AndroidController.start_action(
                "android.settings.DISPLAY_SETTINGS"
            )
            return False

        try:
            ctx = AndroidController.context()
            resolver = ctx.getContentResolver()

            # تحويل 0-100 إلى 0-255
            value = int(
                max(0, min(100, percent)) * 255 / 100
            )

            # إيقاف السطوع التلقائي قبل التحكم اليدوي
            Settings.System.putInt(
                resolver,
                Settings.System.SCREEN_BRIGHTNESS_MODE,
                0
            )

            Settings.System.putInt(
                resolver,
                Settings.System.SCREEN_BRIGHTNESS,
                value
            )

            return True

        except Exception:
            return False

    @staticmethod
    def change_brightness(delta):
        if not ANDROID:
            return False

        if not AndroidController.can_write_settings():
            AndroidController.start_action(
                "android.settings.DISPLAY_SETTINGS"
            )
            return False

        try:
            ctx = AndroidController.context()
            resolver = ctx.getContentResolver()

            current = Settings.System.getInt(
                resolver,
                Settings.System.SCREEN_BRIGHTNESS,
                128
            )

            percent = int(current * 100 / 255)
            percent += delta
            percent = max(0, min(100, percent))

            return AndroidController.set_brightness(percent)

        except Exception:
            return False

    # --------------------------------------------------------
    # التدوير التلقائي
    # --------------------------------------------------------

    @staticmethod
    def set_auto_rotate(enabled):
        if not ANDROID:
            return False

        if not AndroidController.can_write_settings():
            AndroidController.start_action(
                "android.settings.DISPLAY_SETTINGS"
            )
            return False

        try:
            ctx = AndroidController.context()
            resolver = ctx.getContentResolver()

            Settings.System.putInt(
                resolver,
                Settings.System.ACCELEROMETER_ROTATION,
                1 if enabled else 0
            )

            return True

        except Exception:
            return False

    @staticmethod
    def get_auto_rotate():
        if not ANDROID:
            return None

        try:
            ctx = AndroidController.context()
            resolver = ctx.getContentResolver()

            value = Settings.System.getInt(
                resolver,
                Settings.System.ACCELEROMETER_ROTATION,
                1
            )

            return bool(value)

        except Exception:
            return None


# ============================================================
# الشاشة الرئيسية
# ============================================================

class HomeScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.root_box = BoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(10)
        )

        self.add_widget(self.root_box)

    def build_ui(self):

        self.root_box.clear_widgets()

        app = App.get_running_app()

        title = Label(
            text=rtl("التحكم الصوتي") if app.is_arabic
            else "Voice Control",
            font_name=FONT,
            font_size=dp(25),
            color=app.text_color,
            size_hint_y=None,
            height=dp(65)
        )

        self.root_box.add_widget(title)

        # ----------------------------------------------------
        # اللغة
        # ----------------------------------------------------

        lang = Button(
            text="English" if app.is_arabic else "العربية",
            font_name=FONT,
            size_hint_y=None,
            height=dp(50)
        )

        lang.bind(
            on_release=lambda x: app.toggle_language()
        )

        self.root_box.add_widget(lang)

        # ----------------------------------------------------
        # الحالة
        # ----------------------------------------------------

        self.status = Label(
            text=rtl("جاهز للاستماع") if app.is_arabic
            else "Ready",
            font_name=FONT,
            color=app.text_color,
            size_hint_y=None,
            height=dp(45)
        )

        self.root_box.add_widget(self.status)

        # ----------------------------------------------------
        # النص المتعرف عليه
        # ----------------------------------------------------

        self.result_label = Label(
            text=rtl("لم يتم التعرف على أمر بعد")
            if app.is_arabic
            else "No command yet",
            font_name=FONT,
            color=app.text_color,
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=dp(70)
        )

        self.result_label.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.root_box.add_widget(self.result_label)

        # ----------------------------------------------------
        # زر الميكروفون
        # ----------------------------------------------------

        mic = Button(
            text="🎙️\n" + (
                rtl("تحدث الآن")
                if app.is_arabic
                else "Speak now"
            ),
            font_name=FONT,
            font_size=dp(21),
            size_hint_y=None,
            height=dp(120)
        )

        mic.bind(
            on_release=lambda x: app.start_listening()
        )

        self.root_box.add_widget(mic)

        # ----------------------------------------------------
        # إدخال الأمر يدويًا
        # ----------------------------------------------------

        self.input_box = TextInput(
            hint_text=(
                "اكتب الأمر هنا"
                if app.is_arabic
                else "Type command here"
            ),
            multiline=False,
            font_name=FONT,
            size_hint_y=None,
            height=dp(55)
        )

        self.root_box.add_widget(self.input_box)

        execute = Button(
            text=rtl("تنفيذ الأمر")
            if app.is_arabic
            else "Execute",
            font_name=FONT,
            size_hint_y=None,
            height=dp(55)
        )

        execute.bind(
            on_release=lambda x:
            app.execute_command(self.input_box.text)
        )

        self.root_box.add_widget(execute)

        # ----------------------------------------------------
        # الاختصارات
        # ----------------------------------------------------

        quick = Button(
            text=rtl("⚡ الاختصارات السريعة")
            if app.is_arabic
            else "⚡ Quick Actions",
            font_name=FONT,
            size_hint_y=None,
            height=dp(58)
        )

        quick.bind(
            on_release=lambda x:
            app.sm.current = "settings"
        )

        self.root_box.add_widget(quick)

        about = Button(
            text=rtl("ℹ️ من نحن")
            if app.is_arabic
            else "ℹ️ About",
            font_name=FONT,
            size_hint_y=None,
            height=dp(52)
        )

        about.bind(
            on_release=lambda x:
            app.sm.current = "about"
        )

        self.root_box.add_widget(about)


# ============================================================
# شاشة الإعدادات
# ============================================================

class SettingsScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.scroll = ScrollView()

        self.content = GridLayout(
            cols=1,
            spacing=dp(8),
            padding=dp(12),
            size_hint_y=None
        )

        self.content.bind(
            minimum_height=self.content.setter(
                "height"
            )
        )

        self.scroll.add_widget(self.content)
        self.add_widget(self.scroll)

    def section(self, title):

        app = App.get_running_app()

        label = Label(
            text=rtl(title)
            if app.is_arabic
            else title,
            font_name=FONT,
            font_size=dp(19),
            color=app.text_color,
            size_hint_y=None,
            height=dp(55)
        )

        self.content.add_widget(label)

    def button(self, text, callback):

        app = App.get_running_app()

        b = Button(
            text=rtl(text)
            if app.is_arabic
            else text,
            font_name=FONT,
            size_hint_y=None,
            height=dp(58)
        )

        b.bind(on_release=lambda x: callback())

        self.content.add_widget(b)

    def build_ui(self):

        self.content.clear_widgets()

        app = App.get_running_app()

        # ====================================================
        # عنوان
        # ====================================================

        self.section(
            "⚡ الاختصارات السريعة"
        )

        quick_actions = [

            ("📶 Wi-Fi", "wifi"),
            ("🟦 Bluetooth", "bluetooth"),
            ("✈️ وضع الطيران", "airplane"),
            ("📡 نقطة الاتصال", "hotspot"),
            ("📱 بيانات الهاتف", "mobile_data"),
            ("📍 الموقع", "location"),
            ("NFC", "nfc"),
            ("🌐 VPN", "vpn"),
            ("🔄 التدوير التلقائي", "rotate"),
            ("🔆 زيادة السطوع", "brightness_up"),
            ("🔅 خفض السطوع", "brightness_down"),
            ("🔊 رفع الصوت", "volume_up"),
            ("🔉 خفض الصوت", "volume_down"),
            ("🔇 كتم الصوت", "mute"),
            ("🔋 توفير الطاقة", "battery_saver"),
            ("🔕 عدم الإزعاج", "dnd"),
            ("🌙 الوضع الداكن", "dark"),
        ]

        for text, key in quick_actions:
            self.button(
                text,
                lambda key=key:
                app.execute_quick(key)
            )

        # ====================================================
        # الاتصال
        # ====================================================

        self.section("📶 الاتصال والشبكات")

        network = [

            ("Wi-Fi", "android.settings.WIFI_SETTINGS"),
            ("Bluetooth", "android.settings.BLUETOOTH_SETTINGS"),
            (
                "شبكة الهاتف",
                "android.settings.NETWORK_OPERATOR_SETTINGS"
            ),
            (
                "بيانات الهاتف",
                "android.settings.WIRELESS_SETTINGS"
            ),
            (
                "نقطة الاتصال المحمولة",
                "android.settings.TETHER_SETTINGS"
            ),
            (
                "مشاركة الإنترنت",
                "android.settings.TETHER_SETTINGS"
            ),
            (
                "VPN",
                "android.settings.VPN_SETTINGS"
            ),
            (
                "NFC",
                "android.settings.NFC_SETTINGS"
            ),
            (
                "إعدادات الشبكة والإنترنت",
                "android.settings.SETTINGS"
            ),
            (
                "استخدام البيانات",
                "android.settings.DATA_USAGE_SETTINGS"
            ),
        ]

        for text, action in network:
            self.button(
                text,
                lambda action=action:
                app.open_setting(action)
            )

        # ====================================================
        # الإشعارات
        # ====================================================

        self.section("🔔 الإشعارات")

        self.button(
            "إعدادات الإشعارات",
            lambda:
            app.open_setting(
                "android.settings.NOTIFICATION_SETTINGS"
            )
        )

        self.button(
            "إشعارات التطبيق",
            lambda:
            app.open_app_notifications()
        )

        self.button(
            "عدم الإزعاج",
            lambda:
            app.open_setting(
                "android.settings.NOTIFICATION_POLICY_ACCESS_SETTINGS"
            )
        )

        self.button(
            "الوصول إلى الإشعارات",
            lambda:
            app.open_setting(
                "android.settings.ACTION_NOTIFICATION_LISTENER_SETTINGS"
            )
        )

        self.button(
            "سجل الإشعارات",
            lambda:
            app.open_setting(
                "android.settings.NOTIFICATION_HISTORY"
            )
        )

        # ====================================================
        # البطارية
        # ====================================================

        self.section("🔋 البطارية والخلفية")

        battery = [
            (
                "البطارية",
                "android.settings.BATTERY_SAVER_SETTINGS"
            ),
            (
                "استخدام البطارية",
                "android.settings.BATTERY_USAGE_SETTINGS"
            ),
            (
                "توفير الطاقة",
                "android.settings.BATTERY_SAVER_SETTINGS"
            ),
            (
                "تحسين البطارية",
                "android.settings.IGNORE_BATTERY_OPTIMIZATION_SETTINGS"
            ),
            (
                "التطبيقات التي تعمل في الخلفية",
                "android.settings.APPLICATION_SETTINGS"
            ),
            (
                "إعدادات البطارية للتطبيق",
                "android.settings.IGNORE_BATTERY_OPTIMIZATION_SETTINGS"
            ),
        ]

        for text, action in battery:
            self.button(
                text,
                lambda action=action:
                app.open_setting(action)
            )

        # ====================================================
        # النمط
        # ====================================================

        self.section("🎨 النمط والسمات")

        self.button(
            "الوضع الفاتح",
            lambda:
            app.set_theme(False)
        )

        self.button(
            "الوضع الداكن",
            lambda:
            app.set_theme(True)
        )

        self.button(
            "الوضع التلقائي",
            lambda:
            app.open_setting(
                "android.settings.DISPLAY_SETTINGS"
            )
        )

        self.button(
            "السطوع",
            lambda:
            app.open_setting(
                "android.settings.DISPLAY_SETTINGS"
            )
        )

        self.button(
            "حجم الشاشة",
            lambda:
            app.open_setting(
                "android.settings.DISPLAY_SETTINGS"
            )
        )

        self.button(
            "الخط وحجم النص",
            lambda:
            app.open_setting(
                "android.settings.FONT_SETTINGS"
            )
        )

        # ====================================================
        # الشاشة
        # ====================================================

        self.section("🖥️ الشاشة")

        display = [
            (
                "إعدادات العرض",
                "android.settings.DISPLAY_SETTINGS"
            ),
            (
                "السطوع التلقائي",
                "android.settings.DISPLAY_SETTINGS"
            ),
            (
                "مهلة إيقاف الشاشة",
                "android.settings.DISPLAY_SETTINGS"
            ),
            (
                "معدل التحديث",
                "android.settings.DISPLAY_SETTINGS"
            ),
            (
                "التدوير التلقائي",
                "android.settings.DISPLAY_SETTINGS"
            ),
        ]

        for text, action in display:
            self.button(
                text,
                lambda action=action:
                app.open_setting(action)
            )

        # ====================================================
        # الخصوصية والأمان
        # ====================================================

        self.section("🔐 الخصوصية والأمان")

        security = [
            (
                "الخصوصية",
                "android.settings.PRIVACY_SETTINGS"
            ),
            (
                "الأمان",
                "android.settings.SECURITY_SETTINGS"
            ),
            (
                "الموقع",
                "android.settings.LOCATION_SOURCE_SETTINGS"
            ),
            (
                "أذونات التطبيق",
                None
            ),
            (
                "مدير الأذونات",
                "android.settings.MANAGE_APP_ALL_FILES_ACCESS_PERMISSION"
            ),
            (
                "الكاميرا",
                "android.settings.PRIVACY_SETTINGS"
            ),
            (
                "الميكروفون",
                "android.settings.PRIVACY_SETTINGS"
            ),
            (
                "لوحة الخصوصية",
                "android.settings.PRIVACY_SETTINGS"
            ),
        ]

        for text, action in security:

            if action is None:
                self.button(
                    text,
                    lambda:
                    app.open_app_details()
                )
            else:
                self.button(
                    text,
                    lambda action=action:
                    app.open_setting(action)
                )

        # ====================================================
        # شاشة القفل والحماية
        # ====================================================

        self.section("🔒 شاشة القفل والحماية")

        lock_items = [
            (
                "شاشة القفل",
                "android.settings.SECURITY_SETTINGS"
            ),
            (
                "كلمة المرور / PIN",
                "android.settings.SECURITY_SETTINGS"
            ),
            (
                "البصمة",
                "android.settings.SECURITY_SETTINGS"
            ),
            (
                "فتح الوجه",
                "android.settings.SECURITY_SETTINGS"
            ),
            (
                "الحماية",
                "android.settings.SECURITY_SETTINGS"
            ),
            (
                "العثور على الجهاز",
                "android.settings.GOOGLE_SETTINGS"
            ),
            (
                "مدير كلمات المرور",
                "android.settings.GOOGLE_SETTINGS"
            ),
        ]

        for text, action in lock_items:
            self.button(
                text,
                lambda action=action:
                app.open_setting(action)
            )

        # ====================================================
        # الطوارئ
        # ====================================================

        self.section("🚨 الطوارئ والسلامة")

        emergency = [
            (
                "إعدادات الطوارئ",
                "android.settings.SAFETY_CENTER_SETTINGS"
            ),
            (
                "معلومات الطوارئ",
                "android.settings.SAFETY_CENTER_SETTINGS"
            ),
            (
                "جهات اتصال الطوارئ",
                "android.settings.SAFETY_CENTER_SETTINGS"
            ),
            (
                "خدمات السلامة",
                "android.settings.SAFETY_CENTER_SETTINGS"
            ),
        ]

        for text, action in emergency:
            self.button(
                text,
                lambda action=action:
                app.open_setting(
                    action,
                    "android.settings.SECURITY_SETTINGS"
                )
            )

        # ====================================================
        # التحكم الأبوي
        # ====================================================

        self.section("👨‍👩‍👧 التحكم الأبوي")

        self.button(
            "التحكم الأبوي",
            lambda:
            app.open_setting(
                "android.settings.FAMILY_CENTER"
            )
        )

        self.button(
            "الرفاهية الرقمية",
            lambda:
            app.open_setting(
                "android.settings.DIGITAL_WELLBEING_SETTINGS"
            )
        )

        self.button(
            "وقت استخدام الجهاز",
            lambda:
            app.open_setting(
                "android.settings.USAGE_ACCESS_SETTINGS"
            )
        )

        # ====================================================
        # التطبيقات
        # ====================================================

        self.section("📱 التطبيقات")

        apps = [
            (
                "جميع التطبيقات",
                "android.settings.APPLICATION_SETTINGS"
            ),
            (
                "معلومات التطبيق",
                None
            ),
            (
                "التطبيقات الافتراضية",
                "android.settings.MANAGE_DEFAULT_APPS_SETTINGS"
            ),
            (
                "التطبيقات التي تظهر فوق التطبيقات",
                "android.settings.action.MANAGE_OVERLAY_PERMISSION"
            ),
            (
                "تثبيت التطبيقات من مصادر خارجية",
                "android.settings.MANAGE_UNKNOWN_APP_SOURCES"
            ),
            (
                "الوصول الخاص للتطبيقات",
                "android.settings.MANAGE_SPECIAL_APP_ACCESS"
            ),
        ]

        for text, action in apps:

            if action is None:
                self.button(
                    text,
                    lambda:
                    app.open_app_details()
                )
            else:
                self.button(
                    text,
                    lambda action=action:
                    app.open_setting(action)
                )

        # ====================================================
        # الحسابات والنسخ
        # ====================================================

        self.section("☁️ الحسابات والنسخ الاحتياطي")

        cloud = [
            (
                "الحسابات",
                "android.settings.SYNC_SETTINGS"
            ),
            (
                "Google",
                "android.settings.GOOGLE_SETTINGS"
            ),
            (
                "النسخ الاحتياطي",
                "android.settings.BACKUP_SETTINGS"
            ),
            (
                "استعادة البيانات",
                "android.settings.BACKUP_SETTINGS"
            ),
        ]

        for text, action in cloud:
            self.button(
                text,
                lambda action=action:
                app.open_setting(action)
            )

        # ====================================================
        # النظام
        # ====================================================

        self.section("⚙️ النظام")

        system = [
            (
                "اللغة والإدخال",
                "android.settings.LOCALE_SETTINGS"
            ),
            (
                "التاريخ والوقت",
                "android.settings.DATE_SETTINGS"
            ),
            (
                "التخزين",
                "android.settings.INTERNAL_STORAGE_SETTINGS"
            ),
            (
                "إمكانية الوصول",
                "android.settings.ACCESSIBILITY_SETTINGS"
            ),
            (
                "تحديث البرنامج",
                "android.settings.SYSTEM_UPDATE_SETTINGS"
            ),
            (
                "إعدادات النظام المتقدمة",
                "android.settings.SETTINGS"
            ),
            (
                "معلومات الجهاز",
                "android.settings.DEVICE_INFO_SETTINGS"
            ),
            (
                "إعادة ضبط الهاتف",
                "android.settings.BACKUP_AND_RESET_SETTINGS"
            ),
            (
                "دليل المستخدم",
                "android.settings.USER_GUIDE"
            ),
        ]

        for text, action in system:
            self.button(
                text,
                lambda action=action:
                app.open_setting(action)
            )

        # ====================================================
        # خيارات المطور
        # ====================================================

        self.section("👨‍💻 خيارات المطور")

        self.button(
            "خيارات المطور",
            lambda:
            app.open_setting(
                "android.settings.APPLICATION_DEVELOPMENT_SETTINGS"
            )
        )

        # ====================================================
        # إعدادات التطبيق
        # ====================================================

        self.section("🎙️ إعدادات التطبيق")

        self.button(
            "لغة التعرف الصوتي",
            lambda:
            app.toggle_language()
        )

        self.button(
            "تشغيل الاستماع",
            lambda:
            app.start_listening()
        )

        self.button(
            "صفحة الأوامر",
            lambda:
            setattr(
                app.sm,
                "current",
                "commands"
            )
        )

        self.button(
            "معلومات التطبيق",
            lambda:
            app.open_app_details()
        )

        # ====================================================
        # من نحن
        # ====================================================

        self.button(
            "ℹ️ من نحن",
            lambda:
            setattr(
                app.sm,
                "current",
                "about"
            )
        )

        # العودة
        self.button(
            "⬅️ الرئيسية",
            lambda:
            setattr(
                app.sm,
                "current",
                "home"
            )
        )


# ============================================================
# شاشة الأوامر
# ============================================================

class CommandsScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.scroll = ScrollView()

        self.content = GridLayout(
            cols=1,
            spacing=dp(10),
            padding=dp(15),
            size_hint_y=None
        )

        self.content.bind(
            minimum_height=self.content.setter(
                "height"
            )
        )

        self.scroll.add_widget(self.content)
        self.add_widget(self.scroll)

    def build_ui(self):

        self.content.clear_widgets()

        app = App.get_running_app()

        title = Label(
            text=rtl("الأوامر الصوتية")
            if app.is_arabic
            else "Voice Commands",
            font_name=FONT,
            font_size=dp(23),
            color=app.text_color,
            size_hint_y=None,
            height=dp(70)
        )

        self.content.add_widget(title)

        commands = [

            "افتح الإعدادات",
            "افتح الواي فاي",
            "افتح البلوتوث",
            "افتح نقطة الاتصال",
            "افتح بيانات الهاتف",
            "افتح وضع الطيران",
            "افتح الموقع",
            "افتح VPN",
            "افتح NFC",
            "شغل التدوير التلقائي",
            "ارفع الصوت",
            "اخفض الصوت",
            "اكتم الصوت",
            "ارفع السطوع",
            "اخفض السطوع",
            "اجعل السطوع 50 بالمئة",
            "شغل توفير الطاقة",
            "افتح عدم الإزعاج",
            "افتح الخصوصية",
            "افتح الأمان",
            "افتح التطبيقات",
            "افتح الشاشة",
            "افتح التخزين",
            "افتح إمكانية الوصول",
            "افتح خيارات المطور",
            "افتح تحديث البرنامج",
            "افتح الحسابات",
            "افتح النسخ الاحتياطي",
            "من نحن",
        ]

        for command in commands:

            label = Label(
                text=rtl("• " + command)
                if app.is_arabic
                else "• " + command,
                font_name=FONT,
                color=app.text_color,
                halign="right",
                size_hint_y=None,
                height=dp(48)
            )

            self.content.add_widget(label)

        back = Button(
            text=rtl("⬅️ العودة")
            if app.is_arabic
            else "⬅️ Back",
            font_name=FONT,
            size_hint_y=None,
            height=dp(58)
        )

        back.bind(
            on_release=lambda x:
            setattr(
                app.sm,
                "current",
                "home"
            )
        )

        self.content.add_widget(back)


# ============================================================
# من نحن
# ============================================================

class AboutScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.box = BoxLayout(
            orientation="vertical",
            padding=dp(25),
            spacing=dp(15)
        )

        self.add_widget(self.box)

    def build_ui(self):

        self.box.clear_widgets()

        app = App.get_running_app()

        title = Label(
            text=rtl("ℹ️ من نحن")
            if app.is_arabic
            else "ℹ️ About",
            font_name=FONT,
            font_size=dp(26),
            color=app.text_color,
            size_hint_y=None,
            height=dp(70)
        )

        self.box.add_widget(title)

        text = (
            "تطبيق للتحكم الصوتي وفتح إعدادات الهاتف "
            "وتنفيذ الاختصارات السريعة.\n\n"
            "المطور:\n"
            "مهند الحمادي"
        )

        if not app.is_arabic:
            text = (
                "Voice control application for opening "
                "Android settings and using quick actions.\n\n"
                "Developer:\n"
                "Mohand Al-Hammadi"
            )

        description = Label(
            text=rtl(text)
            if app.is_arabic
            else text,
            font_name=FONT,
            font_size=dp(18),
            color=app.text_color,
            halign="center",
            valign="middle"
        )

        description.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        self.box.add_widget(description)

        back = Button(
            text=rtl("⬅️ العودة")
            if app.is_arabic
            else "⬅️ Back",
            font_name=FONT,
            size_hint_y=None,
            height=dp(58)
        )

        back.bind(
            on_release=lambda x:
            setattr(
                app.sm,
                "current",
                "home"
            )
        )

        self.box.add_widget(back)


# ============================================================
# التطبيق
# ============================================================

class VoiceControlApp(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.is_arabic = True
        self.language_code = "ar"

        self.dark_mode = False

        self.sm = ScreenManager()

        self.listening = False

        self.REQUEST_CODE = 7412

        self.home = HomeScreen(name="home")
        self.settings = SettingsScreen(name="settings")
        self.commands = CommandsScreen(name="commands")
        self.about = AboutScreen(name="about")

        self.sm.add_widget(self.home)
        self.sm.add_widget(self.settings)
        self.sm.add_widget(self.commands)
        self.sm.add_widget(self.about)

    # ========================================================
    # الألوان
    # ========================================================

    @property
    def text_color(self):

        if self.dark_mode:
            return DARK_TEXT

        return LIGHT_TEXT

    # ========================================================
    # بدء التطبيق
    # ========================================================

    def build(self):

        Window.clearcolor = (
            DARK_BG if self.dark_mode
            else LIGHT_BG
        )

        self.rebuild_ui()

        return self.sm

    def on_start(self):

        if ANDROID:

            try:
                activity.bind(
                    on_activity_result=
                    self.on_activity_result
                )
            except Exception:
                pass

    def on_stop(self):

        if ANDROID:

            try:
                activity.unbind(
                    on_activity_result=
                    self.on_activity_result
                )
            except Exception:
                pass

    # ========================================================
    # إعادة بناء الواجهة
    # ========================================================

    def rebuild_ui(self):

        self.home.build_ui()
        self.settings.build_ui()
        self.commands.build_ui()
        self.about.build_ui()

    # ========================================================
    # اللغة
    # ========================================================

    def toggle_language(self):

        self.is_arabic = not self.is_arabic

        self.language_code = (
            "ar" if self.is_arabic
            else "en-US"
        )

        self.rebuild_ui()

    # ========================================================
    # النمط
    # ========================================================

    def set_theme(self, dark):

        self.dark_mode = bool(dark)

        Window.clearcolor = (
            DARK_BG if self.dark_mode
            else LIGHT_BG
        )

        self.rebuild_ui()

        self.notify(
            "تم تفعيل الوضع الداكن"
            if dark
            else "تم تفعيل الوضع الفاتح"
        )

    # ========================================================
    # إشعار
    # ========================================================

    def notify(self, message):

        if self.is_arabic:
            self.home.status.text = rtl(message)
        else:
            self.home.status.text = message

    # ========================================================
    # فتح إعدادات Android
    # ========================================================

    def open_setting(self, action, fallback=None):

        success = AndroidController.start_action(
            action,
            fallback
        )

        if success:
            self.notify(
                "تم فتح الإعدادات"
                if self.is_arabic
                else "Settings opened"
            )

        else:
            self.notify(
                "تعذر فتح هذه الصفحة على هذا الجهاز"
                if self.is_arabic
                else "This setting is unavailable"
            )

    def open_app_details(self):

        if AndroidController.app_details():
            self.notify(
                "تم فتح معلومات التطبيق"
                if self.is_arabic
                else "App information opened"
            )

    def open_app_notifications(self):

        if AndroidController.app_notifications():
            self.notify(
                "تم فتح إشعارات التطبيق"
                if self.is_arabic
                else "App notifications opened"
            )

    # ========================================================
    # الاختصارات
    # ========================================================

    def execute_quick(self, key):

        # Wi-Fi
        if key == "wifi":

            AndroidController.start_panel(
                "android.settings.panel.action.WIFI",
                "android.settings.WIFI_SETTINGS"
            )

            self.notify(
                "تم فتح لوحة Wi-Fi"
                if self.is_arabic
                else "Wi-Fi panel opened"
            )

        # Bluetooth
        elif key == "bluetooth":

            AndroidController.start_panel(
                "android.settings.panel.action.BLUETOOTH",
                "android.settings.BLUETOOTH_SETTINGS"
            )

            self.notify(
                "تم فتح لوحة Bluetooth"
                if self.is_arabic
                else "Bluetooth panel opened"
            )

        # وضع الطيران
        elif key == "airplane":

            self.open_setting(
                "android.settings.AIRPLANE_MODE_SETTINGS",
                "android.settings.WIRELESS_SETTINGS"
            )

        # نقطة الاتصال
        elif key == "hotspot":

            self.open_setting(
                "android.settings.TETHER_SETTINGS",
                "android.settings.WIRELESS_SETTINGS"
            )

        # بيانات الهاتف
        elif key == "mobile_data":

            AndroidController.start_panel(
                "android.settings.panel.action.INTERNET_CONNECTIVITY",
                "android.settings.WIRELESS_SETTINGS"
            )

            self.notify(
                "تم فتح لوحة الاتصال"
                if self.is_arabic
                else "Connectivity panel opened"
            )

        # الموقع
        elif key == "location":

            AndroidController.start_panel(
                "android.settings.panel.action.LOCATION",
                "android.settings.LOCATION_SOURCE_SETTINGS"
            )

        # NFC
        elif key == "nfc":

            AndroidController.start_panel(
                "android.settings.panel.action.NFC",
                "android.settings.NFC_SETTINGS"
            )

        # VPN
        elif key == "vpn":

            self.open_setting(
                "android.settings.VPN_SETTINGS"
            )

        # التدوير
        elif key == "rotate":

            current = AndroidController.get_auto_rotate()

            if current is None:

                self.open_setting(
                    "android.settings.DISPLAY_SETTINGS"
                )

            else:

                new_value = not current

                if AndroidController.set_auto_rotate(
                    new_value
                ):

                    self.notify(
                        (
                            "تم تشغيل التدوير التلقائي"
                            if new_value
                            else "تم إيقاف التدوير التلقائي"
                        )
                        if self.is_arabic
                        else (
                            "Auto rotation enabled"
                            if new_value
                            else "Auto rotation disabled"
                        )
                    )

                else:

                    self.open_setting(
                        "android.settings.DISPLAY_SETTINGS"
                    )

        # زيادة السطوع
        elif key == "brightness_up":

            if AndroidController.change_brightness(10):

                self.notify(
                    "تم زيادة السطوع"
                    if self.is_arabic
                    else "Brightness increased"
                )

            else:

                self.open_setting(
                    "android.settings.DISPLAY_SETTINGS"
                )

        # خفض السطوع
        elif key == "brightness_down":

            if AndroidController.change_brightness(-10):

                self.notify(
                    "تم خفض السطوع"
                    if self.is_arabic
                    else "Brightness decreased"
                )

            else:

                self.open_setting(
                    "android.settings.DISPLAY_SETTINGS"
                )

        # الصوت
        elif key == "volume_up":

            if AndroidController.volume_up():

                self.notify(
                    "تم رفع الصوت"
                    if self.is_arabic
                    else "Volume increased"
                )

        elif key == "volume_down":

            if AndroidController.volume_down():

                self.notify(
                    "تم خفض الصوت"
                    if self.is_arabic
                    else "Volume decreased"
                )

        elif key == "mute":

            if AndroidController.volume_mute():

                self.notify(
                    "تم كتم الصوت"
                    if self.is_arabic
                    else "Sound muted"
                )

        # توفير الطاقة
        elif key == "battery_saver":

            self.open_setting(
                "android.settings.BATTERY_SAVER_SETTINGS"
            )

        # عدم الإزعاج
        elif key == "dnd":

            self.open_setting(
                "android.settings.NOTIFICATION_POLICY_ACCESS_SETTINGS",
                "android.settings.NOTIFICATION_SETTINGS"
            )

        # الوضع الداكن
        elif key == "dark":

            self.set_theme(
                not self.dark_mode
            )

    # ========================================================
    # التعرف الصوتي
    # ========================================================

    def start_listening(self):

        if not ANDROID:

            self.notify(
                "التعرف الصوتي متاح على Android فقط"
                if self.is_arabic
                else "Voice recognition is available on Android"
            )

            return

        try:

            request_permissions(
                [Permission.RECORD_AUDIO]
            )

        except Exception:
            pass

        Clock.schedule_once(
            lambda dt:
            self._start_recognizer(),
            0.7
        )

    def _start_recognizer(self):

        if not ANDROID:
            return

        try:

            intent = Intent(
                "android.speech.action.RECOGNIZE_SPEECH"
            )

            intent.putExtra(
                "android.speech.extra.LANGUAGE_MODEL",
                "free_form"
            )

            intent.putExtra(
                "android.speech.extra.LANGUAGE",
                self.language_code
            )

            intent.putExtra(
                "android.speech.extra.LANGUAGE_PREFERENCE",
                self.language_code
            )

            intent.putExtra(
                "android.speech.extra.MAX_RESULTS",
                5
            )

            prompt = (
                "تحدث الآن"
                if self.is_arabic
                else "Speak now"
            )

            intent.putExtra(
                "android.speech.extra.PROMPT",
                prompt
            )

            PythonActivity.mActivity.startActivityForResult(
                intent,
                self.REQUEST_CODE
            )

            self.listening = True

            self.notify(
                "استمع إليك الآن..."
                if self.is_arabic
                else "Listening..."
            )

        except Exception as e:

            self.notify(
                "تعذر تشغيل التعرف الصوتي"
                if self.is_arabic
                else "Could not start speech recognition"
            )

    # ========================================================
    # نتيجة التعرف الصوتي
    # ========================================================

    def on_activity_result(
        self,
        request_code,
        result_code,
        intent
    ):

        if request_code != self.REQUEST_CODE:
            return

        self.listening = False

        try:

            if intent is None:
                return

            results = intent.getStringArrayListExtra(
                "android.speech.extra.RESULTS"
            )

            if results is None:
                return

            if results.size() == 0:
                return

            text = str(results.get(0))

            self.home.result_label.text = (
                rtl(text)
                if self.is_arabic
                else text
            )

            self.execute_command(text)

        except Exception:

            self.notify(
                "لم أستطع قراءة نتيجة الصوت"
                if self.is_arabic
                else "Could not read speech result"
            )

    # ========================================================
    # تحليل الأوامر
    # ========================================================

    def execute_command(self, command):

        if not command:
            return

        original = str(command).strip()

        text = normalize_arabic(
            arabic_digits_to_ascii(original)
        )

        # ----------------------------------------------------
        # من نحن
        # ----------------------------------------------------

        if (
            "من نحن" in text
            or "عن التطبيق" in text
            or "about" in text
        ):

            self.sm.current = "about"
            return

        # ----------------------------------------------------
        # الأوامر
        # ----------------------------------------------------

        if (
            "الاوامر" in text
            or "اوامر صوتيه" in text
            or "commands" in text
        ):

            self.sm.current = "commands"
            return

        # ----------------------------------------------------
        # الرئيسية
        # ----------------------------------------------------

        if (
            text in ["الرئيسيه", "الرئيسية", "home"]
        ):

            self.sm.current = "home"
            return

        # ----------------------------------------------------
        # الإعدادات
        # ----------------------------------------------------

        if (
            "افتح الاعدادات" in text
            or text == "الاعدادات"
            or "settings" in text
        ):

            self.sm.current = "settings"

            self.notify(
                "تم فتح الإعدادات"
                if self.is_arabic
                else "Settings opened"
            )

            return

        # ----------------------------------------------------
        # رفع الصوت
        # ----------------------------------------------------

        if (
            "ارفع الصوت" in text
            or "علي الصوت" in text
            or "رفع الصوت" in text
            or "volume up" in text
        ):

            self.execute_quick("volume_up")
            return

        # ----------------------------------------------------
        # خفض الصوت
        # ----------------------------------------------------

        if (
            "اخفض الصوت" in text
            or "نزل الصوت" in text
            or "خفض الصوت" in text
            or "volume down" in text
        ):

            self.execute_quick("volume_down")
            return

        # ----------------------------------------------------
        # كتم الصوت
        # ----------------------------------------------------

        if (
            "اكتم الصوت" in text
            or "كتم الصوت" in text
            or "mute" in text
        ):

            self.execute_quick("mute")
            return

        # ----------------------------------------------------
        # السطوع بنسبة
        # ----------------------------------------------------

        brightness_match = re.search(
            r"(\d{1,3})\s*(?:%|بالمئه|بالمئة|percent)",
            text
        )

        if (
            brightness_match
            and (
                "سطوع" in text
                or "سطوع" in original
                or "brightness" in text
            )
        ):

            value = int(
                brightness_match.group(1)
            )

            value = max(0, min(100, value))

            if AndroidController.set_brightness(value):

                self.notify(
                    f"تم ضبط السطوع على {value}%"
                    if self.is_arabic
                    else f"Brightness set to {value}%"
                )

            else:

                self.open_setting(
                    "android.settings.DISPLAY_SETTINGS"
                )

            return

        # ----------------------------------------------------
        # زيادة السطوع
        # ----------------------------------------------------

        if (
            "ارفع السطوع" in text
            or "زد السطوع" in text
            or "brightness up" in text
        ):

            self.execute_quick("brightness_up")
            return

        # ----------------------------------------------------
        # خفض السطوع
        # ----------------------------------------------------

        if (
            "اخفض السطوع" in text
            or "خفض السطوع" in text
            or "brightness down" in text
        ):

            self.execute_quick("brightness_down")
            return

        # ----------------------------------------------------
        # التدوير
        # ----------------------------------------------------

        if (
            "شغل التدوير" in text
            or "فعل التدوير" in text
            or "التدوير التلقائي" in text
            or "auto rotation" in text
        ):

            if (
                "وقف" in text
                or "اطف" in text
                or "تعطيل" in text
                or "off" in text
            ):

                if AndroidController.set_auto_rotate(False):

                    self.notify(
                        "تم إيقاف التدوير التلقائي"
                        if self.is_arabic
                        else "Auto rotation disabled"
                    )

                else:

                    self.open_setting(
                        "android.settings.DISPLAY_SETTINGS"
                    )

            else:

                if AndroidController.set_auto_rotate(True):

                    self.notify(
                        "تم تشغيل التدوير التلقائي"
                        if self.is_arabic
                        else "Auto rotation enabled"
                    )

                else:

                    self.open_setting(
                        "android.settings.DISPLAY_SETTINGS"
                    )

            return

        # ----------------------------------------------------
        # Wi-Fi
        # ----------------------------------------------------

        if (
            "واي فاي" in text
            or "wifi" in text
            or "wi fi" in text
        ):

            self.execute_quick("wifi")
            return

        # ----------------------------------------------------
        # Bluetooth
        # ----------------------------------------------------

        if (
            "بلوتوث" in text
            or "bluetooth" in text
        ):

            self.execute_quick("bluetooth")
            return

        # ----------------------------------------------------
        # الطيران
        # ----------------------------------------------------

        if (
            "وضع الطيران" in text
            or "الطيران" in text
            or "airplane" in text
        ):

            self.execute_quick("airplane")
            return

        # ----------------------------------------------------
        # hotspot
        # ----------------------------------------------------

        if (
            "نقطه الاتصال" in text
            or "نقطة الاتصال" in text
            or "الهوتسبوت" in text
            or "hotspot" in text
        ):

            self.execute_quick("hotspot")
            return

        # ----------------------------------------------------
        # بيانات الهاتف
        # ----------------------------------------------------

        if (
            "بيانات الهاتف" in text
            or "بيانات الجوال" in text
            or "mobile data" in text
        ):

            self.execute_quick("mobile_data")
            return

        # ----------------------------------------------------
        # الموقع
        # ----------------------------------------------------

        if (
            text == "الموقع"
            or "افتح الموقع" in text
            or "location" in text
        ):

            self.execute_quick("location")
            return

        # ----------------------------------------------------
        # NFC
        # ----------------------------------------------------

        if "nfc" in text:

            self.execute_quick("nfc")
            return

        # ----------------------------------------------------
        # VPN
        # ----------------------------------------------------

        if (
            "vpn" in text
            or "الشبكه الافتراضيه" in text
        ):

            self.execute_quick("vpn")
            return

        # ----------------------------------------------------
        # توفير الطاقة
        # ----------------------------------------------------

        if (
            "توفير الطاقه" in text
            or "توفير الطاقة" in original
            or "battery saver" in text
        ):

            self.execute_quick("battery_saver")
            return

        # ----------------------------------------------------
        # عدم الإزعاج
        # ----------------------------------------------------

        if (
            "عدم الازعاج" in text
            or "لا تزعج" in text
            or "do not disturb" in text
            or "dnd" in text
        ):

            self.execute_quick("dnd")
            return

        # ----------------------------------------------------
        # الوضع الداكن
        # ----------------------------------------------------

        if (
            "الوضع الداكن" in text
            or "الوضع المظلم" in text
            or "dark mode" in text
        ):

            self.set_theme(True)
            return

        # ----------------------------------------------------
        # الوضع الفاتح
        # ----------------------------------------------------

        if (
            "الوضع الفاتح" in text
            or "light mode" in text
        ):

            self.set_theme(False)
            return

        # ----------------------------------------------------
        # الخصوصية
        # ----------------------------------------------------

        if (
            "الخصوصيه" in text
            or "الخصوصية" in original
            or "privacy" in text
        ):

            self.open_setting(
                "android.settings.PRIVACY_SETTINGS"
            )
            return

        # ----------------------------------------------------
        # الأمان
        # ----------------------------------------------------

        if (
            "الامان" in text
            or "الأمان" in original
            or "security" in text
        ):

            self.open_setting(
                "android.settings.SECURITY_SETTINGS"
            )
            return

        # ----------------------------------------------------
        # التطبيقات
        # ----------------------------------------------------

        if (
            "التطبيقات" in text
            or "apps" in text
        ):

            self.open_setting(
                "android.settings.APPLICATION_SETTINGS"
            )
            return

        # ----------------------------------------------------
        # الشاشة
        # ----------------------------------------------------

        if (
            "الشاشه" in text
            or "الشاشة" in original
            or "display" in text
        ):

            self.open_setting(
                "android.settings.DISPLAY_SETTINGS"
            )
            return

        # ----------------------------------------------------
        # التخزين
        # ----------------------------------------------------

        if (
            "التخزين" in text
            or "مساحه التخزين" in text
            or "storage" in text
        ):

            self.open_setting(
                "android.settings.INTERNAL_STORAGE_SETTINGS"
            )
            return

        # ----------------------------------------------------
        # إمكانية الوصول
        # ----------------------------------------------------

        if (
            "امكانيه الوصول" in text
            or "إمكانية الوصول" in original
            or "accessibility" in text
        ):

            self.open_setting(
                "android.settings.ACCESSIBILITY_SETTINGS"
            )
            return

        # ----------------------------------------------------
        # خيارات المطور
        # ----------------------------------------------------

        if (
            "خيارات المطور" in text
            or "developer options" in text
        ):

            self.open_setting(
                "android.settings.APPLICATION_DEVELOPMENT_SETTINGS"
            )
            return

        # ----------------------------------------------------
        # تحديث النظام
        # ----------------------------------------------------

        if (
            "تحديث البرنامج" in text
            or "تحديث النظام" in text
            or "system update" in text
        ):

            self.open_setting(
                "android.settings.SYSTEM_UPDATE_SETTINGS"
            )
            return

        # ----------------------------------------------------
        # الحسابات
        # ----------------------------------------------------

        if (
            "الحسابات" in text
            or "accounts" in text
        ):

            self.open_setting(
                "android.settings.SYNC_SETTINGS"
            )
            return

        # ----------------------------------------------------
        # النسخ الاحتياطي
        # ----------------------------------------------------

        if (
            "النسخ الاحتياطي" in text
            or "backup" in text
        ):

            self.open_setting(
                "android.settings.BACKUP_SETTINGS"
            )
            return

        # ----------------------------------------------------
        # اللغة
        # ----------------------------------------------------

        if (
            "اللغه" in text
            or "اللغة" in original
            or "language" in text
        ):

            self.open_setting(
                "android.settings.LOCALE_SETTINGS"
            )
            return

        # ----------------------------------------------------
        # التاريخ والوقت
        # ----------------------------------------------------

        if (
            "التاريخ والوقت" in text
            or "date and time" in text
        ):

            self.open_setting(
                "android.settings.DATE_SETTINGS"
            )
            return

        # ----------------------------------------------------
        # الصوت العام
        # ----------------------------------------------------

        if (
            "الصوت" in text
            or "sound" in text
        ):

            self.open_setting(
                "android.settings.SOUND_SETTINGS"
            )
            return

        # ----------------------------------------------------
        # لا يوجد أمر
        # ----------------------------------------------------

        self.notify(
            "لم أفهم الأمر: " + original
            if self.is_arabic
            else "I did not understand: " + original
        )


# ============================================================
# تشغيل
# ============================================================

if __name__ == "__main__":
    VoiceControlApp().run()
