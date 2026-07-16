import random
import re
import string

INVITE_CODE_PATTERN = re.compile(r"^[A-Z]{4}-[0-9]{4}$")


def generate_invite_code() -> str:
    letters = "".join(random.choices(string.ascii_uppercase, k=4))
    digits = "".join(random.choices(string.digits, k=4))
    return f"{letters}-{digits}"


def is_valid_invite_code_format(code: str) -> bool:
    return bool(INVITE_CODE_PATTERN.match(code))
