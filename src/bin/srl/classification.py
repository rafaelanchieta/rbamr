# -*- coding: utf-8 -*-
'''
Created on Apr 12, 2012

@author: feralvam
'''
from nltk.corpus.reader.conll import ConllSRLInstance
from nltk.tree import Tree

# from corpus.reader.pbrconll import ConllSRLInstanceList
from src.bin.srl.base import BaseLabeler
from src.corpus.reader.pbrconll import ConllSRLInstanceList


#from bin.srl.base import BaseLabeler


class SRLBaseline(object):


    def _same_clause(self, tree, treepos_1, treepos_2):
        for i in range(len(treepos_1) - 1, -1, -1):
            parent_treepos1 = treepos_1[:i]
            parent_tree = tree[parent_treepos1]
            cat = parent_tree.node.split("|")[-1]
            if (cat.strip("-") in ["FCL", "ICL", "ACL"]):
                break

        for i in range(len(treepos_2) - 1, -1, -1):
            parent_treepos2 = treepos_2[:i]
            parent_tree = tree[parent_treepos2]
            cat = parent_tree.node.split("|")[-1]
            if (cat.strip("-") in ["FCL", "ICL", "ACL"]):
                break

        return (parent_treepos1==parent_treepos2)

    # Tag target verb and successive particles as V
    def _tag_target_verb(self, tree, tagged_spans, verb_head):
        node_treepos = tree.leaf_treeposition(verb_head)
        verb_treepos_index = node_treepos[-1]
        parent_treepos = node_treepos[:len(node_treepos) - 1]
        parent_tree = tree[parent_treepos]
        tagged_spans.append(((verb_head,verb_head - verb_treepos_index + len(parent_tree)),'V'))

        return

    # Tag "não" in target verb clause as AM-NEG
    def _tag_negation_argument(self, tree, tagged_spans, verb_head):

        node_treepos = tree.leaf_treeposition(verb_head)
        found = False
        # Go up in the tree
        for i in range(len(node_treepos) - 1, -1, -1):
            parent_treepos = node_treepos[:i]
            parent_tree = tree[parent_treepos]
            cat = parent_tree.node.split("|")[-1]

            # Explore all the leaves of the parent in order to find the "não"
            node_treepos_index = 0
            for word,_ in parent_tree.leaves():
                if (word.lower() == "não"):
                    # Save the tree position of the "não"
                    word_treepos = parent_treepos + parent_tree.leaf_treeposition(node_treepos_index)
                    if self._same_clause (tree, word_treepos, node_treepos):
                        found = True
                        break
                node_treepos_index+=1
            if found: break
            # If a clause symbol is found, we've reached the end of the clause
            # and the "não" was not found
            if (cat.strip("-") in ["FCL", "ICL", "ACL"]):
                break
        # Find the index of the "não" in the sentence
        if found:
            for i in range(len(tree.leaves())):
                if tree.leaf_treeposition(i) == word_treepos:
                    tagged_spans.append(((i,i+1),'AM-NEG'))
                    break

        return

    # Tag first NP before target verb as A0
    def _tag_subject_arg0(self, tree, tagged_spans, verb_head):
        node_treepos = tree.leaf_treeposition(verb_head)
        aux = node_treepos[-1]
        found = False
        first = True
        # Go up the tree
        for i in range(len(node_treepos) - 1, -1, -1):
            parent_treepos = node_treepos[:i]
            parent_tree = tree[parent_treepos]
            if first:
                verb_tree = parent_tree
                first = False
            offset_verb = 0

            # Explore all the children of the parent in order to find the "NP"
            for child in parent_tree:

                # Check if the child if before the verb
                if (child != verb_tree):
                    # Check if it is a terminal
                    if not isinstance(child, Tree):
                        offset_verb +=1
                        continue
                    else:
                        # It's a tree. Check if it is a NP
                        cat_child = child.node.split("|")[-1].strip("-")

                        if (cat_child.lower() == "np"):
                            len_tree_np = len(child.leaves())
                            ini_np=offset_verb
                            offset_verb += len_tree_np
                            found = True
                        else:
                            offset_verb +=len(child.leaves())

                else:
                    # The verb_tree was found.
                    # If the NP hasn't been found yet, we continue the search one level up
                    if not found: break
                    # Otherwise, the NP is before the target verb and we process it
                    ini_arg0 = verb_head - (offset_verb + aux) + ini_np
                    tagged_spans.append(((ini_arg0,ini_arg0+len_tree_np),'A0'))
                    break

            if found: break

            verb_tree = parent_tree

        return found

    # Tag first NP after target verb as A1
    def _tag_direct_object_arg1(self, tree, tagged_spans, verb_head):
        node_treepos = tree.leaf_treeposition(verb_head)
        aux = node_treepos[-1]
        found = False
        first = True

        # Go up the tree
        for i in range(len(node_treepos) - 1, -1, -1):
            parent_treepos = node_treepos[:i]
            parent_tree = tree[parent_treepos]
            if first:
                verb_tree = parent_tree
                first = False
                aux = len(parent_tree.leaves()) - aux
            offset_verb = 0
            verb_found = False
            # Explore all the children of the parent in order to find the "NP"
            for child in parent_tree:

                # Check if the child if before the verb
                if (child == verb_tree):
                    verb_found = True
                    continue
                else:
                    # Check if it's AFTER the target verb
                    if verb_found:
                        # Check if it is a terminal
                        if not isinstance(child, Tree):
                            offset_verb +=1
                            continue
                        else:
                            # It's a tree. Check if the tree is a NP
                            cat_child = child.node.split("|")[-1].strip("-")

                            if (cat_child.lower() == "np"):
                                len_tree_np = len(child.leaves())
                                found = True
                                break
                            else:
                                offset_verb +=len(child.leaves())
                    else:
                        continue

            if found:
                ini_arg1 = verb_head + (offset_verb + aux)
                tagged_spans.append(((ini_arg1,ini_arg1+len_tree_np),'A1'))
                break

            verb_tree = parent_tree

        return

    # Tag "que" before target verb as A0
    def _tag_realtive_pronoun_arg0(self, tree, tagged_spans, verb_head):

        node_treepos = tree.leaf_treeposition(verb_head)
        found = False
        # Go up in the tree
        for i in range(len(node_treepos) - 1, -1, -1):
            parent_treepos = node_treepos[:i]
            parent_tree = tree[parent_treepos]
            cat = parent_tree.node.split("|")[-1]

            # Explore all the leaves of the parent in order to find the "que"
            node_treepos_index = 0
            for word,_ in parent_tree.leaves():
                if (word.lower() == "que"):
                    # Save the tree position of the "que"
                    word_treepos = parent_treepos + parent_tree.leaf_treeposition(node_treepos_index)
                    # Check if the word belongs to the same clause as the target verb
                    if self._same_clause (tree, word_treepos, node_treepos):
                        # Check that it is BEFORE the target verb and find its index
                        for i in range(verb_head):
                            if tree.leaf_treeposition(i) == word_treepos:
                                tagged_spans.append(((i,i+1),'A0'))
                                found = True
                                break

                        if found: break
                node_treepos_index+=1
            if found: break
            # If a clause symbol is found, we've reached the end of the clause
            # and the "que" was not found
            if (cat.strip("-") in ["FCL", "ICL", "ACL"]):
                break

        return

    # Switch A0 and A1 if the target verb is in a passive VP clause.
    # A VP clause is considered in passive voice if it contains verbs "ser"
    # or "estar" and the target verb has the syntactic annotation "V-PCP"
    def _treat_passive_voice(self, tree, tagged_spans, verb_head, lexinfo_sent):
        node_treepos = tree.leaf_treeposition(verb_head)
        verb_treepos_index = node_treepos[-1]
        parent_treepos = node_treepos[:len(node_treepos) - 1]
        parent_tree = tree[parent_treepos]
        verb_pos = tree[node_treepos][-1]

        start_vp = verb_head - verb_treepos_index
        end_vp = start_vp + len(parent_tree)

        found = False
        # Check if there's a "ser" or "estar" in the VP and that it isn't the target verb
        for i in range(start_vp, end_vp):
            if (i!=verb_head):
                _,_,lemma,_,_ = lexinfo_sent[i]
                if (lemma.lower() == "ser" or lemma.lower() == "estar"):
                    found = True
                    break

        if not found: return

        # Check if the verb is in passive voice
        if (verb_pos.upper() == "V-PCP"):
            # Change A0 and A1
            for i in range(len(tagged_spans)):
                argspan,argid = tagged_spans[i]
                if (argid == "A0"):
                    tagged_spans[i] = (argspan, "A1")
                    continue
                if (argid == "A1"):
                    tagged_spans[i] = (argspan, "A0")
                    continue
        return

    def execute(self, reader, writer):

        # Get the instances of each sentence
        for lexinfo_sent, sent_ins in zip(reader.lexicalinfo_sents(), reader.srl_instances(None, None, False)):
            # Process each instance
            tree = sent_ins[0].tree
            sent_tagged_ins = ConllSRLInstanceList(tree)

            for ins in sent_ins:
                tagged_spans =[]
                # Rule 1
                self._tag_target_verb(tree, tagged_spans, ins.verb_head)
                # Rule 2
                self._tag_negation_argument(tree, tagged_spans, ins.verb_head)
                # Rule 3
                found = self._tag_subject_arg0(tree, tagged_spans, ins.verb_head)
                # Rule 4
                self._tag_direct_object_arg1(tree, tagged_spans, ins.verb_head)
                # Rule 5
                if not found: self._tag_realtive_pronoun_arg0(tree, tagged_spans, ins.verb_head)
                # Rule 6
                self._treat_passive_voice(tree, tagged_spans, ins.verb_head, lexinfo_sent)

                sent_tagged_ins.append(ConllSRLInstance(tree, ins.verb_head, ins.verb_stem, ins.roleset, tagged_spans))

            # Print the automatically tagged instances
            writer.write(sent_tagged_ins.pprint())

            # Print a line to separate sentences
            writer.write("\n")


class SupervisedClass(BaseLabeler):

    def __init__(self, path_train="", fileid_train="", ins_train=None, path_test="", fileid_test="", ins_test=None,
                 fileid_train_labaled_dep = "", fileid_train_unlabeled_dep = "",
                 model=None, target_verbs=[], features = "all"):

        if features == "all":
            feature_list = ["pred_form", "pred_lemma", "pred_postag", "path", "tree_distance", "num_clauses", "num_clauses_asc", "num_clauses_desc",
                            "num_vp", "num_vp_asc", "num_vp_desc", "phrase_type", "position", "voice", "subcat", "head", "head_postag", "head_lemma",
                            "partial_path", "pred_context_left", "pred_context_right", "pred_context_left_postag", "pred_context_right_postag",
                            "punct_left", "punct_right", "first_form", "first_lemma", "first_postag", "second_form", "second_lemma", "second_postag",
                            "third_form", "third_lemma", "third_postag", "parent_phrase", "parent_head", "parent_head_postag", "right_phrase",
                            "right_head", "right_head_postag", "left_phrase", "left_head", "left_head_postag", "pred_lemma+path", "pred_lemma+head",
                            "pred_lemma+phrase_type", "voice+position", "first_form+first_postag", "last_form+last_postag", "negation", "preposition",
                            "se_in_vp", "bag_of_nouns", "bag_of_adj", "bag_of_adv", "postag_sequence", "top_sequence","dep_rel"]
            # "verb_sense"

        elif features == "best":

            feature_list = ['first_form+first_postag', 'first_lemma', 'head', 'head_lemma', 'top_sequence', 'postag_sequence', 'pred_lemma+phrase_type', 'last_form+last_postag', 'pred_lemma+path', 'first_postag', 'left_head', 'right_head', 'voice+position', 'left_head_postag', 'right_phrase', 'pred_lemma']


        featselec_featorder = ['first_form+first_postag', 'first_lemma', 'head', 'head_lemma', 'top_sequence', 'postag_sequence', 'pred_lemma+phrase_type', 'last_form+last_postag', 'pred_lemma+path', 'first_postag', 'left_head', 'right_head', 'voice+position', 'left_head_postag', 'right_phrase', 'pred_lemma']

        super(SupervisedClass, self).__init__(path_train=path_train, fileid_train_labeled=fileid_train, train_instances_labeled=ins_train,
                                              feature_list=feature_list, path_test=path_test, fileid_test=fileid_test, model=model,
                                              target_verbs=target_verbs, featselec_featorder=featselec_featorder, discard_labels=["A5"],
                                              fileid_train_labeled_dep=fileid_train_labaled_dep,
                                              fileid_train_unlabeled_dep=fileid_train_unlabeled_dep)

