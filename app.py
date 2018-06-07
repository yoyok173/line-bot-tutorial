import requests, pafy, wikipedia
import re, json, urllib, urllib.parse, pytz
import random
import time
from kbbi import KBBI
from argparse import ArgumentParser
from time import sleep
import configparser
from urbandictionary_top import udtop
from googletrans import Translator
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
def split1(text):
    return text.split('/wolfram ', 1)[-1]
    
def split2(text):
    return text.split('/kbbi ', 1)[-1]
    
def split3(text):
    return text.split('/echo ', 1)[-1]
def split4(text):
    return text.split('/wolframs ', 1)[-1]

def split5(text):
    return text.split('/trans ', 1)[-1]

def split6(text):
    return text.split('/wiki ', 1)[-1]

def split7(text):
    return text.split('/wikilang ', 1)[-1]
    
def split8(text):
    return text.split('/urban ', 1)[-1]
def split9(text):
    return text.split('/ox ', 1)[-1]

def split10(text):
    return text.split('/yt-mp4: ', 1)[-1]

def ox(keyword):
    oxdict_appid = ('7dff6c56')
    oxdict_key = ('41b55bba54078e9fb9f587f1b978121f')
    
    word = quote(keyword)
    url = ('https://od-api.oxforddictionaries.com:443/api/v1/entries/en/{}'.format(word))
    req = requests.get(url, headers={'app_id': oxdict_appid, 'app_key': oxdict_key})
    if "No entry available" in req.text:
        return 'No entry available for "{}".'.format(word)
    req = req.json()
    result = ''
    i = 0
    for each_result in req['results']:
        for each_lexEntry in each_result['lexicalEntries']:
            for each_entry in each_lexEntry['entries']:
                for each_sense in each_entry['senses']:
                    if 'crossReferenceMarkers' in each_sense:
                        search = 'crossReferenceMarkers'
                    else:
                        search = 'definitions'
                    for each_def in each_sense[search]:
                        i += 1
                        result += '\n{}. {}'.format(i, each_def)
    if i == 1:
        result = 'Definition of {}:\n'.format(keyword) + result[4:]
    else:
        result = 'Definitions of {}:'.format(keyword) + result
    return result

def wolfram(query):
    wolfram_appid = ('83L4JP-TWUV8VV7J7')
    url = 'https://api.wolframalpha.com/v2/result?i={}&appid={}'
    return requests.get(url.format(quote(query), wolfram_appid)).text
    
def wolframs(query):
    wolfram_appid = ('83L4JP-TWUV8VV7J7')
    url = 'https://api.wolframalpha.com/v2/simple?i={}&appid={}'
    return url.format(quote(query), wolfram_appid)

def trans(word):
    sc = 'en'
    to = 'id'
    
    if word[0:].lower().strip().startswith('sc='):
        sc = word.split(', ', 1)[0]
        sc = sc.split('sc=', 1)[-1]
        word = word.split(', ', 1)[1]

    if word[0:].lower().strip().startswith('to='):
        to = word.split(', ', 1)[0]
        to = to.split('to=', 1)[-1]
        word = word.split(', ', 1)[1]
        
    if word[0:].lower().strip().startswith('sc='):
        sc = word.split(', ', 1)[0]
        sc = sc.split('sc=', 1)[-1]
        word = word.split(', ', 1)[1]
        
    return translator.translate(word, src=sc, dest=to).text
    
def wiki_get(keyword, set_id, trim=True):
    try:
        wikipedia.set_lang(wiki_settings[set_id])
    except KeyError:
        wikipedia.set_lang('en')
    try:
        result = wikipedia.summary(keyword)
    except wikipedia.exceptions.DisambiguationError:
        articles = wikipedia.search(keyword)
        result = "{} disambiguation:".format(keyword)
        for item in articles:
            result += "\n{}".format(item)
    except wikipedia.exceptions.PageError:
        result = "{} not found!".format(keyword)
    else:
        if trim:
            result = result[:2000]
            if not result.endswith('.'):
                result = result[:result.rfind('.')+1]
    return result
    
def wiki_lang(lang, set_id):
    langs_dict = wikipedia.languages()
    if lang in langs_dict.keys():
        wiki_settings[set_id] = lang
        return ("Language has been changed to {} successfully."
                .format(langs_dict[lang]))
    return ("{} not available!\n"
            "See meta.wikimedia.org/wiki/List_of_Wikipedias for "
            "a list of available languages, and use the prefix "
            "in the Wiki column to set the language."
            .format(lang))  
def yt(query):
    with requests.session() as s:
         isi = []
         if query == "":
             query = "S1B tanysyz"   
         s.headers['user-agent'] = 'Mozilla/5.0'
         url    = 'http://www.youtube.com/results'
         params = {'search_query': query}
         r    = s.get(url, params=params)
         soup = BeautifulSoup(r.content, 'html5lib')
         for a in soup.select('.yt-lockup-title > a[title]'):
            if '&list=' not in a['href']:
                if 'watch?v' in a['href']:
                    b = a['href']
                    isi += ['https://www.youtube.com' + b]
         return isi
def find_kbbi(keyword, ex=True):
    try:
        entry = KBBI(keyword)
    except KBBI.TidakDitemukan as e:
        result = str(e)
    else:
        result = "Definisi {}:\n".format(keyword)
        if ex:
            result += '\n'.join(entry.arti_contoh)
        else:
            result += str(entry)
    return result

def urban(keyword, ex=True):
    try:
        entry = udtop(keyword)
    except (TypeError, AttributeError, udtop.TermNotFound) :
        result = "{} definition not found in urbandictionary.".format(keyword)
    else:
        result = "{} definition:\n".format(keyword)
        if ex:
            result += str(entry)
        else:
            result += entry.definition
    return result


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("event.reply_token:", event.reply_token)
    print("event.message.text:", event.message.text)
    text=event.message.text
    if event.message.text == 'id':
        line_bot_api.reply_message(
            event.reply_token, [
                TextSendMessage(
                    text='id: ' + event.source.user_id
                )
            ]
        )
        return 0
    elif text == '/help':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage('Hai kak..ketik /cmd untuk menu lainnya.'))
    
    elif text == '/sp':
        start = time.time()
        elapsed_time = time.time() - start
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(format(str(elapsed_time))))
    elif text == '/leave':
        if isinstance(event.source, SourceGroup):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage('I am leaving the group...'))
            line_bot_api.leave_group(event.source.group_id)
        
        elif isinstance(event.source, SourceRoom):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage('I am leaving the group...'))
            line_bot_api.leave_room(event.source.room_id)
            
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage('>_< cannot do...'))
    
    elif text == '/about':
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage("Hai kak..nama saya Shin Chan \n"
                                "saya akan membuat obrolan kamu jadi makin seru."))
    
    elif text == '/cmd':
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage("Without parameters: \n"
                                "/about, /help, /profile, /leave, /lang \n"
                                "/confirm, /buttons, /search image, \n"
                                "/manga, /dots, /track, /bet \n"
                                "/image_carousel, /imagemap \n"
                                "\n"
                                "With parameters: \n"
                                "/echo, /kbbi, /wolfram, /wolframs, \n"
                                "/trans, /wiki, /wikilang, /urban, /ox"))
    
    elif text == '/lang':
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage("Language for translation see here \n"
                                "https://github.com/Vetrix/ZERO/blob/master/Lang.txt"))
    
    elif text == '/manga':
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage("mangaku.in"))
    
    #elif text == '/dots':
    #   line_bot_api.reply_message(
    #           event.reply_token,
    #           TextSendMessage("https://www.instagram.com/dotaindonesia2/"))
    #
    #elif text == '/track':
    #   line_bot_api.reply_message(
    #           event.reply_token,
    #           TextSendMessage("http://dota2.prizetrac.kr/international2018"))
    #
    #elif text == '/bet':
    #   line_bot_api.reply_message(
    #           event.reply_token,
    #           TextSendMessage("dota2.com/predictions"))
    
    elif text == '/search image':
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage("Try this up \n"
                                "https://reverse.photos/"))
    elif event.message.text == "/ppku":
            profile = line_bot_api.get_group_member_profile(event.source.group_id, event.source.user_id)
            url = profile.picture_url
            image_message = ImageSendMessage(
                original_content_url=url,
                preview_image_url=url
            )
            line_bot_api.reply_message(
                event.reply_token, image_message)
    elif text == '/profilku':
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
            
        
        elif isinstance(event.source, SourceRoom):
            try:
                profile = line_bot_api.get_room_member_profile(event.source.room_id, event.source.user_id)
                result = ("Display name: " + profile.display_name + "\n" +
                          "Profile picture: " + profile.picture_url + "\n" +
                          "User_ID: " + profile.user_id)
            except LineBotApiError:
                pass    
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(result))
            
                
        else:
            try:
                profile = line_bot_api.get_profile(event.source.user_id)
                result = ("Display name: " + profile.display_name + "\n" +
                          "Profile picture: " + profile.picture_url + "\n" +
                          "User_ID: " + profile.user_id)
                if profile.status_message:
                    result += "\n" + "Status message: " + profile.status_message
            except LineBotApiError:
                pass
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(result))
    elif text=='/kbbi':
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage('command /kbbi {input}'))
    
    elif text=='/urban':
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage('command /urban {input}'))
    
    elif text=='/ox':
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage('command /ox {input}'))
    
    elif text=='/wolfram':
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage('command /wolfram {input}'))
                
    elif text=='/trans':
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage('command /trans sc={}, to={}, {text}'))
    
    elif text=='/wiki':
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage('command /wiki {text}'))
                
    elif text=='/wikilang':
        line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage('command /wikilang {language_id}'))
    
    elif text == '/confirm':
        confirm_template = ConfirmTemplate(text='Do it?', actions=[
            MessageTemplateAction(label='Yes', text='Yes!'),
            MessageTemplateAction(label='No', text='No!'),
            ])
        template_message = TemplateSendMessage(
            alt_text='Confirm alt text', template=confirm_template)
        line_bot_api.reply_message(event.reply_token, template_message)
    
    elif text == '/buttons':
        buttons_template = ButtonsTemplate(
            title='My buttons sample', text='Hello, my buttons', actions=[
                URITemplateAction(
                    label='Go to line.me', uri='https://line.me'),
                PostbackTemplateAction(label='ping', data='ping'),
                PostbackTemplateAction(
                    label='ping with text', data='ping',
                    text='ping'),
                MessageTemplateAction(label='Translate Rice', text='米')
            ])
        template_message = TemplateSendMessage(
            alt_text='Buttons alt text', template=buttons_template)
        line_bot_api.reply_message(event.reply_token, template_message)
    
    elif text == '/image_carousel':
        image_carousel_template = ImageCarouselTemplate(columns=[
            ImageCarouselColumn(image_url='https://via.placeholder.com/1024x1024',
                                action=DatetimePickerTemplateAction(label='datetime',
                                                                    data='datetime_postback',
                                                                    mode='datetime')),
            ImageCarouselColumn(image_url='https://via.placeholder.com/1024x1024',
                                action=DatetimePickerTemplateAction(label='date',
                                                                    data='date_postback',
                                                                    mode='date'))
        ])
        template_message = TemplateSendMessage(
            alt_text='ImageCarousel alt text', template=image_carousel_template)
        line_bot_api.reply_message(event.reply_token, template_message)
        
    elif text == '/imagemap':
        pass
    
    elif text[0:].lower().strip().startswith('/wolfram '):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(wolfram(split1(text))))
            
    elif text[0:].lower().strip().startswith('/wolframs '):
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(original_content_url= wolframs(split4(text)),
                                preview_image_url= wolframs(split4(text))))

    elif text[0:].lower().strip().startswith('/kbbi '):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(find_kbbi(split2(text))))
            
    elif text[0:].lower().strip().startswith('/urban '):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(urban(split8(text))))
            
    elif text[0:].lower().strip().startswith('/ox '):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(ox(split9(text))))
            
    elif text[0:].lower().strip().startswith('/echo ') :
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(split3(text)))
            
    elif text[0:].lower().strip().startswith('/trans ') :
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(trans(split5(text))))
    
    elif text[0:].lower().strip().startswith('/wiki ') :
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(wiki_get(split6(text), set_id=set_id)))
            
    elif text[0:].lower().strip().startswith('/wikilang ') :
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(wiki_lang(split7(text), set_id=set_id)))
    elif text[0:].lower().strip().startswith('/yt-mp4: ') :
        query = text.split(":")
        if len(query) == 3:
            isi = yt(query[2])
            hasil = isi[int(query[1])-1]
        else:
            isi = yt(query[1])
            video = pafy.new(isi[0])
            best = video.getbest(preftype="mp4")
            s = best.url
            #video_message = VideoSendMessage(
                #   original_content_url=url,
                #   preview_image_url=video.thumb
            #)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(isi[0]))
            #line_bot_api.reply_message(
            #   event.reply_token, video_message)

#@handler.add(MessageEvent, message=StickerMessage)
#def handle_sticker_message(event):
#    print("package_id:", event.message.package_id)
#    print("sticker_id:", event.message.sticker_id)
#    # ref. https://developers.line.me/media/messaging-api/sticker_list.pdf
#    sticker_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 21, 100, 101, 102, 103, 104, 105, 106,
#                   107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125,
#                   126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 401, 402]
#    index_id = random.randint(0, len(sticker_ids) - 1)
#    sticker_id = str(sticker_ids[index_id])
#    print(index_id)
#    sticker_message = StickerSendMessage(
#        package_id='1',
#        sticker_id=sticker_id
#    )
#    line_bot_api.reply_message(
#        event.reply_token,
#        sticker_message)

@handler.add(JoinEvent)
def handle_join(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='Hi, my name is Shin Chan. Hope we can make some fun in this ' + event.source.type))
        
@handler.add(LeaveEvent)
def handle_leave():
    app.logger.info("Bye")

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
