import json
import logging
import os
import re
import threading

import pymorphy2
from flask import Flask, request

from utils import CityRepository


PROFILE_FILE = 'profiles.json'


morph = pymorphy2.MorphAnalyzer()
app = Flask(__name__)

city_repository = CityRepository()


logging.basicConfig(level=logging.DEBUG)


@app.route("/", methods=['POST'])
def main():
    logging.info('Request: %r', request.json)

    result = switch_state(request.json)
    response = {
        'version': request.json['version'],
        'session': request.json['session'],
        'response': {
            'end_session': result.get('end_session', False),
            'text': result['text'],
        }
    }

    logging.info('Response: %r', response)

    return json.dumps(
        response,
        ensure_ascii=False,
        indent=2
    )


def load_profiles():
    if not os.path.isfile(PROFILE_FILE):
        return {}

    with open(PROFILE_FILE) as f:
        return json.load(f)


profiles = load_profiles()
profile_lock = threading.RLock()

sessions = {}
session_lock = threading.RLock()


def switch_state(request):
    utterance = request['utterance'] = request['request']['original_utterance']
    words = request['words'] = re.findall(r'\w+', utterance, flags=re.UNICODE)
    request['lemmas'] = [morph.parse(word)[0].normal_form for word in words]

    session_id = request['session']['session_id']
    with session_lock:
        if session_id not in sessions:
            state = sessions[session_id] = collect_profile()
            request = None
        else:
            state = sessions[session_id]
    response = state.send(request)

    return response


def collect_profile():
    profile = {}

    req = yield {'text': 'Привет :) Кого ты ищешь - девушку или парня?'}
    while True:
        lemmas = req['lemmas']

        if any(w in lemmas for w in ['парень', 'молодой', 'мч', 'мужчина', 'мальчик']):
            gender = 'female'
            break
        elif any(w in lemmas for w in ['девушка', 'женщина', 'тёлка', 'телок', 'девочка']):
            gender = 'male'
            break

        req = yield {'text': 'Скажи или слово "девушка", или слово "парень"'}
    profile['gender'] = gender

    req = yield {'text': 'Я смогу тебе помочь! Как тебя зовут?'}
    utterance = req['utterance']
    profile['name'] = utterance

    req = yield {'text': 'Сколько тебе лет?'}
    while True:
        utterance = req['utterance'].strip('.')

        if not re.fullmatch(r'\d+', utterance):
            req = yield {'text': 'Назови число'}
            continue
        age = int(utterance)

        if age < 18:
            req = yield {'text': 'Навык доступен только для людей не младше 18 лет, сорян :(',
                         'end_session': True}
            return
        if age > 100:
            req = yield {'text': 'Некорректный возраст, назови возраст ещё раз'}
            continue
        break
    profile['age'] = age

    req = yield {'text': 'А в каком городе ты живёшь?'}
    while True:
        utterance = req['utterance']

        if city_repository.try_get_city(utterance) is not None:
            break

        req = yield {'text': 'Я не знаю такого города. Назови город ещё раз'}
    profile['city'] = utterance

    req = yield {'text': 'Расскажи, где ты работаешь или учишься?'}
    profile['occupation'] = req['lemmas']

    req = yield {'text': 'Чем ты занимаешься в свободное время? Какие у тебя хобби?'}
    profile['hobbies'] = req['lemmas']

    req = yield {'text': 'Какую музыку ты слушаешь? Назови пару исполнителей.'}
    profile['music'] = req['lemmas']

    req = yield {'text': 'Отлично! Тебе осталось сообщить свой номер телефона. Начинай с "восьмёрки".'}
    while True:
        utterance = req['utterance']
        phone = re.sub(r'\D', r'', utterance)

        req = yield {'text': 'Я правильно распознала твой номер телефона?'}
        lemmas = req['lemmas']

        if any(w in lemmas for w in ['да', 'правильно']):
            break
    profile['phone'] = phone

    user_id = req['session']['user_id']
    with profile_lock:
        profiles[user_id] = profile
        with open('profiles.json', 'w') as f:
            json.dump(profiles, f)

    yield {'text': 'Всё понятно',
           'end_session': True}
