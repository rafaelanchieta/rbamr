'''
Created on 26 Sep 2012

@author: feralvam
'''
from numpy import array
from sklearn.base import BaseEstimator
from sklearn.base import MetaEstimatorMixin
from sklearn.base import clone
from sklearn.base import is_classifier
from sklearn.cross_validation import check_cv
from sklearn.feature_extraction import DictVectorizer


class FeatureSalienceCV(BaseEstimator, MetaEstimatorMixin):
    '''
    classdocs
    '''

    def __init__(self, estimator, step=1, forward=True, cv=None, score_func=None, verbose=0, sort_by=None):
        self.estimator = estimator
        self.step = step
        self.forward = forward
        self.cv = cv
        self.score_func = score_func
        self.verbose = verbose
        self.sort_by = sort_by

    def fit_mix(self, X, y):
        """
        Used when the features in X are mixed: nominal and numerical
        """
        # Initialization
        feature_names = X[0].keys()
        cv = check_cv(self.cv, X, y, is_classifier(self.estimator))
        scores = {}

        if self.verbose > 0:
            title = "{:<4}\t{:<25}".format("Fold", "Feature")
            title += "\t{:<16}".format("Progress in fold")
            print title

        # Cross-validation
        n = 0

        for train, test in cv:
            # Score each feature
            for feat in feature_names:
                # Train the model using only the corresponding feature(s)
                selected_X = []

                for feat_set in X:
                    selected_feats = []
                    for name, value in feat_set.iteritems():
                        if name == feat and self.forward:
                            selected_feats.append([name, value])
                        elif name != feat and not self.forward:
                            selected_feats.append([name, value])

                    selected_X.append(dict(selected_feats))

                selected_X = array(selected_X)
                feat_encoder = DictVectorizer().fit(selected_X)

                estimator = clone(self.estimator)
                estimator.fit(feat_encoder.transform(selected_X[train]), y[train])

                if not feat in scores:
                    scores[feat] = {}

                if self.score_func is None:
                    if not "accuracy" in scores[feat]:
                        scores[feat]["accuracy"] = 0.0
                    scores[feat]["accuracy"] += estimator.score(feat_encoder.transform(selected_X[test]), y[test])
                else:
                    for score_func in self.score_func:
                        score_func_name = score_func.__name__
                        if not score_func_name in scores[feat]:
                            scores[feat][score_func_name] = 0.0
                        scores[feat][score_func_name] += score_func(y[test], estimator.predict(
                            feat_encoder.transform(selected_X[test])))

                if self.verbose > 0:
                    progress_line = "{:>4}\t{:<25}".format(n + 1, feat)
                    progress_line += "\t{:>13}/{}".format(feature_names.index(feat) + 1, len(feature_names))
                    print progress_line

            n += 1

        self.cv_scores_ = dict()
        for feat_name, feat_scores in scores.iteritems():
            if not feat_name in self.cv_scores_.keys():
                self.cv_scores_[feat_name] = dict()
            for score_name, score_value in feat_scores.iteritems():
                self.cv_scores_[feat_name][score_name] = score_value / n

        # Report the final results
        if self.verbose:
            # Sort the values of the score function in descending order
            if self.score_func is None:
                self.sort_by = "accuracy"

            scores_list = [(feat_name, feat_scores[self.sort_by]) for feat_name, feat_scores in
                           self.cv_scores_.iteritems()]
            scores_list.sort(key=lambda (k, v): v, reverse=True)

            print "\nFeature Salience in Descending Order of {} for {}:".format(self.sort_by.upper(),
                                                                                self.estimator.__class__.__name__)

            title = "{:<25}".format("Feature")

            if self.score_func is None:
                score_funcs = ["accuracy"]
            else:
                score_funcs = [score_func.__name__ for score_func in self.score_func]

            for score_func in score_funcs:
                title += "\t{:<15}".format(score_func)

            print title

            self.feat_order = []
            for feat_name, _ in scores_list:
                self.feat_order.append(feat_name)
                if self.forward:
                    feat_report_line = "Only\t{:<20}".format(feat_name)
                else:
                    feat_report_line = "All but\t{:<20}".format(feat_name)
                for score_func in score_funcs:
                    feat_report_line += "\t{:>15.1f}".format(self.cv_scores_[feat_name][score_func] * 100)

                print feat_report_line

            print self.feat_order
        return self


class FeatureSelectionCV(BaseEstimator, MetaEstimatorMixin):
    def __init__(self, estimator, step=1, cv=None, feature_order=None, score_func=None, verbose=0):
        self.estimator = estimator
        self.step = step
        self.cv = cv
        self.feature_order = feature_order
        self.score_func = score_func
        self.verbose = verbose

    def fit_mix(self, X, y):
        """
        Used when the features in X are mixed: nominal and numerical
        """
        # Initialization
        if self.feature_order == None:
            self.feature_order = X[0].keys()
        cv = check_cv(self.cv, X, y, is_classifier(self.estimator))
        scores = dict()

        if self.verbose > 0:
            title = "{:<4}\t{:<25}\t{:<5}\t{:<16}".format("Fold", "Adding Feature", "Score", "Progress in fold")
            print title

        # Cross-validation
        n = 0
        for train, test in cv:
            feats_to_analyse = []
            # Score adding each feature
            for feat in self.feature_order:
                # Train the model adding only the corresponding feature
                feats_to_analyse.append(feat)
                selected_X = []

                for feat_set in X:
                    selected_feats = [[name, value] for name, value in feat_set.iteritems() if name in feats_to_analyse]
                    selected_X.append(dict(selected_feats))

                selected_X = array(selected_X)
                feat_encoder = DictVectorizer().fit(selected_X)

                estimator = clone(self.estimator)
                estimator.fit(feat_encoder.transform(selected_X[train]), y[train])

                if not feat in scores:
                    scores[feat] = 0.0

                if self.score_func is None:
                    score_fold = estimator.score(feat_encoder.transform(selected_X[test]), y[test])
                else:
                    score_fold = self.score_func(y[test], estimator.predict(feat_encoder.transform(selected_X[test])))

                scores[feat] += score_fold
                if self.verbose > 0:
                    progress_line = "{:>4}\t{:<25}".format(n + 1, feat)
                    progress_line += "\t{:>5.1f}\t{:>13}/{}".format(score_fold * 100,
                                                                    self.feature_order.index(feat) + 1,
                                                                    len(self.feature_order))
                    print progress_line

            n += 1

        self.cv_scores_ = dict()
        for feat_name, feat_score in scores.iteritems():
            self.cv_scores_[feat_name] = feat_score / n

        # Report the final results
        if self.verbose > 0:
            print "\nFeature performance analysed by {} for {}:".format(self.score_func.__name__,
                                                                        self.estimator.__class__.__name__)

            print "{:<25}\t{:<15}".format("Feature", "Score")

            for feat_name in self.feature_order:
                print "+{:<20}\t{:>15.1f}".format(feat_name, self.cv_scores_[feat_name] * 100)

        return self


