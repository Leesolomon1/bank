[app]

# 앱 이름
title = 은행 알림 음성 안내

# 영문 소문자만 사용
package.name = banktts
package.domain = com.leesolomon

# main.py가 있는 위치
source.dir = .

# APK에 포함할 파일 확장자
source.include_exts = py,json,png,jpg,jpeg,kv,ttf

# 제외할 폴더
source.exclude_dirs = .git,.github,.venv,__pycache__,bin,.buildozer

# 앱 버전
version = 0.1

# 사용할 라이브러리
requirements = python3,kivy,pyjnius

# 화면 방향
orientation = portrait

# 전체 화면 사용 안 함
fullscreen = 0

# Android 설정
android.api = 35
android.minapi = 23
android.ndk = 27c
android.archs = arm64-v8a

android.accept_sdk_license = True

# 현재 단계에서는 기본 권한만 설정
android.permissions = POST_NOTIFICATIONS

# 로그 확인을 위한 설정
android.logcat_filters = *:S python:D

[buildozer]

log_level = 2
warn_on_root = 1