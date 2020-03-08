# -*- coding: utf-8 -*-

from googletrans import Translator
import requests


def get_named_entity(countries, cities, states, continents, name):
    """Returns named entity for civilization"""
    if name in countries:
        return 'país'
    elif name in cities:
        return 'cidade'
    elif name in states:
        return 'estado'
    elif name in continents:
        return 'continente'
    else:
        text = translate(name)
        obj = requests.get('http://api.conceptnet.io/c/en/'+text).json()
        for item in obj['edges']:
            for i in item.items():
                return i[1]['label']


def translate(word):
    translator = Translator()
    t = translator.translate(word, src='pt')
    return t.text.lower()


if __name__ == '__main__':
    print get_named_entity('Angra dos Reis')