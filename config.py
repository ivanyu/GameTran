import os

from dotenv import load_dotenv


class Config:
    def __init__(self) -> None:
        load_dotenv()

    def google_api_key(self) -> str:
        return os.environ.get("GOOGLE_CLOUD_KEY")

    def user_language(self) -> str:
        return os.environ.get("USER_LANGUAGE")
