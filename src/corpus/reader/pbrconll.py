'''
Created on May 15, 2012

@author: feralvam
'''

from __future__ import unicode_literals

# import nltk
from nltk.corpus.reader.conll import ConllCorpusReader
from nltk.parse.dependencygraph import DependencyGraph
from nltk.tree import Tree
from nltk.util import LazyMap, LazyConcatenation


class PropbankBrConllCorpusReader(ConllCorpusReader):
    """
    Corpus reader for the Brazilian version of the Propbank corpus in CoNLL format.
    It's an extension of the ConllCorpusReader capable of handling additional columns
    present in the Propbank.Br corpus (constituent and dependency-based)
    """

    ID = "id"               #: column type for token counter
    WORDS = "words"         #: column type for word forms
    LEMMA = "lemma"         #: column type for gold-standard lemma
    PLEMMA = "plemma"       #: column type for automatically predicted lemma
    POS = "pos"             #: column type for gold-standard part-of-speech tags
    PPOS = "ppos"           #: column type for automatically predicted part-of-speech tags
    FEAT = "feat"           #: column type for gold-standard morphological features
    PFEAT = "pfeat"         #: column type for automatically predicted features
    CLAUSE = "clause"       #: column type for gold-standard clause information
    PCLAUSE = "pclause"     #: column type for automatically predicted clause information
    FCLAUSE = "fclause"     #: column type for gold-standard full clause information
    PFCLAUSE = "pfclause"   #: column type for automatically predicted full clause information
    TREE = "tree"           #: column type for gold-standard constituent parse trees
    PTREE = "ptree"         #: column type for automatically predicted constituent parse trees
    HEAD = "head"           #: column type for gold-standard head of the current token (dependency parse)
    PHEAD = "phead"         #: column type for automatically predicted head of the current token (dependency parse)
    DEPREL = "deprel"       #: column type for gold-standard dependency relation to the HEAD (dependency parse)
    PDEPREL = "pdeprel"     #: column type for automatically predicted dependency relation to the HEAD (dependency parse)
    FILLPRED = "fillpred"   #: column type for indicating if SRL (PRED) is/should be filled
    ROLESET = "roleset"     #: column type for predicate's roleset
    SRL = "srl"             #: column type for predicate (PRED in CoNLL-2009 format)
    IGNORE = "ignore"       #: column type for column that should be ignored

    #: A list of all the column types supported by the propbankbr conll corpus reader.
    COLUMN_TYPES = (ID, WORDS, LEMMA, PLEMMA, POS, PPOS, FEAT, PFEAT, CLAUSE, PCLAUSE, FCLAUSE, PFCLAUSE, TREE, PTREE,
                    HEAD, PHEAD, DEPREL, PDEPREL, FILLPRED, ROLESET, SRL, IGNORE)


    def lemmatized_sents(self, fileids=None):
        self._require(self.WORDS, self.LEMMA)
        def get_lemmatized_words(grid):
            return self._get_lemmatized_words(grid)
        return LazyMap(get_lemmatized_words, self._grids(fileids))

    def morph_analized_sents(self, fileids=None):
        self._require(self.WORDS, self.FEAT)
        def get_morph_analized_words(grid):
            return self._get_morph_analized_words(grid)
        return LazyMap(get_morph_analized_words, self._grids(fileids))

    def lexicalinfo_sents(self,fileids=None, simplify_tags=False):
        self._require(self.ID, self.WORDS, self.LEMMA, self.POS, self.FEAT)
        def get_lexicalinfo_words(grid):
            return self._get_lexicalinfo_words(grid, simplify_tags)
        return LazyMap(get_lexicalinfo_words, self._grids(fileids))

    def dep_parsed_sents(self, gold=True, all_info=True,fileids=None, simplify_tags=False):
        if gold:
            self._require(self.WORDS, self.POS, self.HEAD, self.DEPREL)
        else:
            self._require(self.WORDS, self.POS, self.PHEAD, self.PDEPREL)
        if all_info:
            self._require(self.LEMMA, self.FEAT)
        def get_dep_parsed_sent(grid):
            return self._get_dep_parsed_sent(grid, gold, all_info, simplify_tags)
        return LazyMap(get_dep_parsed_sent, self._grids(fileids))

    def dep_srl_instances(self, fileids=None, flatten = True):
        self._require(self.WORDS, self.POS, self.HEAD, self.DEPREL, self.FILLPRED, self.SRL)
        def get_dep_srl_instances(grid):
                return self._get_dep_srl_instances(grid)
        result = LazyMap(get_dep_srl_instances, self._grids(fileids))
        if flatten: result = LazyConcatenation(result)
        return result

    def dep_srl_spans(self, fileids=None):
        self._require(self.SRL, self.FILLPRED)
        return LazyMap(self._get_dep_srl_spans, self._grids(fileids))


    def _get_lemmatized_words(self, grid):
        lemmas = self._get_column(grid, self._colmap['lemma'])
        return zip(self._get_column(grid, self._colmap['words']), lemmas)

    def _get_morph_analized_words(self, grid):
        morph = self._get_column(grid, self._colmap['feat'])
        return zip(self._get_column(grid, self._colmap['words']), morph)

    def _get_lexicalinfo_words(self, grid, simplify_tags):
        pos_tags = self._get_column(grid, self._colmap['pos'])
        if simplify_tags:
            pos_tags = [self._tag_mapping_function(t) for t in pos_tags]
        return zip(self._get_column(grid, self._colmap['id']),
                   self._get_column(grid, self._colmap['words']),
                   self._get_column(grid, self._colmap['lemma']),
                   pos_tags,
                   self._get_column(grid, self._colmap['feat']))

    def _get_dep_parsed_sent(self, grid, gold=True, lexinfo=True, simplify_tags=False):
        words = self._get_column(grid, self._colmap['words'])
        pos_tags = self._get_column(grid, self._colmap['pos'])
        if simplify_tags:
            pos_tags = [self._tag_mapping_function(t) for t in pos_tags]
        if gold:
            heads = self._get_column(grid, self._colmap['head'])
            deprels = self._get_column(grid, self._colmap['deprel'])
        else:
            heads = self._get_column(grid, self._colmap['phead'])
            deprels = self._get_column(grid, self._colmap['pdeprel'])
        dep_tree_str= ""
        for word, pos_tag, head, deprel in zip (words, pos_tags, heads, deprels):
            dep_tree_str += "%s %s %s %s %s %s %s %s %s %s\n" % ("", word, "", "", pos_tag, "", head, deprel, "", "")
        dep_graph = DependencyGraph(dep_tree_str)

        if lexinfo:
            lexinfo = self._get_lexicalinfo_words(grid, simplify_tags)
            for node in dep_graph.nodelist:
                lex = lexinfo[node["address"]-1]
                node["lemma"] = lex[2]
                node["feat"] = lex[4]
        return dep_graph


    def _get_dep_srl_spans(self, grid):
        """
        List of the (arg_head, arg_id) tuples
        """
        predicates = self._get_column(grid, self._colmap['srl'])
        start_col = self._colmap['srl']+1

        num_preds = len([p for p in predicates if p != '-'])

        predicates_heads = self._get_column(grid, self._colmap['fillpred'])
        predicates_heads = [wordnum for wordnum, fill in enumerate(predicates_heads, start=1) if fill == "Y"]

        spanlists = [] # For all predicates in the sentence
        for i in range(num_preds):
            col = self._get_column(grid, start_col+i)
            spanlist = [] # For just one predicate
            for wordnum, srl_tag in enumerate(col,start=1):
                if srl_tag != "-":
                    spanlist.append((wordnum,srl_tag))
                if wordnum == predicates_heads[i]:
                    spanlist.append( (wordnum,"V") )
            spanlists.append(spanlist)

        return spanlists

    def _get_dep_srl_instances(self, grid):
        dep_graph = self._get_dep_parsed_sent(grid)
        spanlists = self._get_dep_srl_spans(grid)
        predicates = self._get_column(grid, self._colmap['srl'])
        rolesets = [None] * len(predicates)

        instances = ConllDepSRLInstanceList(dep_graph)

        for wordnum, predicate in enumerate(predicates, start=1):
            if predicate == "-": continue
            # Decide which spanlist to use
            for spanlist in spanlists:
                for (arg_head, arg_id) in spanlist:
                    if wordnum == arg_head and arg_id == "V":
                        break
                else: continue
                break
            else:
                raise ValueError('No srl column found for %r' % predicate)
            instances.append(ConllDepSRLInstance(dep_graph, wordnum, predicate, rolesets[wordnum-1], spanlist))
        return instances


class ConllSRLInstanceList(list):
    """
    Set of instances for a single sentence
    """
    def __init__(self, tree, instances=()):
        self.tree = tree
        list.__init__(self, instances)

    def __str__(self):
        return self.pprint()

    def pprint(self, include_tree=False):
        # Sanity check: trees should be the same
        for inst in self:
            if inst.tree != self.tree:
                raise ValueError('Tree mismatch!')

        words = self.tree.leaves()
        # If desired, add trees:
        if include_tree:
            pos = [None] * len(words)
            synt = ['*'] * len(words)
            self._tree2conll(self.tree, 0, words, pos, synt)

        s = ''
        for i in range(len(words)):
            # optional tree columns
            if include_tree:
                s += '%-20s ' % words[i]
                s += '%-8s ' % pos[i]
                s += '%15s*%-8s ' % tuple(synt[i].split('*'))

            # verb head column
            for inst in self:
                if i == inst.verb_head:
                    s += '%-20s ' % inst.verb_stem
                    break
            else:
                s += '%-20s ' % '-'
            # Remaining columns: self
            for inst in self:
                argstr = '*'
                for (start, end), argid in inst.tagged_spans:
                    if i==start: argstr = '(%s%s' % (argid, argstr)
                    if i==(end-1): argstr += ')'
                s += '%-12s ' % argstr
            s += '\n'
        return s

    def _tree2conll(self, tree, wordnum, words, pos, synt):
        assert isinstance(tree, Tree)
        if len(tree) == 1 and isinstance(tree[0], basestring):
            pos[wordnum] = tree.node
            assert words[wordnum] == tree[0]
            return wordnum+1
        elif len(tree) == 1 and isinstance(tree[0], tuple):
            assert len(tree[0]) == 2
            pos[wordnum], pos[wordnum] = tree[0]
            return wordnum+1
        else:
            synt[wordnum] = '(%s%s' % (tree.node, synt[wordnum])
            for child in tree:
                wordnum = self._tree2conll(child, wordnum, words,
                                                  pos, synt)
            synt[wordnum-1] += ')'
            return wordnum


class ConllDepSRLInstance (object):

    def __init__(self, dep_graph, verb_head, verb_stem, roleset, tagged_spans):
        self.verb_head = verb_head
        self.verb_stem = verb_stem
        self.roleset = roleset
        self.arguments = []
        self.tagged_spans = tagged_spans
        self.dep_graph = dep_graph
        for arg_head, arg_id in tagged_spans:
            if arg_id != "V":
                self.arguments.append( (arg_head, arg_id) )

    def __repr__(self):
        plural = len(self.arguments)!=1 and 's' or ''
        return '<ConllDepSRLInstance for %r with %d argument%s>' % ((self.verb_stem, len(self.arguments), plural))

    def pprint(self):
        raise NotImplementedError("This method hasn't been implement yet")


class ConllDepSRLInstanceList(list):

    def __init__(self, dep_graph, instances=()):
        self.dep_graph = dep_graph
        list.__init__(self, instances)

    def __str__(self):
        return self.pprint()

    def pprint(self, columns = ["srl"]):

        for col in columns:
            if not col in ["id","words","lemma", "pos", "feat", "head", "deprel", "fillpred", "srl"]:
                raise ValueError('This corpus does not contain a %s column.' % col)

        s = ""
        # Don't count the first node of the dep_graph which is not actually a word in the sentence
        for i in range(len(self.dep_graph.nodelist)-1):
            token_str = ""
            token_id = i+1
            node = self.dep_graph.nodelist[token_id]
            # ID column
            if "id" in columns: token_str += "{:<2} ".format(node["address"])
            # WORD column
            if "words" in columns: token_str += "{:<25} ".format(node["word"])
            # LEMMA column
            if "lemma" in columns:
                if node["lemma"] == "--" and node["word"] != "--":
                    token_str += "{:<25} ".format(node["word"])
                else:
                    token_str += "{:<25} ".format(node["lemma"])
            # POS column
            if "pos" in columns: token_str += "{:<10} ".format(node["tag"])
            # FEAT column
            if "feat" in columns:
                if  node["feat"] == "--":
                    token_str += "{:<15} ".format("-")
                else:
                    token_str += "{:<15} ".format(node["feat"].replace(" ", "|"))
            # HEAD column
            if "head" in columns: token_str += "{:<5} ".format(node["head"])
            # DEPREL column
            if "deprel" in columns: token_str += "{:<10} ".format(node["rel"])

            fillpred = predicate = "-"
            for ins in self:
                if token_id == ins.verb_head:
                    fillpred = "Y"
                    predicate = ins.verb_stem
                    break

            # FILLPRED column
            if "fillpred" in columns: token_str += "{:<5} ".format(fillpred)
            # SRL column (verb)
            token_str += "{:<20}".format(predicate)

            # SRL column (arguments)
            for ins in self:
                argstr = '-'
                for arghead, argid in ins.arguments:
                    if token_id == arghead:
                        argstr = "{:}".format(argid)
                        break
                token_str += "{:<12} ".format(argstr)
            s += token_str + "\n"

        return s
