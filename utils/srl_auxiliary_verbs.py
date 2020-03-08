#-*- encoding: utf-8 -*-
"""
__author__    = "Nathan Siegle Hartmann"
__contact__   = "nathanshartmann@gmail.com"
__copyright__ = "Copyright 2014, PROSA project"
__license__   = ""
__date__      = "13-11-14"
__version__   = "1.1"
"""

import codecs
from xml.dom import minidom

PATH_RESOURCES = '/home/rafael/PycharmProjects/RBAMR/src/bin/resources/'
#PATH_RESOURCES = path.dirname(path.realpath(__file__)) +\
#    '/../src/bin/resources/'

RULES = [
         ('acabar', '', 'v-ger', 'acabar.201', 'auxiliar aspectual', 'argm-asp'),
         ('acabar', 'de', 'v-inf', 'acabar.202', 'auxiliar aspectual', 'argm-asp'),
         ('acabar', 'por', 'v-inf', 'acabar.203', 'auxiliar aspectual', 'argm-asp'),
         ('andar', '', 'v-ger', 'andar.201', 'auxiliar aspectual', 'argm-asp'),
         ('cessar', 'de', 'v-inf', 'cessar.201', 'auxiliar aspectual', 'argm-asp'),
         ('chegar', 'a', 'v-inf', 'chegar.201', 'auxiliar aspectual', 'argm-asp'),
         ('começar', 'a', 'v-inf', 'comecar.201', 'auxiliar aspectual', 'argm-asp'),
         ('começar', 'por', 'v-inf', 'comecar.202', 'auxiliar aspectual', 'argm-asp'),
         #('conseguir', '', 'v-ger', 'conseguir.202', 'auxiliar aspectual', 'argm-asp'),
         ('continuar', 'a', 'v-inf', 'contunuar.201', 'auxiliar aspectual', 'argm-asp'),
         ('correr', 'a', 'v-inf', 'correr.201', 'auxiliar aspectual', 'argm-asp'),
         ('costumar', '', 'v-inf', 'costumar.201', 'auxiliar aspectual', 'argm-asp'),
         ('dar', 'de', 'v-inf', 'dar.201', 'auxiliar aspectual', 'argm-asp'),
         ('deixar', 'de', 'v-inf', 'deixar.201', 'auxiliar aspectual', 'argm-asp'),
         ('desatar', 'a', 'v-inf', 'desatar.201', 'auxiliar aspectual', 'argm-asp'),
         ('dever', '', 'v-inf', 'dever.201', 'auxiliar modal', 'argm-mod'),
         ('estar', 'para', 'v-inf', 'estar.201', 'auxiliar aspectual', 'argm-asp'),
         ('estar', '', 'v-ger', 'estar.202', 'auxiliar aspectual', 'argm-asp'),
         ('estar', 'por', 'v-inf', 'estar.204', 'auxiliar aspectual', 'argm-asp'),
         ('ficar', '', 'v-ger', 'ficar.201', 'auxiliar aspectual', 'argm-asp'),
         ('ficar', 'sem', 'v-inf', 'ficar.202', 'auxiliar aspectual', 'argm-asp'),
         ('ficar', 'de', 'v-inf', 'ficar.203', 'auxiliar modal', 'argm-mod'),
         ('haver', 'de', 'v-inf', 'haver.201', 'auxiliar modal', 'argm-mod'),
         ('haver', 'que', 'v-inf', 'haver.202', 'auxiliar modal', 'argm-mod'),
         ('haver', '', 'v-pcp', 'haver.203', 'auxiliar temporal', 'argm-tml'),
         ('hesitar', 'em', 'v-inf', 'hesitar.201', 'auxiliar aspectual', 'argm-asp'),
         ('ir', '', 'v-ger', 'ir.201', 'auxiliar aspectual', 'argm-asp'),
         ('ir', '', 'v-inf', 'ir.202', 'auxiliar temporal', 'argm-tml'),
         ('ousar', '', 'v-inf', 'ousar.201', 'auxiliar aspectual', 'argm-asp'),
         ('parar', 'de', 'v-inf', 'parar.201', 'auxiliar aspectual', 'argm-asp'),
         ('passar', 'a', 'v-inf', 'passar.201', 'auxiliar aspectual', 'argm-asp'),
         ('permanecer', '', 'v-ger', 'permanecer.201', 'auxiliar aspectual', 'argm-asp'),
         ('poder', '', 'v-inf', 'poder.201', 'auxiliar modal', 'argm-mod'),
         ('recomeçar', 'a', 'v-inf', 'recomeçar.201', 'auxiliar aspectual', 'argm-asp'),
         ('sair', '', 'v-ger', 'sair.201', 'auxiliar aspectual', 'argm-asp'),
         ('seguir', '', 'v-ger', 'seguir.201', 'auxiliar aspectual', 'argm-asp'),
         ('ser', '', 'v-pcp', 'ser.201', 'auxiliar de voz passiva', 'argm-pas'),
         ('ter', 'de', 'v-inf', 'ter.201', 'auxiliar modal', 'argm-mod'),
         ('ter', 'que', 'v-inf', 'ter.202', 'auxiliar modal', 'argm-mod'),
         ('ter', '', 'v-pcp', 'ter.203', 'auxiliar temporal', 'argm-tml'),
         ('terminar', '', 'v-ger', 'terminar.201', 'auxiliar aspectual', 'argm-asp'),
         ('tornar', 'a', 'v-inf', 'tornar.201', 'auxiliar aspectual', 'argm-asp'),
         ('vir', '', 'v-ger', 'vir.201', 'auxiliar aspectual', 'argm-asp'),
         ('vir', 'a', 'v-inf', 'vir.202', 'auxiliar aspectual', 'argm-asp'),
         ('viver', '', 'v-ger', 'viver.201', 'auxiliar aspectual', 'argm-asp'),
         ('voltar', 'a', 'v-inf', 'voltar.201', 'auxiliar aspectual', 'argm-asp')
        ]


def get_target_verb(sentence):
	"""

		Args:
			sentence (instance): a <DOM Element> object. A instance (sentence) of the annotation instances.

		Returns:
			(instance) - a <DOM Element> object of the terminal target verb.

	"""
	frame_target = [frame for frame in sentence.getElementsByTagName('frame') if frame.attributes['name'].value == 'Argumentos']
	assert frame_target != [], "Sentence has no frame Arguments"
	target_verb_id = frame_target[0].getElementsByTagName('fenode')[0].attributes['idref'].value
	return [terminal for terminal in sentence.getElementsByTagName('t') if terminal.attributes['id'].value == target_verb_id][0]


def get_values(terminals, indexes):
    """

        Args:
            terminals (list) - list of <DOM Element> objects. These objects are syntactic tree`s terminals.
            indexes (list) - indexes to filter terminals.

        Returns:
            (list) - a subset of terminals.

    """
    return [terminals[index] for index in indexes]


def filter_rule(key1, key2=None, key3=None):
    """

        Args:
            key1 (str) - verb starting a rule in RULES.
            key2 (str, optional) - preposition contained in a rule in RULES

        Returns:
            (list) - a subset of RULES containing rules accepted by the restrictions (key1 and/or key).

    """
    if key2 is None:
        return [rule for rule in RULES if rule[0] == key1]
    elif key2 is not None and key3 is None:
        return [rule for rule in RULES if rule[0] == key1 and rule[1] == key2]
    else:
        return [rule for rule in RULES if rule[0] == key1 and rule[1] == key2 and rule[2] == key3]


def find_candidates(terminals, id_target_verb):
    """

        Args:
            terminals (list) - list of <DOM Element> objects. These objects are terminals of the syntactic tree.
            id_target_verb (str) - id of the annotation instance target verb.

        Returns:
            (list) - lists of <DOM Element> objects. Candidates which an auxiliary verb may happen.

    """
    possibles = []
    length = len(terminals)

    for i in range(len(terminals)-1):

        if terminals[i].attributes['pos'].value[0] == 'v':
            if terminals[i+1].attributes['pos'].value in ['prp', 'Vaux','Vaux-s']:

                if length-i >= 3 and terminals[i+2].attributes['pos'].value[0] == 'v':
                    if terminals[i+2].attributes['id'].value == id_target_verb or 'aux' in terminals[i+2].attributes['extra'].value.split():
                        possibles.append(get_values(terminals, [i, i+1, i+2]))
                elif length-i >= 4 and terminals[i+2].attributes['pos'].value == 'adv':
                    if terminals[i+3].attributes['id'].value == id_target_verb or 'aux' in terminals[i+3].attributes['extra'].value.split():
                        possibles.append(get_values(terminals, [i, i+1, i+2, i+3]))

            elif terminals[i+1].attributes['pos'].value[0] == 'v':
                if terminals[i+1].attributes['id'].value == id_target_verb or 'aux' in terminals[i+1].attributes['extra'].value.split():
                    possibles.append(get_values(terminals, [i, i+1]))
            elif terminals[i+1].attributes['pos'].value == 'adv':
                #válido apenas algumas vezes

                if length-i >= 3 and terminals[i+2].attributes['id'].value == id_target_verb:
                    possibles.append(get_values(terminals, [i, i+1, i+2]))

    return possibles


def get_auxiliary_verb(terminals, target_verb):
    """

        Args:
            terminals (list) - list of <DOM Element> objects. These objects are terminals of the syntactic tree.
            target_verb (instance) - <DOM Element> object. This object is a terminal of the syntactic tree.

        Returns:
            (list) - lists of <DOM Element> objects. Candidates which an auxiliary verb may happen.

    """
    verbs1_rules = [rule[0] for rule in RULES]
    words = [terminal.attributes['word'].value for terminal in terminals]
    verb1_expected = terminals[0].attributes['lemma'].value.encode('utf-8')

    if verb1_expected not in [rule[0] for rule in RULES]:
        return None
    if int(target_verb.attributes['id'].value.split('_')[1]) < int(terminals[0].attributes['id'].value.split('_')[1]):
    	return None
    if int(target_verb.attributes['id'].value.split('_')[1]) - int(terminals[0].attributes['id'].value.split('_')[1]) > 5:
    	return None

	[terminal for terminal in terminals if terminal.attributes['id'].value == id_target_verb]
    #rule V + V
    if verb1_expected in verbs1_rules and len(words) == 2:
        verbs2_rules = [rule[2] for rule in filter_rule(verb1_expected)]
        verb2_expected = terminals[1].attributes['pos'].value.encode('utf-8')
        if verb2_expected in verbs2_rules:
            #algumas vezes a cadeia verbo1-verbo2 é aceita, porém ela necessita de preposição para ser válida
            #nesse caso o retorno da regra é nulo
            rule = [rule[5] for rule in filter_rule(verb1_expected, '', verb2_expected)]
            if rule:
                return rule[0]
            else:
                return None
            #return [rule[5] for rule in filter_rule(verb1_expected)][0]

    #rule  V + PRP + V, V + ADV + V
    if verb1_expected in verbs1_rules and len(words) == 3:
        if terminals[1].attributes['pos'].value.encode('utf-8') in ['prp', 'Vaux-s']:
            prep_expected = words[1]
            preps_rules = [rule[1] for rule in filter_rule(verb1_expected)]

            if prep_expected in preps_rules:
                verbs2_rules = [rule[2] for rule in filter_rule(verb1_expected, preps_rules[preps_rules.index(prep_expected)])]
                if terminals[2].attributes['pos'].value in verbs2_rules:
                    return [rule[5] for rule in filter_rule(verb1_expected, preps_rules[preps_rules.index(prep_expected)])][0]

        else:
            verbs2_rules = [rule[2] for rule in filter_rule(verb1_expected)]
            verb2_expected = terminals[2].attributes['pos'].value.encode('utf-8')
            if verb2_expected in verbs2_rules:
                return [rule[5] for rule in filter_rule(verb1_expected)][0]

    #rule V + ADV + ADV + V
    if verb1_expected in verbs1_rules and len(words) == 4:
        if terminals[1].attributes['pos'].value.encode('utf-8') in ['prp', 'Vaux-s'] and terminals[2].attributes['pos'].value.encode('utf-8') == 'adv':
            prep_expected = words[1]
            preps_rules = [rule[1] for rule in filter_rule(verb1_expected)]

            if prep_expected in preps_rules:
                verbs2_rules = [rule[2] for rule in filter_rule(verb1_expected, preps_rules[preps_rules.index(prep_expected)])]
                if terminals[3].attributes['pos'].value in verbs2_rules:
                    return [rule[5] for rule in filter_rule(verb1_expected, preps_rules[preps_rules.index(prep_expected)])][0]


def annotate(corpus_file, sentence, candidate, role):
    """

        Args:
            corpus_file (object): a <xml.dom.minidom.Document> object of a input file
            sentence (object): a <DOM Element> object. A instance (sentence) of the annotation instances.
            candidate (list) - list of <DOM Element> objects. A candidate which an auxiliary verb may happen.
            role (str) - role to be annotated

    """
    fe_node = corpus_file.createElement('fe')
    fe_node.setAttribute('name', role)
    fenode_node = corpus_file.createElement('fenode')
    fenode_node.setAttribute('idref', candidate[0].attributes['id'].value)
    fe_node.appendChild(fenode_node)

    frame = sentence.getElementsByTagName('frame')[0]
    fe_node_list = sentence.getElementsByTagName('fe')
    if len(fe_node_list) > 0:
        fe_node_id = fe_node_list[-1].attributes['id'].value.split('_')
        fe_node_id = '_'.join(fe_node_id[:-1]) + '_e' + str(int(fe_node_id[-1][1:]) + 1)
    else:
        fe_node_id = 'null_e1'

    fe_node.setAttribute('id', fe_node_id)
    frame.appendChild(fe_node)


def insert_auxiliary_verbs():
        """

        Args:
            input_file_name (str): input data to be processed (xml file in PropBank.Br style (Tiger XML))

        """
	INPUT_PATH = PATH_RESOURCES + 'input.xml'
        with open(INPUT_PATH, 'r') as input_fp:
            corpus_file = minidom.parse(input_fp)

        sentences = corpus_file.getElementsByTagName('s')

        with codecs.open(INPUT_PATH, 'w', encoding='utf-16') as output_fp:
            output_fp.write(u'<corpus>\n\t<body>\n\t\t')
            # output_fp.write(u'<corpus>\n' + corpus_file.getElementsByTagName('head')[0].toxml() + '\n\t<body>\n\t\t')

            for sentence in sentences:
            	target_verb = get_target_verb(sentence)
                auxiliary_verbs_candidates = find_candidates(sentence.getElementsByTagName('t'),
                                                             sentence.getElementsByTagName('target')[0].childNodes[1].attributes['idref'].value)

                for candidate in auxiliary_verbs_candidates:
                    role = get_auxiliary_verb(candidate, target_verb)
                    if role is not None:
                        annotate(corpus_file, sentence, candidate, role)

                output_fp.write(sentence.toxml() + '\n')
            output_fp.write(u'\t</body>\n</corpus>')


if __name__ == '__main__':
#
#    assert len(argv) == 2, 'Usage: $python thisfile [input_file]'
#    #example:  python srl\ auxiliary\ verbs.py input_file.xml
    insert_auxiliary_verbs()
