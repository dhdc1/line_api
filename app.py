# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from __future__ import unicode_literals

import errno
import os
import sys
import tempfile
import mysql.connector
import random
import requests
import json

from flask import Flask, request, abort, send_from_directory, render_template
from werkzeug.middleware.proxy_fix import ProxyFix

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    SourceUser, SourceGroup, SourceRoom,
    TemplateSendMessage, ConfirmTemplate, MessageAction,
    ButtonsTemplate, ImageCarouselTemplate, ImageCarouselColumn, URIAction,
    PostbackAction, DatetimePickerAction,
    CameraAction, CameraRollAction, LocationAction,
    CarouselTemplate, CarouselColumn, PostbackEvent,
    StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
    ImageMessage, VideoMessage, AudioMessage, FileMessage,
    UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent,
    FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent,
    TextComponent, SpacerComponent, IconComponent, ButtonComponent,
    SeparatorComponent, QuickReply, QuickReplyButton,
    ImageSendMessage)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1)

# เปลี่ยนเป็นของ chanel ตัวเอง
channel_secret = "d2d9f8b67a4837db81ced2cb47651a4f"
channel_access_token = "ya/3TTMl4IK706X8nqW3A+6qXzRwWwet0LJdplhFtncpNC04cuUL3t25wGPdM9qsggUyQ0Y+H0xu+IpvVCDs2cMm15/A0rPTkiYDwH0vxXpoVnxbImierkix9zeybtxdSgbS4jZEpBCs2ZVLTCPhhwdB04t89/1O/w1cDnyilFU="
api_reply = "https://api.line.me/v2/bot/message/reply"

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')


# function for create tmp dir for download content
def make_static_tmp_dir():
    try:
        os.makedirs(static_tmp_path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(static_tmp_path):
            pass
        else:
            raise


def get_profile(event):
    profile = line_bot_api.get_profile(event.source.user_id)
    return profile.display_name


def con_db():
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="112233",
        database="his",
        port=3306
    )
    return db


def line_message_reply(event, messages):
    payload = {
        'replyToken': event.reply_token,
        "messages": messages
    }
    headers = {
        'Authorization': 'Bearer {0}'.format(channel_access_token),
        'Content-Type': 'application/json'
    }
    r = requests.post(api_reply, data=json.dumps(payload), headers=headers)
    print(r)


def is_member(event):
    line_id = event.source.user_id
    sql = "select count(cid) from line where line_id ='{0}'".format(line_id)
    db = con_db()
    cursor = db.cursor()
    cursor.execute(sql)
    row = cursor.fetchone()

    if row[0] > 0:
        return True
    else:
        return False


# web request
@app.route("/regis", methods=['POST', 'GET'])
def regis():
    if request.method == 'POST':
        cid = request.form['cid']
        line_id = request.form['line_id']
        print(cid, line_id)
        return 'OK'

    elif request.method == 'GET':
        return render_template("regis.html")


# webhook
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        print("\n")
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    if not is_member(event):
        line_message_reply(event, [
            {
                'type': 'text',
                'text': '{0} is not member.'.format(get_profile(event))
            }
        ])

    text = event.message.text
    if text == 'test':
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(text=event.message.text),
                TextSendMessage(text="line_id=" + event.source.user_id),
                TextSendMessage(text=get_profile(event)),
                StickerSendMessage(package_id=1, sticker_id=110),
                LocationSendMessage(address='ที่ไหนซักแห่ง', latitude='16.737367', longitude='100.273091',
                                    title='ส่งพิกัดให้นะ'),

            ]
        )

    if text == 'q':
        quick_reply = QuickReply(items=[
            QuickReplyButton(action=PostbackAction(label="กคลิกันดูสิ", data='ping')),
            QuickReplyButton(action=DatetimePickerAction(label='วันที่', mode='date', data='date1')),
        ])
        line_bot_api.reply_message(event.reply_token, [
            TextSendMessage(text='ได้เลย', quick_reply=quick_reply)
        ])

    if text == 'p':
        line_message_reply(event, [
            {
                "type": "text",
                "text": "Wow Wow"
            },
            {
                "type": "template",
                "altText": "this is a carousel template",
                "template": {
                    "type": "carousel",
                    "actions": [],
                    "columns": [
                        {
                            "text": "Text",
                            "actions": [
                                {
                                    "type": "uri",
                                    "label": "URL",
                                    "uri": "http://google.com?q=" + event.source.user_id
                                },
                                {
                                    "type": "message",
                                    "label": "Action 2",
                                    "text": "Action 2"
                                }
                            ]
                        },
                        {
                            "text": "Text",
                            "actions": [
                                {
                                    "type": "message",
                                    "label": "Action 1",
                                    "text": "Action 1"
                                },
                                {
                                    "type": "message",
                                    "label": "Action 2",
                                    "text": "Action 2"
                                }
                            ]
                        }
                    ]
                }
            },
            {
                "type": "template",
                "altText": "this is a buttons template",
                "template": {
                    "type": "buttons",
                    "actions": [
                        {
                            "type": "message",
                            "label": "Action 1",
                            "text": "Action 1"
                        },
                        {
                            "type": "message",
                            "label": "Action 2",
                            "text": "Action 2"
                        }
                    ],
                    "title": "Title",
                    "text": "Text"
                }
            },
            {
                "type": "template",
                "altText": "this is a confirm template",
                "template": {
                    "type": "confirm",
                    "actions": [
                        {
                            "type": "message",
                            "label": "Yes",
                            "text": "Yes"
                        },
                        {
                            "type": "message",
                            "label": "No",
                            "text": "No"
                        }
                    ],
                    "text": "Continue?"
                }
            },
            {
                "type": "sticker",
                "packageId": "1",
                "stickerId": "100"
            }
        ])


@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        LocationSendMessage(
            title=event.message.title, address=event.message.address,
            latitude=event.message.latitude, longitude=event.message.longitude
        )
    )


@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        StickerSendMessage(
            package_id=event.message.package_id,
            sticker_id=event.message.sticker_id)
    )


@handler.add(PostbackEvent)
def handle_postback(event):
    if event.postback.data == 'ping':
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text='pong'))
    if event.postback.data == 'date1':
        line_bot_api.reply_message(event.reply_token, [
            TextSendMessage(text='date1' + event.postback.params['date'])
        ])


@handler.add(MessageEvent, message=(ImageMessage, VideoMessage, AudioMessage))
def handle_content_message(event):
    if isinstance(event.message, ImageMessage):
        ext = 'jpg'
    elif isinstance(event.message, VideoMessage):
        ext = 'mp4'
    elif isinstance(event.message, AudioMessage):
        ext = 'm4a'
    else:
        return

    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix=ext + '-', delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name

    dist_path = tempfile_path + '.' + ext
    dist_name = os.path.basename(dist_path)
    os.rename(tempfile_path, dist_path)

    url = request.url_root + 'static/tmp/' + dist_name

    line_bot_api.reply_message(
        event.reply_token, [
            TextSendMessage(text='Save content.'),
            TextSendMessage(text=request.host_url + "static/tmp/" + dist_name),
            ImageSendMessage(url, url)
        ])


@handler.add(FollowEvent)  # add ใหม่  / unblock
def handle_follow(event):
    # copy
    liff_url = "line://app/1570842118-JZMKOLgP"  # ใช้ของตัวเอง
    buttons_template = ButtonsTemplate(
        title='ลงทะเบียน', text='หากท่านไม่ลงทะเบียนจะไม่สามารถใช้บริการได้', actions=[
            URIAction(label='>> คลิกเพื่อลงทะเบียน <<', uri=liff_url)
        ])
    template_message = TemplateSendMessage(
        alt_text='การลงทะเบียน', template=buttons_template)
    line_bot_api.reply_message(event.reply_token, template_message)
    # endcopy


@handler.add(UnfollowEvent)  # โดน block
def handle_unfollow(event):
    app.logger.info("Got Unfollow event")
    print(event.source.user_id + " Un followed.")


@handler.add(JoinEvent)
def handle_join(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='Joined this ' + event.source.type))


@handler.add(LeaveEvent)
def handle_leave():
    app.logger.info("Got leave event")


@handler.add(BeaconEvent)
def handle_beacon(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text='Got beacon event. hwid={}, device_message(hex string)={}'.format(
                event.beacon.hwid, event.beacon.dm)))


@app.route('/static/<path:path>')
def send_static_content(path):
    return send_from_directory('static', path)


if __name__ == "__main__":
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # create tmp dir for download content
    make_static_tmp_dir()
    app.run(debug=True, host='0.0.0.0', port=8000)
