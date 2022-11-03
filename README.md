# Mediasoup-Client-PySDK (aka "smcdk")
a simple-to-use, pure python sdk of [mediasoup](https://mediasoup.org/) client, fork from [pymediasoup](https://github.com/skymaze/pymediasoup) and do more.

## Usage
For the purpose of to be an easy-to-use SDK, smcdk API design focus mainly on high level, and for users who know little about the official mediasoup client API. 

```python
from smcdk.api import *

mediasoup_client = MediasoupClient(...)
mediasoup_client.joinRoom(...)
mediasoup_client.play(...)
mediasoup_client.close()
```
more details, please see: examples/sdkApiDemo.py


## Why another mediasoup-client?( My Personal Option, for reference only)
There are several official and unofficial client implementations, but they are not quick and easy to run on all OS's desktop, so are not suitable to be a general SDK: 
1. official client with official dependency lib
- mediasoup-demo/aiortc: because it is based on Unix Socket, so it can't run in Windows
- mediasoup-demo/broadcasters: it is based on bash language, which is good at integrating command line tools, but is not good at developing new features
- mediasoup-demo/app: it can only run in browsers, and Electron-like desktop environment with less disk space occupation, or run in Node.js with more space occupation because of the node_modules directory
- mediasoup-broadcast-demo: it's quite hard to compile and link a libwebrtc dependency successfully on all OS platform, especially in China mainland's network environment

2. no-official client
pymediasoup is quite nice, but its API is a little hard to quick start as SDK

## Architecture & Design
Mediasoup Client contains:
- Mediasoup Signaler Interface: follow the semantics of mediasoup-demo/server
- Loop Tasks & Listeners: to tackle signaler request and notification from server side
- Room and Peer: a group of simple APIs to be integrated to Listeners
- Multimedia Runtime: a stateful mediasoup Device

Business Domain Based Listener Design
There are several business domain in SDK design:
Bandwidth, Peer, Producer, Consumer, DataConsumer, result in 2 request listeners
and 5 notification listeners, which their Respective interesting events to listen and tackle
1. Server Request
Consumer Listener event: newConsumer
DataConsumer Listener event: newDataConsumer
2. Server Notification
Bandwidth Listener event: downlinkBwe
Peer Listener event: newPeer, peerClosed, peerDisplayNameChanged, activeSpeaker
Producer Listener event: producerScore
Consumer Listener event: consumerLayersChanged, consumerScore, consumerClosed, consumerPaused, consumerResumed
DataConsumer Listener event: dataConsumerClosed

## Features
To be an easy-to-use sdk for mediasoup client development
- **quick to run**: as mentioned above
- **all os platform friendly**: as mentioned above
- **signaling pluggable**: based on the mediasoup's design goal of "signaling agnostic", 
    >Be signaling agnostic: do not mandate any signaling protocol.”
   
    (sited from [mediasoup :: Overview](https://mediasoup.org/documentation/overview/)). 
    smcdk provide an out-of-box ProtooSignaler furthermore. 
    Besides the default built-in signaler, which is used to communicate with mediasoup-demo/server, 
    you can provide your own MediasoupSignalerInterface implementation to meet your requirement.
- **listener customizable**: currently, you can customize 2 request listeners and 5 notification listeners 
## About Code Style
  You can see many Camel-Case-Style naming in my Python code, 
e.g. "getRouterRtpCapabilities", not "get_router_rtp_capabilities".
  The reason is not only that I began my career as a Java developer since 2008,
but also that I hope this SDK can be applied by those developers who use Python as a no-major language, 
and developers who have learned mediasoup by its demo app & server.
  Maybe sometime in the future, I'll change this naming to follow Python’s PEP8 rules.
## LICENSE
MIT

## Thanks
special thanks to pymediasoup, mediasoup, and aiortc projects
