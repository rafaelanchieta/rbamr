'''
Created on 03/11/2011

@author: Fernando Alva Manchego
'''

from __future__ import unicode_literals

import codecs
import re
import unicodedata as ud

# from corpus.reader.pbrxml import PropbankBrCorpusReader
from nltk.parse.dependencygraph import DependencyGraph

from src.corpus.reader.pbrconll import PropbankBrConllCorpusReader, ConllDepSRLInstance, ConllDepSRLInstanceList
# from corpus.reader.pbrconll import PropbankBrConllCorpusReader, ConllDepSRLInstance, ConllDepSRLInstanceList
from src.corpus.reader.pbrxml import PropbankBrCorpusReader

discarted_instances = ['bosA.s220','bosB.s220','bosC.s220','bosD.s220','bosE.s220','bosA.s4192']

PATH_ROOT = '/home/rafael/PycharmProjects/RBAMR/src/bin/resources/'
#PATH_ROOT = os.path.dirname(__file__) + "/../../bin/resource/"
PATH_TEST = '/home/rafael/PycharmProjects/RBAMR/src/bin/resources/corpus/test/'
#PATH_TEST = os.path.dirname(__file__) + "/../../bin/resource/corpus/test/"
# ADDING SENSE
token_string = "{ID:<5}\t{FORM:<25}\t{LEMMA:<25}\t{GPOS:<10}\t{FEAT:<15}\t{CLAUSE:<10}\t{FCLAUSE:<10}\t{SYNT:<15}\t{ROLESET:<15}\t{PRED:<10}"

def compare_instances(ins1, ins2):
    if (ins1 == None) or (ins2 == None):
        return -1
    numsen_ins1 = int(re.search(".s([0-9]+)", ins1.instanceid).group(1))
    numsen_ins2 = int(re.search(".s([0-9]+)", ins2.instanceid).group(1))
    if (numsen_ins1 == numsen_ins2):
        return cmp(ins1.instanceid.split(".")[0], ins2.instanceid.split(".")[0])
    else:
        return cmp(numsen_ins1, numsen_ins2)

def compare_sentences(ins1, ins2):
    if (ins1 == None) or (ins2 == None):
        return -1
    numsen_ins1 = int(re.search(".s([0-9]+)", ins1.instanceid).group(1))
    numsen_ins2 = int(re.search(".s([0-9]+)", ins2.instanceid).group(1))
    return cmp (numsen_ins1, numsen_ins2)

def compare_terminals(t1, t2):
    return cmp(t1.num, t2.num)

def compare_ins_basic(ins_basic1, ins_basic2):
    return cmp(ins_basic1["id"], ins_basic2["id"])


def extract_predicate (ins):
    predicate_ids = ins.predicate.get_id()
    if isinstance(predicate_ids, basestring):
        predicate_ids = [predicate_ids]

    return predicate_ids

def extract_basic(ins, tokens):
    """
    @param ins:
    @return: A Map indexed by the terminal "num" with its basic information: word form, gold-standard lemma,
            gold-standard POS, gold-standard morphological features, predicate
    """
    predicate_ids = extract_predicate(ins)


    ins_basic = []

    for terminal in tokens:
        terminal_basic = dict()

        terminal_basic["id_full"] = terminal.id

        terminal_basic["id"] = terminal.num

        word = terminal.word
        terminal_basic ["word"] = word

        lemma = terminal.lemma.replace("--", "-")
        terminal_basic ["lemma"] = lemma

        pos = terminal.pos.upper().replace("--", "-")
        terminal_basic ["pos"] = pos

        morph = terminal.morph.replace(" ", "|")
        morph = morph.replace("--", "-")
        terminal_basic ["morph"] = morph

        if (terminal.id == predicate_ids[0]):
            pred = lemma
        else:
            pred = "-"

        terminal_basic ["pred"] = pred

        # Adding SENSE
        if (terminal.id == predicate_ids[0]):
            if ins.roleset <> None:
                roleset = ins.roleset[ins.roleset.index(".")+1:]
            else:
                roleset = "-"
        else:
            roleset = "-"

        terminal_basic ["roleset"] = roleset

        ins_basic.append(terminal_basic)

    return  ins_basic


def extract_syntactic(ins, tokens):
    """
    @return:
    """
    ins_syntactic = []

    for terminal in tokens:
        terminal_syntactic = dict()

        ins_tree = ins.parse_tree
        terminal_treepos = ins_tree.leaf_treeposition(terminal.num - 1)
        clause = full_clause = synt = "*"
        for i in range(len(terminal_treepos) - 1, -1, -1):
            parent_treepos = terminal_treepos[:i]
            parent_tree = ins_tree[parent_treepos]
            min_terminal = parent_tree.min_terminal_position
            max_terminal = parent_tree.max_terminal_position
            #cat = parent_tree.label().split("|")[-1]
            #print cat
            cat = parent_tree.node.split("|")[-1]
            #cat = parent_tree.label

            # Check if cat is a syntax mark
            if (cat.strip("-") in ["np", "vp", "pp", "adjp", "advp", "fcl", "icl", "acl", "x", "cu", "sq"]):
                # Check if it is the beginning of a constituent
                if (terminal.num == min_terminal):
                    if (cat.strip("-") in ["fcl", "icl", "acl"]):
                        clause = "(S" + clause
                        full_clause = "(%s" % cat.upper() + full_clause

                    synt = "(" + cat.upper() + synt

                # Check if it is the end of a constituent
                if (terminal.num == max_terminal):
                    if (cat.strip("-") in ["fcl", "icl", "acl"]):
                        clause += ")"
                        full_clause = clause

                    synt += ")"

        terminal_syntactic ["clause"] = clause
        terminal_syntactic ["fclause"] = full_clause
        terminal_syntactic ["synt"] = synt

        ins_syntactic.append(terminal_syntactic)

    return ins_syntactic

def extract_semantic(ins, tokens):
    """
    @return:
    """
    predicate_treepos = ins.predicate.treepos(ins.parse_tree)

    if type(predicate_treepos) is not list:
        predicate_treepos = [predicate_treepos]

    # Get the arguments of the instance
    args = ins.arguments
    args = [(argloc.treepos(ins.parse_tree), argid) for (argloc, argid) in args]
    argloc_tuples = [argloc for (argloc, argid) in args]

    # Process split arguments
    argloc_split_tuples = []
    for argloc_tuple in argloc_tuples:
        if type(argloc_tuple) is list:
            argloc_split_tuples.append(argloc_tuple)

    arg_split_processed = []

    predicate_began = False

    ins_semantic = []

    for terminal in tokens:
        terminal_semantic_roles = dict()
        ins_tree = ins.parse_tree
        terminal_treepos = ins_tree.leaf_treeposition(terminal.num - 1)
        arg = "*"
        for i in range(len(terminal_treepos) - 1, -1, -1):
            parent_treepos = terminal_treepos[:i]
            parent_tree = ins_tree[parent_treepos]
            min_terminal = parent_tree.min_terminal_position
            max_terminal = parent_tree.max_terminal_position

            #Check for predicate argument
            if (parent_treepos in argloc_tuples):
                index = argloc_tuples.index(parent_treepos)
                argid = args[index][1]
                if (terminal.num == min_terminal):
                    arg = "(" + argid.upper().replace("ARG", "A") + arg
                if (terminal.num == max_terminal):
                    arg += ")"
            else:
                # Check for split predicate argument
                for argloc_split_tuple in argloc_split_tuples:
                    # An argloc_split_tuple is a list of tuples for each constituent of the argument
                    if (parent_treepos in argloc_split_tuple):
                        index = argloc_tuples.index(argloc_split_tuple)
                        argid = args[index][1]
                        if (terminal.num == min_terminal):
                            if argid in arg_split_processed:
                                arg = "(C-" + argid.upper().replace("ARG", "A") + arg
                            else:
                                arg = "(" + argid.upper().replace("ARG", "A") + arg

                        if (terminal.num == max_terminal):
                            arg += ")"
                            arg_split_processed.append(argid)

            # Check for the predicate
            if (parent_treepos in predicate_treepos):
                if (terminal.num == min_terminal):
                    if (predicate_began):
                        arg = "(C-V" + arg
                    else:
                        arg = "(V" + arg

                if (terminal.num == max_terminal):
                    arg += ")"
                    predicate_began = True
                    predicate_treepos.remove(parent_treepos)

        terminal_semantic_roles["arg"] = arg
        ins_semantic.append(terminal_semantic_roles)

    return ins_semantic


def join_predicates(new_ins, ins_basic):
    """
    """
    new_pred_id = int(re.search("_([0-9]+)", extract_predicate(new_ins)[0]).group(1))

    for terminal_basic in ins_basic:
        if terminal_basic["id"] == new_pred_id:
            terminal_basic["pred"] = terminal_basic["lemma"]
    return

def join_rolesets(new_ins, ins_basic):
    """
    """
    new_pred_id = int(re.search("_([0-9]+)", extract_predicate(new_ins)[0]).group(1))

    for terminal_basic in ins_basic:
        if terminal_basic["id"] == new_pred_id:
            if new_ins.roleset <> None:
                terminal_basic ["roleset"] = new_ins.roleset[new_ins.roleset.index(".")+1:]
            else:
                terminal_basic ["roleset"] = "-"
    return


def print_instance(ins_basic, ins_syntactic, ins_semantic, file_pbr):
    """
    Prints a PropBank.Br instance in the CoNLL column format
    """
    for token in ins_basic:
        # Print the basic and syntactic information
        file_pbr.write(token_string.format(ID=token["id"], FORM=token["word"], LEMMA=token["lemma"], GPOS=token["pos"], CLAUSE=ins_syntactic[token["id"] - 1]["clause"],
                                          FCLAUSE=ins_syntactic[token["id"] - 1]["fclause"], FEAT=token["morph"], SYNT=ins_syntactic[token["id"] - 1]["synt"],
                                          ROLESET=token["roleset"], PRED=token["pred"]))


#         file_pbr.write(token_string.format(ID=token["id"], FORM=token["word"], LEMMA=token["lemma"], GPOS=token["pos"], FEAT=token["morph"],
#                                            SYNT=ins_syntactic[token["id"] - 1]["synt"], PRED=token["pred"]))
#
        # Print the semantic roles information
        sem_token_info = ""

        for ins_sem in ins_semantic:

            sem_token_info += "\t{:<10}".format(ins_sem[token["id"] - 1]["arg"])

        # End of a line (information of a token)
        sem_token_info += "\n"

        # Print the semantic information

        file_pbr.write(sem_token_info)

    # End of an instance
    file_pbr.write("\n")

    return

def format_constituents(pbr, file_pbr):
    # print "Sorting instances..."
    instances = [ins for ins in pbr.instances() if ins != None]
    instances.sort(cmp=compare_instances)

    # We keep track of the previous instance processed in order to join the semantic information
    prev_ins = None

    # Initializing variables
    ins_basic = ins_syntactic = ins_semantic = []

    for ins in instances:

        # print "Processing instance {%s}" % ins.instanceid

        #if (ins.roleset[:ins.roleset.index(".")] == "ser"): continue

        if (ins.instanceid in discarted_instances): continue

        if (compare_sentences(prev_ins, ins) != 0):
            # It's either the first or the instance of a new sentence.
            if (prev_ins != None):
                # It's the instance of a new sentence. Print the previous one.
                ins_basic.sort(cmp=compare_ins_basic)
                # print "...Printing instance {%s}" % prev_ins.instanceid
                print_instance(ins_basic, ins_syntactic, ins_semantic, file_pbr)
                ins_basic = ins_syntactic = ins_semantic = []

            tokens = ins.parse_tree.leaves
            tokens = [token for token in tokens()]
            tokens.sort(cmp=compare_terminals)
            ins_basic = extract_basic(ins, tokens)
            ins_syntactic = extract_syntactic(ins, tokens)
            ins_semantic.append(extract_semantic(ins, tokens))

        else:
            # It's the same sentence. Join the semantic information.
            # Join the predicate
            join_predicates (ins, ins_basic)
            # Join the rolesets
            join_rolesets(ins, ins_basic)
            # Join the semantic roles
            ins_semantic.append(extract_semantic(ins, tokens))

        prev_ins = ins

    # Print the last processed instance
    # print "...Printing instance {%s}" % prev_ins.instanceid

    print_instance(ins_basic, ins_syntactic, ins_semantic, file_pbr)

    file_pbr.close()

    # print "File created."

    return

def format_dependencies(pbr, file_pbr):
    # print "Sorting instances..."
    instances = [ins for ins in pbr.instances(False) if ins != None]
    instances.sort(cmp=compare_instances)

    prev_ins = None
    formatted_props = None

    for ins in instances:
        # print "Processing instance {%s}" % ins.instanceid

        if (ins.instanceid in discarted_instances): continue

        if (compare_sentences(prev_ins, ins) != 0):
            # It's either the first or the instance of a new sentence.
            if (prev_ins != None):
                # It's a new sentence
                # Print the propositions of the previous one
                file_pbr.write(formatted_props.pprint(["id","words","lemma", "pos", "feat", "head", "deprel", "fillpred", "srl"]))
                # End of an instance
                file_pbr.write("\n")
            # Create a new list of propositions for the new sentence
            formatted_props = ConllDepSRLInstanceList(ins.dep_graph)
            # Get the verb_stem of the instance
            for node in ins.dep_graph.nodelist:
                if node["address"] == ins.predicate:
                    verb_stem = node["lemma"]
                    break
            formatted_props.append(ConllDepSRLInstance(ins.dep_graph, ins.predicate, verb_stem, ins.roleset,
                                                           ins.arguments + [(ins.predicate,"V")]))
            # Update the prev_ins
            prev_ins = ins

        else:
            # It's a new instance of the same sentence
            # Get the verb_stem of the instance
            for node in ins.dep_graph.nodelist:
                if node["address"] == ins.predicate:
                    verb_stem = node["lemma"]
                    break
            formatted_props.append(ConllDepSRLInstance(ins.dep_graph, ins.predicate, verb_stem, ins.roleset,
                                                           ins.arguments + [(ins.predicate,"V")]))


    # Printing the last instance
    file_pbr.write(formatted_props.pprint(["id","words","lemma", "pos", "feat", "head", "deprel", "fillpred", "srl"]))

    file_pbr.close()

    # print "File created."

    return

def format_depgraph():
    sentences = [ins for ins in pbr.instances(False) if ins != None]

    for sent in sentences:
        print "Processing sentence {}".format(sent.instanceid)
        formatted_props = ConllDepSRLInstanceList(sent.dep_graph)
        file_pbr.write(formatted_props.pprint(["id","words","lemma", "pos", "feat", "head", "deprel", "fillpred", "srl"]))
        file_pbr.write("\n")
    return


def format_autoparse_cg():
    reader = open(PATH_ROOT + "test.out", "r")
    writer = open(PATH_ROOT + "test.conll", "w")
    dep_graph = DependencyGraph()
    nodelist = dep_graph.nodelist
    address = 0
    for line in reader:
        if "</s>" in line:
            # End of a sentence.
            formatted_props = ConllDepSRLInstanceList(dep_graph)
            writer.write(formatted_props.pprint(["id","words","lemma", "pos", "feat", "head", "deprel"]))
            writer.write("\n")
            dep_graph = DependencyGraph()
            nodelist = dep_graph.nodelist
            address = 0
        elif "\n" == line:
            continue
        else:
            address+=1
            if line[0] == "$":
                # It's a punctuation signal
                info_word = re.split("[\s\t\n]+",line)
                word = info_word[0][-1]
                head = info_word[-2].split("->")[-1]
                nodelist.append({'address': address, 'word': word, 'lemma':word, 'tag': "pu", 'morph': "-",
                                   'head': head, 'rel': "PU"})
                continue
            info_word = re.split("[\s\t\n]+",line)
            morph = ""
            tag_found = False
            for i in range(len(info_word)):
                if i==0:
                    word = info_word[i]
                elif i==1:
                    lemma = info_word[i].strip("[]")
                elif "<" in info_word[i]:
                    continue
                elif "@" in info_word[i]:
                    rel = info_word[i]
                elif "#" in info_word[i]:
                    head = int(info_word[i].split("->")[-1])
                elif not tag_found:
                    tag = info_word[i].lower()
                    tag_found = True
                else:
                    morph += "|{:}".format(info_word[i])

            morph = morph.strip("|")
            # Special case for verbs
            if tag == "v":
                tag = morph.split("|")[-1].lower()
                if tag == "inf":
                    tag = "vinf"
                morph = "|".join(morph.split("|")[:-1])

            if morph == "": morph = "-"

            nodelist.append({'address': address, 'word': word, 'lemma':lemma, 'tag': tag, 'morph': morph,
                                   'head': int(head), 'rel': rel})

    formatted_props = ConllDepSRLInstanceList(dep_graph)
    writer.write(formatted_props.pprint(["id","words","lemma", "pos", "feat", "head", "deprel"]))
    writer.write("\n")
    writer.close()
    return


def copy_semroles():
    column_types = ["id", "words", "lemma", "pos", "feat", "head", "deprel"]
    column_types_gold = ["id", "words", "lemma", "pos", "feat", "head", "deprel", "fillpred", "srl"]

    reader_auto = PropbankBrConllCorpusReader(PATH_ROOT, "PBrDep_Auto.conll", column_types, None , "FCL", False , False, "utf-8")
    reader_gold = PropbankBrConllCorpusReader(PATH_ROOT, "PBrDep.conll", column_types_gold, None , "FCL", False , False, "utf-8")

    auto_pbr = open(PATH_ROOT + "PBrDep_Auto_Sem.conll", "w")

    gold_instances = [x for x in reader_gold.dep_srl_instances()]
    auto_sentences = [x for x in reader_auto.dep_parsed_sents()]
    count_sent = 0
    for auto_sent in auto_sentences:
        count_sent+=1
        if count_sent in [8,18,112,133,159,176,179,186,192]:
            gold_instances = gold_instances[1:]
            continue
        if count_sent in [81]:
            gold_instances = gold_instances[2:]
            continue
        if count_sent in [66]:
            gold_instances = gold_instances[3:]
            continue
        props = ConllDepSRLInstanceList(auto_sent)
        num_props = 0
        for gold_ins in gold_instances:
            if _compare_depgraphs(gold_ins.dep_graph,auto_sent):
                auto_ins = _transfer_semroles(gold_ins,auto_sent)
                props.append(auto_ins)
                num_props+=1
            elif len(props) == 0:
                raise ValueError("No matching gold sentence found for {:}: {:}".format(count_sent,auto_sent.nodelist))
            else:
                break
        # auto_pbr.write(props.pprint(["id","words","lemma", "pos", "feat", "head", "deprel", "fillpred", "srl"]))
        gold_instances = gold_instances[num_props:]
    return


def _compare_depgraphs(depgraph1, depgraph2):
    w_dg1 = ""
    w_dg2 = ""
    count = 0
    for (node1,node2) in zip(depgraph1.nodelist,depgraph2.nodelist):
        if node1["rel"]=="TOP" or node2["rel"]=="TOP":
            continue
        count+=1
        if node1["word"] == "--": node1["word"] = "-"
        w_dg1 += "{} ".format(ud.normalize('NFC',unicode(node1["word"])).lower())
        w_dg2 += "{} ".format(ud.normalize('NFC',unicode(node2["word"])).lower())
        if count == 2:
            return (w_dg1 == w_dg2)

def _transfer_semroles(gold_ins,auto_depgraph):
    return


def main():

    pbr = PropbankBrCorpusReader(PATH_ROOT, 'input.xml', 'verbs.txt')

    file_pbr_C = codecs.open(PATH_TEST + "inputConst.conll", mode="w", encoding="utf-8")
    file_pbr_D = codecs.open(PATH_TEST + "inputDep.conll", mode="w", encoding="utf-8")

    format_constituents(pbr, file_pbr_C)
    format_dependencies(pbr, file_pbr_D)

    # print "Process finished"
