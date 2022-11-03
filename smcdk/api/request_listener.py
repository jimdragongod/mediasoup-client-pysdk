import asyncio.coroutines

from .mediasoup_listener import MediasoupListener
from .mediasoup_signaler import Request
from .room_peer import Peer


class ConsumerRequestListener(MediasoupListener):
    def __init__(self, mePeer: Peer):
        super(ConsumerRequestListener, self).__init__(mePeer)

    async def onNewConsumer(self, doSignalerResponse: asyncio.coroutines, message: Request, otherPeer: Peer):
        await doSignalerResponse
        pass


class DataConsumerRequestListener(MediasoupListener):
    def __init__(self, mePeer: Peer):
        super(DataConsumerRequestListener, self).__init__(mePeer)

    async def onNewDataConsumer(self, doSignalerResponse: asyncio.coroutines, message: Request, otherPeer: Peer):
        await doSignalerResponse
        pass
