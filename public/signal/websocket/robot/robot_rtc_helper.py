import argparse
import asyncio
import logging
import time

from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription
import requests
import platform
import os
import json

import cv2
import numpy as np
import websockets
from aiortc.contrib.media import MediaPlayer, MediaRelay
from aiortc.rtcrtpsender import RTCRtpSender


from_name = 'Robot'
to_name = 'Controller'
dc = None
async def setup_callbacks(lc : RTCPeerConnection, dc):
    #dc.onmessage = lambda e : print("Message from robot:", e.data, e)

    @dc.on("message")
    def on_message(message):
        if isinstance(message, str):
            print(message)

    @lc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is %s", lc.connectionState)
        if lc.connectionState == "failed":
            stay_alive = False
            await lc.close()
        if lc.connectionState == 'disconnected':
            stay_alive = False
            
    @lc.on("icecandidate")
    async def on_icecandidate(e):
        print("SDP:", json.dumps(lc.localDescription, separators=(',', ':')))
        
    @lc.on("datachannel")
    async def on_datachannel(e):
        dc = e
        print("Dc established")
        @dc.on("message")
        async def on_message(e):    
            print("from robot:", e.data)
        @dc.on("open")
        async def on_open(e):    
            print("Data Channel Connection opened on remote")
        
        
        








lc = RTCPeerConnection()
stay_alive = True
from aiortc.contrib.media import MediaPlayer, MediaRelay
from aiortc.rtcrtpsender import RTCRtpSender

ROOT = os.path.dirname(__file__)

def force_codec(lc, sender, forced_codec):
    kind = forced_codec.split("/")[0]
    codecs = RTCRtpSender.getCapabilities(kind).codecs
    transceiver = next(t for t in lc.getTransceivers() if t.sender == sender)
    transceiver.setCodecPreferences(
        [codec for codec in codecs if codec.mimeType == forced_codec]
    )
    
    

def channel_log(channel, t, message):
    print("channel(%s) %s %s" % (channel.label, t, message))
    


async def set_answer(answer):
    answer_wrapped = RTCSessionDescription(answer['sdp'], answer['type'])
    await lc.setRemoteDescription(answer_wrapped)


async def send_msg_to_client(msg): 
    global dc
    if dc: dc.send(msg)

async def get_offer(video_track):
    global dc
    dc = lc.createDataChannel("input")
    
    # from .my_track import NumpyVideoTrack
    if(video_track == None):
        import my_track
        video_track = my_track.VideoStreamTrack();
    video_sender = lc.addTrack(video_track)
    force_codec(lc, video_sender, 'video/h264')

    
    channel_log(dc, "-", "created by local party")

    await setup_callbacks(lc, dc)
    # print(dc.event_names)
    #lc.onicecandidate = lambda e : print("SDP:", json.dumps(lc.localDescription, separators=(',', ':'))); 
    offer = await lc.createOffer()
    await lc.setLocalDescription(offer)
    while True:
        print(f"icegatheringstate:{lc.iceGatheringState}")
        if lc.iceGatheringState == "complete":
            break
    req_body = {
        'type':lc.localDescription.type,
        'sdp':lc.localDescription.sdp,
        'from':from_name,
        'to':to_name
        }
    
    return req_body
    
