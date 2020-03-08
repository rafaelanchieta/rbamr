# -*- coding: utf-8 -*-
'''
Created on May 29, 2012

@author: feralvam
'''

#import bin.features.util as util
#from bin.srl.base import BaseLabeler
# from bin.srl.base import BaseLabeler
from nltk.tree import Tree

import src.bin.features.util as util
# import bin.features.util as util
from src.bin.srl.base import BaseLabeler


def prune_argcands(tree, verb_treepos):
    """
    Uses the Pruning Algorithm of Xue and Palmer (2004) to get the argument candidates
    @return: A list of the candidates' tree positions
    """
    # Check if it isn't a root node
    if len(verb_treepos) == 0: return []

    argcands = []
    # Go up one level of the tree
    parent_treepos = verb_treepos[:-1]
    parent_tree = tree[parent_treepos]
    verb_tree = tree[verb_treepos]

    # Check if the sisters are not coordinated with the verb
    parent_cat = util.get_postag(parent_tree)
    if parent_cat == "cu": return []

    # In the case of the annotation of Bosque, VPs are just formed by verbs.
    # So, we have to start looking for the sisters one more level up
    if parent_cat != "vp":
        # Explore all the children of the parent
        child_count = 0
        for child in parent_tree:
            child_treepos = parent_treepos + (child_count,)
            child_count += 1
            # Check if the child is different from the verb
            if isinstance(child, Tree) and child != verb_tree:
                argcands.append(child_treepos)
                # Check if the child is a PP
                cat_child = util.get_postag(child)
                if (cat_child == "pp"):
                    # Collect its immediate children
                    subchild_count = 0
                    for _ in child:
                        subchild_treepos = child_treepos + (subchild_count,)
                        subchild_count += 1
                        argcands.append(subchild_treepos)

    parent_argcands = prune_argcands(tree, parent_treepos)
    if len(parent_argcands) > 0: argcands.extend(parent_argcands)

    return argcands


class SupervisedIdent(BaseLabeler):
    def __init__(self, path_train="", fileid_train="", path_test="", fileid_test="", model=None, target_verbs=[],
                 fileid_train_dep="", features="all", train_method="supervised"):

        if features == "all":

            feature_list = ["pred_form", "pred_lemma", "pred_postag", "path", "tree_distance", "num_clauses",
                            "num_clauses_asc", "num_clauses_desc",
                            "num_vp", "num_vp_asc", "num_vp_desc", "phrase_type", "position", "voice", "subcat", "head",
                            "head_postag", "head_lemma",
                            "partial_path", "pred_context_left", "pred_context_right", "pred_context_left_postag",
                            "pred_context_right_postag",
                            "punct_left", "punct_right", "first_form", "first_lemma", "first_postag", "second_form",
                            "second_lemma", "second_postag",
                            "third_form", "third_lemma", "third_postag", "parent_phrase", "parent_head",
                            "parent_head_postag", "right_phrase",
                            "right_head", "right_head_postag", "left_phrase", "left_head", "left_head_postag",
                            "pred_lemma+path", "pred_lemma+head",
                            "pred_lemma+phrase_type", "voice+position", "first_form+first_postag",
                            "last_form+last_postag", "negation", "preposition",
                            "se_in_vp", "bag_of_nouns", "bag_of_adj", "bag_of_adv", "postag_sequence", "top_sequence",
                            "dep_rel"]

        elif features == "best":

            feature_list = ["path", "left_phrase", "first_form+first_postag"]

        featselec_featorder = ['path', 'left_phrase', 'first_form+first_postag']

        super(SupervisedIdent, self).__init__(path_train=path_train, fileid_train_labeled=fileid_train,
                                              filter_func=prune_argcands,
                                              feature_list=feature_list, path_test=path_test, fileid_test=fileid_test,
                                              model=model,
                                              target_verbs=target_verbs, special_label="ARG",
                                              featselec_featorder=featselec_featorder,
                                              train_method=train_method,
                                              fileid_train_labeled_dep=fileid_train_dep)
