import asyncio
import logging
from abc import ABCMeta, abstractmethod

from smcdk.log import Logger
from .mediasoup_listener import MediasoupListener
from .mediasoup_signaler import MessageType, Notification
from .room_peer import Peer, PeerAppData

# logger of module level
logger = Logger.getLogger(__name__)


class QueuedNotificationListener(MediasoupListener, metaclass=ABCMeta):

    def __init__(self, mePeer: Peer):
        super(QueuedNotificationListener, self).__init__(mePeer)
        self._notificationQueue: asyncio.Queue = None

    def setQueue(self, notificationQueue):
        self._notificationQueue = notificationQueue

    async def enqueue(self, message):
        # print('equeue: ', end=',')
        # print(asyncio.get_running_loop())
        await self._notificationQueue.put(Notification(None, message['method'], message['data']))

    async def dequeue(self):
        # print('dequeue: ', end=',')
        # print(asyncio.get_running_loop())
        return await self._notificationQueue.get()

    # for statistic and monitor purpose
    def queueSize(self):
        return self._notificationQueue.qsize()

    def resetQueue(self, notificationQueue):
        self._notificationQueue = notificationQueue

    @abstractmethod
    async def runLoop(self, notificationQueue: asyncio.Queue):
        pass


class BandwidthNotificationListener(QueuedNotificationListener):
    def __init__(self, mePeer: Peer):
        super(BandwidthNotificationListener, self).__init__(mePeer)

    async def runLoop(self, notificationQueue: asyncio.Queue):
        super().setQueue(notificationQueue)
        # print('runLoop: ', end=',')
        # print(asyncio.get_running_loop())
        while True:
            message = await self.dequeue()
            if message.method == MessageType.SERVER_NOTIFICATION_downlinkBwe.value:
                await self.onDownlinkBwe(message)
            else:
                pass

    # high frequency
    async def onDownlinkBwe(self, message: Notification):
        logger.debug('notification: %s', message)


class PeerNotificationListener(QueuedNotificationListener):
    def __init__(self, mePeer: Peer):
        super(PeerNotificationListener, self).__init__(mePeer)

    async def runLoop(self, notificationQueue: asyncio.Queue):
        super().setQueue(notificationQueue)
        # print('runLoop: ', end=',')
        # print(asyncio.get_running_loop())
        while True:
            message = await self.dequeue()
            if message.method == MessageType.SERVER_NOTIFICATION_activeSpeaker.value:
                speakPeer = self.mePeer.room.getPeerByPeerId(message.data['peerId'])
                await self.onActiveSpeaker(message, speakPeer)
            elif message.method == MessageType.SERVER_NOTIFICATION_newPeer.value:
                newPeer = self.mePeer.room.addPeer(peerId=message.data['id'],
                                                   data=PeerAppData(displayName=message.data['displayName'],
                                                                    device=message.data['device']))
                await self.onNewPeer(message, newPeer)
            elif message.method == MessageType.SERVER_NOTIFICATION_peerDisplayNameChanged.value:
                otherPeer = self.mePeer.room.getPeerByPeerId(message.data['peerId'])
                otherPeer.data.displayName = message.data['displayName']
                await self.onPeerDisplayNameChanged(message, otherPeer)
            elif message.method == MessageType.SERVER_NOTIFICATION_peerClosed.value:
                closedPeer = self.mePeer.room.removePeer(message.data['peerId'])
                await self.onPeerClosed(message, closedPeer)
            else:
                pass

    async def onNewPeer(self, message: Notification, newPeer: Peer):
        logger.debug('notification: %s, newPeer: %s', message, newPeer)

    # high frequency
    async def onActiveSpeaker(self, message: Notification, speakPeer: Peer):
        logger.debug('notification: %s, speakPeer: %s', message, speakPeer)

    async def onPeerDisplayNameChanged(self, message: Notification, otherPeer: Peer):
        logger.debug('notification: %s, otherPeer: %s', message, otherPeer)

    async def onPeerClosed(self, message: Notification, closedPeer: Peer):
        logger.debug('notification: %s, closedPeer: %s', message, closedPeer)


class ProducerNotificationListener(QueuedNotificationListener):
    def __init__(self, mePeer: Peer):
        super(ProducerNotificationListener, self).__init__(mePeer)

    async def runLoop(self, notificationQueue: asyncio.Queue):
        super().setQueue(notificationQueue)
        # print('runLoop: ', end='')
        # print(asyncio.get_running_loop())
        while True:
            message = await self.dequeue()
            if message.method == MessageType.SERVER_NOTIFICATION_producerScore.value:
                await self.onProducerScore(message)
            else:
                pass

    # high frequency
    async def onProducerScore(self, message: Notification):
        logger.debug('notification: %s', message)


class ConsumerNotificationListener(QueuedNotificationListener):
    def __init__(self, mePeer: Peer):
        super(ConsumerNotificationListener, self).__init__(mePeer)

    async def runLoop(self, notificationQueue: asyncio.Queue):
        super().setQueue(notificationQueue)
        # print('runLoop: ', end='')
        # print(asyncio.get_running_loop())
        while True:
            message = await self.dequeue()
            otherPeer = self.mePeer.room.getPeerByConsumerId(message.data['consumerId'])
            if message.method == MessageType.SERVER_NOTIFICATION_consumerScore.value:
                await self.onConsumerScore(message, otherPeer)
            elif message.method == MessageType.SERVER_NOTIFICATION_consumerLayersChanged.value:
                await self.onConsumerLayersChanged(message, otherPeer)
            elif message.method == MessageType.SERVER_NOTIFICATION_consumerPaused.value:
                await self.onConsumerPaused(message, otherPeer)
            elif message.method == MessageType.SERVER_NOTIFICATION_consumerResumed.value:
                await self.onConsumerResumed(message, otherPeer)
            elif message.method == MessageType.SERVER_NOTIFICATION_consumerClosed.value:
                await self.onConsumerClosed(message, otherPeer)
            else:
                pass

    async def onConsumerLayersChanged(self, message: Notification, otherPeer: Peer):
        logger.debug('notification: %s, otherPeer: %s', message, otherPeer)

    # high frequency
    async def onConsumerScore(self, message: Notification, otherPeer: Peer):
        logger.debug('notification: %s, otherPeer: %s', message, otherPeer)

    async def onConsumerPaused(self, message: Notification, otherPeer: Peer):
        logger.debug('notification: %s, otherPeer: %s', message, otherPeer)

    async def onConsumerResumed(self, message: Notification, otherPeer: Peer):
        logger.debug('notification: %s, otherPeer: %s', message, otherPeer)

    async def onConsumerClosed(self, message: Notification, otherPeer: Peer):
        logger.debug('notification: %s, otherPeer: %s', message, otherPeer)


class DataConsumerNotificationListener(QueuedNotificationListener):
    def __init__(self, mePeer: Peer):
        super(DataConsumerNotificationListener, self).__init__(mePeer)

    async def runLoop(self, notificationQueue: asyncio.Queue):
        super().setQueue(notificationQueue)
        # print('runLoop: ', end='')
        # print(asyncio.get_running_loop())
        while True:
            message = await self.dequeue()
            if message.method == MessageType.SERVER_NOTIFICATION_dataConsumerClosed.value:
                otherPeer = self.mePeer.room.getPeerByDataConsumerId(message.data['dataConsumerId'])
                await self.onDataConsumerClosed(message, otherPeer)
            else:
                pass

    async def onDataConsumerClosed(self, message: Notification, otherPeer: Peer):
        logger.debug('notification: %s, otherPeer: %s', message, otherPeer)

    def onMessage(self, otherPeer: Peer, message: str, label, protocol, appData):
        logger.debug('message from %s: %s, label:%s, protocol: %s, appData: %s',
                     otherPeer, message, label, protocol, appData)
