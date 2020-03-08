# -*- encoding:utf-8 -*-

import re

CONTRACTIONS = {
    # Complementação de 'a'
    'a': {
        # Contração com artigo definido
        'a': 'à',
        'as': 'às',
        'aquele': 'àquele',
        'aqueles': 'àqueles',
        'aquela': 'àquela',
        'aquelas': 'àquelas',
        'aquilo': 'àquilo',

        # Combinação com advérbio',
        'onde': 'aonde'},

    # Complementação "de"
    'de': {
        'o': 'do',
        'os': 'dos',
        'a': 'da',
        'as': 'das',

        # Contração com pronome pessoal',
        'ele': 'dele',
        'eles': 'deles',
        'ela': 'dela',
        'elas': 'delas',

        # Contração com pronome demonstrativo',
        'este': 'deste',
        'estes': 'destes',
        'esta': 'desta',
        'estas': 'destas',
        'esse': 'desse',
        'esses': 'desses',
        'essa': 'dessa',
        'essas': 'dessas',
        'aquele': 'daquele',
        'aqueles': 'daqueles',
        'aquela': 'daquela',
        'aquelas': 'daquelas',
        'isto': 'disto',
        'isso': 'disso',
        'aquilo': 'daquilo',

        # Contração com advérbio',
        'aqui': 'daqui',
        'aí': 'daí',
        'ali': 'dali',
        'acolá': 'dacolá',
        'onde': 'donde',

        # Contração com pronome indefinido',
        'outro': 'doutro',
        'outros': 'doutros',
        'outra': 'doutra',
        'outras': 'doutras',
        'outrem': 'doutrem'},

    # Preposição 'em'
    'em': {
        # Contração com artigo definido',
        'o': 'no',
        'os': 'nos',
        'a': 'na',
        'as': 'nas',

        # Contração com artigo indefinido',
        'um': 'num',
        'uns': 'nuns',
        'uma': 'numa',
        'umas': 'numas',

        # Contração com pronome pessoal',
        'ele': 'nele',
        'eles': 'neles',
        'ela': 'nela',
        'elas': 'nelas',

        # Contração com pronome demonstrativo',
        'o': 'no',
        'os': 'nos',
        'a': 'na',
        'as': 'nas',
        'esse': 'nesse',
        'esses': 'nesses',
        'essa': 'nessa',
        'essas': 'nessas',
        'este': 'neste',
        'estes': 'nestes',
        'esta': 'nesta',
        'estas': 'nestas',
        'aquele': 'naquele',
        'aqueles': 'naqueles',
        'aquela': 'naquela',
        'aquelas': 'naquelas',
        'isto': 'nisto',
        'isso': 'nisso',
        'aquilo': 'naquilo',

        # Contração com pronome indefinido',
        'outro': 'noutro',
        'outros': 'noutros',
        'outra': 'noutra',
        'outras': 'noutras',
        'outrem': 'noutrem'},

    # Complemento de 'para'
    'para': {
        # Contração com artigo definido ou pronome',
        'os': 'pro',
        'os': 'pros',
        'a': 'pra',
        'as': 'pras'},

    # Complementação "por"',
    'por': {
        # Contração com artigo definido ou pronome',
        'o': 'pelo',
        'os': 'pelos',
        'a': 'pela',
        'as': 'pelas',

        # Entre preposições',
        'entre': 'dentre'}
}


def parse_list(file, terminals, expand=False, comp_contractions=False):
    '''
    Change the flat output format of PLAVRAS to a dictonary

    :param file -> file to be parsed
    :param sentence The sentence that will be processed
    :param expand If True, the entities identified by PALAVRAS are splitted
           For instance, Dilma=Rousseff is showed two words Dilma and Rousseff
    :param comp_contractions If True, the contractions from PALAVRAS are
           compressed, as de + o as showed as do
    '''

    # parsed_sentence = self.parse(sentence)
    # self.local_parser(sentence)
    regex = r'#(-?[0-9]+)->([0-9]+)'

    parsed_sentence = open(file, 'r').read()

    default = lambda x, y: x[0] if len(x) > 0 else y

    tokens = list()
    pointers = dict()

    flag = False

    if terminals[0].attributes['word'].value == 'Eu':
        flag = True
        tokens.append(('Eu', {
            'lemma': 'eu',
            'morpho': ['M/F', '1S', 'NOM'],
            'POS': 'pron-pers',
            'semantic': ['eu'],
            'relation': '#-1->1'}))

    for line in parsed_sentence.split('\n'):

        if len(line.strip()) > 0:

            relation = default(re.findall('#\d+->\d+', line), '')

            original_word = re.findall('[^\t ]+', line)[0]
            original_word = [original_word]

            if expand and original_word[0] != '=':
                original_word = original_word[0].split('=')

            for word in original_word:
                if word.startswith('$'):
                    word = word[1:]
                    lemma = word
                    morpho = ['punct']
                    pos = 'punct'
                    word = word.replace('=', ' ')
                    semantic_info = ['']

                else:
                    lemma = default(
                        re.findall('(?<=\[)[^\]]+', line), word)

                    # Morpho Syntactic information
                    morpho = default(re.findall(
                        '[^>\[\]]+@', line), '', ).strip().split()
                    if len(morpho) > 0:
                        morpho.pop(-1)

                    # The word id is its position in sentence
                    pos = default(re.findall('(?<=@)[^ ]+', line), '')

                    semantic_info = re.findall('(?<=<)[^> ]+', line)

                if len(tokens) > 0:
                    contraction = CONTRACTIONS.get(
                        tokens[-1][0], {}).get(word, None)

                    if not (contraction is None):
                        tokens[-1][1]['lemma'] = contraction
                        tokens[-1] = (contraction, tokens[-1][1])
                        word = None

                try:
                    if morpho[2] == '1S' and not flag:
                        target = re.search(regex, relation).group(1)
                        tokens.append(('eu', {
                            'lemma': 'eu',
                            'morpho': ['M/F', '1S', 'NOM'],
                            'POS': 'pron-pers',
                            'semantic': ['eu'],
                            'relation': '#-2->' + target}))
                except IndexError:
                    pass
                flag = False
                if not (word is None):
                    tokens.append((word, {
                        'lemma': lemma,
                        'morpho': morpho,
                        'POS': pos,
                        'semantic': semantic_info,
                        'relation': relation, }))

                    index = relation.replace('#', '').split('->')[0]
                    pointers[index] = len(tokens) - 1

    return tokens, pointers