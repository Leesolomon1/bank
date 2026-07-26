import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class Transaction:
    bank: str
    transaction_type: str
    amount: int
    name: str


def clean_text(text: str) -> str:
    """줄바꿈과 불필요한 공백을 정리합니다."""
    return "\n".join(
        line.strip()
        for line in text.replace("\r", "\n").split("\n")
        if line.strip()
    )


def parse_amount(text: str) -> Optional[tuple[str, int]]:
    """
    입금/출금 금액을 추출합니다.

    지원 예:
    입금 10,000원
    농협 입금10,000원
    FBS입금 10,000
    """
    match = re.search(
        r"(입금|출금)\s*([\d,]+)\s*원?",
        text,
    )

    if not match:
        return None

    transaction_type = match.group(1)
    amount = int(match.group(2).replace(",", ""))

    return transaction_type, amount


def parse_post_office(text: str) -> Optional[Transaction]:
    """우체국 SMS를 분석합니다."""
    cleaned = clean_text(text)

    if "우체국" not in cleaned:
        return None

    amount_result = parse_amount(cleaned)
    if not amount_result:
        return None

    transaction_type, amount = amount_result
    lines = cleaned.splitlines()

    ignored_patterns = (
        "[Web발신]",
        "우체국,",
        "입금",
        "출금",
        "잔액",
    )

    name = ""

    # 우체국 문자는 거래 상대가 마지막 줄에 위치합니다.
    for line in reversed(lines):
        if any(pattern in line for pattern in ignored_patterns):
            continue

        if re.search(r"\d{2,3}[-*]+\d", line):
            continue

        name = line
        break

    if not name:
        name = "거래 상대"

    return Transaction(
        bank="우체국",
        transaction_type=transaction_type,
        amount=amount,
        name=name,
    )


def parse_nh(text: str) -> Optional[Transaction]:
    """NH스마트뱅킹 알림을 분석합니다."""
    cleaned = clean_text(text)

    if "농협" not in cleaned and "NH" not in cleaned.upper():
        return None

    amount_result = parse_amount(cleaned)
    if not amount_result:
        return None

    transaction_type, amount = amount_result

    # 날짜, 시간, 계좌번호 뒤에 나오는 거래 상대 추출
    name_match = re.search(
        r"\d{2}/\d{2}\s+\d{1,2}:\d{2}"
        r"\s+\S+\s+([^\n]+)",
        cleaned,
    )

    name = name_match.group(1).strip() if name_match else "거래 상대"

    # 잔액 문구가 같은 줄에 붙은 경우 제거
    name = re.sub(r"\s*잔액.*$", "", name).strip()

    return Transaction(
        bank="농협",
        transaction_type=transaction_type,
        amount=amount,
        name=name,
    )


def parse_kb(text: str) -> Optional[Transaction]:
    """KB국민은행 알림을 분석합니다."""
    cleaned = clean_text(text)

    if (
        "KB" not in cleaned.upper()
        and "국민은행" not in cleaned
        and "FBS입금" not in cleaned
        and "FBS출금" not in cleaned
    ):
        return None

    amount_result = parse_amount(cleaned)
    if not amount_result:
        return None

    transaction_type, amount = amount_result
    name = ""

    # FBS입금 또는 FBS출금 바로 앞의 거래 상대를 우선 사용
    fbs_match = re.search(
        r"(?:^|\n)([^\n]+?)\s+FBS(?:입금|출금)",
        cleaned,
    )

    if fbs_match:
        name = fbs_match.group(1).strip()

        # 같은 줄 앞부분에 날짜, 계좌번호 등이 있을 경우 뒤쪽 이름만 남김
        parts = name.split()
        if parts:
            name = parts[-1]

    # 첫 줄에 "정*진님"처럼 일부 가려진 이름만 있는 경우의 보조 처리
    if not name:
        masked_match = re.search(r"([가-힣*]+)님", cleaned)
        if masked_match:
            name = masked_match.group(1)

    if not name:
        name = "거래 상대"

    return Transaction(
        bank="국민은행",
        transaction_type=transaction_type,
        amount=amount,
        name=name,
    )


def parse_transaction(
    text: str,
    package_name: str = "",
) -> Optional[Transaction]:
    """
    문자 또는 알림 내용을 은행별로 분석합니다.

    package_name은 안드로이드 알림 연결 단계에서 사용합니다.
    PC 테스트에서는 비워둬도 됩니다.
    """
    cleaned = clean_text(text)

    parsers = []

    # 내용과 앱 패키지명을 통해 가장 가능성 높은 파서를 먼저 실행
    package_lower = package_name.lower()

    if "nh" in package_lower or "농협" in cleaned:
        parsers.append(parse_nh)

    if "kb" in package_lower or "국민" in cleaned or "FBS" in cleaned:
        parsers.append(parse_kb)

    if "우체국" in cleaned:
        parsers.append(parse_post_office)

    # 중복 파서 제거
    ordered_parsers = list(dict.fromkeys(parsers))

    # 은행을 확실히 식별하지 못했을 때 전체 검사
    for parser in (parse_post_office, parse_nh, parse_kb):
        if parser not in ordered_parsers:
            ordered_parsers.append(parser)

    for parser in ordered_parsers:
        result = parser(cleaned)
        if result:
            return result

    return None