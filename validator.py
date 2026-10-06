import re
from datetime import datetime


class Validator:
    """Checks user input. Every method returns a clean value or raises ValueError with a message."""

    @staticmethod
    def required(value, field):
        value = (value or "").strip()
        if not value:
            raise ValueError(f"{field} is required.")
        return value

    @staticmethod
    def username(value):
        value = Validator.required(value, "Username")
        if not re.fullmatch(r"[A-Za-z0-9_]{3,20}", value):
            raise ValueError("Username must be 3 to 20 letters, numbers or underscores.")
        return value.lower()

    @staticmethod
    def password(value):
        value = value or ""
        if len(value) < 6:
            raise ValueError("Password must be at least 6 characters.")
        return value

    @staticmethod
    def choice(value, field, options):
        if value not in options:
            raise ValueError(f"Please choose a valid {field.lower()}.")
        return value

    @staticmethod
    def whole_number(value, field, minimum=0, required=True, default=0):
        text = (value or "").strip()
        if not text:
            if required:
                raise ValueError(f"{field} is required.")
            return default
        try:
            number = int(text)
        except ValueError:
            raise ValueError(f"{field} must be a whole number.") from None
        if number < minimum:
            raise ValueError(f"{field} must be {minimum} or more.")
        return number

    @staticmethod
    def decimal_number(value, field, minimum=0, required=True, default=0):
        text = (value or "").strip()
        if not text:
            if required:
                raise ValueError(f"{field} is required.")
            return default
        try:
            number = float(text)
        except ValueError:
            raise ValueError(f"{field} must be a number.") from None
        if number < minimum:
            raise ValueError(f"{field} must be {minimum} or more.")
        return number

    @staticmethod
    def date_text(value, field, required=True):
        text = (value or "").strip()
        if not text:
            if required:
                raise ValueError(f"{field} is required.")
            return ""
        try:
            parsed = datetime.strptime(text, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"{field} must be a valid date like 2026-12-31.") from None
        if parsed.year < 2000:
            raise ValueError(f"{field} must be a valid date like 2026-12-31.")
        # always save the date in the same format, for example 2026-10-01
        return parsed.strftime("%Y-%m-%d")