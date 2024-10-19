from cfgr.manager import BaseConfig


class LagrangeConfig(BaseConfig):
    uin: int
    sign_url: str


class ChattingConfig(BaseConfig):
    prompt: str
    api_key: str


class ChatterConfig(BaseConfig):
    lagrange: LagrangeConfig
    chatting: ChattingConfig

