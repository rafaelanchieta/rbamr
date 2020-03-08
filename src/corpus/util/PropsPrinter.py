'''
Created on Apr 26, 2012

@author: feralvam
'''

from src.corpus.reader.pbrconll import PropbankBrConllCorpusReader, ConllSRLInstanceList

# from corpus.reader.pbrconll import PropbankBrConllCorpusReader, ConllSRLInstanceList


PATH_ROOT = '/home/rafael/PycharmProjects/RBAMR/src/bin/resources/corpus/test/'
# PATH_ROOT = os.path.dirname(__file__) + "/../../bin/resource/corpus/test/"
# print PATH_ROOT

# PATH_ROOT = "/Users/feralvam/Dropbox/ICMC/Mestrado/Densenvolvimento/APSBr_Sup/resources/corpus/test/"
# PATH_ROOT = "../../../resources/corpus/test/"

column_types = ["id", "words", "lemma", "pos", "feat", "ignore", "ignore", "tree", "srl"]


def props_printer():
    reader = PropbankBrConllCorpusReader(PATH_ROOT, "inputConst.conll", column_types, None, "FCL", False, True, "utf-8")
    prop_corpus = open(PATH_ROOT + "inputConst_Props.conll", "w")

    for ins in reader.srl_instances(None, None, False):
        ins_aux = ConllSRLInstanceList(ins.tree, ins)
        prop_corpus.write(ins_aux.pprint())
        prop_corpus.write("\n")

    # if i == 1000: break

#	print "Process finished."
