from pydantic import BaseSettings


class Config(BaseSettings):
    # plugin custom config
    save_emote_path: str = "./data/custom_emote_data/"
    save_emote_mode: int = 0

    class Config:
        extra = "ignore"
