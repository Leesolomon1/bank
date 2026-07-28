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
requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.0,pyjnius

# 화면 방향
orientation = portrait

# 전체 화면 사용 안 함
fullscreen = 0

# Android 설정
android.api = 34
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a

# Java 소스 폴더
android.add_src = java

# NotificationListenerService 등록
android.extra_manifest_application_arguments = manifest/notification_service.xml


android.accept_sdk_license = True

# 알림 권한
android.permissions = POST_NOTIFICATIONS

# 로그 설정
android.logcat_filters = *:S python:D

[buildozer]

log_level = 2
warn_on_root = 1