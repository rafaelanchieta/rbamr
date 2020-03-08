# -*- coding: utf-8 -*-
#
# Data structures to represent entities from the Propbank.Br corpus.
# They were intended to be similar to those for Propbank, which can be
# found in the NLTK <http://www.nltk.org>
#
# Author: Erick Rocha Fonseca
#         Fernando Alva Manchego

import os.path
import re

from nltk.corpus.reader import CorpusReader, XMLCorpusView
from nltk.corpus.reader.propbank import PropbankTreePointer, PropbankSplitTreePointer
from nltk.corpus.reader.util import StreamBackedCorpusView, read_line_block
from nltk.parse.dependencygraph import DependencyGraph
from nltk.tree import Tree


class PropbankBrCorpusReader(CorpusReader):
    """
    Corpus reader for the Brazilian version of the Propbank corpus.
    """
    def __init__(self, root, propfile, verbsfile=None, encoding=None):
        """
        @param root: The root directory for this corpus.
        @param propfile: The name of the file containing the predicate argument annotations (relative to C{root}).
        It must be a XML file.
        @param verbsfile: The name of the file containing a list of verbs lemmas in the corpus (relative to C{root})
        It must be a text file.
        """
        # Check if the files are of the proper type
        propfile_type = os.path.splitext(propfile)[1]
        verbsfile_type = os.path.splitext(verbsfile)[1]

        if (propfile_type.lower() != ".xml"):
            raise TypeError ("Propfile must be a XML file.")

        if (verbsfile_type.lower() != ".txt"):
            raise TypeError ("Verbsfile must be a text file.")

        CorpusReader.__init__(self, root, [propfile, verbsfile], encoding)
        self._propfile = propfile
        self._verbsfile = verbsfile

    def instances(self, constituent = True):
        """
        @return: a corpus view that acts as a list of L{PropbankBrInstance} objects,
        one for each verb instance in the corpus
        """
        if constituent:
            return XMLCorpusView(self.abspath(self._propfile), "corpus/body/s", self.__transform_xml_instance)
        else:
            return XMLCorpusView(self.abspath(self._propfile), "corpus/body/s", self.__transform_xml_instance_dep)



    def verbs(self):
        """
        @return: a corpus view that acts as a list of all verb lemmas in this corpus (from verbsfile).
        """
        return StreamBackedCorpusView(self.abspath(self._verbsfile),
                                      read_line_block, encoding=self.encoding(self._verbsfile))

    def roleset(self, roleset_id):
        """
        @param roleset_id: the id of a roleset
        @return: the xml description for the given roleset
        """
        raise NotImplementedError('No roleset information in PropBank.Br (yet)')

    def __transform_xml_instance(self, instance_xml, context):
        return PropbankBrInstance.parse(instance_xml)

    def __transform_xml_instance_dep(self, instance_xml, context):
        return PropbankBrInstance.parse(instance_xml, False)


# It doesn't inherit from PropbankInstance because no method or member of the base class will be used as is.
class PropbankBrInstance(object):

    def __init__(self, instanceid, parse_tree, dep_graph, roleset, predicate, arguments):

        self.instanceid = instanceid
        """The instance's id in the corpus."""

        self.parse_tree = parse_tree
        """The instance's syntactic tree."""

        self.dep_graph = dep_graph
        """The instance's dependency graph."""

        self.roleset = roleset
        """The name of the roleset used by this instance predicate."""

        self.predicate = predicate
        """A L{PropbankBrTreePointer} indicating the position of this
        instance's predicate within its containing sentence."""

        self.arguments = arguments
        """A list of tuples (argloc, argid), specifying the location and identifier (type)
        for each of the predicate's argument in the containing sentence. This list
        does not contain the predicate."""


    def __repr__(self):
        return ('<PropbankBrInstance: %s>' % self.instanceid)


    def __str__(self):

        if self.parse_tree == None and self.dep_graph != None:
            words = map(str, self.dep_graph.tree().leaves())
        else:
            words = map(str, self.parse_tree.leaves())

        # Indicate which word is the target verb of the instance
        predicate_ids = self.predicate.get_id()
        if isinstance(predicate_ids, basestring):
            predicate_ids = [predicate_ids]
        predicate_words = [self.parse_tree.subtree(predicate_id).leaves_text()[0] for predicate_id in predicate_ids]

        formatted_words = []
        for word in words:
            if word in predicate_words:
                word = "[%s]" % word
            formatted_words.append(word)

        s = " ".join(formatted_words)
        s = s.replace(" ,", ",")
        s = s.replace(" .", ".")
        return s


    @staticmethod
    def parse(instance_xml, constituent_based = True):
        """
        @param instance_xml: A XML ElementTree with all the information of an instance in the Propbank.Br corpus
        @param consituent: Indicates if the information on the PropbankBrInstance should be constituent or dependency-based
        @return: a PropbankBrInstance
        """

        # Check if the sentence is flagged as WRONGSUBCORPUS to discard it

        globals_frame = instance_xml.find("sem/globals")
        if globals_frame:
            globals_list = instance_xml.findall("sem/globals/global")
            for g in globals_list:
                if (g.get("type") == "WRONGSUBCORPUS"):
                    return None

        # Check if the instance has been annotated (i.e, has a semantic frame)

        sem_frames = instance_xml.find("sem/frames")
        if sem_frames is None: return None
        if len(sem_frames) <> 1:
            print(instance_xml.get("id"))
            return None

        # Each instance has just one semantic frame corresponding to the verb sense whose arguments are being annotated
        sem_frame = sem_frames[0]

        graph_xml = instance_xml.find("graph")

        predicate = None
        arguments = None
        roleset = None

        if constituent_based:
            # Get the parse tree
            parse_tree = PropbankBrInstance.__make_parse_tree(graph_xml)
            # Check if there is a correct parse tree for the instance
            if (parse_tree == None): return None
            dep_graph = None

            predicate = PropbankBrInstance.__extract_predicate(sem_frame, parse_tree)
            arguments = PropbankBrInstance.__extract_arguments(sem_frame, parse_tree)
            roleset = PropbankBrInstance.__extract_roleset(instance_xml, predicate.get_id())
        else:
            # Get the dependency graph
            dep_graph = PropbankBrInstance.__make_dependency_graph(graph_xml)
            # Check if there is a correct dependency graph for the instance
            if (dep_graph == None): return None
            parse_tree = None

            predicate = PropbankBrInstance.__extract_predicate_dep(graph_xml, sem_frame)
            arguments = PropbankBrInstance.__extract_arguments_dep(graph_xml, sem_frame, dep_graph)
            #roleset = PropbankBrInstance.__extract_roleset(instance_xml, predicate.get_id())

        instance_id = instance_xml.get("id")

        return PropbankBrInstance(instance_id, parse_tree, dep_graph, roleset, predicate, arguments)

    @staticmethod
    def __make_parse_tree(graph_xml):
        """
        @param graph_xml: A XML ElementTree containing all the syntactic information of an instance
        @return: the parse tree in NLTK format
        """
        root_id = graph_xml.get("root")
        nonterminal_nodes = graph_xml.findall("nonterminals/nt")
        terminal_nodes = graph_xml.findall("terminals/t")

        # Create a dictionary for all terminal and nonterminal nodes using their ids
        tuples = map(lambda x: (x.get("id"), x), nonterminal_nodes + terminal_nodes)
        tree_nodes = dict(tuples)

        root = tree_nodes.pop(root_id)
        root_edge = root.findall("edge")[0]

        # print "TREE_NODES 1", len(tree_nodes)
        # The first node has no information. Therefore, we start from its only child (the actual tree root)
        parse_tree = PropbankBrInstance.__make_subtree(root_edge, tree_nodes)

        # print "TREE_NODES 2", len(tree_nodes), tree_nodes

        # In order for the parse tree to be correct, all nodes should have been processed
        if (len(tree_nodes) != 0):
            return None
        else:
            return parse_tree


    @staticmethod
    def __make_subtree(subtree_root_edge, tree_nodes):
        """
        @param subtree_root_edge: An edge of the tree containing the root of the subtree
        @param tree_nodes: A dictionary with the terminal and nonterminal nodes available
        @return: A PropbankBrTree corresponding to the subtree with syntactic information
        """
        # The subtree is constructed recursively, from root to leaves

        subtree_root_edge_label = subtree_root_edge.get("label")
        subtree_root_id = subtree_root_edge.get("idref")
        subtree_root = tree_nodes.pop(subtree_root_id)

        if subtree_root.tag == "t":
            # It's a terminal node
            tree_node = subtree_root_edge_label + "|" + subtree_root.get("pos")
            t = PropbankBrTerminalNode(subtree_root)

            return PropbankBrTree(subtree_root_id, tree_node, [t])
        else:
            # It's a nonterminal node. Its edges should be processed recursively
            subtree_children_edges = subtree_root.findall("edge")
            children = []

            for subtree_child_edge in subtree_children_edges:
                subtree_child = PropbankBrInstance.__make_subtree(subtree_child_edge, tree_nodes)
                # Check if the subtree is formed by non continuous terminals
                split_subtree_child = PropbankBrInstance.__split_tree (subtree_child)
                for split_child in split_subtree_child:
                    children.append(split_child)

            tree_node = subtree_root_edge_label + "|" + subtree_root.get("cat")

            # Sort the children according to the order in which terminals appear
            children.sort(key=lambda child:child.max_terminal_position)

            return PropbankBrTree(subtree_root_id, tree_node, children)


    @staticmethod
    def __split_tree(tree):
        # It's going to be split at most in two
        children_subtree1 =[]
        children_subtree2 =[]
        already_split = False
        children = []
        for child in tree:
            if not isinstance(child,Tree):
                return [tree]
            else:
                children.append(child)

        for i in range(len(children)):
            curr_child = children[i]
            if (already_split):
                children_subtree2.append(curr_child)
            else:
                children_subtree1.append(curr_child)
                if (i == len(children)-1): break
                next_child = children[i+1]
                # Check if they are continuous
                if (curr_child.max_terminal_position + 1 != next_child.min_terminal_position):
                    already_split = True

        # Check if the tree was split
        if (len(children_subtree2)>0):
            split_tree = []
            split_tree.append(PropbankBrTree(tree.id, tree.node + '-', children_subtree1))
            split_tree.append(PropbankBrTree(tree.id, tree.node.split("|")[0] + "|" + "-" + tree.node.split("|")[-1] , children_subtree2))
            return split_tree
        else:
            return [tree]


    @staticmethod
    def __make_dependency_graph(graph_xml):
        """
        @param graph_xml: A XML ElementTree containing all the syntactic information of an instance
        @return: a NLTK dependency graph
        """
        root_id = graph_xml.get("root")
        nonterminal_nodes = graph_xml.findall("nonterminals/nt")
        terminal_nodes = graph_xml.findall("terminals/t")

        # Create a dictionary for all terminal and nonterminal nodes using their ids
        tuples = map(lambda x: (x.get("id"), x), nonterminal_nodes + terminal_nodes)
        graph_nodes = dict(tuples)

        root = graph_nodes.pop(root_id)
        root_edge = root.findall("edge")[0]

        # The first node has no information. Therefore, we start from its only child (the actual tree root)
        dep_graph = DependencyGraph()
        PropbankBrInstance.__make_subgraph(graph_xml,root_edge, graph_nodes, dep_graph.nodelist,0, root_edge.get("label"),[])
        #PropbankBrInstance.__make_subgraph(graph_xml,root_edge, graph_nodes, dep_graph., 0, root_edge.get("label"),[])

        # Sort the graph's node list according to the order in which terminals appear
        dep_graph.nodelist.sort(key=lambda node:node["address"])

        # In order for the parse tree to be correct, all nodes should have been processed
        if (len(graph_nodes) != 0):
            return None
        else:
            return dep_graph

    @staticmethod
    def _max_terminal(graph_xml, edge):
        max_terminal = 1
        # Check if the edge is a terminal node
        for terminal in graph_xml.iterfind("terminals/t"):
            if terminal.get("id") == edge.get("idref"):
                max_terminal = int(re.search("_([0-9]+)", edge.get("idref")).group(1))
        else:
            # It isn't a terminal node. Find its children
            for nonterminal in graph_xml.iterfind("nonterminals/nt"):
                if nonterminal.get("id") == edge.get("idref"):
                    # Find the max terminal for each of its children
                    children = []
                    for child in nonterminal.iterfind("edge"):
                        children.append(PropbankBrInstance._max_terminal(graph_xml,child))
                        max_terminal = max(children)

        return max_terminal

    @staticmethod
    def __make_subgraph(graph_xml,subgraph_root_edge, graph_nodes, graph_nodelist, head, head_rel, deps):
        """
        @param subgraph_root_edge: An edge of the graph containing the root of the subgraph
        @param graph_nodes: A dictionary with the terminal and nonterminal nodes available
        @return: A NLTK Dependency Graph corresponding to the subgraph with syntactic information
        """
        # The subgraph is constructed recursively, from root to leaves

        subgraph_root_id = subgraph_root_edge.get("idref")
        subgraph_root = graph_nodes.pop(subgraph_root_id)

        if subgraph_root.tag == "t":
            # It's a terminal node
            address = int(re.search("_([0-9]+)", subgraph_root.get("id")).group(1))
            word = subgraph_root.get("word")
            lemma = subgraph_root.get("lemma")
            tag = subgraph_root.get("pos")
            morph = subgraph_root.get("morph")
            deps = []
            graph_nodelist.append({'address': address, 'word': word, 'lemma':lemma, 'tag': tag, 'feat': morph,
                                   'head': int(head), 'rel': head_rel, 'deps': deps})

            return address

        else:
            # It's a nonterminal node.
            subgraph_nodes_edges = subgraph_root.findall("edge")

            # Sort the subgraph's node according to the order they appear in the sentence
            subgraph_nodes_edges.sort(key=lambda edge:PropbankBrInstance._max_terminal(graph_xml,edge))

            subgraph_root_cat = subgraph_root.get("cat")

            # Identify which is the head of this nonterminal
            head_label_list = PropbankBrInstance.__find_head_rule(subgraph_root_cat, subgraph_nodes_edges)

            # Find the subgraph where the head is located
            for subgraph_node_edge in subgraph_nodes_edges:
                if (subgraph_node_edge.get("label") in head_label_list):
                    head_node_edge = subgraph_node_edge
                    break
            else:
                # Pick the first edge as head
                head_node_edge = subgraph_nodes_edges[0]

            # Get the head
            #subgraph_head = re.search("_([0-9]+)", head_node_edge.get("idref")).group(1)
            # Find the nonterminal that corresponds to the head
            head_subgraph = graph_nodes.get(head_node_edge.get("idref"))
            head_subgraph_edge = head_node_edge

            # Process the head node to get the exact head position (word number)
            subgraph_head = PropbankBrInstance.__make_subgraph(graph_xml,head_subgraph_edge, graph_nodes, graph_nodelist, head, head_rel, deps)
            aux_head = -1
            edges_head = []
            edges_headaux = []
            deps_aux = []
            # One head rule missing:
            # "Subjects and subordinators attach to the finite verb, the rest of the clause level functions attach to the main verb"
            # Check if the head node is a VP formed by more than one node
            if (head_subgraph.get("cat") == "vp" and head_subgraph.findall("edge") >1):
                # In this case, the subgraph_head already found is the correct head for subordinators.
                # It's necessary to find the MV for it to become the head of the other functions
                for edge in head_subgraph.iterfind("edge"):
                    if edge.get("label") == "MV":
                        # It's always going to be a terminal node
                        aux_head = int(re.search("_([0-9]+)", edge.get("idref")).group(1))
                        break
                else:
                    aux_head = subgraph_head

                edges_head = ["SUBJ", "SUB", "PU"]
                edges_headaux = []

            # Special case: When processing a VP, for the constituents out of the clause, the first AUX is the head
            # but for MV inside the VP, its head is the last AUX.
            elif subgraph_root_cat == "vp" and len(subgraph_nodes_edges) > 1 and subgraph_node_edge.get("label")!="MV":
                # It's necessary to find the last AUX before the MV for it to become the head of the MV
                for subgraph_node_edge in subgraph_nodes_edges:
                    if subgraph_node_edge.get("label") == "AUX":
                        # It's always going to be a terminal node
                        aux_head = int(re.search("_([0-9]+)", subgraph_node_edge.get("idref")).group(1))

                edges_head = []
                edges_headaux = ["MV"]

            two_heads = False
            # Two heads: Check if the constituent has two heads ("H")
            for subgraph_node_edge in subgraph_nodes_edges:
                if subgraph_node_edge != head_subgraph_edge:
                    if subgraph_node_edge.get("label") == "H":
                        edge_num = int(re.search("_([0-9]+)", subgraph_node_edge.get("idref")).group(1))
                        if edge_num != subgraph_head:
                            # Process the second head
                            aux_head = PropbankBrInstance.__make_subgraph(graph_xml, subgraph_node_edge, graph_nodes,
                                                                                          graph_nodelist, head, head_rel, deps_aux)
                            # aux_head = edge_num
                            two_heads = True
                            break

            if two_heads:
                post_head = False
                for subgraph_node_edge in subgraph_nodes_edges:
                    edge_num = int(re.search("_([0-9]+)", subgraph_node_edge.get("idref")).group(1))
                    if subgraph_node_edge == head_subgraph_edge: continue
                    if edge_num == aux_head:
                        post_head = True
                        continue
                    edge_label = subgraph_node_edge.get("label")
                    if not post_head:
                        deps.append(PropbankBrInstance.__make_subgraph(graph_xml,subgraph_node_edge, graph_nodes, graph_nodelist,
                                                                       subgraph_head, edge_label,[]))

                    else:
                        deps_aux.append(PropbankBrInstance.__make_subgraph(graph_xml,subgraph_node_edge, graph_nodes, graph_nodelist,
                                                                       aux_head, edge_label,[]))
            else:
                # Process each edge (different from the head) to:
                # (i) Get the dependencies of the head;
                # (ii) Propagate the head information
                for subgraph_node_edge in subgraph_nodes_edges:
                    if subgraph_node_edge != head_subgraph_edge:
                        edge_label = subgraph_node_edge.get("label")
                        if (edges_head == [] and not edge_label in edges_headaux) or edge_label in edges_head:
                            deps.append(PropbankBrInstance.__make_subgraph(graph_xml,subgraph_node_edge, graph_nodes, graph_nodelist,
                                                                       subgraph_head, edge_label,[]))

                        elif edges_headaux == [] or edge_label in edges_headaux:
                            deps_aux.append(PropbankBrInstance.__make_subgraph(graph_xml,subgraph_node_edge, graph_nodes, graph_nodelist,
                                                                       aux_head, edge_label,[]))


            # Update the head information in the graph_nodelist with the dependencies
            found_head = found_auxhead = False
            for i in range(len(graph_nodelist)):
                node_address = graph_nodelist[i]["address"]
                if node_address == subgraph_head:
                    graph_nodelist[i]["deps"] = deps
                    found_head = True
                elif node_address == aux_head:
                    graph_nodelist[i]["deps"] = deps_aux
                    found_auxhead = True
                if found_head and found_auxhead: break

            return subgraph_head

    @staticmethod
    def __find_head_rule(subgraph_root_cat, subgraph_nodes_edges):

        if len(subgraph_nodes_edges) == 1: return []
        # The rules in the README file from the CoNNL-X Bosque corpus were used
        # In an fcl or icl, the first verb is head, subordinators become dependents, even if they don't have a real clause function
        if subgraph_root_cat in ["fcl", "icl","x"]:
            head_label_list = ["P", "PMV","PAUX","X"]

        # Main verbs are attached to auxiliaries
        elif subgraph_root_cat in ["vp"] and len(subgraph_nodes_edges)>1:
            head_label_list = ["AUX", "MV"]

        # In hypotactic groups and pp's, H stays head
        elif subgraph_root_cat in ["np","ap","advp","pp"]:
            head_label_list = ["H"]

        # In acl, first constituent gets to be the head (typically the SUB)
        elif subgraph_root_cat in ["acl"]:
            head_label_list = ["P"]

        # Coordinators and second and following conjuncts attach to the first conjunct
        elif subgraph_root_cat in ["cu"]:
            # "non-regular" par is treated like an acl, i.e. the first constituent becomes head (if there's no predicate)
            head_label_list = ["P"]
            # Determine if it's a "regular" par (with CJT)
            for subgraph_node_edge in subgraph_nodes_edges:
                if subgraph_node_edge.get("label") == "CJT":
                    # In a "regular" par, first CJT gets to be the head
                    head_label_list = ["CJT"]
                    break
                elif subgraph_node_edge.get("label") == "X":
                    # In a "non-regular" par, without CJTs, X becomes head, if there is one. If X is itself a "regular" par,
                    # this automatically means, its CJT will become head
                    head_label_list = ["X"]
        # In averbal clauses, the first constituent is regarded the head
        else:
            head_label_list = ["H"]

        return head_label_list


    @staticmethod
    def __extract_predicate(sem_frame, parse_tree):
        """
        @param sem_frame: The semantic frame of the instance.
        @param parse_tree: The syntactic parse tree of the sentence.
        @return: A PropbankBrTreePointer indicating the position of the predicate in the sentence.
        """

        target_verb = sem_frame.find("target")
        # The target verb can be formed by more than one node in the tree
        target_verb_nodes = target_verb.findall("fenode")

        if len(target_verb_nodes) > 1:
            pointers = []
            for target_verb_node in target_verb_nodes:
                target_verb_node_id = target_verb_node.get("idref")
                pointer = PropbankBrTreePointer(parse_tree, target_verb_node_id)
                pointers.append(pointer)
            return PropbankBrSplitTreePointer(pointers)
        else:
            idref = target_verb_nodes[0].get("idref")
            return PropbankBrTreePointer(parse_tree, idref)

    @staticmethod
    def __extract_arguments(sem_frame, parse_tree):
        """
        @param sem_frame: The semantic frame of the instance.
        @param parse_tree: The syntactic parse tree of the sentence.
        @return: A list of tuples (argloc, argid), specifying the location and identifier for each of the
                predicate's argument in the containing sentence.
        """
        sem_frame_elements = sem_frame.findall("fe")
        arguments = []
        for sem_frame_element in sem_frame_elements:
            argid = sem_frame_element.get("name")

            # An argument can be formed by more than one node in the tree
            argloc_nodes = sem_frame_element.findall("fenode")

            if len(argloc_nodes) > 1:
                pointers = []
                for argloc_node in argloc_nodes:
                    argloc_node_id = argloc_node.get("idref")
                    pointer = PropbankBrTreePointer(parse_tree.subtree(argloc_node_id))
                    pointers.append(pointer)
                argloc = PropbankBrSplitTreePointer(pointers)
            else:
                argloc_id = argloc_nodes[0].get("idref")
                argloc = PropbankBrTreePointer(parse_tree.subtree(argloc_id))

            arguments.append((argloc, argid))

        return arguments

    @staticmethod
    def __extract_roleset(instance_xml, predicate_id):
        """
        @param instance_xml: A XML ElementTree with all the information of an instance in the Propbank.Br corpus
        @param predicate_id: An string or list of strings with the ids of the target verbs in the instance
        @return: The name of the roleset used by this instance's predicate
        """
        wordtags = instance_xml.findall("sem/wordtags/wordtag")
        # caso devesse haver necessariamente 1 wordtag, poderia fazer:
        # assert len(wordtags) == 1

        if len(wordtags) == 0: return None
        if type(predicate_id) is not list:
            predicate_id = [predicate_id]
        senses = [x for x in wordtags if x.get("idref") in predicate_id and x.get("name") in ["sentido", "PB-roleset"]]

        # Check that there's at least one sense defined for the target verb in the instance
        # assert len(senses) <= 1
        roleset = None
        for sense in senses:
            if sense.get("name") == "sentido":
                roleset = sense.text

        return roleset

    @staticmethod
    def __extract_predicate_dep(graph_xml, sem_frame):
        """
        @param graph_xml:
        @param sem_frame: The semantic frame of the instance.
        @return: A integer indicating the position of the predicate in the sentence.
        """
        target_verb = sem_frame.find("target")
        # The target verb can be formed by more than one node in the tree
        target_verb_nodes = target_verb.findall("fenode")

        if len(target_verb_nodes) == 1:
            pred_num = re.search("_([0-9]+)", target_verb_nodes[0].get("idref")).group(1)
        else:
            for node in target_verb_nodes:
                node_id = node.get("idref")
                # Check if it is a verbal terminal node
                for terminal in graph_xml.iterfind("terminals/t"):
                    if terminal.get("id") == node_id and terminal.get("pos") in ["v-fin", "v-inf", "v-pcp", "v-ger"]:
                        pred_num = re.search("_([0-9]+)", node_id).group(1)
                        break
                else:
                    continue
                break

        return int(pred_num)

    @staticmethod
    def __extract_arguments_dep(graph_xml, sem_frame, dep_graph):
        arguments = []
        for fe in sem_frame.iterfind("fe"):
            argid = fe.get("name").upper().replace("ARG", "A")
            # Find the head of the semantic argument following the CoNLL-2008 approach:
            # "The head of a semantic argument is assigned to the token inside the argument
            #  whose head is a token outside the argument boundaries"

            arg_heads = PropbankBrInstance.__extract_argument_head(fe, graph_xml, dep_graph)

            if len(arg_heads)==0: return []

            if len(arg_heads)>1:
                # If several syntactic heads are detected, split the original argument into
                # a sequence of discontinuous arguments:[A] [C-A]
                for i in range(len(arg_heads)):
                    if i==0:
                        arguments.append( (arg_heads[i],argid) )
                    else:
                        arguments.append( (arg_heads[i],"C-{:}".format(argid)) )
            else:
                arguments.append( (arg_heads[0],argid) )

        return arguments

    @staticmethod
    def __extract_argument_head (arg_frame, graph_xml, dep_graph):
        arg_heads = []
        to_process = []
        processed = []
        for fenode in arg_frame.iterfind("fenode"):
            to_process.append( fenode.get("idref") )

        while len(to_process)>0:
            curr_node = to_process.pop()
            # Check if it's a terminal
            for terminal in graph_xml.iterfind("terminals/t"):
                if terminal.get("id") == curr_node:
                    node_id = int(re.search("_([0-9]+)", curr_node).group(1))
                    # Get it's head
                    for node in dep_graph.nodelist:
                        if node["address"] == node_id:
                            processed.append( (int(node_id),int(node["head"])) )
                            break
            else:
                # It's a non-terminal
                for nonterminal in graph_xml.iterfind("nonterminals/nt"):
                    if nonterminal.get("id") == curr_node:
                        # Add all of its children to the list to be processed
                        for edge in nonterminal.iterfind("edge"):
                            to_process.append(edge.get("idref"))
                        break

        # Order the processed nodes by their word number (first argument in the tuple)
        processed.sort()

        # Find the min and max word number in the list
        min_wordnum,_ = processed[0]
        max_wordnum,_ = processed[-1]

        # Check each of the processed nodes to find which ones have a head outside the argument
        for wordnum,head  in processed:
            if (head < min_wordnum) or (head >max_wordnum):
                arg_heads.append(wordnum)

        # NOTE: The last procedure automatically does the merging of discontinuous arguments

        return arg_heads


class PropbankBrTerminalNode(object):
    """
    Represents a terminal node in a PropBank.Br syntactic tree.
    """
    def __init__(self, element_xml):
        '''
        @param A XML ElementTree containing information of the word in the terminal node
        '''
        self.lemma = element_xml.get("lemma")
        """Lemma of the word."""

        self.extra = element_xml.get("extra")
        """Extra information about the word."""

        self.word = element_xml.get("word")
        """The word itself."""

        self.sem = element_xml.get("sem")
        """Semantic information of the word (named entity)"""

        self.morph = element_xml.get("morph")
        """Morphological information of the word (gender, number, etc.)."""

        self.pos = element_xml.get("pos")
        """Part-of-speech information of the word."""

        node_id = element_xml.get("id")
        self.num = re.search("_([0-9]+)", node_id).group(1)
        self.num = int(self.num)
        """The number (position) of the word in its containing sentence (starting with 1)."""

        self.id = node_id
        """The id of the node in the parse tree."""


    def __str__(self):
        return self.word

    def __repr__(self):
        return "PropbankBrTerminalNode (%s)" % (self.word)


class PropbankBrTree(Tree):
    """
    Extends NLTK Tree with an extra member named id to uniquely identify the tree.
    It also implements a method to look for subtrees using their id.
    """

    def __new__(cls, idTree, node_or_string, children=None):
        return super(PropbankBrTree, cls).__new__(cls, node_or_string, children)

    def __init__(self, idTree, node_or_string, children=None):
        if children is None: return # see note in Tree.__init__()
        Tree.__init__(self, node_or_string, children)

        self.id = idTree

        terminal_nodes = self.subtrees(lambda x: isinstance(x[0], PropbankBrTerminalNode))
        terminal_nodes_positions = [x[0].num for x in terminal_nodes]

        self.min_terminal_position = min(terminal_nodes_positions)
        self.max_terminal_position = max(terminal_nodes_positions)


    def subtree(self, idSubtree):
        """
        @param idSubtree: The id of a subtree in this PropbankBrTree.
        @return: The subtree with the id indicated, or None if it doesn't exist.
        """
        gen_subtrees = self.subtrees(lambda x: x.id == idSubtree)
        subtree = [subtree for subtree in gen_subtrees][0]
        if subtree:
            return subtree
        else:
            return None

    def leaves_text(self):
        """
        @return: The tree leaves as plain text.
        """
        leaves = self.leaves()
        return [leave.word for leave in leaves]


class PropbankBrTreePointer(PropbankTreePointer):
    """
    Pointer to a constituent of a PropbankBrTree.
    """
    def __init__(self, tree, idSubtree=None):
        """
        @param tree: a PropbankBrTree
        @param idSubtree: the id of a subtree in tree to which create a pointer. If None, a pointer to
                        the tree is created.
        """

        if (idSubtree != None):
            tree = tree.subtree(idSubtree)

        wordnum = tree.min_terminal_position - 1

        # Find the height of the subtree
        height = 0
        while isinstance(tree[0], PropbankBrTree):
            tree = tree[0]
            height += 1

        self.id = tree.id
        PropbankTreePointer.__init__(self, wordnum, height)

    def __repr__(self):
        return "PropbankBrTreePointer(%d,%d)" % (self.wordnum, self.height)

    def get_id(self):
        return self.id


class PropbankBrSplitTreePointer(PropbankBrTreePointer, PropbankSplitTreePointer):
    """
    Pointer to separated constituents in a same PropbankBrTree.
    """
    def __init__(self, pieces):
        self.pieces = pieces
        """List of PropbankBrTreePointers which form the pointed sequence."""

    def get_id(self):
        return [x.get_id() for x in self.pieces]

    def select(self, tree):
        subtrees = []
        for piece in self.pieces:
            subtrees.append(piece.select(tree))
        return PropbankBrTree(None, "*SPLIT*", subtrees)


    def __str__(self):
        return ','.join('%s' % p for p in self.pieces)

    def treepos(self, tree):
        treepos_list = []
        for piece in self.pieces:
            treepos_list.append(piece.treepos(tree))
        return treepos_list

