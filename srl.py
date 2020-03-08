#!/usr/bin/env python
# -*- encoding:utf-8 -*-

# SRL.py - Semantic role labeling algorithm described by Alva-Manchego [2013]
#
# Copyright (C) 2015  SAMSUNG Eletrônica da Amazônia LTDA
#
# Authors:  Alessandro Bokan Garay <alessandro.bokan@gmail.com>
#           Nathan Siegle Hartmann <nathanshartmann@gmail.com> (creator of
#           the SRL models)
import codecs
import re
import string
from bs4 import BeautifulSoup

import penman
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

import parsing
from src.bin.srl.main import classify
from src.corpus.util.CoNLLFormatter import main
from src.corpus.util.PropsPrinter import props_printer
from utils import anota_verbo_conll
from utils.CONLL import annotate_instance
from utils.anota_verbo_conll import anota_verbo_conll, anota_auxiliares_conll
from utils.insert_subject import insert_first_person_subj
from utils.run_palavras import (run_palavras_sentence,
                                add_semantic_tags)
from utils.srl_auxiliary_verbs import insert_auxiliary_verbs
from utils.subject_fixer import subject_fixer


# sys.path.append('src')

class SRLClassifier(object):

    def __init__(self, file, sentences, AI_model, AC_model):
        self.amr_result = codecs.open('result/result.txt', 'a', 'utf-8')
        self.argident_sys, self.argclass_sys = AI_model, AC_model
        self.annotated_sentences = self.annotate(sentences)

    @staticmethod
    def remove_stopwords(sentences):
        """
        Added for AMR parser
        :param sentences: input sentences
        :return: tokens
        """
        tokens = word_tokenize(sentences)
        tokens = [t for t in tokens if t not in stopwords.words(u'portuguese')]
        return tokens

    def annotate(self, sentences):
        annotated_sentences = []
        id = 1
        flag = False
        # Iterate all sentences
        for sentence in sentences:
            # Sentence pre-processing
            sentence = re.sub('[\"|\[|\]]', '', sentence).strip()
            # Initialize "annotated_sentence"
            annotated_sentence = sentence
            # Run PALAVRAS TigerXML. Get a list of words of the sentence
            try:
                regex = re.compile('[%s]' % re.escape(string.punctuation))
                new_sentence = regex.sub('', sentence)
                xml_file = run_palavras_sentence(new_sentence)
                insert_first_person_subj(xml_file)
                subject_fixer(xml_file)
                words = add_semantic_tags(xml_file)
                insert_auxiliary_verbs()
            except Exception as e:
                print str(e)
                # annotated_sentences.append(annotated_sentence)
                continue
            if words:
                try:
                    main()
                    props_printer()
                    # Semantic Role Labelling (SRL)
                    classify(self.argident_sys, self.argclass_sys)
                    anota_verbo_conll()
                    anota_auxiliares_conll()
                    # Get sentence annotated with "semantic roles"
                    annotated_sentence = annotate_instance(words[0])
                except Exception as e:
                    print str(e)
            print 'Annotated sentence: ', annotated_sentence
            # exit()
            if len(annotated_sentence.split()) == 2:
                self.verify_sentence(annotated_sentence.encode('utf-8'))
                modified_sentence = {}
                modified_sentence['V'] = annotated_sentence.split()[0]
                modified_sentence[':mod'] = annotated_sentence.split()[1]
                parser = parsing.Parsing()
                amr = parser.parsing(modified_sentence)
                flag = True
            else:
                modified_sentence = self.transform_dict(annotated_sentence)
            #
            if not modified_sentence:
                modified_sentence = self.empty_dict(annotated_sentence)
            annotated_sentences.append(modified_sentence)
            print 'Modified sentence:', modified_sentence
            if not flag:
                parser = parsing.Parsing()
                amr = parser.parsing(annotated_sentences)
            print 'Tuples AMR: ', amr
            self.amr_result.write('# ::id ')
            self.amr_result.write(str(id))
            self.amr_result.write('\n')
            self.amr_result.write('# ::snt ')
            self.amr_result.write(sentence)
            self.amr_result.write('\n')
            try:
                print penman.Graph(amr)
                self.amr_result.write(str(penman.Graph(amr)))
            except Exception:
                print 'Empty graph'
                empyt = '(e / empty)'
                self.amr_result.write(str(empyt))
            self.amr_result.write('\n\n')
            id += 1
            flag = False
        return annotated_sentences

    @staticmethod
    def empty_dict(annotated_sentence):
        aux = {}
        for word in annotated_sentence.split():
            aux[word] = '_'
        modified_sentence = dict(sorted(aux.items(), key=lambda x: x[0]))
        return modified_sentence

    @staticmethod
    def verify_sentence(annotated_sentence):
        l = annotated_sentence.replace('.', '').strip().split(',')
        flag = []
        for idx, val in enumerate(l):
            cont = 0
            for k in val:
                if k == '"':
                    cont += 1
            if cont != 4:
                flag.append(val)

    @staticmethod
    def transform_dict(annotated_sentence):
        regex_role = r'<role>(.+)</role>'
        regex_text = r'<text>(.+)</text>'

        l, aux_l = [], []

        aux = ''
        role_aux = ''

        flag = False

        srl, aux_d = {}, {}

        soup = BeautifulSoup(annotated_sentence, 'lxml')
        roles = soup.find_all('role')
        texts = soup.find_all('text')

        for idx, val in enumerate(texts):
            role = roles[idx].text
            if len(val.contents) > 1:
                role_aux = role
                for v in val.contents:
                    v = str(v).strip()
                    match_role = re.match(regex_role, v)
                    match_text = re.match(regex_text, v)
                    if match_role:
                        aux = match_role.group(1)
                    elif match_text:
                        flag = True
                        l.append(match_text.group(1))
                        # if match_text.group(1) != 'que':
                        aux_d[aux] = match_text.group(1)
                    else:
                        if not v.isspace():
                            aux_l.append(v)
            else:
                if str(val.text) not in l:
                    if val.text == 'Eu':
                        role = 'A0'
                        # roles[idx].text = 'A0'
                    if srl.has_key(role):
                        value = srl[role] + ' ' + val.text
                        srl[role] = value
                    else:
                        srl[role] = val.text
        if flag:
            aux_l = filter(None, aux_l)
            if len(aux_l) > 1:
                stn = ''
                for i in aux_l:
                    if type(i) == str:
                        stn += i + ' '
                        aux_l.remove(i)
                aux_l[0] = stn
            aux_l.append(aux_d)
            if len(aux_l) > 1 and type(aux_l[1]) != dict:
                aux_l.remove(aux_l[1])
            if srl.has_key(role_aux):
                print aux_l[0]
                print srl[role_aux]
                if type(aux_l[0]) is dict:
                    for k, v in aux_l[0].items():
                        if k in srl.keys():
                            srl[k] = srl[k] + ' ' + v
                else:
                    aux_l[0] = srl[role_aux] + ' ' + aux_l[0]
                # srl[role_aux] = [srl[role_aux],aux_l[0]]
            srl[role_aux] = aux_l
        return srl

    @staticmethod
    def transform_json(annotated_sentence):
        l = list(annotated_sentence)
        l[-1] = ''
        l[-2] = ''
        if l[-3] == '"' and l[-4] == ',':
            l[-3] == ''
            l[-4] == ''

        final = '{' + ''.join(l) + '}'
        return final