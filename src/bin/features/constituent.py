# -*- coding: utf-8 -*-
'''
Created on May 14, 2012

@author: feralvam
'''

from __future__ import unicode_literals

from util import *
from src.bin.features.dependency import head_dep
#from bin.features.dependency import head_dep

def find_contentword(prop_depgraph, word_info):
    # Check the direct dependents for a noun or a proper noun
    aux_candidate = None
    for dep_address in word_info["deps"]:
        dep_info = prop_depgraph.get_by_address(dep_address)
        if (dep_info["tag"] in ["n","prop","pron-pers","pron-indp"]) and not ("$" in dep_info["word"]):
            return dep_info
        elif dep_info["tag"] in ["adv","pron-det"]:
            aux_candidate = dep_info
        elif dep_info["tag"] in ["num","v-inf"]:
            aux_candidate = dep_info

    if aux_candidate is not None:
        return aux_candidate

    # If no direct dependent is a suitable content word, then look in their dependents
    for dep_address in word_info["deps"]:
        dep_info = prop_depgraph.get_by_address(dep_address)
        content_word = find_contentword(prop_depgraph, dep_info)
        if content_word is not None:
            return content_word

    return None


def phrase_type(tree, phrase_treepos):
    """
    Indicates the syntactic category of the phrase expressing the semantic role
    @param tree: the parse tree of the whole sentence
    @param phrase_treepos: the tree position of constituent phrase
    """
    return get_postag(tree[phrase_treepos])

def _governing_category(tree_root):
    """
    Indicates if this NP is a subject of a sentence or object of a verb
    @param tree_root: the root of tree containing a phrase
    """
    raise NotImplementedError("The syntactic annotation doesn't allow to extract this information")
    return

def parse_tree_path(argcand):
    """
    The synt_path from the target verb through the parse tree to the constituent in question,
    represented as a string of parse tree nonterminals linked by symbols indicating upward (¡)
    or downward (!) movement through the tree
    @param tree: the parse tree of the whole sentence
    @param phrase_treepos: the tree position of constituent phrase
    @param verb_pos: the position in the sentence of the target verb
    """
    tree = argcand["ins"].tree
    verb_pos = argcand["ins"].verb_head
    phrase_treepos = argcand["info"]["treepos"]

    verb_treepos = tree.leaf_treeposition(verb_pos)[:-1]
    path_verb = get_path_to_root(tree, verb_treepos)
    path_phrase = get_path_to_root(tree, phrase_treepos)

    # Find the intersection of the paths (preserving the order)
    intersec_node = [x for x in path_verb if x in path_phrase][0]

    intersec_pos = path_phrase.index(intersec_node)
    # Consider only the nodes before the intersection point
    path_phrase = path_phrase[:intersec_pos+1]
    # Invert the list to make the concatenation easier
    path_phrase.reverse()

    # Form the syntactic path
    synt_path = ""
    # Make the necessary counts
    num_clauses = 0
    num_clauses_asc = 0
    num_clauses_desc = 0
    num_vp = 0
    num_vp_asc = 0
    num_vp_desc = 0
    # Go up the verb syntactic path until the intersection point
    for node in path_verb:
        if node == intersec_node: break
        synt_path += "{:}^".format(node[-1])
        if node[-1] in ["fcl","icl","acl"]:
            num_clauses+=1
            num_clauses_asc+=1
        if node[-1] in ["vp"]:
            num_vp += 1
            num_vp_asc += 1

    for node in path_phrase:
        synt_path += "{:}_".format(node[-1])
        if node[-1] in ["fcl","icl","acl"]:
            num_clauses+=1
            num_clauses_desc+=1
        if node[-1] in ["vp"]:
            num_vp += 1
            num_vp_desc += 1

    # Remove the last "_"
    synt_path = synt_path[:-1]

    path = dict()
    path["synt_path"] = synt_path
    path["length"] = len(path_verb) + len(path_phrase)
    path["num_clauses"] = num_clauses
    path["num_clauses_asc"] = num_clauses_asc
    path["num_clauses_desc"] = num_clauses_desc
    path["num_vp"] = num_vp
    path["num_vp_asc"] = num_vp_asc
    path["num_vp_desc"] = num_vp_desc

    return path

def position(argcand):
    """
    Indicates whether the constituent occurs before(0) or after(1) the target verb
    """
    verb_pos = argcand["ins"].verb_head
    const_start, _ = argcand["info"]["span"]

    if verb_pos < const_start:
        return 1
    else:
        return 0

def voice(argcand):
    """
    Indicates whether the verb clause is in active(0) or passive voice(1)
    @param tree: the parse tree of the whole sentence
    @param verb_pos: the position in the sentence of the target verb
    @param lexinfo_sent: lexical information of all the words in the sentence
    """

    tree = argcand["ins"].tree
    verb_pos = argcand["ins"].verb_head
    info_sent = argcand["info_sent"]

    verb_treepos = tree.leaf_treeposition(verb_pos)
    # Check if the verb is in passive voice
    verb_postag = tree[verb_treepos][-1]
    if (verb_postag.upper() == "V-PCP"):
        # Find the VP: the parent of the target verb
        parent_treepos = verb_treepos[:len(verb_treepos) - 1]
        parent_tree = tree[parent_treepos]
        # Determine the limits of the VP
        verb_treepos_index = verb_treepos[-1]
        start_vp = verb_pos - verb_treepos_index
        end_vp = start_vp + len(parent_tree)

        # Check if there's a "ser" or "estar" in the VP and that it isn't the target verb
        for i in range(start_vp, end_vp):
            if (i!=verb_pos):
                lemma = info_sent[i][2]
                if (lemma.lower() == "ser" or lemma.lower() == "estar"):
                    return 1

    return 0

def head_word(tree, phrase_treepos, phrase_tree=None, pp_contentword=False, depgraph=None, const_span=None):

    if phrase_tree == None:
        phrase_tree = tree[phrase_treepos]

    phrase_type = get_postag(phrase_tree)

    if depgraph is not None:
        head_info = head_dep(const_span,depgraph)

        if phrase_type == "pp" and pp_contentword:
            contentword_info = find_contentword(depgraph,head_info)
            if contentword_info is None:
                if len(head_info["deps"]) > 0:
                    contentword_info = depgraph.get_by_address(head_info["deps"][0])
                else:
                    contentword_info = head_info
            head_info = contentword_info

        return head_info["word"], head_info["tag"], head_info["address"]-1

    head_rule, final_head = _find_head_rule(phrase_type)

    if phrase_type == "pp" and pp_contentword:
        final_head = False

    if final_head:
        if isinstance(phrase_tree, Tree):
            phrase_tokens = phrase_tree.leaves()
            child_pos = treepos_to_tuple(tree, phrase_treepos)[0]
            for (token,postag) in phrase_tokens:
                if (postag.lower() in head_rule) or (len(head_rule)==0):
                    return token,postag,child_pos
                child_pos+=1
            else:
                token, postag = phrase_tokens[0]
                return token, postag, treepos_to_tuple(tree, phrase_treepos)[0]
        else:
            token, postag = phrase_tree
            return token, postag, treepos_to_tuple(tree, phrase_treepos)[0]
    else:
        child_pos = 0
        for child in phrase_tree:
            if not (get_postag(child) in head_rule):
                return head_word(tree, phrase_treepos + (child_pos,), child, pp_contentword)
            child_pos+=1
        else:
            return head_word(tree, phrase_treepos + (0,), phrase_tree[0], pp_contentword)

def _find_head_rule(phrase_type):
    final_head = True
    # In a noun phrase, the head is the noun or pronoun
    if phrase_type in ["np"]:
        head_rule = ["n","n-adj","prop","pron-pers","pron-det", "pron-indp","num"]
    # In an adjective phrase, the head is the adjective or determiner
    elif phrase_type in ["adjp"]:
        head_rule = ["adj","pron-det","num","v-pcp"]
    # In an adverb phrase, the head is the adverb
    elif phrase_type in ["advp"]:
        head_rule = ["adv"]
    # In a verb phrase, the head is the auxiliary verb (generally, the first one to appear)
    elif phrase_type in ["vp"]:
        head_rule = []
    # In an prepositional phrase, the head is the preposition
    elif phrase_type in ["pp"]:
        head_rule = ["prp"]
    # In finite or non-finite clauses, the first verb is head
    elif phrase_type in ["fcl","icl","x"]:
        head_rule = ["v-fin","v-inf","v-pcp","v-ger"]
    # In an averbal clause, the first constituent is the head
    elif phrase_type in ["acl"]:
        head_rule = []
    # In a compound unit, the first constituent is head
    elif phrase_type in ["cu"]:
        head_rule = ["conj-c"]
        final_head = False
    else:
        head_rule = []

    return head_rule, final_head

def subcategorization(argcand):
    """
    Intends to differentiate between transitive and intransitive uses of a verb.
    Indicates the phrase structure rule expanding the target verb parent node in the parse tree.
    @param tree: the parse tree of the whole sentence
    @param verb_pos: the position in the sentence of the target verb
    """
    verb_treepos = argcand["ins"].tree.leaf_treeposition(argcand["ins"].verb_head)
    # Go up the tree until finding a clause identifier
    for i in range(len(verb_treepos) - 1, -1, -1):
        parent_treepos = verb_treepos[:i]
        parent_tree = argcand["ins"].tree[parent_treepos]
        cat = get_postag(parent_tree)
        if cat in ["fcl","icl","acl","x"]:
            break
    else:
        raise ValueError("No clause symbol found {}".format(argcand["ins"].tree))

    sub_rule = "{:}=".format(cat)
    for child in parent_tree:
        sub_rule += "{:}_".format(get_postag(child))

    return sub_rule.rstrip("_")

def partial_path(argcand):
    tree = argcand["ins"].tree
    verb_pos = argcand["ins"].verb_head
    phrase_treepos = argcand["info"]["treepos"]

    verb_treepos = tree.leaf_treeposition(verb_pos)[:-1]
    path_verb = get_path_to_root(tree, verb_treepos)
    path_phrase = get_path_to_root(tree, phrase_treepos)

    # Find the intersection of the paths (preserving the order)
    intersec_node = [x for x in path_verb if x in path_phrase][0]

    # Form the path
    path = ""
    # Go up the verb path until the intersection point
    for node in path_verb:
        path += "{:} ".format(node[-1])
        if node == intersec_node: break

    return path.strip()

def predicate_context(verb_pos,lexinfo_sent):
    context = dict()
    left_pos = verb_pos-1
    right_pos = verb_pos+1

    if left_pos >=0 and lexinfo_sent[left_pos][3].lower() != "pu":
        context["left"] = lexinfo_sent[left_pos]
    else:
        context["left"] = ("","","","","")

    if right_pos < len(lexinfo_sent) and lexinfo_sent[right_pos][3].lower() != "pu":
        context["right"] = lexinfo_sent[right_pos]
    else:
        context["right"] = ("","","","","")

    return context

def punctuation_context(argcand,lexinfo_sent):
    context = dict()
    left_pos = argcand["info"]["span"][0] - 1
    right_pos = argcand["info"]["span"][-1] + 1

    if left_pos >=0 and lexinfo_sent[left_pos][3].lower() == "pu":
        context["left"] = lexinfo_sent[left_pos]
    else:
        context["left"] = ("","N","","","")

    if right_pos < len(lexinfo_sent) and lexinfo_sent[right_pos][3].lower() == "pu":
        context["right"] = lexinfo_sent[right_pos]
    else:
        context["right"] = ("","","","","")


    return context

def relatives_features(argcand, lexinfo_sent, depgraph):
    context = dict()

    # Get the parent information
    parent_treepos = argcand["info"]["treepos"][:-1]
    parent_tree = argcand["ins"].tree[parent_treepos]
    parent_head, parent_head_postag, _ = head_word(argcand["ins"].tree, parent_treepos, parent_tree, pp_contentword=True, depgraph=depgraph, const_span=argcand["info"]["span"])
    context["parent"] = {"cat":get_postag(parent_tree),"head":parent_head,"head_cat":parent_head_postag}

    # Get the sibling's information
    argcand_index = argcand["info"]["treepos"][-1]
    left_index = argcand_index - 1
    right_index = argcand_index + 1

    if left_index >=0:
        left_treepos = parent_treepos + (left_index,)
        left_tree = argcand["ins"].tree[left_treepos]
        left_head, left_head_postag, _ = head_word(argcand["ins"].tree, left_treepos, left_tree, pp_contentword=True, depgraph=depgraph, const_span=argcand["info"]["span"])
        context["left"] = {"cat":get_postag(left_tree),"head":left_head, "head_cat":left_head_postag}
    else:
        context["left"] = {"cat":"","head":"","head_cat":""}

    if right_index < len(parent_tree):
        right_treepos= parent_treepos + (right_index,)
        right_tree = argcand["ins"].tree[right_treepos]
        right_head, right_head_postag, _ = head_word(argcand["ins"].tree,right_treepos,right_tree, pp_contentword=True, depgraph=depgraph, const_span=argcand["info"]["span"])
        context["right"] = {"cat":get_postag(right_tree),"head":right_head, "head_cat":right_head_postag}
    else:
        context["right"] = {"cat":"","head":"","head_cat":""}

    return context

def tokens_lexinfo(argcand):
    """
    All the tokens that form the constituent with their respective lexical information
    """
    tokens_lexinfo = []
    start = argcand["info"]["span"][0] + 1
    end = argcand["info"]["span"][-1]

    for i in range(start,end+1):
        index = str(i)
        if index in argcand["info"]["lexinfo"].keys():
            tokens_lexinfo.append(argcand["info"]["lexinfo"][index])

    return tokens_lexinfo

def particle_in_vp(argcand, particle):
    has_particle = 0
    tree = argcand["ins"].tree
    verb_treepos = tree.leaf_treeposition(argcand["ins"].verb_head)

    # Go up in the tree
    for i in range(len(verb_treepos) - 1, -1, -1):
        parent_treepos = verb_treepos[:i]
        parent_tree = tree[parent_treepos]
        cat = get_postag(parent_tree)

        # Explore all the leaves of the parent in order to find the particle
        for word,_ in parent_tree.leaves():
            if (word.lower() == particle):
                has_particle = 1
                return has_particle
        else:
            if (cat.strip("-") in ["fcl", "icl", "acl", "x"]):
                break

    return has_particle


def postag_sequence(argcand):
    phrase_tree = argcand["ins"].tree[argcand["info"]["treepos"]]

    if isinstance(phrase_tree, Tree):
        phrase_tokens = phrase_tree.leaves()
    else:
        phrase_tokens = [phrase_tree]

    sequence = ""
    for child in phrase_tokens:
        sequence+="{}_".format(get_postag(child))

    return sequence.rstrip("_")

def bag_of_words(argcand, to_string=False):
    phrase_tree = argcand["ins"].tree[argcand["info"]["treepos"]]

    if isinstance(phrase_tree, Tree):
        phrase_tokens = phrase_tree.leaves()
    else:
        phrase_tokens = [phrase_tree]

    bag_of_nouns = set()
    bag_of_adj = set()
    bag_of_adv = set()

    for child in phrase_tokens:
        postag = get_postag(child)
        if postag in ["n","prop"]:
            bag_of_nouns.add(child[0])
        elif postag in ["adj"]:
            bag_of_adj.add(child[0])
        elif postag in ["adv"]:
            bag_of_adv.add(child[0])


    bag_of_nouns = list(bag_of_nouns)
    bag_of_nouns.sort()
    bag_of_adj = list(bag_of_adj)
    bag_of_adj.sort()
    bag_of_adv = list(bag_of_adv)
    bag_of_adv.sort()

    if to_string:
        bag_of_nouns = ("/".join(bag_of_nouns)).rstrip("/")
        bag_of_adj = ("/".join(bag_of_adj)).rstrip("/")
        bag_of_adv = ("/".join(bag_of_adv)).rstrip("/")

    bags = {"noun":bag_of_nouns,"adj":bag_of_adj,"adv":bag_of_adv}

    return bags

def TOP_sequence(argcand):
    phrase_tree = argcand["ins"].tree[argcand["info"]["treepos"]]

    sequence = ""
    if isinstance(phrase_tree, Tree):
        for child in phrase_tree:
            postag = get_postag(child)
            sequence+="{}_".format(postag)
        return sequence.rstrip("_")
    else:
        return phrase_tree[-1]


def feature_extractor_const(argcand, feature_list, depgraph=None):
    #depgraph=None
    features_set = dict()

    lexinfo_sent = argcand["info_sent"]
    verb_info = lexinfo_sent[argcand["ins"].verb_head]

    # Predicate related features
    if "pred_form" in feature_list:
        features_set["pred_form"] = verb_info[1].lower()
    if ("pred_lemma" in feature_list) or ("pred_lemma+phrase_type" in feature_list):
        features_set["pred_lemma"] = verb_info[2].lower()
    if "pred_postag" in feature_list:
        features_set["pred_postag"] = verb_info[3].lower()

    # Path related features
    path_feats =  parse_tree_path(argcand)
    if ("path" in feature_list) or ("pred_lemma+path" in feature_list):
        features_set["path"] = path_feats["synt_path"]
    if "tree_distance" in feature_list:
        features_set["tree_distance"] = path_feats["length"]
    if "num_clauses" in feature_list:
        features_set["num_clauses"] = path_feats["num_clauses"]
    if "num_clauses_asc" in feature_list:
        features_set["num_clauses_asc"] = path_feats["num_clauses_asc"]
    if "num_clauses_desc" in feature_list:
        features_set["num_clauses_desc"] = path_feats["num_clauses_desc"]
    if "num_vp" in feature_list:
        features_set["num_vp"] = path_feats["num_vp"]
    if "num_vp_asc" in feature_list:
        features_set["num_vp_asc"] = path_feats["num_vp_asc"]
    if "num_vp_desc" in feature_list:
        features_set["num_vp_desc"] = path_feats["num_vp_desc" ]

    # Phrase type
    if ("phrase_type" in feature_list) or ("pred_lemma+phrase_type" in feature_list):
        features_set["phrase_type"] = argcand["info"]["cat"].lower()

    # Position
    if ("position" in feature_list) or ("voice+position" in feature_list):
        features_set["position"] = position(argcand)

    # Voice
    if ("voice" in feature_list) or ("voice+position" in feature_list):
        features_set["voice"] = voice(argcand)

    # SubCategorization
    if "subcat" in feature_list:
        features_set["subcat"]= subcategorization(argcand)

    # Head word related features
    phrase_tree = argcand["ins"].tree[argcand["info"]["treepos"]]
    head, head_postag, head_pos = head_word(argcand["ins"].tree, argcand["info"]["treepos"], phrase_tree, pp_contentword=True, depgraph=depgraph, const_span = argcand["info"]["span"])
    if ("head" in feature_list) or ("pred_lemma+head" in feature_list):
        features_set["head"] = head
    if "head_postag" in feature_list:
        features_set["head_postag"] = head_postag
    if "head_lemma" in feature_list:
        features_set["head_lemma"] = lexinfo_sent[head_pos][2]

    # Path Generalizations
    if "partial_path" in feature_list:
        features_set["partial_path"] = partial_path(argcand)

    # Predicate Context
    pred_context = predicate_context(argcand["ins"].verb_head,lexinfo_sent)
    if "pred_context_left" in feature_list:
        features_set["pred_context_left"] = pred_context["left"][1]
    if "pred_context_right" in feature_list:
        features_set["pred_context_right"] = pred_context["right"][1]
    if "pred_context_left_postag" in feature_list:
        features_set["pred_context_left_postag"] = pred_context["left"][3]
    if "pred_context_right_postag" in feature_list:
        features_set["pred_context_right_postag"] = pred_context["right"][3]

    # Punctuation
    punct_context = punctuation_context(argcand, lexinfo_sent)
    if "punct_left" in feature_list:
        features_set["punct_left"] = punct_context["left"][1]
    if "punct_right" in feature_list:
        features_set["punct_right"] = punct_context["right"][1]

    # Tokens that form the constituent
    constituent_tokens = tokens_lexinfo(argcand)
    if "first_form" in feature_list:
        if len(constituent_tokens) > 0:
            features_set["first_form"] = constituent_tokens[0]["word"]
        else:
            features_set["first_form"] = ""
    if "first_lemma" in feature_list:
        if len(constituent_tokens) > 0:
            features_set["first_lemma"] = constituent_tokens[0]["lemma"]
        else:
            features_set["first_lemma"] = ""
    if "first_postag" in feature_list:
        if len(constituent_tokens) > 0:
            features_set["first_postag"] = constituent_tokens[0]["pos"]
        else:
            features_set["first_postag"] = ""
    if "second_form" in feature_list:
        if len(constituent_tokens) > 1:
            features_set["second_form"] = constituent_tokens[1]["word"]
        else:
            features_set["second_form"] = ""
    if "second_lemma" in feature_list:
        if len(constituent_tokens) > 1:
            features_set["second_lemma"] = constituent_tokens[1]["lemma"]
        else:
            features_set["second_lemma"] = ""
    if "second_postag" in feature_list:
        if len(constituent_tokens) > 1:
            features_set["second_postag"] = constituent_tokens[1]["pos"]
        else:
            features_set["second_postag"] = ""
    if "third_form" in feature_list:
        if len(constituent_tokens) > 2:
            features_set["third_form"] = constituent_tokens[2]["word"]
        else:
            features_set["third_form"] = ""
    if "third_lemma" in feature_list:
        if len(constituent_tokens) > 2:
            features_set["third_lemma"] = constituent_tokens[2]["lemma"]
        else:
            features_set["third_lemma"] = ""
    if "third_postag" in feature_list:
        if len(constituent_tokens) > 2:
            features_set["third_postag"] = constituent_tokens[2]["pos"]
        else:
            features_set["third_postag"] = ""

    # Constituent Relative
    rel_feats = relatives_features(argcand, lexinfo_sent, depgraph)
    # Parent
    if "parent_phrase" in feature_list:
        features_set["parent_phrase"] = rel_feats["parent"]["cat"]
    if "parent_head" in feature_list:
        features_set["parent_head"] = rel_feats["parent"]["head"]
    if "parent_head_postag" in feature_list:
        features_set["parent_head_postag"] = rel_feats["parent"]["head_cat"]
    # Right sibling
    if "right_phrase" in feature_list:
        features_set["right_phrase"] = rel_feats["right"]["cat"]
    if "right_head" in feature_list:
        features_set["right_head"] = rel_feats["right"]["head"]
    if "right_head_postag" in feature_list:
        features_set["right_head_postag"] = rel_feats["right"]["head_cat"]
    # Left sibling
    if "left_phrase" in feature_list:
        features_set["left_phrase"] = rel_feats["left"]["cat"]
    if "left_head" in feature_list:
        features_set["left_head"] = rel_feats["left"]["head"]
    if "left_head_postag" in feature_list:
        features_set["left_head_postag"] = rel_feats["left"]["head_cat"]

    # Feature Combinations
    if "pred_lemma+path" in feature_list:
        features_set["pred_lemma+path"] = "{}+{}".format(features_set["pred_lemma"],features_set["path"])
    if "pred_lemma+head" in feature_list:
        features_set["pred_lemma+head"] = "{}+{}".format(features_set["pred_lemma"],features_set["head"])
    if "pred_lemma+phrase_type" in feature_list:
        features_set["pred_lemma+phrase_type"] = "{}+{}".format(features_set["pred_lemma"], argcand["info"]["cat"].lower())
    if "voice+position" in feature_list:
        features_set["voice+position"] = "{}+{}".format(features_set["voice"],features_set["position"])

    # First and Last Word/POS in Constituent
    constituent_tokens = tokens_lexinfo(argcand)
    if "first_form+first_postag" in feature_list:
        features_set["first_form+first_postag"] = "{}+{}".format(constituent_tokens[0]["word"],constituent_tokens[0]["pos"])
    if "last_form+last_postag" in feature_list:
        features_set["last_form+last_postag"] = "{}+{}".format(constituent_tokens[-1]["word"],constituent_tokens[-1]["pos"])

    # Negation
    if "negation" in feature_list:
        features_set["negation"] = particle_in_vp(argcand,"não")

    # Identity of the preposition
    if "preposition" in feature_list:
        if argcand["info"]["cat"].lower() == "pp":
            features_set["preposition"],_,_ = head_word(argcand["ins"].tree, argcand["info"]["treepos"], phrase_tree, pp_contentword=False, depgraph=depgraph, const_span=argcand["info"]["span"])
        else:
            features_set["preposition"] = ""

    # Use of "se" in Verb Clause
    if "se_in_vp" in feature_list:
        features_set["se_in_vp"] = particle_in_vp(argcand,"se")

    # Bag of words for nouns, adjectives and adverbs
    bags = bag_of_words(argcand, to_string = True)
    if "bag_of_nouns" in feature_list:
        features_set["bag_of_nouns"] = bags["noun"]
    if "bag_of_adj" in feature_list:
        features_set["bag_of_adj"] = bags["adj"]
    if "bag_of_adv" in feature_list:
        features_set["bag_of_adv"] = bags["adv"]

    # Roleset (sense) of the target verb
    if "verb_sense" in feature_list:
        features_set["verb_sense"] =  features_set["pred_lemma"] + "." + argcand["ins"].roleset

    # Others
    if "postag_sequence" in feature_list:
        features_set["postag_sequence"] = postag_sequence(argcand)
    if "top_sequence" in feature_list:
        features_set["top_sequence"] = TOP_sequence(argcand)

    return features_set


