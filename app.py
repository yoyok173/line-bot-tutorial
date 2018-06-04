import requests
import re, json, urllib, urllib.parse, pytz
import random
import configparser
from bs4 import BeautifulSoup
from flask import Flask, request, abort
from imgurpython import ImgurClient

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

app = Flask(__name__)
config = configparser.ConfigParser()
config.read("config.ini")

line_bot_api = LineBotApi(config['line_bot']['Channel_Access_Token'])
handler = WebhookHandler(config['line_bot']['Channel_Secret'])
client_id = config['imgur_api']['Client_ID']
client_secret = config['imgur_api']['Client_Secret']
album_id = config['imgur_api']['Album_ID']
API_Get_Image = config['other_api']['API_Get_Image']


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    # print("body:",body)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'ok'


def pattern_mega(text):
    patterns = [
        'mega', 'mg', 'mu', 'ＭＥＧＡ', 'ＭＥ', 'ＭＵ',
        'ｍｅ', 'ｍｕ', 'ｍｅｇａ', 'GD', 'MG', 'google',
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True



@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("event.reply_token:", event.reply_token)
    print("event.message.text:", event.message.text)
    if event.message.text == 'id':
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(
                    text='id: ' + event.source.user_id
                )
            ]
        )
        return 0
    if event.message.text == "test":
        profile = line_bot_api.get_group_member_profile(event.source.group_id, event.source.user_id)
        url = profile.picture_url
        image_message = ImageSendMessage(
            original_content_url=url,
            preview_image_url=url
        )
        line_bot_api.reply_message(
            event.reply_token, image_message)
        return 0
    if event.message.text == '/profilku':
		if isinstance(event.source, SourceGroup):
			try:
				profile = line_bot_api.get_group_member_profile(event.source.group_id, event.source.user_id)
				result = ("Display name: " + profile.display_name + "\n" +
						  "Profile picture: " + profile.picture_url + "\n" +
						  "User_ID: " + profile.user_id)
			except LineBotApiError:
				pass	
			line_bot_api.reply_message(
				event.reply_token,
				TextSendMessage(result))
            return 0

@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker_message(event):
    print("package_id:", event.message.package_id)
    print("sticker_id:", event.message.sticker_id)
    # ref. https://developers.line.me/media/messaging-api/sticker_list.pdf
    sticker_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 21, 100, 101, 102, 103, 104, 105, 106,
                   107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125,
                   126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 401, 402]
    index_id = random.randint(0, len(sticker_ids) - 1)
    sticker_id = str(sticker_ids[index_id])
    print(index_id)
    sticker_message = StickerSendMessage(
        package_id='1',
        sticker_id=sticker_id
    )
    line_bot_api.reply_message(
        event.reply_token,
        sticker_message)

@handler.add(PostbackEvent)
def handle_postback(event):
    if event.postback.data == 'update':
        the_day = event.postback.params['date']
        last_date = datetime.strptime(the_day,"%Y-%m-%d")
        period = last_date + timedelta(days=28) #月經日期是第一天加上週期
        preg = last_date + timedelta(days=10) #經期來後10天開始的一周內容易懷孕
        diet = last_date + timedelta(days=7) #經期來後7天開始的一周內容易懷孕
        bra = last_date + timedelta(days=17)

        the_id = event.source.user_id
        profile = line_bot_api.get_profile(the_id)
        user_name = profile.display_name

        content = ''
        content += user_name + ' 你好~'
        content += '已成功紀錄你最近來的日期' + event.postback.params['date'] + '\n\n'
        content += '預計下一次差不多會是' + period.strftime("%m/%d") + '來 (σ`・∀・)σ\n\n'
        content += preg.strftime("%m/%d") + ' 開始的一週很容易懷孕 (╯°Д°)╯ ┻━┻\n\n'
        content += diet.strftime("%m/%d") + ' 開始的一週內少吃多動會瘦很快唷!!\n☜（ﾟ∀ﾟ☜）!!\n\n'
        content += bra.strftime("%m/%d") + ' 開始的一週多按摩奶奶會長很大唷\n\n'


        auth_json_path = 'google_sheet.json'
        gss_scopes = ['https://spreadsheets.google.com/feeds']
        gss_client = google_sheet.auth_gss_client(auth_json_path, gss_scopes)
        spreadsheet_key = '1Q4hWEVjTB-rdc7HAi_Yc_cF4uymjfPHe70Cc36fLHyM'

        google_sheet.update_sheet(gss_client, spreadsheet_key, the_id, the_day)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=content))



    elif event.postback.data == 'contact_me':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='找我嗎(〃▽〃)?'))
    

if __name__ == '__main__':
    app.run()
