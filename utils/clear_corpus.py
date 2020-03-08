import codecs
import re


def extract_snt(file):
    lines = codecs.open(file, 'r', 'utf-8').readlines()
    corpus = codecs.open(file + '.snt', 'w', 'utf-8')
    regex = r'# ::snt (.+)'

    for line in lines:
        match = re.match(regex, line)
        if match:
            corpus.write(match.group(1))
            corpus.write('\n')
    corpus.close()
