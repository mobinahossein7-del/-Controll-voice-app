# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.core.audio import SoundLoader
from kivy.metrics import dp
from kivy.properties import ColorProperty, StringProperty
from kivy.graphics import Color, RoundedRectangle, Ellipse, Rectangle
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
import os

# محاولة استيراد مكتبات معالجة النصوص العربية
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:
    arabic_reshaper = None
    get_display = None

# إعدادات الملفات والخطوط الثابتة
FONT = "NotoKufiArabic-VariableFont_wght.ttf"
BACKGROUND_FILE = "tanjiro_background.jpg"
MUSIC_FILE = "app_music.mp3"

# تسسجيل الخط العربي
try:
    LabelBase.register(name="ArabicFont", fn_regular=FONT)
    ACTIVE_FONT = "ArabicFont"
except Exception:
    ACTIVE_FONT = "Roboto"


def rtl(text):
    """معالجة النصوص العربية لتظهر بالشكل الصحيح في Kivy"""
    text = str(text)
    if not arabic_reshaper or not get_display:
        return text
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped, base_dir="R")
    except Exception:
        return text


class BackgroundWidget(BoxLayout):
    """وحدة مخصصة لعرض الخلفية المطلوبة Tanjiro Background"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            if os.path.exists(BACKGROUND_FILE):
                self.bg_rect = Rectangle(source=BACKGROUND_FILE, pos=self.pos, size=self.size)
            else:
                self.bg_rect = Color(0.05, 0.05, 0.08, 1) # خلفية افتراضية في حال عدم توفر الصورة
                self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        if hasattr(self, 'bg_rect') and isinstance(self.bg_rect, Rectangle):
            self.bg_rect.pos = self.pos
            self.bg_rect.size = self.size


class ProfessionalCard(ButtonBehavior, BoxLayout):
    """بطاقة تفاعلية بتصميم عصري وجميل"""
    text = StringProperty("")
    subtitle = StringProperty("")
    icon = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12), spacing=dp(4), **kwargs)
        self.size_hint_y = None
        self.height = dp(90)
        
        with self.canvas.before:
            Color(0.12, 0.14, 0.20, 0.85) # شفافية خفيفة لإظهار الخلفية خلف البطاقات
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])
        self.bind(pos=self._update, size=self._update)

        # محتوى البطاقة
        self.icon_lbl = Label(text=self.icon, font_size=dp(20), color=(0.2, 0.7, 1, 1), size_hint_y=None, height=dp(25))
        self.title_lbl = Label(text=rtl(self.text), font_name=ACTIVE_FONT, font_size=dp(14), bold=True, color=(1, 1, 1, 1), halign="right")
        self.sub_lbl = Label(text=rtl(self.subtitle), font_name=ACTIVE_FONT, font_size=dp(10), color=(0.7, 0.7, 0.8, 1), halign="right")

        for lbl in (self.title_lbl, self.sub_lbl):
            lbl.bind(size=lambda w, _: setattr(w, 'text_size', (w.width, None)))

        self.add_widget(self.icon_lbl)
        self.add_widget(self.title_lbl)
        self.add_widget(self.sub_lbl)

    def _update(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class VoiceControlProApp(App):
    title = "Voice Control Pro"

    def build(self):
        Window.size = (400, 700)
        
        # تشغيل الموسيقى الخلفية
        self.play_music()

        # مدير الشاشات الأساسي
        sm = ScreenManager()
        sm.add_widget(self.create_home_screen())
        sm.add_widget(self.create_settings_screen())
        sm.add_widget(self.create_commands_screen())
        sm.add_widget(self.create_about_screen())
        
        return sm

    def play_music(self):
        """تشغيل ملف الموسيقى بشكل متكرر"""
        try:
            if os.path.exists(MUSIC_FILE):
                self.music = SoundLoader.load(MUSIC_FILE)
                if self.music:
                    self.music.loop = True
                    self.music.volume = 0.5
                    self.music.play()
        except Exception as e:
            print("Music error:", e)

    def create_home_screen(self):
        screen = Screen(name="home")
        root = BackgroundWidget(orientation="vertical", padding=dp(16), spacing=dp(12))

        # رأس الصفحة
        header = Label(
            text=rtl("التحكم الصوتي الاحترافي"),
            font_name=ACTIVE_FONT,
            font_size=dp(22),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(40)
        )
        root.add_widget(header)

        # زر الميكروفون المركزي المتطور
        mic_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(140), padding=dp(20))
        self.mic_btn = Label(
            text=rtl("🎙\nاضغط للتحدث"),
            font_name=ACTIVE_FONT,
            font_size=dp(16),
            bold=True,
            halign="center",
            valign="middle"
        )
        mic_box.add_widget(self.mic_btn)
        root.add_widget(mic_box)

        # شبكة الاختصارات السريعة
        grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(200))
        
        cards_data = [
            ("شبكة الاتصال", "Wi-Fi & Bluetooth", "🌐", "wifi"),
            ("إعدادات الشاشة", "السطوع والوضع الليلي", "💡", "display"),
            ("حالة البطارية", "الطاقة والأداء", "🔋", "battery"),
            ("الأمان والخصوصية", "الصلاحيات والحماية", "🔒", "privacy")
        ]

        for title, sub, icon, action in cards_data:
            card = ProfessionalCard(text=title, subtitle=sub, icon=icon)
            card.bind(on_release=lambda instance, act=action: self.on_card_clicked(act))
            grid.add_widget(card)

        root.add_widget(grid)

        # شريط التنقل السفلي
        nav = GridLayout(cols=4, spacing=dp(5), size_hint_y=None, height=dp(55))
        nav_items = [("الرئيسية", "home"), ("الإعدادات", "settings"), ("الأوامر", "commands"), ("من نحن", "about")]
        
        for name, screen_name in nav_items:
            btn = ProfessionalCard(text=name, subtitle="", icon="")
            btn.height = dp(50)
            btn.bind(on_release=lambda instance, s=screen_name: setattr(sm_goto(self, s), 'current', s)) if 'sm_goto' else None
            # تبسيط التنقل المباشر
            btn.bind(on_release=lambda inst, s=screen_name: self.change_screen(s))
            nav.add_widget(btn)

        root.add_widget(nav)
        screen.add_widget(root)
        return screen

    def create_settings_screen(self):
        screen = Screen(name="settings")
        root = BackgroundWidget(orientation="vertical", padding=dp(16), spacing=dp(10))
        root.add_widget(Label(text=rtl("إعدادات التطبيق"), font_name=ACTIVE_FONT, font_size=dp(20), bold=True, size_hint_y=None, height=dp(40)))
        
        back_btn = ProfessionalCard(text="العودة للرئيسية", subtitle="الانتقال للشاشة الرئيسية", icon="⬅")
        back_btn.bind(on_release=lambda x: self.change_screen("home"))
        root.add_widget(back_btn)
        
        screen.add_widget(root)
        return screen

    def create_commands_screen(self):
        screen = Screen(name="commands")
        root = BackgroundWidget(orientation="vertical", padding=dp(16), spacing=dp(10))
        root.add_widget(Label(text=rtl("الأوامر الصوتية المتاحة"), font_name=ACTIVE_FONT, font_size=dp(20), bold=True, size_hint_y=None, height=dp(40)))
        
        back_btn = ProfessionalCard(text="العودة للرئيسية", subtitle="الانتقال للشاشة الرئيسية", icon="⬅")
        back_btn.bind(on_release=lambda x: self.change_screen("home"))
        root.add_widget(back_btn)

        screen.add_widget(root)
        return screen

    def create_about_screen(self):
        screen = Screen(name="about")
        root = BackgroundWidget(orientation="vertical", padding=dp(16), spacing=dp(10))
        root.add_widget(Label(text=rtl("من نحن"), font_name=ACTIVE_FONT, font_size=dp(20), bold=True, size_hint_y=None, height=dp(40)))
        
        back_btn = ProfessionalCard(text="العودة للرئيسية", subtitle="الانتقال للشاشة الرئيسية", icon="⬅")
        back_btn.bind(on_release=lambda x: self.change_screen("home"))
        root.add_widget(back_btn)

        screen.add_widget(root)
        return screen

    def change_screen(self, screen_name):
        self.root.current = screen_name

    def on_card_clicked(self, action):
        print(f"Action triggered: {action}")


if __name__ == "__main__":
    VoiceControlProApp().run()
