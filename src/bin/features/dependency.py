# -*- coding: utf-8 -*-
'''
Created on May 29, 2012

@author: feralvam
'''


def position(argcand):
    """
    Indicates whether the word occurs before(0) or after(1) the target verb
    """
    verb_pos = argcand["verb"]["address"]
    arg_pos = argcand["info"]["address"]

    if arg_pos < verb_pos:
        return 0
    else:
        return 1


def voice(argcand):
    """
    Indicates whether the verb clause is in active(0) or passive voice(1)
    """
    # Check if the verb is in passive voice
    verb_postag = argcand["verb"]["tag"]
    if (verb_postag.lower() == "v-pcp"):
        # Its head must be a form of "ser" or "estar"
        verb_head_id = argcand["verb"]["head"]
        verb_head_lemma = argcand["depgraph"].get_by_address(verb_head_id)["lemma"]

        if verb_head_lemma.lower() in ["ser", "estar"]:
            return 1

    return 0


def path_deprel(depgraph, address_from, address_to):
    """
    Gets the path of dependency relations between two nodes in the dependency graph
    @param depgraph: dependency graph of the sentence
    @param addres_from: the address of the starting point of the path
    @param addres_to: the address of the finishing point of the path
    """

    direct_path = _get_path_deprel(depgraph, depgraph.get_by_address(address_from), address_to)
    path = []
    if len(direct_path) > 0:
        path_to = direct_path
    else:
        path_from = _get_path_deprel(depgraph, depgraph.root, address_from)
        path_to = _get_path_deprel(depgraph, depgraph.root, address_to)

        # Find the intersection of the paths (preserving the order)
        intersec_path = [x for x in path_from if x in path_to]

        # Removing the intersection
        if len(intersec_path) > 0:
            intersec = list(intersec_path)[-1]
            path_from = path_from[path_from.index(intersec) + 1:]
            path_to = path_to[path_to.index(intersec) + 1:]

        path_from.reverse()
        # Forming the path
        path = []
        for path_node in path_from:
            path.append("{}¡".format(path_node[1]))

    for path_node in path_to:
        path.append("{}{}".format(path_node[1], path_node[2]))

    return path


def path_postag(depgraph, address_from, address_to):
    """
    Gets the path of Part-of-Speech tags between two nodes in the dependency graph
    @param depgraph: dependency graph of the sentence
    @param addres_from: the address of the starting point of the path
    @param addres_to: the address of the finishing point of the path
    """

    direct_path = _get_path_postag(depgraph, depgraph.get_by_address(address_from), address_to)
    path = []

    if len(direct_path) > 0:
        path_to = direct_path
    else:
        # Look for the inverse direct path
        inv_direct_path = _get_path_postag(depgraph, depgraph.get_by_address(address_to), address_from)

        if len(inv_direct_path) > 0:
            inv_direct_path.reverse()
            path_to = inv_direct_path
        else:
            path_from = _get_path_postag(depgraph, depgraph.root, address_from)
            path_to = _get_path_postag(depgraph, depgraph.root, address_to)

            # Find the intersection of the paths (preserving the order)
            intersec_path = [x for x in path_from if x in path_to]

            # Removing the intersection
            if len(intersec_path) > 0:
                intersec = list(intersec_path)[-1]
                path_from = path_from[path_from.index(intersec) + 1:]
                path_to = path_to[path_to.index(intersec) + 1:]

            path_from.reverse()
            # Forming the path
            path = []
            for path_node in path_from:
                path.append("{}".format(path_node[1]))

    for path_node in path_to:
        path.append("{}".format(path_node[1]))

    return path


def _get_path_deprel(depgraph, node_from, address_to):
    for dep in node_from["deps"]:
        if dep == address_to:
            return [(node_from["address"], depgraph.get_by_address(address_to)["rel"], "!", dep)]

    for dep in node_from["deps"]:
        path = _get_path_deprel(depgraph, depgraph.get_by_address(dep), address_to)
        if len(path) > 0:
            path.insert(0, (node_from["address"], depgraph.get_by_address(dep)["rel"], "!", dep))
            return path
    return []


def _get_path_postag(depgraph, node_from, address_to):
    path = depgraph.get_cycle_path(node_from, address_to)

    if len(path) > 0:
        # There is a direct path. Give it form
        postag_path = []
        for node_address in path:
            postag_path.append((node_address, (depgraph.get_by_address(node_address)["tag"])))
        postag_path.append((address_to, (depgraph.get_by_address(address_to)["tag"])))
        return postag_path
    else:
        return path


def head_dep(const_span, depgraph):
    const_start, const_end = const_span
    const_start += 1

    for i in range(const_start, const_end + 1):
        node = depgraph.get_by_address(i)
        if node["head"] < const_start or node["head"] > const_end:
            return {"word": node["word"], "lemma": node["lemma"], "rel": node["rel"], "tag": node["tag"],
                    "address": node["address"],
                    "deps": node["deps"]}

    raise ValueError("No head found.")

    return


def feature_extractor_dep(argcand, feature_list):
    features_set = dict()

    head_info = head_dep(argcand["info"]["span"], argcand["depgraph"])

    if "head_dep" in feature_list:
        features_set["head_dep"] = head_info["word"]

    if "dep_rel" in feature_list:
        features_set["dep_rel"] = head_info["rel"]

    return features_set

