#!/usr/bin/env python
#-*- encoding:utf-8 -*-

# CONLL.py - A set of functions to process the CoNLL standard output (.conll)
# of the SRL (semantic role labeling) algorithm
#
# Copyright (C) 2015  SAMSUNG Eletrônica da Amazônia LTDA
#
# Authors:  Alessandro Bokan Garay <alessandro.bokan@gmail.com>

import re
import codecs
import copy

PATH_OUTPUT_CONLL = '/home/rafael/PycharmProjects/RBAMR/src/bin/resources/output/output.conll'
#PATH_OUTPUT_CONLL = os.path.dirname(os.path.realpath(__file__)) + \
    #'/../src/bin/resources/output/output.conll'


def get_CoNLL_tags_from_instance(CoNLL_file):
    """
    Get all CoNLL tags and its positions (position of a word in a sentence):

        Sentence:
        ---------
        O primo Favio comprou um frango para comer de noite.

        input:
        ------
            O        0  -                 (A0*         *
            primo    1  -                 *            *
            Favio    2  -                 *)           *
            comprou  3  comprar           *            *
            um       4  -                 (A1*         *
            frango   5  -                 *            *
            para     6  -                 *)           *
            comer    7  comer             *            *
            de       8  -                 *            (AM-TMP*
            noite    9  -                 *            *)
            .        10 -                 *            *

        output:
        -------
            [("(A0", 0),     (")", 2),
             ("(A1", 4),     (")", 6),
             ("(AM-TMP", 8), (")", 9)]

    """
    # Initialize variables
    tags, pos = [], 0
    # Iterate all lines in the CoNLL_file
    for i, line in enumerate(CoNLL_file.readlines()[:-1]):
        line = line.strip()
	args_per_verb = line.split('*')
        # Find all semantic labels (A0, A1, AM-TMP, etc)
        cm = re.compile(r'(\([\w-]+|\))')
        match = [(it.start(), it.end()) for it in re.finditer(cm, line)]
        # Save the semantic label and its position in a list
        for m in match:
	    semantic_role = line[m[0]+1:m[1]]
	    correct_verb = [k for k in range(len(args_per_verb)) if semantic_role in args_per_verb[k]][0]
            tags.append((line[m[0]:m[1]] + "|" + str(correct_verb), i))
    # Close file
    CoNLL_file.close()
    # Return tags
    return tags


def map_CoNLL_tags(tags):
    """
    Identify the position of ')' simbol in the array "tags".
    This is necessary to determine the words between "(" and ")".

        Sentence:
        ---------
        O primo Favio comprou um frango para comer de noite.

        input:
        ------
            0: ("(A0", 0)
            1: (")", 2),
            2: ("(A1", 4)
            3: (")", 6)
            4: ("(AM-TMP", 8)
            5: (")", 9)

        output:
        -------
        [("(A0", 0, 1), (")", 2, -1), ("(A1", 4, 3), (")", 6, -1),
        ("(AM-TMP", 8, 5), (")", 9, -1)]

    Then ("(A0", 0, 1) -> (")", 2, -1) means that "O primo Favio" (0, 2)
    were tagged with the label "A0".

    """
    new = []
    for i in range(len(tags)):
        # Add position 'j' if the simbol is '(' (open)
        if tags[i][0].find('(') > -1:
            # Initialize breakers
            A, B = 1, 0
            for j in range(i + 1, len(tags)):
                # Identifier open simbol '('
                if tags[j][0].find('(') > -1:
                    A += 1
                # Identifier close simbol ')'
                if tags[j][0].find(')') > -1:
                    B += 1
                # Means that simbol ')' closes simbol '('
                if A - B == 0:
                    new.append((tags[i][0], tags[i][1], j))
                    break
        # Add position '-1' if the simbol is ')' (close)
        else:
            new.append((tags[i][0], tags[i][1], -1))
    # Return
    return new


def annotate_instance(words):
    
    """
    Annotate an instance (sentence) with microaspects

        input:
        ------
            words = [
                'A', 'prisão', 'aconteceu', 'em', 'Taboão da Serra', ',',
                'em', 'a', 'Grande São Paulo', '.'
            ]

        output:
        -------
            annotated_sentence = 
                'A prisão aconteceu <aspect SRL="WHERE">em Taboão da
                 Serra</aspect>, <aspect SRL="WHERE">em a Grande São
                 Paulo</aspect>.'

    """
    # Open CoNLL file
    f = codecs.open(PATH_OUTPUT_CONLL, 'r', encoding='utf-8')
    # Get all CoNLL tags (semantic labels)
    tags = get_CoNLL_tags_from_instance(f)
    # Initialize variables
    n_words = copy.deepcopy(words)
    # Convert CoNLL tags to SRL tags
    tags = map_CoNLL_tags(tags)
    # Add tags "<aspect>...</aspect>" inside the sentence
    for tag in tags[::-1]:
        if n_words[tag[1]] == 'de':
            n_words.remove(n_words[tag[1]])
            continue
        word = 'nda'
        word = n_words[tag[1]]
        if tag[0].find('(') > -1:
	    raw_role = tag[0][1:]
	    role = raw_role.split('|')[0]
	    verbo_alvo = raw_role.split('|')[1]

	    if verbo_alvo == '0':
		cor = '#31b0d5'
	    elif verbo_alvo == '1':
		cor = '#c9302c'
	    elif verbo_alvo == '2':
		cor = '#449d44'
	    else:
		cor = '#ec971f'
            #w = '<div  class="btn btn-default"><span class="badge" style="background-color:'+ cor +'; display:block;"> ' + role + ' </span> ' + word
            #w = '<role>' + role + '</role><text>' + word
            if role == 'V':
                w = '<role>' + role + verbo_alvo + '</role><text>' + word
            else:
                w = '<role>' + role + '</role><text>' + word
            n_words[tag[1]] = w
        if tag[0].find(')') > -1:
            w = word + '</text>'
            n_words[tag[1]] = w



    annotated_sentence = clean_sentence(n_words)
    # Return all sentences annotated with SRL-microaspects
    return annotated_sentence


def clean_sentence(words):
    """
    Process to join all words in a sentence and, then, clean it.

    """
    # Join all words in a sentence
    
    #for i, w in enumerate(words):
    #    if w == ',':
    #        del words[i]
    sentence = ' '.join(words)
    # Clean the sentence
    sentence = sentence.replace(' , ', ', ')
    sentence = sentence.replace(' . ', '.').replace(' .', '.')
    sentence = sentence.replace('( ', '(').replace(' )', ')')
    # Return clean sentence
    return sentence
