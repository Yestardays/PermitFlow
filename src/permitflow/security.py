import html
import re


def plain_text(value: object, max_length: int = 1000) -> str:
    text = str(value).replace("\x00", "").strip()[:max_length]
    text = re.sub(r"[\r\n]{3,}", "\n\n", text)
    return html.escape(text, quote=False)


def assert_self_application(applicant_email: str, requested_email: str | None) -> None:
    if requested_email and requested_email.casefold() != applicant_email.casefold():
        raise ValueError("当前版本仅允许为自己申请权限")
