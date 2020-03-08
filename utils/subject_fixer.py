# -*- coding: utf-8 -*-
"""
__author__    = "Nathan Siegle Hartmann"
__contact__   = "nathanshartmann@gmail.com"
__copyright__ = "Copyright 2014, PROSA project"
__license__   = ""
__date__      = "26-11-14"
__version__   = "1.1"

It inserts missed tags in the automatic inserted subject.
It fixes the indexes of the sentences.
"""

import codecs
from sys import argv
from xml.dom import minidom


def set_attributes(terminal):
    """

        Args:
            terminal (instance) - <DOM Element> object of a terminal node.

    """ 
    if not terminal.hasAttribute('pos'):
        terminal.setAttribute('pos', "pron-pers")
    if not terminal.hasAttribute('extra'):
        terminal.setAttribute('extra', 'left soia')
    if terminal.attributes['lemma'].value == 'eu':
        terminal.setAttribute('morph','M/F 1S NOM')
    elif terminal.attributes['lemma'].value == u'nós':
        terminal.setAttribute('morph','M/F 1P NOM')


def update_id(current_sentence, current_index):
    """

        Args:
            current_sentence (instance) - <DOM Element> object of the current processed sentence.
            correct_index (int) - Integer of the index that should be put in inserted subject terminal.

    """     
    t_list = current_sentence.getElementsByTagName('t')
    edge_list = current_sentence.getElementsByTagName('edge')
    
    current_id = t_list[current_index].attributes['id'].value
    new_id = current_id.split('_')[0] + '_' + str(current_index + 1)
    
    t_list[current_index].attributes['id'].value = new_id
    for edge in edge_list:
        if current_id == edge.attributes['idref'].value:
            edge.attributes['idref'].value = new_id


def update_other_ids(current_sentence, start_index):
    """

        Args:
            current_sentence (instance) - <DOM Element> object of the current processed sentence.
            start_index (int) - Integer of the index of the token direct after the inserted subject.

    """ 
    t_list =current_sentence.getElementsByTagName('t')
    edge_list = current_sentence.getElementsByTagName('edge')
    fenode_list = current_sentence.getElementsByTagName('fenode')
    wordtag_list = current_sentence.getElementsByTagName('wordtag')

    for t in reversed(t_list[start_index:]):
        t_id = t.attributes['id'].value
        new_id = t.attributes['id'].value.split('_')[0] + '_' + str(t_list.index(t) + 1)
        t.attributes['id'].value = new_id
        for edge in edge_list:
            if t_id == edge.attributes['idref'].value:
                edge.attributes['idref'].value = new_id
        for fenode in fenode_list:
            if t_id == fenode.attributes['idref'].value:
                fenode.attributes['idref'].value = new_id
        for wordtag in wordtag_list:
            if t_id == wordtag.attributes['idref'].value:
                wordtag.attributes['idref'].value = new_id
   

def subject_fixer(INPUT_PATH):
    """

        Args:
            root (str) - string of the root target directory.

    """ 
        
    with open(INPUT_PATH) as fp:
	dom = minidom.parse(fp)
    
    s_list = dom.getElementsByTagName('s')
    for s in s_list:
	t_list = s.getElementsByTagName('t')
	for t in reversed(t_list):
	    if 'suj' in t.attributes['id'].value:
		set_attributes(t)
		update_other_ids(s, t_list.index(t) + 1)
		update_id(s, t_list.index(t))

    with codecs.open(INPUT_PATH, 'w', encoding='utf-16') as fp:
	fp.write(dom.toxml())


if __name__ == "__main__":
    assert len(argv) == 2, 'Usage: $python thisfile [input_dir]'
    #example:  python subject_fixer.py Letra\ B\ C/
    subject_fixer(argv[1])
