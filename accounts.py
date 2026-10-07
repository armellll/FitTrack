import hashlib
import hmac
import os

from validator import Validator


class User:
    """A logged in person. Attributes are private and read through properties."""

    def __init__(self, user_id, full_name, username, weight_kg=None, height_cm=None):
        self._id = user_id
        self._full_name = full_name
        self._username = username
        self._weight_kg = weight_kg
        self._height_cm = height_cm

    @property
    def id(self):
        return self._id

    @property
    def full_name(self):
        return self._full_name

    @property
    def username(self):
        return self._username

    @property
    def weight_kg(self):
        return self._weight_kg

    @property
    def height_cm(self):
        return self._height_cm

    @staticmethod
    def clean_profile(full_name, weight_text, height_text):
        """Check the profile fields and return clean values. Saves nothing."""
        full_name = Validator.required(full_name, "Full name")
        if len(full_name) > 60:
            raise ValueError("Full name must be 60 characters or less.")
        weight = Validator.decimal_number(weight_text, "Weight", minimum=1,
                                          required=False, default=None)
        height = Validator.decimal_number(height_text, "Height", minimum=1,
                                          required=False, default=None)
        if weight is not None and weight > 500:
            raise ValueError("Weight must be 500 kg or less.")
        if height is not None and height > 300:
            raise ValueError("Height must be 300 cm or less.")
        return full_name, weight, height

    def update_profile(self, db, full_name, weight_text, height_text):
        full_name, weight, height = self.clean_profile(full_name, weight_text, height_text)
        db.execute("UPDATE users SET full_name = ?, weight_kg = ?, height_cm = ? WHERE id = ?",
                   (full_name, weight, height, self._id))
        self._full_name = full_name
        self._weight_kg = weight
        self._height_cm = height


class Auth:
    """Handles register, login, logout and password changes."""

    def __init__(self, db):
        self._db = db
        self._current_user = None

    @property
    def current_user(self):
        return self._current_user

    @staticmethod
    def _hash_password(password, salt):
        return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000).hex()

    @staticmethod
    def _make_stored_password(password):
        salt = os.urandom(16)
        return salt.hex() + "$" + Auth._hash_password(password, salt)

    @staticmethod
    def _verify_password(password, stored):
        try:
            salt_hex, hash_hex = stored.split("$")
            candidate = Auth._hash_password(password, bytes.fromhex(salt_hex))
        except ValueError:
            return False
        return hmac.compare_digest(candidate, hash_hex)

    def register(self, full_name, username, password, confirm):
        full_name = Validator.required(full_name, "Full name")
        if len(full_name) > 60:
            raise ValueError("Full name must be 60 characters or less.")
        username = Validator.username(username)
        password = Validator.password(password)
        if password != confirm:
            raise ValueError("Passwords do not match.")
        if self._db.fetch_one("SELECT id FROM users WHERE username = ?", (username,)):
            raise ValueError("That username is already taken.")
        return self._db.execute(
            "INSERT INTO users (full_name, username, password_hash) VALUES (?, ?, ?)",
            (full_name, username, self._make_stored_password(password)))

    def login(self, username, password):
        username = Validator.required(username, "Username").lower()
        password = Validator.required(password, "Password")
        row = self._db.fetch_one("SELECT * FROM users WHERE username = ?", (username,))
        if row is None or not self._verify_password(password, row["password_hash"]):
            raise ValueError("Wrong username or password.")
        self._current_user = User(row["id"], row["full_name"], row["username"],
                                  row["weight_kg"], row["height_cm"])
        return self._current_user

    def logout(self):
        self._current_user = None

    def change_password(self, current_password, new_password, confirm):
        if self._current_user is None:
            raise ValueError("You must be logged in.")
        if not current_password:
            raise ValueError("Enter your current password to change it.")
        row = self._db.fetch_one("SELECT password_hash FROM users WHERE id = ?",
                                 (self._current_user.id,))
        if row is None or not self._verify_password(current_password, row["password_hash"]):
            raise ValueError("Your current password is wrong.")
        new_password = Validator.password(new_password)
        if new_password != confirm:
            raise ValueError("The new passwords do not match.")
        self._db.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                         (self._make_stored_password(new_password), self._current_user.id))