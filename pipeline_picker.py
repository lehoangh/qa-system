import os
import pickle

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline

df = pd.read_csv('../data/annotated/pipeline_picker_questions.csv',
                 delimiter=';', encoding='latin1')
df.columns = ['question', 'pipeline']
# print(df.head())

questions = df['question']
pipelines = df['pipeline']

train_questions, test_questions, train_pipelines, test_pipelines = \
    train_test_split(
    questions, pipelines, test_size=0.2, random_state=7)

"""get bags of words"""
count_vect = CountVectorizer()
# questions_bow = count_vect.fit_transform(questions)
# pipelines_bow = count_vect.fit_transform(pipelines)
# train_questions_counts = count_vect.fit_transform(train_questions)
# test_questions_counts = count_vect.transform(test_questions)

"""do tfidf transforming"""
tfidf_transformer = TfidfTransformer()
# questions_tfidf = tfidf_transformer.fit_transform(questions_bow)
# pipelines_tfidf = tfidf_transformer.fit_transform(pipelines_bow)
# train_questions_tfidf = tfidf_transformer.fit_transform(
# train_questions_counts)
# test_questions_tfidf = tfidf_transformer.transform(test_questions_counts)


"""train a classifier"""
SGD = SGDClassifier(loss='squared_hinge', penalty='l2', alpha=1e-3,
                    random_state=42, max_iter=5, tol=None)
KNN = KNeighborsClassifier(n_neighbors=3)

# clf = MultinomialNB().fit(train_questions_tfidf, train_pipelines)
# predicted_pipelines = clf.predict(test_questions_tfidf)


"""OR define a pipeline and apply it"""
ppp_sgd = Pipeline([
    ('vect', CountVectorizer()),
    ('tfidf', TfidfTransformer()),
    ('clf', SGD),
])

ppp_knn = Pipeline([
    ('vect', CountVectorizer()),
    ('tfidf', TfidfTransformer()),
    ('clf', KNN),
])

ppp_sgd.fit(train_questions, train_pipelines)
ppp_knn.fit(train_questions, train_pipelines)

"""predict and evaluate"""

predicted_pipelines_sgd = ppp_sgd.predict(test_questions)
# print("SGD testset accuracy =", np.mean(predicted_pipelines_sgd ==
# test_pipelines))

predicted_pipelines_knn = ppp_knn.predict(test_questions)
# print("KNN testset accuracy =", np.mean(predicted_pipelines_knn ==
# test_pipelines))

# print(metrics.classification_report(test_pipelines,
# predicted_pipelines_knn, target_names=["advice", "analytics"]))


"""grid search with cross val"""

# print(KNN.get_params().keys())

knn_parameters = {
    "n_neighbors": [2, 3, 4, 5], "weights": ['uniform', 'distance'],
    "algorithm": ['auto'], "leaf_size": [20, 25, 30, 33]
}
grid_search = GridSearchCV(KNeighborsClassifier(), knn_parameters, cv=5)

ppp_gs = Pipeline([
    ('vect', CountVectorizer()),
    ('tfidf', TfidfTransformer()),
    ('clf', grid_search),
])


# ppp_gs.fit(train_questions, train_pipelines)

# print('Best parameters for classifier=', grid_search.best_params_)
# print('Best score for GridSearch=', grid_search.best_score_)

# print('dumping.....')

# pickle.dump(ppp_knn, open(model_path, 'wb'))


def pipeline_picker(question):
    model_path = os.path.join("..", "models/pipe_model_december.sav")
    loaded_model = pickle.load(open(model_path, 'rb'))

    pipeline = loaded_model.predict([question])
    return pipeline
