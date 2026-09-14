[app]

title = Voice Control
package.name = voicecontrol
package.domain = org.voice

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,otf

version = 1.0

requirements = python3,kivy,pyjnius

android.permissions = INTERNET,RECORD_AUDIO

orientation = portrait

android.api = 33
android.minapi = 21
android.ndk = 25b

android.accept_sdk_license = True

[buildozer]

log_level = 2
warn_on_root = 1
