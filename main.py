import logging
import json
import random
import os
import requests
from flask import Flask, request
from sqlalchemy.sql.expression import func
from data import db_session
from data.normal_event_types import *
from data.normal_event_texts import *
from data.secondary_event_types import *
from data.secondary_event_texts import *
from data.buttons import *


app = Flask(__name__)
app.config['SECRET_KEY'] = 'praise_the_eight'
logging.basicConfig(level=logging.INFO)
sessionStorage = {}

# удалены перед публикацией на GitHub
API_KEY = ""
ALICE_TOKEN = ""
SKILL_ID = ""


def load_image(im_url):
    """Загрузка изображения для использования Яндекс.Диалогами."""
    headers = {
        'Authorization': f'OAuth {ALICE_TOKEN}',
    }
    json_data = {
        'url': im_url,
    }
    response = requests.post(f'https://dialogs.yandex.net/api/v1/skills/{SKILL_ID}/images',
                             headers=headers, json=json_data)
    if not response:
        logging.error(f"{response.status_code}: {response.reason}")
        return None
    response = response.json()

    id = response["image"]["id"]
    logging.info(f"Uploaded image {id} to Yandex")
    return id


def end_session(storage, res):
    """Удаляет использованные картинки и завершает сессию."""
    headers = {
        'Authorization': f'OAuth {ALICE_TOKEN}',
    }
    for image in storage["images"]:
        host = f'https://dialogs.yandex.net/api/' \
               f'v1/skills/{SKILL_ID}/images/{image}'
        requests.delete(host, headers=headers)

    res["response"]["end_session"] = True


def get_correct_button(utterance, vars, db_sess):
    """Ищет, какой кнопке соответствует ответ пользователя."""
    buttons_to_check = db_sess.query(Button).filter(Button.id.in_(vars))
    for button in buttons_to_check:
        if any([sign in utterance for sign in button.signs.split(';')]):
            return button
    return None


def get_doggo_image(storage, breed=None):
    """Получение изображения с dog.ceo"""
    if breed:
        url = f"https://dog.ceo/api/breed/{breed}/images/random"
    else:
        url = "https://dog.ceo/api/breeds/image/random"
    response = requests.get(url)
    if not response:
        logging.error(f"{response.status_code}: {response.reason}")
        return None

    im_url = response.json()["message"]
    id = load_image(im_url)
    if not id:
        return None
    storage["images"].append(id)

    logging.info(f"Received image from {im_url}")
    return id


def get_pexels_image(tag, storage):
    """Получение картинки с pexels.com."""
    # получаем список изображений по запросу
    params = {
        "query": tag,
        "orientation": "landscape",
        "per_page": 80
    }
    resp = requests.get("https://api.pexels.com/v1/search", params=params,
                        headers={'Authorization': API_KEY})
    if not resp:
        logging.error(f"{resp.status_code}: {resp.reason}")
        return None
    resp = resp.json()

    # выбираем конкретное изображение и загружаем его
    n = random.randint(0, len(resp["photos"]) - 1)
    im_url = resp["photos"][n]["src"]["medium"]
    id = load_image(im_url)
    if not id:
        return None
    storage["images"].append(id)

    logging.info(f"Received image from {im_url}")
    return id


def check_requirements(event, storage):
    """Проверяет, соответствует ли текущая ситуация
    условиям отображения конкретного события."""
    reqs = event.requirements
    if not reqs:
        return True
    reqs = reqs.split(';')
    for req in reqs:
        req = req.split('=')
        if storage[req[0]] != int(req[1]):
            return False
    return True


def form_response(event, res, storage, db_sess):
    """Формирует ответ из имеющейся информации о следующем
    событии и сопутствующем этому событию контенте."""

    # текст, картинка и звуки (если есть)
    sound_tag = None
    if type(event) is NormalEventType:
        # находим в БД
        ev = db_sess.query(NormalEventText).filter(NormalEventText.type_id ==
                                                       event.id).order_by(func.random()).first()
        txt = ev.text
        res["response"]["tts"] = txt
        if ev.tags:
            tags = ev.tags.split(';')
            if len(tags) > 1:
                sound_tag = tags[1:]
            im_tag = tags[0]
            if im_tag:
                desc = ""
                if im_tag == 'dog':
                    id = get_doggo_image(storage)
                else:
                    id = get_pexels_image(im_tag, storage)
                    desc = "Фотография предоставлена pexels.com"
                res["response"]["card"] = {
                    "type": "BigImage",
                    "image_id": id,
                    "title": txt,
                    "description": desc
                }
    elif type(event) is SecondaryEventType:
        ev = db_sess.query(SecondaryEventText).filter(SecondaryEventText.type_id ==
                                                       event.id).order_by(func.random()).first()
        txt = ev.text
        res["response"]["tts"] = txt
        if event.tags:
            tags = event.tags.split(';')
            if len(tags) > 1:
                sound_tag = tags[1:]
            im_tag = tags[0]
            if im_tag:
                desc = "Фотография предоставлена pexels.com"
                id = get_pexels_image(im_tag, storage)
                res["response"]["card"] = {
                    "type": "BigImage",
                    "image_id": id,
                    "title": txt,
                    "description": desc
                }
    res["response"]["text"] = txt

    # добавляем звук, если он нужен
    if sound_tag:
        if sound_tag[0] == 'dog':
            n = random.randint(3, 5)
            audio = f'<speaker audio="alice-sounds-animals-dog-{n}.opus"> '
        else:
            f = random.choice(sound_tag)
            audio = f'<speaker audio="alice-sounds-{f}.opus"> '
        res["response"]["tts"] = audio + res["response"]["text"]

    # кнопки
    buttons = []
    buttons_prev = []
    if event.b1:
        b = event.b1
        to_use = random.randint(0, 100) < b.weight
        if to_use:
            buttons.append({"title": b.text})
            buttons_prev.append(b.id)
    if event.b2:
        b = event.b2
        to_use = random.randint(0, 100) < b.weight
        if to_use:
            buttons.append({"title": b.text})
            buttons_prev.append(b.id)

    res["response"]["buttons"] = buttons
    storage["prev_buttons"] = buttons_prev
    storage["event_count"] += 1


def handle_death(storage, res):
    """Обработка ситуации поражения игрока."""
    texts = ["Герой погибает славной смертью",
             "К сожалению, ваш странник погибает",
             "Героическая смерть настигает исследователя Бесконечья."]
    res["response"]["text"] = random.choice(texts)

    sound_n = random.randint(1, 3)
    tts = f'<speaker audio="alice-sounds-game-loss-{sound_n}.opus"> '
    res["response"]["tts"] = tts + res["response"]["text"]

    end_session(storage, res)


def handle_incorrect(utt, res):
    """Ответ на запрос, не соответствующий ни одному из возможных действия."""
    texts = [f"В вашу голову пришла мысль {utt}, однако претворить её в жизнь вам не удалось.",
             "Вы не смогли этого сделать.",
             f"Голос в голове предложил: {utt}, но вы проигнорировали его"]
    res["response"]["text"] = random.choice(texts)


def handle_utterance(storage, req, db_sess):
    """Определяет, нужно ли искать следующее событие,
    или реплика пользователя касалась чего-то другого."""
    command = req["request"]["command"]

    if any([i in command for i in ["помощь", "умеешь"]]):
        return -1

    selected_option = get_correct_button(command,
                                         storage["prev_buttons"], db_sess)
    return selected_option


def handle_victory(storage, res):
    """Обработка завершения игры победой."""
    texts = ["Перед вами сокровище. Ура!",
             "Кажется, вы наконец нашли то, что так долго искали. Сокровище у вас!",
             "Сокровище наконец оказалось у вас в руках. Ура!"]
    res["response"]["text"] = random.choice(texts)

    sound_n = random.randint(1, 5)
    if sound_n == 4:
        tts = '<speaker audio="alice-sounds-human-crowd-6.opus"> '
    elif sound_n == 5:
        tts = '<speaker audio="alice-sounds-human-cheer-1.opus">'
    else:
        tts = f'<speaker audio="alice-sounds-game-win-{sound_n}.opus"> '
    res["response"]["tts"] = tts + res["response"]["text"]

    end_session(storage, res)


def select_normal_event(db_sess, storage):
    """Выбирает тип нормального (независимого) события."""
    # решаем, не пора ли игру завершать
    is_finished = random.randint(0, 100) < storage["event_count"] * 2
    if is_finished:
        return 2

    # если нет -- выбираем случайное обычное событие
    while True:
        event_type = db_sess.query(NormalEventType).order_by(func.random()).first()
        if check_requirements(event_type, storage):
            return event_type


def setup_new_session(sess_id, res):
    """Инициализация новой сессии."""
    sessionStorage[sess_id] = {
        "event_count": 0,
        "has_key": 0,
        "prev_buttons": [6],
        "images": []
    }

    # приветствие
    res["response"]["text"] = "Добро пожаловать в Бесконечье!"
    res["response"]["buttons"] = [{"title": "Начать игру"}]


def show_help(res):
    """Ответ на вопрос "Что ты умеешь?" и команду "Помощь"."""
    txt = "Добро пожаловать в подземелье Бесконечья! Ваша цель -- " \
          "найти сокровище, хранящееся в его глубинах. Неизвестно, что " \
          "ждёт вас на следующем шагу. С помощью кнопок выбирайте, как " \
          "поступить в том или ином событии, чтобы выжить и как можно " \
          "скорее достичь своей цели."
    res["response"]["text"] = txt


def handle_dialog(req, res):
    session_id = req["session"]["session_id"]

    # обработка начала сессии
    if req["session"]["new"]:
        setup_new_session(session_id, res)
        return

    storage = sessionStorage[session_id]
    db_sess = db_session.create_session()

    # понять, какая опция выбрана
    button = handle_utterance(storage, req, db_sess)
    if button is None:
        handle_incorrect(req["request"]["command"], res)
        return
    elif button == -1:
        show_help(res)
        return

    # выполнить необходимые действия
    if button.actions:
        actions = button.actions.split(';')
        for action in actions:
            action = action.split('=')
            param = action[0]
            value = int(action[1])
            storage[param] = value

    # выбрать тип следующего события
    evs = []
    if button.ev1 and check_requirements(button.ev1, storage):
        evs.append(button.ev1)
    if button.ev2 and check_requirements(button.ev2, storage):
        evs.append(button.ev2)
    if button.ev3 and check_requirements(button.ev3, storage):
        evs.append(button.ev3)
    evs.sort(key=lambda x: x.id, reverse=True)
    weights = []
    for ev in evs:
        if ev.id in [1, 2, 3]:
            w = 1 - sum(weights)
        else:
            w = ev.weight / 100
        weights.append(w)
    ev_type = random.choices(evs, k=1, weights=weights)[0]

    # для первичных -- выбрать конкретное событие
    if ev_type.id == 1:
        event = select_normal_event(db_sess, storage)
        if event == 2:
            handle_victory(storage, res)
            return
    elif ev_type.id == 2:
        handle_victory(storage, res)
        return
    elif ev_type.id == 3:
        handle_death(storage, res)
        return
    else:
        event = ev_type

    # сформировать ответ
    form_response(event, res, storage, db_sess)


@app.route('/post', methods=['POST'])
def main():
    request.get_json(force=True)
    logging.info(f'Request: {request.json!r}')

    response = {
        "version": request.json['version'],
        "session": request.json['session'],
        "response": {
            "end_session": False
        }
    }
    handle_dialog(request.json, response)
    return json.dumps(response)


if __name__ == '__main__':
    db_session.global_init("db/content.sqlite")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)