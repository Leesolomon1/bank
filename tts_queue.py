import os
import queue
import subprocess
import threading
import time
from typing import Callable, Optional


class TTSQueue:
    def __init__(
        self,
        on_status: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.message_queue: queue.Queue[str | None] = queue.Queue()
        self.on_status = on_status
        self.running = True

        self.worker = threading.Thread(
            target=self._run,
            daemon=True,
        )
        self.worker.start()

    def add(self, message: str) -> None:
        cleaned_message = message.strip()

        if cleaned_message:
            self.message_queue.put(cleaned_message)

    def stop(self) -> None:
        self.running = False
        self.message_queue.put(None)

    def _set_status(self, message: str) -> None:
        if self.on_status:
            self.on_status(message)

    @staticmethod
    def _escape_powershell_text(text: str) -> str:
        return text.replace("'", "''")

    @staticmethod
    def _get_powershell_path() -> str:
        system_root = os.environ.get("SystemRoot", r"C:\Windows")

        powershell_path = os.path.join(
            system_root,
            "System32",
            "WindowsPowerShell",
            "v1.0",
            "powershell.exe",
        )

        if not os.path.isfile(powershell_path):
            raise FileNotFoundError(
                f"PowerShell을 찾을 수 없습니다: {powershell_path}"
            )

        return powershell_path

    def _speak(self, message: str) -> None:
        safe_message = self._escape_powershell_text(message)
        powershell_path = self._get_powershell_path()

        powershell_command = (
            "Add-Type -AssemblyName System.Speech; "
            "$speaker = New-Object "
            "System.Speech.Synthesis.SpeechSynthesizer; "
            "$speaker.Volume = 100; "
            "$speaker.Rate = 0; "
            f"$speaker.Speak('{safe_message}'); "
            "$speaker.Dispose();"
        )

        startup_info = subprocess.STARTUPINFO()
        startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        result = subprocess.run(
            [
                powershell_path,
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                powershell_command,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            startupinfo=startup_info,
        )

        if result.returncode != 0:
            error_message = result.stderr.strip()

            if not error_message:
                error_message = (
                    f"PowerShell 음성 실행 실패 "
                    f"(종료 코드: {result.returncode})"
                )

            raise RuntimeError(error_message)

    def _run(self) -> None:
        self._set_status("음성 대기 중")

        while self.running:
            message = self.message_queue.get()

            try:
                if message is None:
                    return

                self._set_status(f"읽는 중: {message}")

                self._speak(message)

                time.sleep(0.3)
                self._set_status("음성 대기 중")

            except Exception as error:
                self._set_status(f"TTS 오류: {error}")

            finally:
                self.message_queue.task_done()