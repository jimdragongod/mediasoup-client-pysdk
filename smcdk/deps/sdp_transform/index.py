from .parser import parse, parseParams, parseImageAttributes, parseSimulcastStreamList
from .writer import write, defaultOuterOrder, defaultInnerOrder


class sdp_transform:

    @staticmethod
    def parse(sdp: str) -> dict:
        return parse(sdp)

    @staticmethod
    def parseParams(string: str):
        return parseParams(string)

    @staticmethod
    def parseImageAttributes(string: str):
        return parseImageAttributes(string)

    @staticmethod
    def parseSimulcastStreamList(string: str):
        return parseSimulcastStreamList(string)

    @staticmethod
    def write(session: dict, outerOrder: list = defaultOuterOrder, innerOrder: list = defaultInnerOrder):
        return write(session, outerOrder, innerOrder)
