import queue
import threading
import time
from typing import Callable, Optional

from jnius import autoclass, cast
from kivy.clock import Clock


class TTSQueue:
    def __init__(
        self,
        on_status: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.on_status = on_status
        self.message_queue = queue.Queue()
        self.running = True
        self.tts = None
        self.context = None

        Clock.schedule_once(self._initialize_android_tts, 0.5)

        self.worker = threading.Thread(
            target=self._run,
            daemon=True,
        )
        self.worker.start()

    def _set_status(self, message: str) -> None:
        if self.on_status:
            self.on_status(message)

    def _initialize_android_tts(self, dt=None) -> None:
        try:
            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )
            TextToSpeech = autoclass(
                "android.speech.tts.TextToSpeech"
            )

            self.context = PythonActivity.mActivity

            self.tts = TextToSpeech(
                self.context,
                None,
            )

            self._set_status("Android 음성 준비됨")

        except Exception as error:
            self.tts = None
            self._set_status(
                f"TTS 초기화 오류: {error}"
            )

    def add(self, message: str) -> None:
        cleaned_message = message.strip()

        if cleaned_message:
            self.message_queue.put(cleaned_message)

    def stop(self) -> None:
        self.running = False
        self.message_queue.put(None)

        if self.tts is not None:
            try:
                self.tts.stop()
                self.tts.shutdown()
            except Exception:
                pass

    def _speak(self, message: str) -> None:
        if self.tts is None:
            raise RuntimeError(
                "Android 음성이 아직 준비되지 않았습니다."
            )

        TextToSpeech = autoclass(
            "android.speech.tts.TextToSpeech"
        )
        Locale = autoclass("java.util.Locale")
        Bundle = autoclass("android.os.Bundle")
        JavaString = autoclass("java.lang.String")

        korean = Locale("ko", "KR")
        language_result = self.tts.setLanguage(korean)

        if language_result in (
            TextToSpeech.LANG_MISSING_DATA,
            TextToSpeech.LANG_NOT_SUPPORTED,
        ):
            raise RuntimeError(
                "휴대폰에서 한국어 음성을 지원하지 않습니다."
            )

        params = Bundle()

        java_message = JavaString(message)
        java_message = cast(
            "java.lang.CharSequence",
            java_message,
        )

        utterance_id = JavaString(
            "bank_tts_message"
        )

        result = self.tts.speak(
            java_message,
            TextToSpeech.QUEUE_FLUSH,
            params,
            utterance_id,
        )

        if result == TextToSpeech.ERROR:
            raise RuntimeError(
                "음성 재생 요청에 실패했습니다."
            )
        

    def _run(self) -> None:
        while self.running:
            message = self.message_queue.get()

            try:
                if message is None:
                    return

                self._set_status(
                    f"읽는 중: {message}"
                )

                self._speak(message)

                time.sleep(1)
                self._set_status("음성 대기 중")

            except Exception as error:
                self._set_status(
                    f"TTS 오류: {error}"
                )

            finally:
                self.message_queue.task_done()