# -*- coding: utf-8 -*-

import codecs
import re
from xml.dom import minidom

from unidecode import unidecode
from nltk.corpus import stopwords

import palavras
from utils import named_entity
from utils.text2num import text2num


class Parsing(object):
    """Rule-Based AMR Parser"""

    def __init__(self):
        self.regex = r'#(-?[0-9]+)->([0-9]+)'
        self.amr_tuples = ()
        self.amr_list = []
        self.target = []
        self.value = []
        self.variables = {}
        self.main = ''
        self.top = ''
        self.stopwords = ['artd', 'arti', 'clb']
        self.preps = []
        self.relation = []
        self.lemma = ''
        self.countries = self._get_list('utils/countries.txt')
        self.cities = self._get_list('utils/cities.txt')
        self.natio = self._get_list('utils/nationalities.txt')
        self.natio1 = self._get_list('utils/nationalities1.txt')
        self.states = self._get_list('utils/states.txt')
        self.continents = self._get_list('utils/continents.txt')
        self.weeks = self._get_list('utils/weeks.txt')

    def _get_list(self, input_f):
        l = []
        with codecs.open(input_f, 'r', 'utf-8') as f:
            for line in f.readlines():
                l.append(line.strip())
        return l

    def _get_variable(self, variable, cont=0):
        if variable not in self.variables.keys():
            return variable
        else:
            cont += 1
            variable = variable[:1] + str(cont)
            return self._get_variable(variable, cont=cont)

    def _is_concept(self, value):
        if value in self.variables.values():
            return True
        return False

    def _get_concept(self, value):
        for k, v in self.variables.items():
            if v == value:
                return k
        return self.top

    def _less_tokens(self, annotated_sentences):
        if type(annotated_sentences) is tuple:
            if annotated_sentences.get('V'):
                self.amr_tuples = (str(annotated_sentences['V'][0]).lower(), 'instance', str(annotated_sentences['V']))
                # print 'Tuple: ', self.amr_tuples
                # exit()
                self.amr_list.append(self.amr_tuples)
                #self.amr_tuples = (str(annotated_sentences[':mod'][0]).lower(), 'instance', str(annotated_sentences[':mod']))
                #self.amr_list.append(self.amr_tuples)
                self.amr_tuples = (str(annotated_sentences['V'][0]).lower(), 'mod', str(annotated_sentences[':mod']).lower())
                self.amr_list.append(self.amr_tuples)
        else:

            print annotated_sentences
            self.amr_tuples = (str(annotated_sentences[-1].keys()[0][0]).lower(), 'instance', str(annotated_sentences[-1].keys()[0]).lower())
            self.amr_list.append(self.amr_tuples)
            self.amr_tuples = (str(annotated_sentences[-1].keys()[0][0]).lower(), 'mod', str(annotated_sentences[-1].keys()[1]).lower())
            self.amr_list.append(self.amr_tuples)

    def _link_verb(self, tokens):
        flag = False
        for t in tokens[:-1]:
            if re.search(self.regex, t[1]['relation']).group(2) == '0':
                if t[1]['lemma'] == 'ser' or t[1]['lemma'] == 'estar':
                    self.main = re.search(self.regex, t[1]['relation']).group(1)
                    self.target.append(re.search(self.regex, t[1]['relation']).group(1))
                    flag = True
                    break
                break
        if flag:
            self.find_top(self.main, tokens)
            self._link_arguments(tokens, )
            # for t in tokens[:-1]:
            #     if re.search(self.regex, t[1]['relation']).group(2) == self.main:
            #         if t[1]['semantic'] and (t[1]['semantic'][0] == 'hum' or
            #                                  t[1]['semantic'][0] == 'inst'):
            #             self._named_entities(top, t)
            #         elif t[1]['semantic'] and (t[1]['semantic'][0] == 'civ' or
            #                                    t[1]['semantic'][0] == 'org'):
            #             self._named_entities_civ(top, t)
            #         elif t[1]['morpho'][0] == 'N' and t[1]['lemma'] != self.amr_list[0][2]:
            #             self._set_relation(top, t, 'domain')
            #         elif 'arg' in t[1] and t[1]['arg'] == ':polarity':
            #             self.amr_tuples = (top, 'polarity', '-')
            #             self.amr_list.append(self.amr_tuples)
            #     elif re.search(self.regex, t[1]['relation']).group(2) == relation:
            #         if t[1]['morpho'][0] == 'ADJ':
            #             self._set_relation(top, t, 'mod')
        return flag

    def parsing(self, annotated_sentences):
        tokens = self.run_palavras()
        print 'Tokens: ', tokens
        if len(tokens) <= 3:
            print 'Annotated: ', annotated_sentences
            self._less_tokens(annotated_sentences)
            return self.amr_list
        tokens = self.join_arguments(annotated_sentences, tokens)
        print tokens
        if self._link_verb(tokens):
            return self.amr_list
        self._main_predicate(tokens)
        self._link_arguments(tokens)
        return self.amr_list

    @staticmethod
    def run_palavras():
        document = minidom.parse('utils/input.xml')
        terminals = document.getElementsByTagName('t')
        tokens, pointers = palavras.parse_list('utils/input.txt', terminals)
        return tokens

    def join_arguments(self, annotated_sentences, tokens):
        for sentence in annotated_sentences:
            for key, value in sentence.items():
                if type(value) is list:
                    if type(value[0]) is unicode or type(value[0]) is str:
                        for v in value[0].split():
                            for t in tokens[:-1]:
                                for element in t[0].split('='):
                                    self._loop(v, element, key, t)
                        # self._loop(key, value, tokens)
                    elif type(value[0]) is dict:
                        for k, v in value[0].items():
                            for i in v.split():
                                for t in tokens[:-1]:
                                    for element in t[0].split('='):
                                        self._loop(i, element, k, t)
                    if len(value) > 1:
                        for k, v in value[1].items():
                            for i in v.split():
                                for t in tokens[:-1]:
                                    for element in t[0].split('='):
                                        self._loop(i, element, k, t)
                else:
                    for v in value.split():
                        for t in tokens[:-1]:
                            for element in t[0].split('='):
                                self._loop(v, element, key, t)
        return tokens

    @staticmethod
    def _loop(v, element, key, token):
        if v.lower() == element.decode('utf-8').lower():
            if key == 'A0':
                token[1]['arg'] = ':ARG0'
            elif key == 'A1':
                token[1]['arg'] = ':ARG1'
            elif key == 'A2':
                token[1]['arg'] = ':ARG2'
            elif key == ':ARG0-of':
                token[1]['arg'] = ':ARG0-of'
            elif 'V' in key:
                token[1]['arg'] = 'V'
            elif key == 'AM-NEG':
                token[1]['arg'] = ':polarity'
            elif key == 'AM-MNR':
                token[1]['arg'] = ':manner'
            elif key == 'AM-TMP':
                token[1]['arg'] = ':time'
            elif key == 'AM-LOC':
                token[1]['arg'] = ':location'

    def _main_predicate(self, tokens):
        for t in tokens[:-1]:
            if re.search(self.regex, t[1]['relation']).group(2) == '0':
                self.target.append(re.search(self.regex, t[1]['relation']).group(1))
                value = t[1]['lemma'].lower()
                self.value.append(value)
                self.top = self._get_variable(t[1]['lemma'][0])
                self.amr_tuples = (self.top, 'instance', value+'-01')
                self.amr_list.append(self.amr_tuples)
                self.variables[self.top] = value.lower()
                return

    def _link_arguments(self, tokens):
        for idx, arg in enumerate(self.target):
            if int(arg) < 0:
                continue
            for t in tokens[:-1]:
                if re.search(self.regex, t[1]['relation']).group(2) == arg:
                    target = re.search(self.regex, t[1]['relation']).group(1)
                    if target not in self.target:
                        self.target.append(re.search(self.regex, t[1]['relation']).group(1))
                        self.value.append(t[1]['lemma'])
                    if self.lemma == t[1]['lemma']:
                        continue
                    if len(t[1]['morpho']) > 0 and t[1]['morpho'][0] == 'PRP' \
                            or t[1]['lemma'] == 'ser' or t[1]['lemma'] == 'estar':
                        self.preps.append(re.search(self.regex, t[1]['relation']).group(1))
                        self.relation.append(arg)
                        continue
                    if any(i in t[1]['semantic'] for i in self.stopwords):
                        # CRIAR UM PONTEIRO PARA APONTAR PARA O TOP
                        continue
                    if arg in self.preps:
                        idx = self.target.index(self.relation[self.preps.index(arg)])
                    if t[1]['morpho'] and t[1]['morpho'][0] == 'V':
                        self._set_relation(self._get_concept(self.value[idx]), t, 'ARG1', frameset='-01')
                    elif len(t[1]['semantic']) > 0 and t[1]['semantic'] and (t[1]['semantic'][0] == 'hum' or
                                               t[1]['semantic'][0] == 'org'):
                        self._named_entities(self._get_concept(self.value[idx]), t)
                    elif 'arg' in t[1] and t[1]['arg'] != ':polarity' and len(t[1]['morpho']) == 0:
                        self.amr_tuples = (self._get_concept(self.value[idx]), t[1]['arg'][1:], t[1]['lemma'])
                        self.amr_list.append(self.amr_tuples)
                    elif len(t[1]['semantic']) > 0 and t[1]['semantic'][0] == 'civ':
                        self._named_entities_civ(self._get_concept(self.value[idx]), t)
                    elif len(t[1]['semantic']) >= 3:
                        relation = 'unit' if 'unit' in t[1]['semantic'] else None
                        if relation:
                            self._set_relation(self._get_concept(self.value[idx]), t, relation)
                        else:
                            continue
                    elif len(t[1]['semantic']) > 0 and 'arg' in t[1] and t[1]['arg'] != ':polarity' and \
                            t[1]['morpho'][0] != 'PERS' and t[1]['semantic'][0] != 'poss' \
                            and t[1]['semantic'][0] != 'pp' and t[1]['semantic'][0] != 'jh':
                        if not t[1]['lemma'].isdigit():
                            self._set_relation(self._get_concept(self.value[idx]), t, t[1]['arg'][1:])
                        else:
                            self.amr_tuples = (self._get_concept(self.value[idx]), t[1]['arg'][1:], t[1]['lemma'])
                            self.amr_list.append(self.amr_tuples)
                    elif 'arg' in t[1] and t[1]['arg'] != ':polarity' and t[1]['morpho'][0] == 'PERS':
                        if not t[1]['lemma'].isdigit():
                            self._set_relation(self._get_concept(self.value[idx]), t, t[1]['arg'][1:])
                        else:
                            self.amr_tuples = (self._get_concept(self.value[idx]), 'domain', t[1]['lemma'])
                            self.amr_list.append(self.amr_tuples)
                    elif 'arg' not in t[1] and t[1]['morpho'][0] == 'PERS':
                        self._set_relation(self._get_concept(self.value[idx]), t, 'domain')
                    elif len(t[1]['semantic']) > 0 and t[1]['semantic'] and t[1]['semantic'][0] == 'poss':
                        if self._is_concept('eu'):
                            variable = self._get_concept('eu')
                            k = self._get_concept(self.value[idx])
                            self.amr_tuples = (k, 'poss', variable)
                            self.amr_list.append(self.amr_tuples)
                        else:
                            self._set_relation(self._get_concept(self.value[idx]), t, 'poss')
                    elif len(t[1]['semantic']) > 0 and t[1]['morpho'][0] == 'ADJ' and t[1]['semantic'] \
                            and t[1]['semantic'][0] == 'NUM-ord':
                        variable = self._get_concept('o')
                        self.variables[variable] = 'ordinal-entity'
                        self.amr_tuples = (variable, 'instance', 'ordinal-entity')
                        self.amr_list.append(self.amr_tuples)
                        k = self._get_concept(self.value[idx])
                        self.amr_tuples = (k, 'ord', variable)
                        self.amr_list.append(self.amr_tuples)
                        self.amr_tuples = (variable, 'value', text2num(t[1]['lemma']))
                        self.amr_list.append(self.amr_tuples)
                    elif t[1]['morpho'][0] == 'ADJ':
                        self._set_relation(self._get_concept(self.value[idx]), t, 'mod')
                    elif 'arg' in t[1] and len(t[1]['semantic']) > 0 and t[1]['morpho'][0] == 'ADV' and \
                            t[1]['arg'] != ':polarity' and t[1]['semantic'][0] == 'quant':
                        self._set_relation(self._get_concept(self.value[idx]), t, 'degree')
                    elif 'arg' in t[1] and t[1]['morpho'][0] == 'ADV' and t[1]['arg'] != ':polarity' and \
                            t[1]['POS'] == '<ADVL':
                        self._set_relation(self._get_concept(self.value[idx]), t, 'manner')
                    elif t[1]['morpho'][0] == 'NUM':
                        if not t[0].isdigit():
                            self.amr_tuples = (self._get_concept(self.value[idx]), 'quant', text2num(t[0]))
                        else:
                            self.amr_tuples = (self._get_concept(self.value[idx]), 'quant', t[0])
                        self.amr_list.append(self.amr_tuples)
                    elif 'arg' in t[1] and t[1]['arg'] == ':polarity':
                        self.amr_tuples = (self._get_concept(self.value[idx]), 'polarity', '-')
                        self.amr_list.append(self.amr_tuples)

    def find_top(self, target, tokens):
        for t in reversed(tokens[:-1]):
            try:
                if re.search(self.regex, t[1]['relation']).group(2) == target and t[1]['lemma'] not in stopwords.words(u'portuguese'):
                    # variable_top = self._get_variable(t[1]['lemma'][0])
                    self.top = self._get_variable(t[1]['lemma'][0])
                    self.lemma = t[1]['lemma']
                    self.value.append(t[1]['lemma'].lower())
                    # self.amr_tuples = (variable_top, 'instance', t[1]['lemma'])
                    self.amr_tuples = (self.top, 'instance', t[1]['lemma'])
                    self.amr_list.append(self.amr_tuples)
                    # relation = re.search(self.regex, t[1]['relation']).group(1)
                    # self.target.append(re.search(self.regex, t[1]['relation']).group(1))
                    # self.variables[variable_top] = t[1]['lemma'].lower()
                    self.variables[self.top] = t[1]['lemma'].lower()
                    break
            except Exception as e:
                print(e)
        # return variable_top, relation

    def _set_relation(self, top, token, relation, frameset=None):
        if token[1]['lemma'][0].lower() == '\xc3':
            u = token[1]['lemma'].lower().decode('utf-8')
            c = unidecode(u[0])
            variable = self._get_variable(c.lower())
        else:
            variable = self._get_variable(token[1]['lemma'][0].lower())
        if frameset:
            self.amr_tuples = (variable, 'instance', token[1]['lemma'] + frameset)
        else:
            self.amr_tuples = (variable, 'instance', token[1]['lemma'])
        self.amr_list.append(self.amr_tuples)
        if top is None:
            self.amr_tuples = (self.top, relation, variable)
            self.amr_list.append(self.amr_tuples)
            self.variables[variable] = token[1]['lemma'].lower()
        elif token[0] in self.weeks:
            variable_time = self._get_variable('d')
            self.amr_tuples = (variable_time, 'instance', 'date-entity')
            self.amr_list.append(self.amr_tuples)
            self.amr_tuples = (top, 'time', variable_time)
            self.amr_list.append(self.amr_tuples)
            self.amr_tuples = (variable_time, 'weekday', variable)
            self.amr_list.append(self.amr_tuples)
            self.variables[variable] = token[1]['lemma'].lower()
            self.variables[variable_time] = 'date-entity'
        else:
            self.amr_tuples = (top, relation, variable)
            self.amr_list.append(self.amr_tuples)
            self.variables[variable] = token[1]['lemma'].lower()

    def _named_entities_civ(self, top, token):
        if '=' in token[0]:
            ner = ' '.join(token[0].split('='))
        else:
            ner = token[0]
        civ = str(named_entity.get_named_entity(self.countries, self.cities, self.states, self.continents, ner))
        variable_civ = self._get_variable(civ[0])
        self.variables[variable_civ] = civ
        self.amr_tuples = (variable_civ, 'instance', civ)
        self.amr_list.append(self.amr_tuples)
        if token[1].get('arg'):
            self.amr_tuples = (top, token[1]['arg'][1:], variable_civ)
        else:
            self.amr_tuples = (top, 'location', variable_civ)
        self.amr_list.append(self.amr_tuples)
        variable = self._get_variable('n')
        self.variables[variable] = 'name'
        self.amr_tuples = (variable, 'instance', 'name')
        self.amr_list.append(self.amr_tuples)
        self.amr_tuples = (variable_civ, 'name', variable)
        self.amr_list.append(self.amr_tuples)
        self._ops(variable, token)

    def _named_entities(self, top, token):
        if token[1]['semantic'][0] == 'hum':
            variable = self._get_variable('p')
            self.variables[variable] = 'pessoa'
            self.amr_tuples = (variable, 'instance', 'pessoa')
        else:
            variable = self._get_variable('o')
            self.variables[variable] = 'organização'
            self.amr_tuples = (variable, 'instance', 'organização')
        self.amr_list.append(self.amr_tuples)
        if token[1].get('arg'):  # ['arg']:
            self.amr_tuples = (top, token[1]['arg'][1:], variable)
        else:
            self.amr_tuples = (top, 'domain', variable)
        self.amr_list.append(self.amr_tuples)
        variable_name = self._get_variable('n')
        self.variables[variable_name] = 'name'
        self.amr_tuples = (variable_name, 'instance', 'name')
        self.amr_list.append(self.amr_tuples)
        self.amr_tuples = (variable, 'name', variable_name)
        self.amr_list.append(self.amr_tuples)
        self._ops(variable_name, token)

    def _ops(self, variable, token):
        for idx, op in enumerate(token[0].split('=')):
            name = '"' + op + '"'
            self.amr_tuples = (variable, 'op'+str(idx+1), name)
            self.amr_list.append(self.amr_tuples)
