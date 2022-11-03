from .room_peer import Peer


class MediasoupListener:
    """
    top abstract class for ConsumerRequestListener and QueuedNotificationListener,
    with the information of current peer
    """

    def __init__(self, mePeer: Peer):
        self._mePeer = mePeer

    @property
    def mePeer(self) -> Peer:
        return self._mePeer

    @mePeer.setter
    def mePeer(self, mePeer):
        self._mePeer = mePeer
