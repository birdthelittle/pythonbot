
import vk_api
import requests
import random
import string
import datetime
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
### from threading import Thread

### Used functions


# One of main functions for sending message to user.
# Takes an input two values: user id and text string

def write_msg(peer_id, msg):
    vk.method('messages.send', {'peer_id': peer_id, 'message': msg})
    send_log(str(peer_id)+': Message Send')

# One of main functions for writing every event to log
# Takes an input barely one value: text string

def send_log(msg):
    time_string = datetime.datetime.today().strftime('[%H:%M:%S]')
    print(time_string, msg)

# Secondary function for uploading photo and sending to user
# Takes an input two values: user id and filename string

def send_img(peer_id, img_name):
    link = vk.method("photos.getMessagesUploadServer")
    b = requests.post(link['upload_url'], files={'photo': open('tmp/'+img_name, 'rb')}).json()
    c = vk.method('photos.saveMessagesPhoto', {'photo': b['photo'], 'server': b['server'], 'hash': b['hash']})[0]
    d = "photo{}_{}".format(c['owner_id'], c['id'])
    vk.method('messages.send', {'peer_id': peer_id, 'attachment': d})

# Function for choice of suitable answer
# Takes an input one value: type of expected phrase

def respond_phrase(type):
    file = open('data/respond.txt', 'r', encoding='utf-8')
    phrases = [line.strip() for line in file]
    res = None

    if type == 'wait':
        res = phrases[random.randint(1, 9)]
    elif type == 'not':
        res = phrases[random.randint(21, 33)]
    elif type == 'start':
        res = phrases[41]
    elif type == 'sorry':
        res = phrases[42]
    elif type == 'request':
        res = phrases[43]
    elif type == 'success':
        res = phrases[44]
    elif type == 'oops':
        res = phrases[45]
    return res

# Main function for show current marks of the student
# Takes an input three values: student id, login and password

def show_marks(id, login, password):

    driver = webdriver.Chrome('C:\Program Files\ChromeDriver\chromedriver.exe')
    driver.implicitly_wait(10)
    driver.get("http://diary-db.kirov.ru/sch37/")

    elem = driver.find_element_by_name("user")
    elem.clear()
    elem.send_keys(login)

    elem = driver.find_element_by_name("password")
    elem.clear()
    elem.send_keys(password)

    i = 0
    elem = driver.find_element_by_class_name("x-btn-icon-small-left")

    while i < 10:
            elem.click()
            i += 1

    driver.refresh()
    write_msg(id, respond_phrase('wait'))

    # Page loading

    try:
        elem = driver.find_element_by_id("main-tab__mymarks")
    except BaseException:
        write_msg(id, respond_phrase('oops'))
        driver.close()
        return

    elem.click()

    elem = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "printer_1"))
    )
    time.sleep(5)
    elem.click()

    driver.switch_to_window(driver.window_handles[1])

    # Taking screenshot

    element = driver.find_element_by_tag_name("tbody")

    location = element.location
    size = element.size

    letters = string.ascii_lowercase
    photo_name = str(''.join(random.choice(letters) for i in range(8))) + '.png'
    driver.save_screenshot("tmp/{}".format(photo_name))

    x = location['x']
    y = location['y']
    width = location['x'] + size['width']
    height = location['y'] + size['height']

    im = Image.open("tmp/{}".format(photo_name))
    im = im.crop((int(x), int(y), int(width), int(height)))
    im.save("tmp/{}".format(photo_name))

    send_img(id, photo_name)

    driver.quit()
    os.remove("tmp/{}".format(photo_name))

# Authorization in VK.API

_TOKEN = None

if not _TOKEN:
    print("Please, insert VK_API_TOKEN!")
    quit()

vk = vk_api.VkApi(token=_TOKEN)
vk._auth_token()
send_log('Success auth!')

_values = {"offset": 0, "count": 20, "filter": "unanswered"}

# Main loop, manages of the logic, receives and answers on all requests

while True:
        response = vk.method('messages.getConversations', _values)

        if response['items']:
            for item in response['items']:
                _id = response['items'][0]['last_message']['from_id']
                _message = response['items'][0]['last_message']['text']
                send_log(str(_id) + ': Message received')

                # Message is received

                # Key phrase for start a dialog
                if _message == '/start':
                    write_msg(_id, respond_phrase('start'))

                # Key phrase for show current marks
                elif _message == '/marks':

                    file = open('data/users.txt', 'r')
                    isExist = False
                    _login = None
                    _password = None
                    for line in file:
                        if line.strip().split(':')[0] == str(_id):
                            isExist = True
                            _login = line.split(':')[1]
                            _password = line.split(':')[2]
                    file.close()

                    if isExist:
                        show_marks(_id, _login, _password)
                    else:
                        write_msg(_id, respond_phrase('sorry'))
                        write_msg(_id, respond_phrase('request'))

                elif _message == '/timetable':

                    file = open('data/timetable.txt', 'r')
                    list = [line.strip() for line in file]
                    file.close()
                    weekday = datetime.datetime.today().isoweekday() # from 1 to 7
                    # Sunday ==> Monday
                    if weekday == 7:
                        weekday = 1
                    msg = datetime.datetime.today().strftime("+++ %A +++<br>") + list[weekday * 2 - 1]
                    write_msg(_id, msg)

                elif _message == '/breaks':

                    file = open('data/breaks_schedule.txt', 'r')
                    list = [line.strip() for line in file]
                    file.close()
                    weekday = datetime.datetime.today().isoweekday() # from 1 to 7
                    if weekday == 6:
                        msg = datetime.datetime.today().strftime("+++ %A +++<br>") + list[3]
                        write_msg(_id, msg)
                    else:
                        msg = datetime.datetime.today().strftime("+++ %A +++<br>") + list[1]
                        write_msg(_id, msg)

                else:

                    # Else message is no phrase matches

                    if _message.find(':') > 0:

                        # WRITE LOG:PAS IN TXT

                        _login = _message.split(':')[0]
                        _password = _message.split(':')[1]

                        file = open('data/users.txt', 'r+')
                        for line in file:
                            if line.strip().split(':')[0] == str(_id):

                                break
                        file.write('\n{}:{}:{}'.format(str(_id), str(_login), str(_password)))
                        file.close()
                        write_msg(str(_id), respond_phrase('success'))

                    else:
                        write_msg(str(_id), respond_phrase('not'))
        time.sleep(1)
