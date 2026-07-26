import queue
import threading
import time
from typing import Callable, Optional

from jnius import autoclass
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

        korean = Locale("ko", "KR")
        self.tts.setLanguage(korean)

        self.tts.speak(
            message,
            TextToSpeech.QUEUE_FLUSH,
            None,
            "bank_tts_message",
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