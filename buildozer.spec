[app]

# =========================================================
# معلومات التطبيق
# =========================================================

title = Voice Control

package.name = voicecontrol

package.domain = org.voice

source.dir = .

source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,otf,mp3,wav

version = 1.0


# =========================================================
# المكتبات
# =========================================================

requirements = python3,kivy==2.3.0,pyjnius==1.6.1,arabic-reshaper,python-bidi


# =========================================================
# صلاحيات Android
# =========================================================

android.permissions = INTERNET,RECORD_AUDIO,WRITE_SETTINGS,ACCESS_WIFI_STATE,CHANGE_WIFI_STATE,NEARBY_WIFI_DEVICES


# =========================================================
# اتجاه الشاشة
# =========================================================

orientation = portrait

fullscreen = 0


# =========================================================
# Android SDK / NDK
# =========================================================

android.api = 33

android.minapi = 21

android.sdk = 33

android.sdk_build_tools_version = 33.0.0

android.ndk = 25b

android.accept_sdk_license = True


# =========================================================
# python-for-android
# =========================================================

p4a.branch = v2024.01.21


# =========================================================
# Buildozer
# =========================================================

[buildozer]

log_level = 2

warn_on_root = 1
