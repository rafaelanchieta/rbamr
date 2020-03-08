'''
Created on Sep 25, 2012

@author: fernando
'''

from __future__ import unicode_literals

# from corpus.reader.pbrconll import ConllSRLInstanceList
from nltk.corpus.reader.conll import ConllSRLInstance

from src.corpus.reader.pbrconll import ConllSRLInstanceList


def _compare_sentences(ins1, ins2):
    if (ins1 == None) or (ins2 == None):
        return -1

    if (ins1.tree == ins2.tree):
        return 0
    else:
        return -1


def pprint_output(tagged_argcands, writer):
    sent_tagged_props = None
    prev_ins = None
    tagged_spans = []
    for argcand in tagged_argcands:

        ins = argcand[0]["ins"]
        # Check if it's a new sentence
        if (_compare_sentences(prev_ins, ins) != 0):
            # It's either the first or the instance of a new sentence.
            if (prev_ins != None):
                # It's a new sentence
                sent_tagged_props.append(ConllSRLInstance(prev_ins.tree, prev_ins.verb_head, prev_ins.verb_stem, prev_ins.roleset, tagged_spans))
                # Print the propositions of the previous one
                var = sent_tagged_props.pprint().encode('utf-8')
                # var = sent_tagged_props.pprint()
                writer.write(var)
                # Print a line to separate sentences
                writer.write("\n")

            # Create a new list of propositions for the new sentence
            sent_tagged_props = ConllSRLInstanceList(ins.tree)
            if (argcand[-1] != "NULL"):
                tagged_spans = [(argcand[0]["info"]["span"],argcand[-1])]
            else:
                tagged_spans = []
        else:
            # Check if it's a new instance of the same sentence
            if (prev_ins.verb_head != ins.verb_head):
                sent_tagged_props.append(ConllSRLInstance(prev_ins.tree, prev_ins.verb_head, prev_ins.verb_stem, prev_ins.roleset, tagged_spans))
                if (argcand[-1] != "NULL"):
                    tagged_spans = [(argcand[0]["info"]["span"],argcand[-1])]
                else:
                    tagged_spans = []
            else:
                if (argcand[-1] != "NULL"):
                    tagged_spans.append( (argcand[0]["info"]["span"],argcand[-1]) )

        prev_ins = ins

    sent_tagged_props.append(ConllSRLInstance(prev_ins.tree, prev_ins.verb_head, prev_ins.verb_stem, prev_ins.roleset, tagged_spans))
    writer.write(sent_tagged_props.pprint().encode('utf-8'))
    writer.write("\n")
    writer.close()

    return
