#!/usr/bin/env python
# -*- encoding:utf-8 -*-
import argparse
import codecs

import sys

from src.bin.srl.main import load_models
from srl import SRLClassifier

if __name__ == "__main__":

    argparser = argparse.ArgumentParser(description='Rule-Based AMR Parser')
    argparser.add_argument('-f', '--file', help='Input file', required=True)
    # argparser.add_argument('-s', '--save', help='Save result', required=True)
    args = argparser.parse_args()
    # Clear corpus
    # clear_corpus.extract_snt('corpus/test_gold.txt')
    # exit()
    print 'Read file ...'
    # s = []
    sentences = []
    f = codecs.open(args.file, 'r', 'UTF-8')
    # for line in f.readlines():
    #     if line.strip():
    #         word, _ = line.strip().split('\t')
    #         s.append(word)
    #     else:
    #         sentences.append(' '.join(s))
    #         s = []
    sentences = [item.strip() for item in f.readlines()]
    f.close()
    print 'Sentence(s): ', sentences
    # Loading models ...
    print 'Done'
    print 'Loading models ...'
    AI_model, AC_model = load_models()
    print 'Done'
    # Initialize SRLClassifier
    print 'Classifying sentences'
    clf = SRLClassifier(args.file, sentences, AI_model, AC_model)
    print 'Done'
