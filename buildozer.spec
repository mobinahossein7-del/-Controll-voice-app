[app]

# اسم التطبيق
title = Voice Control App

# اسم الحزمة
package.name = voicecontrol

# نطاق الحزمة
package.domain = org.voice

# مجلد المشروع
source.dir = .

# الملفات التي يجب تضمينها داخل APK
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,otf,mp3,wav

# إصدار التطبيق
version = 1.0

# مكتبات Python المطلوبة
requirements = python3,kivy==2.3.0,pyjnius==1.6.1,arabic-reshaper,python-bidi

# صلاحيات Android
android.permissions = INTERNET,RECORD_AUDIO,WRITE_SETTINGS,ACCESS_WIFI_STATE,CHANGE_WIFI_STATE,NEARBY_WIFI_DEVICES

# اتجاه الشاشة
orientation = portrait

# لا تستخدم ملء الشاشة
fullscreen = 0

# إصدار Android المستهدف
android.api = 33

# أقل إصدار Android
android.minapi = 21

# إصدار Android SDK
android.sdk = 33

# إصدار Build Tools
android.sdk_build_tools_version = 33.0.0

# إصدار NDK
android.ndk = 25b

# قبول تراخيص Android SDK
android.accept_sdk_license = True

# إصدار python-for-android
p4a.branch = v2024.01.21


[buildozer]

# مستوى سجل البناء
log_level = 2

# إظهار تحذير عند تشغيل Buildozer بصلاحيات root
warn_on_root = 1
