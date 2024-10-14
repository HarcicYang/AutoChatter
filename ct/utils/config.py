from cfgr.manager import BaseConfig


class LagrangeConfig(BaseConfig):
    uin: int
    sign_url: str


class ChattingConfig(BaseConfig):
    prompt: str


class ChatterConfig(BaseConfig):
    lagrange: LagrangeConfig
    chatting: ChattingConfig

