# -*- coding: utf-8 -*-
"""
__author__    = "Nathan Siegle Hartmann"
__contact__   = "nathanshartmann@gmail.com"
__copyright__ = "Copyright 2014, PROSA project"
__license__   = ""
__date__      = "18-11-14"
__version__   = "1.2.1"
"""

import codecs
from xml.dom import minidom

EXCEPTION_ADVPS = [u'não', u'nunca', u'sempre', u'quase', u'só', u'já', u'também']

IMPERSONAL_VERBS = ['haver', 'existir', 'chover', 'nevar', 'ventar']

OBLIQUE_PRONOUNS = ['me', 'te', 'nos', 'vos', 'lhe', 'lhes']

UTTERANCE_VERBS = [u'acentuar', u'acrescentar', u'afirmar', u'alegar', u'argumentar', u'berrar', u'bradar', u'clamar', u'contar',
                   u'dizer', u'exclamar', u'falar', u'gritar', u'indagar', u'informar', u'perguntar', u'responder', u'sustentar']

class Subject_insertor(object):
    """First person subject insertor"""

    def load(self, sentence):
        """

            Args:
                sentence (instance) - a <DOM Element> containing a sentence pointer.

        """
        self.sentence = sentence
        self.COUNT_SUJ = -1
        self.terminals = sentence.getElementsByTagName('terminals')[0]
        self.nonterminals = sentence.getElementsByTagName('nonterminals')[0]
        self.t_list = self.terminals.getElementsByTagName('t')
        self.nt_list = sentence.getElementsByTagName('nt')
        self.vp_list = [vp for vp in self.get_nt_vps() if not self.has_exception_verb(vp)]

    def is_comma_before(self, vp):
        """

            Args:
                vp (instance) - a <DOM Element> containing a VP node.

            Returns:
                (bool) - returns True if it is a comma immediately before vp

        """
        vp_terminal = [t for t in self.t_list if t.attributes['id'].value == self.get_first_syntactic_son(vp).attributes['idref'].value]
        vp_terminal_index = self.t_list.index(vp_terminal[0])
        return True if self.t_list[vp_terminal_index - 1].attributes['word'].value == ',' else False


    def is_punct_before(self, vp):
        """

            Args:
                vp (instance) - a <DOM Element> containing a VP node.

            Returns:
                (bool) - returns True if it is a punctuation immediately before vp

        """
        vp_terminal = [t for t in self.t_list if t.attributes['id'].value == self.get_first_syntactic_son(vp).attributes['idref'].value]
        vp_terminal_index = self.t_list.index(vp_terminal[0])
        return True if self.t_list[vp_terminal_index - 1].attributes['pos'].value == 'pu' else False


    def is_np(self, node):
        """

            Args:
                node (instance) - a <DOM Element> containing a nonterminal node.

            Returns:
                (bool) - returns True if node is an NP.

        """
        nt_node = self.get_nt_node(node)
        if nt_node:
            return True if nt_node.attributes['cat'].value == 'np' else False


    def is_pp(self, node):
        """

            Args:
                node (instance) - a <DOM Element> containing a nonterminal node.

            Returns:
                (bool) - returns True if node is a PP.

        """
        nt_node = self.get_nt_node(node)
        if nt_node:
            return True if nt_node.attributes['cat'].value in ['pp', 'advp', 'fcl'] else False


    def is_advp(self, node):
        """

            Args:
                node (instance) - a <DOM Element> containing a nonterminal node.

            Returns:
                (bool) - returns True if node is an ADVP.

        """
        nt_node = self.get_nt_node(node)
        if nt_node:
            return True if nt_node.attributes['cat'].value == 'advp' else False


    def is_verb_ser_exception(self, vp):
        """

            Args:
                vp (instance) - a <DOM Element> containing a VP node.

            Returns:
                (bool) - returns True if vp has a verb Ser/To be annotation exception. A verb to be is only annotated when it
                        starts a sentence; when it comes after a punctuation; or when it is an auxiliary verb.

        """
        vp_parent = self.get_vp_parent(vp)
        try:
            if vp_parent.attributes['cat'].value == 'fcl':
                verb_terminal = [t for t in self.t_list if t.attributes['id'].value == self.get_first_syntactic_son(vp).attributes['idref'].value]
                if len(verb_terminal) == 0:
                    return False
                return True if self.t_list.index(verb_terminal[0]) == 0\
                            or (self.t_list.index(verb_terminal[0]) == 1 and self.t_list[self.t_list.index(verb_terminal[0])-1].attributes['pos'].value == 'adv')\
                            or self.t_list[self.t_list.index(verb_terminal[0])-1].attributes['pos'].value == 'pu'\
                            or verb_terminal[0].attributes['extra'].value == 'aux'\
                        else False
            else:
                return False
        except:
            return False


    def is_first_person_verb(self, vp):
        """

            Args:
                vp (instance) - a <DOM Element> containing a VP node.

            Returns:
                (bool) - returns True if vp has a first person's verb (singular or plural).

        """
        first_vp_element = self.get_first_syntactic_son(vp)
        first_vp_terminal = [t for t in self.t_list if t.attributes['id'].value == first_vp_element.attributes['idref'].value][0]
        return True if '1S' in first_vp_terminal.attributes['morph'].value.split()\
                    or '1P' in first_vp_terminal.attributes['morph'].value.split()\
                else False


    def is_direct_object(self, np):
        """

            Args:
                vp (instance) - a <DOM Element> containing a NP node.

            Returns:
                (bool) - returns True if np is a direct object. PALAVRAS parser tags direct objects with an ACC label.

        """
        return True if np.attributes['label'].value == 'ACC' else False


    def is_insertion_needed(self, vp, vp_parent, left_neighbor):
        """

            Returns:
                (bool) - returns True if a subject insertion is expected.

        """
        left_neighbor2 = self.get_left_neighbor(vp, vp_parent, 2)
        left_neighbor3 = self.get_left_neighbor(vp, vp_parent, 3)
        if self.has_no_left_neighbor(vp, vp_parent)\
                or (self.is_punct_before(vp) and (not self.is_np(left_neighbor)) and (not self.is_np(left_neighbor2)))\
                or (not self.is_np(left_neighbor) and not self.is_advp(left_neighbor) and not self.is_punct_before(vp))\
                or (self.is_advp(left_neighbor) and (self.has_no_left_neighbor(left_neighbor, vp_parent) or not self.is_np(left_neighbor2)))\
                or (self.is_np(left_neighbor) and self.has_oblique_pronoun(left_neighbor) and not self.is_np(left_neighbor2))\
                or (self.is_np(left_neighbor) and self.is_direct_object(left_neighbor) and not (self.is_np(left_neighbor2) or self.is_advp(left_neighbor2) and self.is_np(left_neighbor3))):

            if (not self.has_utterance_verb(vp) and not self.has_pp_between_commas(left_neighbor2))\
                    or (self.has_utterance_verb(vp) and not self.has_complete_utterance_verb_chain(vp, vp_parent)):
                return True
        return False


    def has_pp_between_commas(self, node):
        """

            Args:
                node (instance) - a <DOM Element> containing a nonterminal node.

            Returns:
                (bool) - returns True if node has a PP and it is between commas.

        """
        nt_node = self.get_nt_node(node)
        if nt_node:
            pp_terminal = [t for t in self.t_list if t.attributes['id'].value == self.get_first_syntactic_son(nt_node).attributes['idref'].value]
            return False if not self.is_pp(node)\
                         or len(pp_terminal) == 0\
                         or self.t_list[self.t_list.index(pp_terminal[0])-1].attributes['word'].value != ','\
                        else True


    def has_exception_advp(self, node):
        """

            Args:
                node (instance) - a <DOM Element> containing a nonterminal node.

            Returns:
                (bool) - returns True if node has an exception ADVP. We defined ADVP's which shouldn't be
                         immediately before a verb as exception ADVPs. In these cases, the subject appears after the ADVP.

        """
        nt_node = self.get_nt_node(node)
        left_vp_nonterminal_neighbor = nt_node.getElementsByTagName('edge')[-1]
        verb_terminal = [t for t in self.t_list if t.attributes['id'].value == left_vp_nonterminal_neighbor.attributes['idref'].value]
        if verb_terminal:
            return False if 'ks' in verb_terminal[0].attributes['extra'].value.split()\
                         or verb_terminal[0].attributes['word'].value.lower() not in EXCEPTION_ADVPS\
                    else True


    def has_oblique_pronoun(self, np):
        """

            Args:
                node (instance) - a <DOM Element> containing an NP node.

            Returns:
                (bool) - returns True if np is an oblique pronoun.

        """
        left_vp_nonterminal_neighbor = [nt for nt in self.nt_list if nt.attributes['id'].value == np.attributes['idref'].value][0].getElementsByTagName('edge')[-1]
        verb_terminal = [t for t in self.t_list if t.attributes['id'].value == left_vp_nonterminal_neighbor.attributes['idref'].value]
        if verb_terminal:
            return True if verb_terminal[0].attributes['word'].value.lower() in OBLIQUE_PRONOUNS else False


    def has_exception_verb(self, vp):
        """

            Args:
                t_list (list) - list of <DOM Element> objects. These objects are terminals of the syntactic tree.
                vp (instance) - a <DOM Element> containing an VP node.

            Returns:
                (bool) - returns True if vp has a verb that shouldn't be annotated.
                         We defined a list of some kind of verbs that are not annotated by

        """
        edge_list = vp.getElementsByTagName('edge')
        aux = [t for t in self.t_list if t.attributes['id'].value == edge_list[0].attributes['idref'].value]
        if not aux:
            return True
        verb_terminal = aux[0]
        pos = verb_terminal.attributes['pos'].value
        lemma = verb_terminal.attributes['lemma'].value
        extra = verb_terminal.attributes['extra'].value
        return True if (pos in ['v-inf', 'v-ger', 'v-pcp'])\
                    or (lemma == 'ser' and not self.is_verb_ser_exception(vp))\
                    or (lemma in IMPERSONAL_VERBS and extra != 'aux')\
                    or (extra == 'nofsubj')\
                else False


    def has_utterance_verb(self, vp):
        """

            Args:
                vp (instance) - a <DOM Element> containing a VP node.

            Returns:
                (bool) - returns True if vp has an utterance verb.

        """
        first_vp_element = self.get_first_syntactic_son(vp)
        return True if [t for t in self.t_list if t.attributes['id'].value == first_vp_element.attributes['idref'].value][0].attributes['lemma'].value in UTTERANCE_VERBS else False


    def has_no_left_neighbor(self, node, parent):
        """

            Args:
                node (instance) - a <DOM Element> containing a nonterminal node.
                parent (instance) - a <DOM Element> containing a nonterminal node, syntactic parent of node.

            Returns:
                (bool) - returns True if node has no left syntactic neighbor.

        """
        if node.hasAttribute('id'):
            return self.get_first_syntactic_son(parent).attributes['idref'].value == node.attributes['id'].value
        else:
            return self.get_first_syntactic_son(parent).attributes['idref'].value == node.attributes['idref'].value


    def has_complete_utterance_verb_chain(self, vp, parent):
        """

            Args:
                vp (instance) - a <DOM Element> containing a VP node.
                parent (instance) - a <DOM Element> containing a nonterminal node, syntactic parent of vp.

            Returns:
                (bool) - returns True if is in a utterance verb chain/rule.

        """
        edge_list = parent.getElementsByTagName('edge')
        for i in range(len(edge_list)):
            if edge_list[i].attributes['idref'].value == vp.attributes['id'].value:
                right_neighbor1 = [nt for nt in self.nt_list if nt.attributes['id'].value == edge_list[i+1].attributes['idref'].value]
                if right_neighbor1:
                    if right_neighbor1[0].attributes['cat'].value == 'np':
                        return True
                    elif right_neighbor1[0].attributes['cat'].value == 'advp':
                        right_neighbor2 = [nt for nt in self.nt_list if nt.attributes['id'].value == edge_list[i+2].attributes['idref'].value]
                        if right_neighbor2:
                            return True if right_neighbor2[0].attributes['cat'].value == 'np' else False


    def get_nt_node(self, node):
        """

            Args:
                node (instance) - a <DOM Element> instance, nonterminal elements of a syntactic tree.

            Returns:
                (list) - returns a list of <DOM Element> instances, VPs of the sentence.

        """
        nt_node = [nt for nt in self.nt_list if nt.attributes['id'].value == node.attributes['idref'].value]
        if nt_node:
            return nt_node[0]


    def get_nt_vps(self):
        """

            Args:
                nt_list (list) - a list of <DOM Element> instances, nonterminal elements of a syntactic tree.

            Returns:
                (list) - returns a list of <DOM Element> instances, VPs of the sentence.

        """
        return [i for i in self.nt_list if i.attributes['cat'].value == 'vp']


    def get_vp_parent(self, vp):
        """

            Args:
                vp (instance) - a <DOM Element> containing a VP node.
                nt_list (list) - a list of <DOM Element> instances, nonterminal elements of a syntactic tree.

            Returns:
                (instance) - returns a <DOM Element> instance that is the syntactic parent of vp.

        """
        for nt in self.nt_list:
            for edge in nt.getElementsByTagName('edge'):
                if edge.attributes['idref'].value == vp.attributes['id'].value:
                    return nt


    def get_left_neighbor(self, vp, parent, distance=1):
        """

            Args:
                vp (instance) - a <DOM Element> containing a VP node.
                parent (instance) - a <DOM Element> containing a nonterminal node, syntactic parent of vp.

            Returns:
                (instance) - returns a <DOM Element> instance of the left syntactic neighbor of vp.

        """
        edge_list = parent.getElementsByTagName('edge')
        for i in range(len(edge_list)):
            if edge_list[i].attributes['idref'].value == vp.attributes['id'].value:
                if i == 0:
                    first_vp_element = self.get_first_syntactic_son(vp)
                    for i in range(len(self.t_list)):
                        if self.t_list[i].attributes['id'].value == first_vp_element.attributes['idref'].value:
                            left_neighbor = minidom.Document().createElement('edge')
                            left_neighbor.setAttribute('idref', self.t_list[i - distance].attributes['id'].value)
                            left_neighbor.setAttribute('label', 'no left neighbor')
                            return left_neighbor
                return edge_list[i - distance]


    def get_first_syntactic_son(self, node):
        """

            Args:
                node (instance) - a <DOM Element> containing a nonterminal node.

            Returns:
                (instance) - returns a <DOM Element> instance of first syntactic son of node

        """
        return node.getElementsByTagName('edge')[0]


    def get_num_sons(self, edge):
        """

            Args:
                edge (instance) - a <DOM Element> containing a nonterminal node.

            Returns:
                (int) - returns the number of syntactic sons of edge.

        """
        nt_node = [nt for nt in self.nt_list if nt.attributes['id'].value == edge.attributes['idref'].value][0]
        return len(nt_node.getElementsByTagName('edge'))


    def select_insertion_position(self, vp, vp_parent, left_neighbor):
        """

            Returns:
                (str) - returns a string with the position of the subject to be inserted.

        """
        left_neighbor2 = self.get_left_neighbor(vp, vp_parent, 2)
        left_neighbor3 = self.get_left_neighbor(vp, vp_parent, 3)
        if [nt for nt in self.nt_list if nt.attributes['id'].value == left_neighbor.attributes['idref'].value] and self.is_advp(left_neighbor) and self.has_exception_advp(left_neighbor):
            method = str(0 - self.get_num_sons(left_neighbor))
        elif not self.is_comma_before(vp) and self.is_np(left_neighbor) and self.has_oblique_pronoun(left_neighbor):
            if not self.is_advp(left_neighbor2):
                method = '-1'
            elif self.is_advp(left_neighbor2) and not self.has_exception_advp(left_neighbor2) :
                method = '-1'
            elif self.is_advp(left_neighbor2) and self.has_exception_advp(left_neighbor2) :
                method = '-2'
        elif self.is_np(left_neighbor) and self.is_direct_object(left_neighbor) and not (self.is_np(left_neighbor2)):
            method = '-1'
        elif self.is_np(left_neighbor) and self.is_direct_object(left_neighbor) and self.is_advp(left_neighbor2) and self.is_np(left_neighbor3):
            method = '-2'
        else:
            method = None
        return method


    def create_node(self, method):
        """

            Args:
                method (str) - a string containing the type of node to be created.

            Returns:
                (instance) - returns a <DOM Element> instance of a syntactic tree node.

        """
        string_id = self.sentence.attributes['id'].value + "_" + "suj"

        if method in ['t_1S', 't_1P']:
            suj_node = self.dom.createElement('t')
            suj_node.setAttribute('pos', "pron-pers")
            suj_node.setAttribute('extra', 'left soia')
            if method == 't_1S':
                suj_node.setAttribute('id', string_id + str(self.COUNT_SUJ))
                suj_node.setAttribute('lemma', "eu")
                suj_node.setAttribute('word', "eu")
            else:
                suj_node.setAttribute('id', string_id + str(self.COUNT_SUJ))
                suj_node.setAttribute('lemma', u"nós")
                suj_node.setAttribute('word', u"nós")
        elif method == 'np':
            suj_node = self.dom.createElement('nt')
            suj_node.setAttribute('cat', 'np')
            suj_node.setAttribute('id', string_id + str(600 + self.COUNT_SUJ))

            suj_node2 = self.dom.createElement('edge')
            suj_node2.setAttribute('idref', string_id + str(self.COUNT_SUJ))
            suj_node.appendChild(self.dom.createTextNode('\n\t\t\t\t\t\t'))
            suj_node.appendChild(suj_node2)
            suj_node.appendChild(self.dom.createTextNode('\n\t\t\t\t\t'))
        elif method == 'edge':
            suj_node = self.dom.createElement('edge')
            suj_node.setAttribute('idref', string_id + str(600 + self.COUNT_SUJ))
        return suj_node


    def insert_terminal_nodes(self, vp, method):
        """

            Args:
                vp (instance) - a <DOM Element> containing a VP node.
                terminals (list) - list of <DOM Element> instances of terminal nodes.
                method (str) - a string containing the position of the subject to be inserted.

        """
        element_after_suj = self.get_first_syntactic_son(vp)
        verb_terminal = [t for t in self.t_list if t.attributes['id'].value == element_after_suj.attributes['idref'].value][0]

        if '1S' in verb_terminal.attributes['morph'].value.split():
            suj_t_node = self.create_node('t_1S')
        elif '1P' in verb_terminal.attributes['morph'].value.split():
            suj_t_node = self.create_node('t_1P')

        slice_t_index = [self.t_list.index(t) for t in self.t_list if t.attributes['id'].value == element_after_suj.attributes['idref'].value][0] * 2

        if method == '-1' and self.t_list[(slice_t_index / 2) - 1].attributes['pos'].value != 'pu':
            slice_t_index -= 1
        elif method == '-2' and self.t_list[(slice_t_index / 2) - 1].attributes['pos'].value != 'pu':
            slice_t_index -= 3

        if self.terminals.childNodes[slice_t_index].nodeType ==  self.dom.TEXT_NODE:
            slice_t_index += 1

        if self.terminals.childNodes[slice_t_index].attributes['word'].value[0].isupper():
            self.terminals.childNodes[slice_t_index].attributes['word'].value = self.terminals.childNodes[slice_t_index].attributes['word'].value.lower()
            suj_t_node.setAttribute('word', suj_t_node.attributes['word'].value.capitalize())

        self.terminals.childNodes.insert(slice_t_index, self.dom.createTextNode('\n\t\t\t\t\t'))
        self.terminals.childNodes.insert(slice_t_index, suj_t_node)


    def insert_nonterminal_nodes(self, vp, vp_parent, neighbor):
        """

            Args:
                vp (instance) - a <DOM Element> containing a VP node.
                vp_parent (instance) - a <DOM Element> containing the syntactic parent of vp.
                neighbor (instance) - a <DOM Element> containing syntactic neighbor of vp.
                nonterminals (list) - list of <DOM Element> instances of nonterminal nodes.
                terminals (list) - list of <DOM Element> instances of terminal nodes.

        """
        element_after_suj = self.get_first_syntactic_son(vp)
        verb_terminal = [t for t in self.t_list if t.attributes['id'].value == element_after_suj.attributes['idref'].value][0]

        suj_np_node = self.create_node('np')
        suj_np_node.childNodes[1].attributes['label'] = 'H'
        suj_edge_node = self.create_node('edge')
        suj_edge_node.attributes['label'] = 'SUBJ'
        edge_list = vp_parent.getElementsByTagName('edge')
        if neighbor.attributes['label'].value == 'no left neighbor':
            slice_edge_index = [edge_list.index(edge) for edge in edge_list if edge.attributes['idref'].value == vp.attributes['id'].value][0]
        else:
            slice_edge_index = [edge_list.index(edge) for edge in edge_list if edge.attributes['idref'].value == neighbor.attributes['idref'].value][0]

        if self.nonterminals.childNodes[slice_edge_index].nodeType == self.dom.TEXT_NODE:
            slice_edge_index += 1
        self.nonterminals.childNodes[self.nonterminals.childNodes.index(vp_parent)].childNodes.insert(slice_edge_index, self.dom.createTextNode('\n\t\t\t\t\t'))
        self.nonterminals.childNodes[self.nonterminals.childNodes.index(vp_parent)].childNodes.insert(slice_edge_index, suj_edge_node)
        self.nonterminals.childNodes.insert(-1, self.dom.createTextNode('\n\t\t\t\t\t'))
        self.nonterminals.childNodes.insert(-1, suj_np_node)


def insert_first_person_subj(PATH_INPUT):
    """

            Args:
                input_dir (str) - String with the input directory to be processed.
                output_dir (str) - String with the directory with the script output.


    """
    insertor = Subject_insertor()

    with open(PATH_INPUT) as fp:
        insertor.dom = minidom.parse(fp)

    s_list = insertor.dom.getElementsByTagName('s')
    for s in s_list:
        insertor.load(s)

        for vp in insertor.vp_list:
            insertor.COUNT_SUJ += 1
            if not insertor.is_first_person_verb(vp):
                continue
            try:
                vp_parent = insertor.get_vp_parent(vp)
                left_neighbor = insertor.get_left_neighbor(vp, vp_parent)

                if insertor.is_insertion_needed(vp, vp_parent, left_neighbor):
                    insertor.insert_terminal_nodes(vp, insertor.select_insertion_position(vp, vp_parent, left_neighbor))
                    insertor.insert_nonterminal_nodes(vp, vp_parent, left_neighbor)
                    insertor.t_list = insertor.terminals.getElementsByTagName('t')
            except AttributeError:
                pass
    with codecs.open(PATH_INPUT, 'w', encoding='utf-16') as fp:
        fp.write(insertor.dom.toxml())
    return insertor.dom
