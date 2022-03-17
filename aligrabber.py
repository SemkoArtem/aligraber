from admitad.items import deeplinks
import vk
import re
import time
import json
import telebot
import requests
from admitad import api, items
from telebot.types import InputMediaPhoto
from requests.structures import CaseInsensitiveDict

file = open('./config.json')
config = json.load(file)

session = vk.Session(access_token=config['token_vk'])
vk_api = vk.API(session)

bot = telebot.TeleBot(config['token_tg'])

offset = config['offset']

def send_post_in_tg (post):
    media_group = []
    num = 0
    
    for num in range(len(post['photo_urls'])):
        if num == 0:
            media_group.append(InputMediaPhoto(post['photo_urls'][num], caption = post['text_post']))
            time.sleep(1)
        else: 
            media_group.append(InputMediaPhoto(post['photo_urls'][num]))
            time.sleep(1)
    time.sleep(1)
    bot.send_media_group(config['chanel_name'], media=media_group)
    print("sendet now",post['text_post'], post['photo_urls'])
    return 0

def writer_idposts(post_id):
    fp = open('./id_posts.txt', "r+")
    lines = fp.readlines()
    fp.close()
    lines.insert( 0 , str(post_id) + '\n')
    fp = open('./id_posts.txt', "w+")
    fp.writelines(lines)
    fp.close()
    return 0

def autorizated ():
    headers = CaseInsensitiveDict()
    headers["Authorization"] = "Basic " + config['base64']
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    data = "grant_type=client_credentials&client_id=" + config['client_id'] + "&scope=short_link"
    resp = requests.post("https://api.admitad.com/token/", headers=headers, data=data)
    json_info = json.loads(resp.text)
    return json_info['access_token']

def get_short_link(link):
    headers = CaseInsensitiveDict()
    headers["Authorization"] = "Bearer " + autorizated ()
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    data = "link=" + link
    data = data.replace('subid=' + config['subid'] + '&', '')
    time.sleep(1)
    json_short_link = requests.post("https://api.admitad.com/shortlink/modify/", headers=headers,  data=data)
    json_data = json.loads(json_short_link.text)
    print(json_data['short_link'])
    return json_data['short_link']

def cheker_posts(post_id):
    with open('./id_posts.txt', "r", encoding="utf-8") as fp:
        id_posts = fp.readlines()
        fp.close()
    how_lines_id_posts = len(id_posts)
    i=0
    if how_lines_id_posts != 0:
        while i <= how_lines_id_posts:
            if str(post_id) == id_posts[i-1].rstrip('\n'):
                return False
            i+=1 
    writer_idposts(post_id)
    return True

def admitad_deep(ali_url):
    scope = ' '.join(set([items.DeeplinksManage.SCOPE]))
    client = api.get_oauth_client_client(
    config['client_id'],
    config['client_secret'],
    scope,
)
    deep_link = client.DeeplinksManage.create(config['websites'], config['offers'], ulp=ali_url, subid=config['subid'])
    short_link = get_short_link(deep_link[0])

    return short_link

def write_in_file(posts):
    original_url = re.findall("(?P<url>https?://[^\s]+)", posts['text_post'])
    i=0
    while i < len(original_url):
        responce_url = requests.get(original_url[i]).url
        ali_url = responce_url.split('?')
        final_url = admitad_deep(ali_url)
        posts['text_post'] = posts['text_post'].replace(original_url[i],final_url)
        final_url = ''
        i+=1

    #with open('./posts.json','a') as file:
        #json.dump(posts,file, indent=4, ensure_ascii=True)
    send_post_in_tg(posts)
    return 0

def find_post(owner_id,offset):

    while offset != 0:
        wall_posts = vk_api.wall.get(owner_id = owner_id, offset = offset, count = config['count_post'], v = 5.81)
        time.sleep(1)
        for post in wall_posts['items']:
                id_post = ''
                text_post = ''
                photo_urls = []
                gif_urls = []
                offset-=1
                if cheker_posts(post['id']) == True:
                    id_post = str(post['id'])
                    text_post = str(post['text'])
                    if "attachments" in post:
                        for attachments in post ['attachments']:
                            if attachments ['type'] == 'doc':
                                for doc in attachments ['doc'] ['ext']:
                                    if attachments ['doc'] ['ext'] == 'gif':
                                        gif_urls = attachments ['doc'] ['url']
                            if attachments ['type'] == 'photo':
                                for photo in attachments ['photo'] ['sizes']:
                                    if photo ['type'] == 'x' :
                                        photo_urls.append(str(photo['url']))
                    time.sleep(1)
                    inf_posts = {
                        "owner_id": owner_id,
                        "id_post": id_post,
                        "text_post": text_post,
                        "gif_urls": gif_urls,
                        "photo_urls": photo_urls
                        
                    }
                    write_in_file(inf_posts)
    return 0
               
def open_all_group(offset):
    owner_id = config['group_ids'] 
    how_lines = len(owner_id)
    i=0
    while i < how_lines:
        print("serch in group :", i+1)
        find_post(owner_id[i],offset)
        i+=1
    #print(posts)
    return 0                                                           

while True:
    open_all_group(offset)
    print("waiting time: ", config['udate_time'])
    time.sleep(config['udate_time'])
       
bot.polling()