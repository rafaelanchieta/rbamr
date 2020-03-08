# -*- coding: utf-8 -*-
'''
Created on Mar 28, 2012

@author: Fernando Alva Manchego
'''

import string
from collections import OrderedDict
from nltk.probability import FreqDist
from src.corpus.reader.pbrconll import PropbankBrConllCorpusReader
#from corpus.reader.pbrconll import PropbankBrConllCorpusReader


def dep_syntactic_frequencies(reader, exclude=[]):
    synt_freq = FreqDist()
    for sent in reader.dep_parsed_sents():
        for node in sent.nodelist:
            if not node["rel"] in exclude:
                synt_freq.inc(node["rel"])
    return synt_freq

def dep_semantic_frequencies (reader):
    sem_freq = dict()
    for ins in reader.dep_srl_instances():
        for _, arg_id in ins.arguments:
            # Arguments labeled as "C-" are already part of an argument,
            # so they shouldn't be counted again.
            if "C-" in arg_id or "R-" in arg_id: continue
            if arg_id in sem_freq:
                sem_freq[arg_id] += 1
            else:
                sem_freq[arg_id] = 1
    return sem_freq

def statistics_pbr_consituent(reader):

    # For counting sentences
    sent_num = 0
    
    # For counting tokens
    token_num = 0
    
    # For counting propositions
    prop_num = 0
    
    # For counting verbs
    verb_freq = dict()
    
    # For counting arguments
    arg_num = 0
    arg_freq = dict()
    
    
    for sent in reader.sents():
        sent_num += 1
        # Counting tokens
        for word in sent:
            if not (word.isdigit() or (word in string.punctuation)):
                token_num += 1
    
    for sent_ins in reader.srl_instances(None, None, False):
        
        for ins in sent_ins:
            # Each instance is a new proposition to be counted
            prop_num += 1
            
            # Determine the frequency of the target verbs
            if (ins.verb_stem in verb_freq):
                verb_freq[ins.verb_stem] += 1
            else:
                verb_freq[ins.verb_stem] = 1
        
            # Determine the frequency of the arguments
            for _, argid in ins.arguments:
                # Arguments labeled as "C-" are already part of an argument,
                # so they shouldn't be counted again.
                if "C-" in argid: continue
                if (argid in arg_freq):
                    arg_freq[argid] += 1
                else:
                    arg_freq[argid] = 1
                
    verb_num = len(verb_freq)
    
    print "Sentences: {}".format(sent_num)
    print "Tokens: {}".format(token_num)
    print "Propositions: {}".format(prop_num)
    print "Verbs: {}".format(verb_num)
    
    # Printing the frequency of the arguments
    arg_freq_keys = arg_freq.keys()
    arg_freq_keys.sort()
    for key in arg_freq_keys:
        arg_num += arg_freq[key]
        print "{} : {}".format(key.upper(), arg_freq[key])
        
    print "Arguments: {}".format(arg_num)
    
    return

def dep_contingency_table(reader):
    
    stats_args = OrderedDict()
    sem_labels = OrderedDict()
    synt_labels = OrderedDict()
    
    num_ins = 0
    
    # Calculate the statistics
    for ins in reader.dep_srl_instances():
        num_ins += 1
        # print "Processing instance {:}".format(num_ins)
        for arg_head, arg_id in ins.arguments:
            # Don't double count split arguments
            if "C-" in arg_id or "R-" in arg_id: continue
            
            # Get the syntactic function
            for node in ins.dep_graph.nodelist:
                if node["address"] == arg_head: 
                    arg_synt = node["rel"]
                    if arg_synt in synt_labels:
                        synt_labels[arg_synt] += 1
                    else:
                        synt_labels[arg_synt] = 1
                        
            if not arg_id in stats_args:
                stats_args[arg_id] = OrderedDict()
                
            # Make the count
            if arg_synt in stats_args[arg_id]:
                stats_args[arg_id][arg_synt] += 1
            else:  
                stats_args[arg_id][arg_synt] = 1
                
            if arg_id in sem_labels:
                sem_labels[arg_id] += 1
            else:
                sem_labels[arg_id] = 1
                
    return synt_labels, sem_labels, stats_args
    
    
def pprint_conttable(synt_labels, sem_labels, stats_args):
    
    # Sort the syntactic labels by frequency
    synt_labels_sorted = synt_labels.items()
    synt_labels_sorted.sort(key=lambda (k,v):v,reverse=True)
    
    # Print the statistics
    title = "{:>6}\t".format(" ")
    for synt_label,_ in synt_labels_sorted:
        title += "{:>8}\t".format(synt_label)
    title += "{:>8}\t".format("Total")
    
    print title
    
    # Sort the semantic role labels by name
    sem_labels_sorted = sem_labels.keys()
    sem_labels_sorted.sort()

    for sem_label in sem_labels_sorted:
        s = "{:>6}\t".format(sem_label)
        for synt_label,_ in synt_labels_sorted:
            if synt_label in stats_args[sem_label]:
                s += "{:>8}\t".format(stats_args[sem_label][synt_label])
            else:
                s += "{:>8}\t".format(0)
        # Print total for each argument semantic label
        s += "{:>8}\t".format(sem_labels[sem_label])
        print s
    
    # Print total for each syntactic function
    total_synt = "{:>6}\t".format("Total")
    total_general = 0
    for _,synt_total in synt_labels_sorted:
        total_synt += "{:>8}\t".format(synt_total)
        total_general += synt_total
    total_synt += "{:>8}\t".format(total_general)
    print total_synt
 
    return


def statistical_significance_formatter(reader_auto, reader_gold, writer):

    for ins_auto, ins_gold in zip(reader_auto.srl_spans(), reader_gold.srl_spans()):
        ins_auto = ins_auto[0]
        ins_gold = ins_gold[0]
        tp = 0 # true positives
        fp = 0 # false positives
        fn = 0 # false negatives
        
        for argspan_auto, argid_auto in ins_auto:
            for argspan_gold, argid_gold in ins_gold:
                if (argspan_auto == argspan_gold and argid_auto == argid_gold):
                    # The constituent is an argument
                    tp+=1
                    break
            else:
                # The constituent is not an argument
                fp+=1
        
        # Don't count the Verb
        fn = (len(ins_gold) - 1) - tp 
        
#        precision = tp/(tp+fp)
#        recall = tp/(tp+fn)
#        f1 = (2*precision*recall)/(precision+recall)
        
        writer.write("{} {} {}\n".format(tp, tp+fp, tp+fn))
        
    return

def results_per_verb(reader_auto, reader_gold):
    
    per_verb = dict()
    
    for ins_auto, ins_gold in zip(reader_auto.srl_spans(), reader_gold.srl_spans()):
        ins_auto = ins_auto[0]
        ins_gold = ins_gold[0]
        tp = 0 # true positives
        fp = 0 # false positives
        fn = 0 # false negatives
        
        for argspan_auto, argid_auto in ins_auto:
            for argspan_gold, argid_gold in ins_gold:
                if (argspan_auto == argspan_gold and argid_auto == argid_gold):
                    # The constituent is an argument
                    tp+=1
                    break
            else:
                # The constituent is not an argument
                fp+=1
        
        # Don't count the Verb
        fn = (len(ins_gold) - 1) - tp 
        
        precision = tp/(tp+fp)
        recall = tp/(tp+fn)
        f1 = (2*precision*recall)/(precision+recall)
    
    return
    
if __name__ == '__main__':
    PATH_ROOT_OUTPUT = "/home/fernandoalva/Dropbox/Projeto Mestrado/Densenvolvimento/APSBr/resources/output/"
    PATH_ROOT_TEST   = "/home/fernandoalva/Dropbox/Projeto Mestrado/Densenvolvimento/APSBr/resources/corpus/test/"

    column_types = ["srl"]

    reader_auto = PropbankBrConllCorpusReader(PATH_ROOT_OUTPUT, "PBrConst_AIAC_LR-All.conll", column_types, None , "S", False , False, "utf-8")
    reader_gold = PropbankBrConllCorpusReader(PATH_ROOT_TEST, "PBrConst_Props.conll", column_types, None , "S", False , False, "utf-8")
    writer = open(PATH_ROOT_OUTPUT + "AIAC_LR-All.sigf","w")
    statistical_significance_formatter(reader_auto, reader_gold, writer)
    
    print "File created."
    #statistics_pbr_consituent(reader)
    
