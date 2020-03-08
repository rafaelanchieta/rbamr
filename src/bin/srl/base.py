# -*- coding: utf-8 -*-

'''
Created on Sep 25, 2012

@author: fernando
'''
import cPickle

# from corpus.reader.pbrconll import PropbankBrConllCorpusReader
from sklearn.cross_validation import StratifiedKFold, KFold
from sklearn.feature_extraction import DictVectorizer
from sklearn.grid_search import GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, f1_score
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC, LinearSVC

import src.bin.features.util as util
# from bin.features.dependency import feature_extractor_dep
from src.bin.features.analysis import FeatureSalienceCV, FeatureSelectionCV
# import bin.features.util as util
from src.bin.features.constituent import feature_extractor_const
# from bin.features.constituent import feature_extractor_const
from src.bin.features.dependency import feature_extractor_dep
# from bin.features.analysis import FeatureSalienceCV, FeatureSelectionCV
from src.corpus.reader.pbrconll import PropbankBrConllCorpusReader


class BaseLabeler(object):

    def __init__(self, path_train="", fileid_train_labeled="", fileid_train_unlabeled="",
                 train_instances_labeled=None, train_instances_unlabeled=None,
                 fileid_train_labeled_dep="", fileid_train_unlabeled_dep="",
                 filter_func=None, special_label="", featselec_featorder=[], feature_list=[],
                 path_test="", fileid_test="", model=None, target_verbs=[],
                 discard_labels=[], train_method="supervised", verbose_fileid=None):

        self.filter_func = filter_func
        self.feature_list = feature_list
        self.path_test = path_test
        self.fileid_test = fileid_test
        self.model = model
        self.target_verbs = target_verbs
        self.discard_labels = discard_labels
        self.prop_num_per_verb = None
        self.verbose_fileid = verbose_fileid

        self.train_feats, self.train_labels, self.train_props = self._load_instances(path_train, fileid_train_labeled, train_instances_labeled, filter_func,
                                                                   special_label, False, fileid_train_labeled_dep, self.prop_num_per_verb)

        if train_method == "self-training":
            unlabeled_instances = self._load_instances(path_train, fileid_train_unlabeled, train_instances_unlabeled, filter_func,
                                                                 special_label, True, fileid_train_unlabeled_dep,
                                                                 self.prop_num_per_verb)
            # Extract features
            self.train_unlabeled_props = []
            self.train_unlabeled_feats = []
            self.train_unlabeled_labels = []
            for argcand in unlabeled_instances:
                argcand_feats, argcand_prop = self.extract_features(argcand)
                self.train_unlabeled_feats.append(argcand_feats)
                self.train_unlabeled_props.append(argcand_prop)

                argcand_label = argcand["info"]["label"]
                if argcand_label == "NULL":
                    self.train_unlabeled_labels.append("NULL")
                elif special_label != "":
                    self.train_unlabeled_labels.append(special_label)
                else:
                    self.train_unlabeled_labels.append(argcand_label)

        self.featselec_featorder = featselec_featorder
        self.train_method = train_method

    def set_params(self, path_test="", fileid_test="", fileid_test_dep="", prop_num_per_verb=None):
        self.path_test = path_test
        self.fileid_test = fileid_test
        self.fileid_test_dep = fileid_test_dep

        try:
            if self.prop_num_per_verb is None or prop_num_per_verb is not None:
                self.prop_num_per_verb = prop_num_per_verb

        except AttributeError:
            self.prop_num_per_verb = prop_num_per_verb

        return

    def _load_instances(self, path, fileid, instances=None, filter_func=None, special_label = "", test=False, fileid_dep="", prop_num_per_verb=None):

        if instances is None:
            column_types = ["id", "words", "lemma", "pos", "feat", "clause", "fclause","tree","srl"]
            reader = PropbankBrConllCorpusReader(path, fileid, column_types, None , "S", False, True, "utf-8")

            column_types_dep = ["id", "words", "lemma", "pos", "feat", "head", "deprel","fillpred","srl"]
            reader_dep = PropbankBrConllCorpusReader(path, fileid_dep, column_types_dep, None , "FCL", False , False, "utf-8")
            # Get the argument candidates
            argcands, self.prop_num_per_verb = self._read_instances(reader, filter_func, reader_dep, prop_num_per_verb)
        else:
            argcands = instances

        if test:
            return argcands

        # Extract the necessary features from the argument candidates
        train_argcands_props = []
        train_argcands_feats = []
        train_argcands_target = []

        for argcand in argcands:
            argcand_label = argcand["info"]["label"]
            if (argcand_label in self.discard_labels) or ("C-" in argcand_label):
                continue

            arg_feats, arg_prop = self.extract_features(argcand)
            train_argcands_feats.append(arg_feats)
            train_argcands_props.append(arg_prop)

            if argcand_label == "NULL":
                train_argcands_target.append("NULL")
            elif special_label != "":
                train_argcands_target.append(special_label)
            else:
                train_argcands_target.append(argcand_label)

        # Create an encoder for the features
        self.feature_encoder = DictVectorizer()
        self.feature_encoder.fit(train_argcands_feats)

        # Create and encoder for the target labels
        self.label_encoder = LabelEncoder()
        self.label_encoder.fit(train_argcands_target)

        return train_argcands_feats, train_argcands_target, train_argcands_props

    def _read_instances(self, reader, filter_func=None, reader_dep=None, prop_num_per_verb=None):
        arg_cands = []
        if reader_dep is None:
            info_sent = zip(reader.lexicalinfo_sents(), reader.srl_instances(None, None, False), None)
        else:
            info_sent = zip(reader.lexicalinfo_sents(), reader.srl_instances(None, None, False), reader_dep.dep_parsed_sents())

        if prop_num_per_verb is None:
            prop_num_per_verb = dict()

        for lexinfo_sent, sent_ins, sent_ins_depgraph in info_sent:
            # Get the parse tree of the sentence
            tree = sent_ins.tree
            for ins in sent_ins:
                # Check if the instance belongs to one of the target verbs
                if (ins.verb_stem in self.target_verbs) or (self.target_verbs == []):
                    if ins.verb_stem in prop_num_per_verb:
                        prop_num_per_verb[ins.verb_stem] +=1
                    else:
                        prop_num_per_verb[ins.verb_stem] = 1
                    verb_prop_num = prop_num_per_verb[ins.verb_stem]
                    if filter_func is None:
                        # Get the gold arguments
                        for arg in ins.arguments:
                            arg_cands.append( {"ins":ins, "verb_prop_num":verb_prop_num,"info_sent":lexinfo_sent,
                                               "info":self._format_argcand(arg,lexinfo_sent,tree), "depgraph":sent_ins_depgraph} )
                    else:
                        # Prune the constituents of the sentence to get the argument candidates
                        pruned_argcands = filter_func(tree, tree.leaf_treeposition(ins.verb_head))
                        # Format each argument candidate
                        for argcand_treepos in pruned_argcands:
                            argcand_span = util.treepos_to_tuple(tree,argcand_treepos)
                            # Get the label of the argument candidate
                            for arg in ins.arguments:
                                if argcand_span == arg[0]:
                                    argcand_label = arg[-1]
                                    break
                            else:
                                argcand_label = "NULL"

                            arg_cands.append({"ins":ins, "verb_prop_num":verb_prop_num, "info_sent":lexinfo_sent,"depgraph":sent_ins_depgraph,
                                              "info":self._format_argcand((argcand_span,argcand_label), lexinfo_sent, tree, argcand_treepos)})

        return arg_cands, prop_num_per_verb

    def extract_features(self, argcand):
        feats_dep = feature_extractor_dep(argcand, self.feature_list)
        feats_const = feature_extractor_const(argcand, self.feature_list, argcand["depgraph"])
        feats_const.update(feats_dep)
        return feats_const, argcand["verb_prop_num"]

    def fit_mix(self, model_name="LogisticRegression"):
        if self.model==None:
            if model_name == "LinearSVC":
                model = LinearSVC(C=1, loss="l2")
            elif model_name == "SVC":
                model = SVC(kernel="poly")
            elif model_name == "LogisticRegression":
                model = LogisticRegression(C=8, penalty="l1")
            else:
                raise ValueError("Invalid model name.")

        if self.train_method == "supervised":
            self.model = model
            self.model.fit(self.feature_encoder.transform(self.train_feats), self.label_encoder.transform(self.train_labels))

        return self.model

    def _join_test_discarded(self, test, discarded, test_order, discarded_order):
        joined = test
        for arg, order in zip(discarded, discarded_order):
            joined.insert(order, arg)
        return joined

    def predict_mix(self, test_instances=[], filter_first = False):
        if test_instances == []:
            if (self.fileid_test <> None):
                # Get the instances from the test set
                test_instances = self._load_instances(path=self.path_test, fileid=self.fileid_test, filter_func=self.filter_func, test=True,
                                                  fileid_dep = self.fileid_test_dep, prop_num_per_verb = self.prop_num_per_verb)
            else:
                return []

        # We got the instances right from the output of the identification system
        # Therefore, we need to filter out first those that are not argument candidates
        if filter_first:
            test_argcands = []
            test_argcands_order = []
            discarded_argcands = []
            discarded_argcands_order = []
            discarded_argcands_labels = []
            order = 0
            for argcand,label in test_instances:
                if label != "NULL":
                    test_argcands.append(argcand)
                    test_argcands_order.append(order)
                else:
                    discarded_argcands.append(argcand)
                    discarded_argcands_order.append(order)
                    discarded_argcands_labels.append("NULL")
                order +=1
        else:
            test_argcands = test_instances

        # Extract features
        test_argcands_feats = []
        for argcand in test_argcands:
            argcands_feats,_ = self.extract_features(argcand)
            test_argcands_feats.append(argcands_feats)


        # Transform the features to the format required by the classifier
        test_argcands_feats = self.feature_encoder.transform(test_argcands_feats)

        # Classify the candidate arguments
        test_argcands_targets = self.model.predict(test_argcands_feats)

        # Get the correct label names
        test_argcands_labels = self.label_encoder.inverse_transform(test_argcands_targets)

        if filter_first:
            test_argcands = self._join_test_discarded(test_argcands, discarded_argcands, test_argcands_order, discarded_argcands_order)
            test_argcands_labels = self._join_test_discarded(test_argcands_labels.tolist(), discarded_argcands_labels, test_argcands_order, discarded_argcands_order)

        return zip(test_argcands, test_argcands_labels)

    def set_model_parameters(self, model_name, verbose=3, file_path=""):
        if not self.model is None:
            model_name = self.model.__class__.__name__

        if model_name == "LinearSVC":
            model_to_set = LinearSVC()
            parameters = {"C":[1,2,4,8], "loss":["l1","l2"]}
        elif model_name == "SVC":
            model_to_set = OneVsRestClassifier(SVC(kernel="poly"))
            parameters = {"estimator__C":[1,2,4,8], "estimator__kernel":["poly","rbf"],"estimator__degree":[1,2,3,4]}
        elif model_name == "LogisticRegression":
            model_to_set = LogisticRegression()
            parameters = {"penalty":["l1","l2"], "C":[1,2,4,8]}
        else:
            raise ValueError("Invalid model name.")

        # Perform Grid Search with 10-fold cross-validation to estimate the parameters
        # cv_generator = StratifiedKFold(self.label_encoder.transform(self.train_labels), n_folds=7)
        cv_generator = KFold(len(self.train_labels), n_folds=10, shuffle=True)
        model_tunning = GridSearchCV(model_to_set, param_grid=parameters, scoring=f1_score, n_jobs=1,
                                     cv=cv_generator, verbose=verbose)

        # Perform parameter setting
        model_tunning.fit(self.train_feats, self.label_encoder.transform(self.train_labels))

        if verbose > 0:
            print "Best model:"
            print model_tunning.best_estimator_
            print "Best parameters:"
            print model_tunning.best_params_
            print "Best score {}:".format(model_tunning.get_params()["score_func"])
            print model_tunning.best_score_

        if file_path != "":
            file_name = file_path + model_name + "AI_Semi.bin"
            if verbose > 0:
                print "Saving best model {}...".format(file_name)
            tunned_model_file = open(file_name,"wb")
            cPickle.dump(model_tunning.best_estimator_, tunned_model_file)
            tunned_model_file.close()

        self.model = model_tunning.best_estimator_

        return self.model

    def analyse_feature_salience(self, model_name="LogisticRegression", forward=True, verbose=0):
        if self.model==None:
            if model_name == "LinearSVC":
                model = LinearSVC(C=1, loss="l2")
            elif model_name == "SVC":
                model = SVC(kernel="poly")
            elif model_name == "LogisticRegression":
                model = LogisticRegression(C=8, penalty="l1")
            else:
                raise ValueError("Invalid model name.")
        else:
            model = self.model

        # cv_generator = KFold(len(self.train_labels), n_folds=10, shuffle=True)
        cv_generator = StratifiedKFold(self.label_encoder.transform(self.train_labels), n_folds=7)
        fscv = FeatureSalienceCV(model, cv = cv_generator, forward=forward, score_func=[precision_score, recall_score, f1_score],
                                 sort_by = "f1_score", verbose=verbose)

        fscv.fit_mix(self.train_feats, self.label_encoder.transform(self.train_labels))

        return fscv

    def analyse_feature_selection(self, model_name="LogisticRegression", forward=True, verbose=0):
        if self.model==None:
            if model_name == "LinearSVC":
                model = LinearSVC(C=1, loss="l2")
            elif model_name == "SVC":
                model = SVC(kernel="poly")
            elif model_name == "LogisticRegression":
                model = LogisticRegression(C=8, penalty="l1")
            else:
                raise ValueError("Invalid model name.")
        else:
            model = self.model

        # cv_generator = KFold(len(self.train_labels), n_folds=10, shuffle=True)
        cv_generator = StratifiedKFold(self.label_encoder.transform(self.train_labels), n_folds=7)
        fscv = FeatureSelectionCV(model, cv = cv_generator, feature_order=self.featselec_featorder, score_func=f1_score, verbose=verbose)

        fscv.fit_mix(self.train_feats, self.label_encoder.transform(self.train_labels))

        return fscv

    def _format_argcand(self, argcand_tuple, lexinfo_sent, tree, argcand_treepos=None):

        start_arg, end_arg = argcand_tuple[0]

        if argcand_treepos == None:
            argcand_treepos = tree.treeposition_spanning_leaves(start_arg,end_arg)

        argcand = dict()
        argcand["treepos"] = argcand_treepos
        argcand["span"] = argcand_tuple[0]
        argcand["label"] = argcand_tuple[-1]
        argcand["cat"] = util.get_postag(tree[argcand_treepos])
        argcand["lexinfo"] = dict()

        for i in range(start_arg, end_arg):
            id_token,word,lemma,pos,feat = lexinfo_sent[i]
            argcand["lexinfo"][id_token] = {"word":word,"lemma":lemma,"pos":pos,"feat":feat}

        return argcand
