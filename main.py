from datetime import datetime
from pathlib import Path
from typing import Any

from kivy.logger import Logger
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.textinput import TextInput
from kivy.utils import platform

# Android에서 Java NotificationService가 보낸 브로드캐스트 수신
if platform == "android":
    from jnius import autoclass

from parser import Transaction, parse_transaction
from settings_manager import load_settings, save_settings
from tts_queue import TTSQueue


# =========================================================
# 한글 글꼴 설정
# =========================================================

from pathlib import Path

def find_korean_font() -> str:
    font_path = Path(__file__).resolve().parent / "NanumGothic.ttf"

    if font_path.is_file():
        return str(font_path)

    return "Roboto"


FONT_PATH = find_korean_font()

class KoreanLabel(Label):
    """한글 글꼴이 적용된 Label"""

    def __init__(self, **kwargs):
        kwargs.setdefault("font_name", FONT_PATH)
        super().__init__(**kwargs)


class KoreanButton(Button):
    """한글 글꼴이 적용된 Button"""

    def __init__(self, **kwargs):
        kwargs.setdefault("font_name", FONT_PATH)
        super().__init__(**kwargs)


class KoreanTextInput(TextInput):
    """한글 글꼴이 적용된 TextInput"""

    def __init__(self, **kwargs):
        kwargs.setdefault("font_name", FONT_PATH)
        super().__init__(**kwargs)


class KoreanSpinnerOption(SpinnerOption):
    """시간 선택 목록에 표시되는 한글 글꼴 옵션"""

    def __init__(self, **kwargs):
        kwargs.setdefault("font_name", FONT_PATH)
        super().__init__(**kwargs)


class KoreanSpinner(Spinner):
    """한글 글꼴이 적용된 Spinner"""

    def __init__(self, **kwargs):
        kwargs.setdefault("font_name", FONT_PATH)
        kwargs.setdefault("option_cls", KoreanSpinnerOption)
        super().__init__(**kwargs)


# =========================================================
# 은행별 테스트 알림
# =========================================================

POST_OFFICE_SAMPLE = """[Web발신]
우체국,07/15 18:19
110******246
입금 11,000원
잔액 1,405,715원
이지연"""


NH_DEPOSIT_SAMPLE = """입출금 알림
농협 입금10,000원
07/15 18:38 356-****-0576-13 정효진
잔액10,000원"""


NH_WITHDRAW_SAMPLE = """입출금 알림
농협 출금10,000원
07/15 18:39 356-****-0576-13 카카오페이
잔액0원"""


KB_DEPOSIT_SAMPLE = """KB스타뱅킹
입금 10,000원
정*진님 07/15 18:39 582102-**-***852
정효진 FBS입금 10,000 잔액10,000"""


KB_WITHDRAW_SAMPLE = """KB스타뱅킹
출금 10,000원
정*진님 07/15 18:39 582102-**-***852
카카오페이 FBS출금 10,000 잔액0"""


# =========================================================
# 메인 앱
# =========================================================

class BankTTSApp(App):
    def build(self) -> ScrollView:
        self.title = "은행 입출금 음성 알림"
        self.settings: dict[str, Any] = load_settings()
        self.last_notification_id = 0
        self.notification_poll_event = None

        self.tts = TTSQueue(
            on_status=self.schedule_status_update
        )

        root = ScrollView()

        content = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
            size_hint_y=None,
        )

        content.bind(
            minimum_height=content.setter("height")
        )

        # 제목
        title = KoreanLabel(
            text="은행 입출금 음성 알림",
            font_size="24sp",
            size_hint_y=None,
            height=dp(55),
        )
        content.add_widget(title)

        # 설정 체크박스
        content.add_widget(
            self.make_checkbox_row(
                "음성 알림 사용",
                "enabled",
            )
        )

        content.add_widget(
            self.make_checkbox_row(
                "입금 읽기",
                "read_deposit",
            )
        )

        content.add_widget(
            self.make_checkbox_row(
                "출금 읽기",
                "read_withdraw",
            )
        )

        content.add_widget(
            self.make_checkbox_row(
                "무음 시간 사용",
                "quiet_enabled",
            )
        )

        # 최소 금액 설정
        minimum_row = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            spacing=dp(10),
        )

        minimum_label = KoreanLabel(
            text="최소 읽기 금액",
            halign="left",
            valign="middle",
        )
        minimum_label.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )
        minimum_row.add_widget(minimum_label)

        self.minimum_input = KoreanTextInput(
            text=str(self.settings["minimum_amount"]),
            multiline=False,
            input_filter="int",
            size_hint_x=0.45,
        )
        minimum_row.add_widget(self.minimum_input)

        minimum_row.add_widget(
            KoreanLabel(
                text="원",
                size_hint_x=0.2,
            )
        )

        content.add_widget(minimum_row)

        # 무음 시간 설정
        time_grid = GridLayout(
            cols=2,
            spacing=dp(8),
            size_hint_y=None,
            height=dp(105),
        )

        time_grid.add_widget(
            KoreanLabel(text="무음 시작")
        )

        self.quiet_start_spinner = KoreanSpinner(
            text=self.settings["quiet_start"],
            values=self.make_time_values(),
        )
        time_grid.add_widget(
            self.quiet_start_spinner
        )

        time_grid.add_widget(
            KoreanLabel(text="무음 종료")
        )

        self.quiet_end_spinner = KoreanSpinner(
            text=self.settings["quiet_end"],
            values=self.make_time_values(),
        )
        time_grid.add_widget(
            self.quiet_end_spinner
        )

        content.add_widget(time_grid)

        # 설정 저장 버튼
        save_button = KoreanButton(
            text="설정 저장",
            size_hint_y=None,
            height=dp(52),
        )
        save_button.bind(
            on_release=self.save_current_settings
        )
        content.add_widget(save_button)
        
        # 음성 출력 단독 테스트 버튼
        voice_test_button = KoreanButton(
            text="음성 테스트",
            size_hint_y=None,
            height=dp(52),
        )

        voice_test_button.bind(
            on_release=self.test_voice
        )

        content.add_widget(voice_test_button)

        # 상태 표시
        self.status_label = KoreanLabel(
            text="상태: 준비됨",
            size_hint_y=None,
            height=dp(70),
            halign="center",
            valign="middle",
        )
        self.status_label.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )
        content.add_widget(self.status_label)

        # 은행별 테스트 제목
        test_title = KoreanLabel(
            text="은행별 테스트",
            font_size="20sp",
            size_hint_y=None,
            height=dp(45),
        )
        content.add_widget(test_title)

        # 은행별 테스트 버튼
        test_buttons = [
            (
                "우체국 입금 테스트",
                POST_OFFICE_SAMPLE,
            ),
            (
                "농협 입금 테스트",
                NH_DEPOSIT_SAMPLE,
            ),
            (
                "농협 출금 테스트",
                NH_WITHDRAW_SAMPLE,
            ),
            (
                "국민은행 입금 테스트",
                KB_DEPOSIT_SAMPLE,
            ),
            (
                "국민은행 출금 테스트",
                KB_WITHDRAW_SAMPLE,
            ),
        ]

        for button_text, sample in test_buttons:
            button = KoreanButton(
                text=button_text,
                size_hint_y=None,
                height=dp(50),
            )

            button.bind(
                on_release=lambda instance, value=sample:
                self.process_notification(value)
            )

            content.add_widget(button)

        # 연속 입금 테스트
        queue_test_button = KoreanButton(
            text="연속 입금 3건 대기열 테스트",
            size_hint_y=None,
            height=dp(55),
        )

        queue_test_button.bind(
            on_release=self.test_multiple_deposits
        )

        content.add_widget(queue_test_button)

        # 직접 입력 테스트 제목
        custom_title = KoreanLabel(
            text="직접 알림 내용 테스트",
            font_size="20sp",
            size_hint_y=None,
            height=dp(45),
        )
        content.add_widget(custom_title)

        # 직접 입력창
        self.custom_text = KoreanTextInput(
            hint_text=(
                "은행 문자 또는 앱 알림 내용을 "
                "여기에 붙여넣으세요."
            ),
            multiline=True,
            size_hint_y=None,
            height=dp(190),
        )
        content.add_widget(self.custom_text)

        # 직접 입력 분석 버튼
        custom_button = KoreanButton(
            text="붙여넣은 내용 분석하고 읽기",
            size_hint_y=None,
            height=dp(55),
        )

        custom_button.bind(
            on_release=lambda instance:
            self.process_notification(
                self.custom_text.text
            )
        )

        content.add_widget(custom_button)

        root.add_widget(content)
        return root

    # =====================================================
    # Android 실제 알림 수신
    # =====================================================

    def on_start(self) -> None:
        """Java 서비스가 저장한 실제 알림을 주기적으로 확인한다."""
        if platform != "android":
            return

        self.notification_poll_event = Clock.schedule_interval(
            self.check_saved_notification,
            1.0,
        )

        Logger.info("BankTTS: 실제 알림 확인 시작")


    def check_saved_notification(self, dt) -> None:
        try:
            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )

            context = PythonActivity.mActivity

            preferences = context.getSharedPreferences(
                "bank_notifications",
                0,
            )

            notification_id = preferences.getLong(
                "notification_id",
                0,
            )

            if notification_id == 0:
                return

            if notification_id == self.last_notification_id:
                return

            self.last_notification_id = notification_id

            package_name = preferences.getString(
                "package_name",
                "",
            ) or ""

            title = preferences.getString(
                "title",
                "",
            ) or ""

            text = preferences.getString(
                "text",
                "",
            ) or ""

            combined_text = "\n".join(
                part.strip()
                for part in (title, text)
                if part and part.strip()
            )

            Logger.info(f"BankTTS: {package_name} {combined_text}")
            

            if combined_text:
                self.process_notification(combined_text)

        except Exception:
            Logger.exception("BankTTS: 실제 알림 확인 오류")


    # =====================================================
    # 설정 UI
    # =====================================================

    def make_checkbox_row(
        self,
        text: str,
        setting_key: str,
    ) -> BoxLayout:
        row = BoxLayout(
            size_hint_y=None,
            height=dp(44),
        )

        label = KoreanLabel(
            text=text,
            halign="left",
            valign="middle",
        )

        label.bind(
            size=lambda instance, value:
            setattr(instance, "text_size", value)
        )

        checkbox = CheckBox(
            active=bool(
                self.settings[setting_key]
            ),
            size_hint_x=0.25,
        )

        checkbox.bind(
            active=lambda instance, value, key=setting_key:
            self.update_boolean_setting(
                key,
                value,
            )
        )

        row.add_widget(label)
        row.add_widget(checkbox)

        return row

    @staticmethod
    def make_time_values() -> tuple[str, ...]:
        values = []

        for hour in range(24):
            for minute in (0, 30):
                values.append(
                    f"{hour:02d}:{minute:02d}"
                )

        return tuple(values)

    def update_boolean_setting(
        self,
        key: str,
        value: bool,
    ) -> None:
        self.settings[key] = value

    def save_current_settings(
        self,
        instance=None,
    ) -> bool:
        try:
            minimum_amount = int(
                self.minimum_input.text.strip()
                or "0"
            )

            if minimum_amount < 0:
                raise ValueError

        except ValueError:
            self.set_status(
                "최소 금액은 0 이상의 숫자로 입력해줘."
            )
            return False

        self.settings["minimum_amount"] = (
            minimum_amount
        )

        self.settings["quiet_start"] = (
            self.quiet_start_spinner.text
        )

        self.settings["quiet_end"] = (
            self.quiet_end_spinner.text
        )

        save_settings(self.settings)
        self.set_status("설정이 저장됐어.")

        return True

    # =====================================================
    # 알림 분석 및 음성 출력
    # =====================================================

    def process_notification(
        self,
        text: str,
    ) -> None:
        if not self.save_current_settings():
            return

        transaction = parse_transaction(text)

        if not transaction:
            self.set_status(
                "은행 거래 내용을 찾지 못했어."
            )
            return

        reason = self.get_skip_reason(
            transaction
        )

        if reason:
            self.set_status(
                f"{transaction.bank} "
                f"{transaction.transaction_type} "
                f"{transaction.amount:,}원: "
                f"{reason}"
            )
            return

        message = self.make_speech_message(
            transaction
        )

        self.set_status(
            f"대기열 추가: {message}"
        )

        self.tts.add(message)

    def get_skip_reason(
        self,
        transaction: Transaction,
    ) -> str | None:
        if not self.settings["enabled"]:
            return "음성 알림이 꺼져 있음"

        if (
            transaction.transaction_type
            == "입금"
            and not self.settings["read_deposit"]
        ):
            return "입금 읽기가 꺼져 있음"

        if (
            transaction.transaction_type
            == "출금"
            and not self.settings["read_withdraw"]
        ):
            return "출금 읽기가 꺼져 있음"

        if (
            transaction.amount
            < int(
                self.settings["minimum_amount"]
            )
        ):
            return "최소 금액보다 작음"

        if self.is_quiet_time():
            return "현재 무음 시간임"

        return None

    # =====================================================
    # 무음 시간
    # =====================================================

    def is_quiet_time(self) -> bool:
        if not self.settings["quiet_enabled"]:
            return False

        now = datetime.now()

        current_minutes = (
            now.hour * 60
            + now.minute
        )

        start_minutes = self.time_to_minutes(
            self.settings["quiet_start"]
        )

        end_minutes = self.time_to_minutes(
            self.settings["quiet_end"]
        )

        # 시작과 종료가 같으면 하루 종일 무음
        if start_minutes == end_minutes:
            return True

        # 예: 오후 11시부터 다음 날 오전 8시
        if start_minutes > end_minutes:
            return (
                current_minutes >= start_minutes
                or current_minutes < end_minutes
            )

        return (
            start_minutes
            <= current_minutes
            < end_minutes
        )

    @staticmethod
    def time_to_minutes(
        value: str,
    ) -> int:
        hour_text, minute_text = value.split(":")

        return (
            int(hour_text) * 60
            + int(minute_text)
        )

    # =====================================================
    # 음성 문장 생성
    # =====================================================

    @staticmethod
    def make_speech_message(
        transaction: Transaction,
    ) -> str:
        amount_text = (
            f"{transaction.amount:,}원"
        )

        if (
            transaction.transaction_type
            == "입금"
        ):
            return (
                f"{transaction.name}님, "
                f"{amount_text} 입금"
            )

        return (
            f"{transaction.name}, "
            f"{amount_text} 출금"
        )
        
            # =====================================================
    # 음성 출력 단독 테스트
    # =====================================================

    def test_voice(
        self,
        instance=None,
    ) -> None:
        if not self.save_current_settings():
            return

        if not self.settings["enabled"]:
            self.set_status(
                "음성 알림 사용이 꺼져 있어."
            )
            return

        message = "음성 테스트입니다."

        self.set_status(
            f"대기열 추가: {message}"
        )

        self.tts.add(message)

    # =====================================================
    # 연속 알림 테스트
    # =====================================================

    def test_multiple_deposits(
        self,
        instance=None,
    ) -> None:
        if not self.save_current_settings():
            return

        samples = [
            """농협 입금5,000원
07/15 18:38 356-****-0576-13 이진서
잔액5,000원""",

            """농협 입금10,000원
07/15 18:39 356-****-0576-13 정효진
잔액15,000원""",

            """[Web발신]
우체국,07/15 18:40
110******246
입금 11,000원
잔액 26,000원
이지연""",
        ]

        added = 0

        for sample in samples:
            transaction = parse_transaction(
                sample
            )

            if not transaction:
                continue

            reason = self.get_skip_reason(
                transaction
            )

            if reason:
                continue

            message = self.make_speech_message(
                transaction
            )

            self.tts.add(message)
            added += 1

        self.set_status(
            f"연속 입금 {added}건을 "
            f"대기열에 넣었어."
        )

    # =====================================================
    # 상태 표시
    # =====================================================

    def schedule_status_update(
        self,
        message: str,
    ) -> None:
        Clock.schedule_once(
            lambda dt:
            self.set_status(message),
            0,
        )

    def set_status(
        self,
        message: str,
    ) -> None:
        self.status_label.text = (
            f"상태: {message}"
        )

    def on_stop(self) -> None:
        if self.notification_poll_event is not None:
            self.notification_poll_event.cancel()
            self.notification_poll_event = None

        self.tts.stop()


if __name__ == "__main__":
    BankTTSApp().run()