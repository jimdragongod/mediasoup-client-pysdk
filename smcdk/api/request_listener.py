import asyncio.coroutines

from smcdk.log import Logger
from .mediasoup_listener import MediasoupListener
from .mediasoup_signaler import Request
from .room_peer import Peer

# logger of module level
logger = Logger.getLogger(__name__)


class ConsumerRequestListener(MediasoupListener):
    def __init__(self, mePeer: Peer):
        super(ConsumerRequestListener, self).__init__(mePeer)

    async def onNewConsumer(self, doSignalerResponse: asyncio.coroutines, message: Request, otherPeer: Peer):
        """

        :param doSignalerResponse: must invoke await as soon as possible
        :param message:
        :param otherPeer:
        :return:
        """
        logger.debug('request: %s, otherPeer: %s', message, otherPeer)
        await doSignalerResponse


class DataConsumerRequestListener(MediasoupListener):
    def __init__(self, mePeer: Peer):
        super(DataConsumerRequestListener, self).__init__(mePeer)

    async def onNewDataConsumer(self, doSignalerResponse: asyncio.coroutines, message: Request, otherPeer: Peer):
        """

        :param doSignalerResponse: must invoke await as soon as possible
        :param message:
        :param otherPeer:
        :return:
        """
        logger.debug('request: %s, otherPeer: %s', message, otherPeer)
        await doSignalerResponse
