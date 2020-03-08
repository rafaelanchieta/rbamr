# -*- coding: utf-8 -*-
'''
Created on May 14, 2012

@author: feralvam
'''
from nltk.tree import Tree
from numpy import array


def get_postag(tree_node):
    if isinstance(tree_node, Tree):
        return tree_node.node.split("|")[-1].strip("-").lower()
    return tree_node[-1].strip("-").lower()


def get_path_to_root(tree, node_treepos):
    path = [(node_treepos, get_postag(tree[node_treepos]))]
    for i in range(len(node_treepos) - 1, -1, -1):
        node_treepos = node_treepos[:i]
        path.append((node_treepos, get_postag(tree[node_treepos])))
    return path


def treepos_to_tuple(tree, node_treepos):
    if node_treepos == ():
        return (0, len(tree.leaves()))

    subtree = tree[node_treepos]
    start = _get_offset(tree, node_treepos[:-1], node_treepos[-1])
    if isinstance(subtree, Tree):
        subtree_leaves = subtree.leaves()
        end = start + len(subtree_leaves)
    else:
        end = start + 1
    return (start, end)


def _get_offset(tree, node_treepos, limit):
    subtree = tree[node_treepos]
    i = 0
    offset = 0
    for child in subtree:
        if i == limit: break
        if isinstance(child, Tree):
            offset += len(child.leaves())
        else:
            offset += 1
        i += 1

    if len(node_treepos) == 0:
        return offset
    else:
        return offset + _get_offset(tree, node_treepos[:-1], node_treepos[-1])


def constituent_treepos(tree, const_span):
    path_start = get_path_to_root(tree, tree.leaf_treeposition(const_span[0]))
    path_end = get_path_to_root(tree, tree.leaf_treeposition(const_span[-1]))

    # Find the intersection of the paths (preserving the order)
    intersec_path = [x for x in path_start if x in path_end]

    return intersec_path[0]


class FeatureEncoder(object):
    def __init__(self):
        self.features_ = []
        self.feature_values_ = dict()
        return

    def fit_transform(self, X):
        new_X = []
        for feat_set in X:
            new_feat_set = []
            for feat_name, feat_value in feat_set.iteritems():
                if not (feat_name in self.features_):
                    self.features_.append(feat_name)
                    self.feature_values_[feat_name] = []

                if not (feat_value in self.feature_values_[feat_name]):
                    self.feature_values_[feat_name].append(feat_value)

                new_feat_set.append(float(self.feature_values_[feat_name].index(feat_value)))

            new_X.append(array(new_feat_set))

        return array(new_X)

    def transform(self, X):
        new_X = []
        for feat_set in X:
            new_feat_set = []
            for feat_name, feat_value in feat_set.iteritems():
                if not (feat_name in self.features_):
                    raise ValueError("Invalid feature name.")

                if feat_value in self.feature_values_[feat_name]:
                    new_feat_value = float(self.feature_values_[feat_name].index(feat_value))
                else:
                    new_feat_value = float(len(self.feature_values_[feat_name]))

                new_feat_set.append(new_feat_value)

            new_X.append(array(new_feat_set))

        return array(new_X)
