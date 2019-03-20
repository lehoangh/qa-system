import pickle
import random

import numpy as np
import pandas as pd
import sklearn_crfsuite
import spacy
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn_crfsuite import metrics

from resources.en.gazetteers import gazetteers
from resources.en.value_mapping import value_mapper

nlp = spacy.load('en')


def word2features(train, num):  # tokens as tuple, wordnumber

    word = train[num][0]
    postag = train[num][1]
    lemma = train[num][2]

    features = [
        'bias=' + str(1.0),
        'position=' + str(num),  # custom
        'word.lower=' + word.lower(),
        'lemma=' + lemma.lower(),
        'word[-3:]=' + word[-3:],
        'word[-2:]=' + word[-2:],
        'word[:2]=' + word[:2],  # custom
        'word[:3]=' + word[:3],  # custom
        'word_length=' + str(len(word)),  # custom
        'word.isupper=%s' % word.isupper(),
        'word.istitle=%s' % word.istitle(),
        'word.isdigit=%s' % word.isdigit(),
        'postag=' + postag,
        'postag[:2]=' + postag[:2],
        'word.deviceTypes=%s' % str(
            word.lower() in gazetteers['gaz_deviceTypes']),
        'word.referralDomain=%s' % str(
            word.lower() in gazetteers['gaz_referralDomain']),
        'word.cfCountry=%s' % str(word.lower() in gazetteers['gaz_cfCountry']),
        'word.browserTypes=%s' % str(
            word.lower() in gazetteers['gaz_browserTypes']),
        'word.languages=%s' % str(word.lower() in gazetteers['gaz_languages']),
        'word.deviceBrands=%s' % str(
            word.lower() in gazetteers['gaz_deviceBrands']),
        'word.osTypes=%s' % str(word.lower() in gazetteers['gaz_osTypes']),
        'word.referralType=%s' % str(
            word.lower() in gazetteers['gaz_referralType']),
        'word.touch=%s' % str(word.lower() in gazetteers['gaz_touch']),
        'word.adblock=%s' % str(word.lower() in gazetteers['gaz_adblock']),
        'word.visitorId=%s' % str(word.lower() in gazetteers['gaz_visitorId']),
        'word.visitTime=%s' % str(word.lower() in gazetteers['gaz_visitTime']),
        'word.pagesPerVisitore=%s' % str(
            word.lower() in gazetteers['gaz_pagesPerVisitor']),
        'word.bounce=%s' % str(word.lower() in gazetteers['gaz_bounce']),

    ]

    if num > 0:
        word1 = train[num - 1][0]
        # postag1 = train[num-1][1]
        features.extend([
            '-1:word.lower=' + word1.lower(),
            '-1:word.istitle=%s' % word1.istitle(),
            '-1:word.isupper=%s' % word1.isupper(),
            # '-1:postag=' + postag1,
            # '-1:postag[:2]=' + postag1[:2],
            '-1:word[-3:]=' + word1[-3:],
            '-1:word[-2:]=' + word1[-2:],
            '-1:word[:2]=' + word1[:2],  # custom
            '-1:word[:3]=' + word1[:3],  # custom
            '-1:word_length=' + str(len(word1)),  # custom
        ])
    else:
        features.insert(0, 'First Word')

    if num > 1:
        word2 = train[num - 2][0]
        # postag2 = train[num-2][1]
        features.extend([
            '-2:word.lower=' + word2.lower(),
            '-2:word.istitle=%s' % word2.istitle(),
            '-2:word.isupper=%s' % word2.isupper(),
            # '-2:postag=' + postag2,
            # '-2:postag[:2]=' + postag2[:2],
            '-2:word[-3:]=' + word2[-3:],
            '-2:word[-2:]=' + word2[-2:],
            '-2:word[:2]=' + word2[:2],  # custom
            '-2:word[:3]=' + word2[:3],  # custom
            '-2:word_length=' + str(len(word2)),  # custom
        ])

    if num > 3:
        firstword = train[0][0]
        # firstpos = train[0][1]
        secword = train[1][0]
        # secpos = train[1][1]
        features.extend([
            'firstword=' + firstword,
            # 'first_pos=' + firstpos,
            'secword=' + secword,
            # 'sec_pos=' + secpos
        ])

    if num < len(train) - 1:
        word1 = train[num + 1][0]
        # postag1 = train[num+1][1]
        features.extend([
            '+1:word.lower=' + word1.lower(),
            '+1:word.istitle=%s' % word1.istitle(),
            '+1:word.isupper=%s' % word1.isupper(),
            # '+1:postag=' + postag1,
            # '+1:postag[:2]=' + postag1[:2],
            '+1:word[-3:]=' + word1[-3:],
            '+1:word[-2:]=' + word1[-2:],
            '+1:word[:2]=' + word1[:2],  # custom
            '+1:word[:3]=' + word1[:3],  # custom
            '+1:word_length=' + str(len(word1)),  # custom
        ])
    else:
        features.append('Last Word')

    if num < len(train) - 2:
        word1 = train[num + 2][0]
        # postag1 = train[num+2][1]
        features.extend([
            '+2:word.lower=' + word1.lower(),
            '+2:word.istitle=%s' % word1.istitle(),
            '+2:word.isupper=%s' % word1.isupper(),
            # '+2:postag=' + postag1,
            # '+2:postag[:2]=' + postag1[:2],
            '+2:word[-3:]=' + word1[-3:],
            '+2:word[-2:]=' + word1[-2:],
            '+2:word[:2]=' + word1[:2],  # custom
            '+2:word[:3]=' + word1[:3],  # custom
            '+2:word_length=' + str(len(word1)),  # custom
        ])
    else:
        features.append('Last Word')

    return features


def train2features(train):
    return [word2features(train, num) for num in range(len(train))]


def train2labels(train):
    return [train_tuple[-1] for train_tuple in train]


def train2tokens(train):
    return [train_tuple[0] for train_tuple in train]


def map_labels_to_dictionary(question, prediction):
    output = {}
    targets = ['visitorId', 'pageviews', 'bounce', 'adBlock', 'deviceTypes',
               'deviceBrands', 'browserTypes', 'osTypes',
               'returningByVisitors',
               'cfCountry', 'languages', 'visitTime', 'conversion',
               'referralType',
               'referralDomain', 'touch', 'pagesPerVisitor']

    for target in targets:
        output[target] = list()
    extra = ''
    for num, (tok, label) in enumerate(zip(question.tokens, prediction)):
        if label != 'O':
            if label.startswith('B'):
                label = label[2:]
                if label in targets:
                    extra = tok
                try:
                    if prediction[num + 1].startswith('I'):
                        pass
                    else:
                        output[label].append(extra)
                except IndexError:
                    output[label].append(extra)

            elif label.startswith('I'):
                label = label[2:]
                extra += ' ' + tok
                output[label].append(extra)
                extra = ''
            else:
                output[label].append(extra)

    return output


def map_ne_db_strings(output):
    output2 = {}
    output3 = {}
    for key, val in output.items():
        if output[key] != []:
            output2[key] = val

    # print("before value mapping: ", output2)

    for target in output2:
        val = output2[target]

        if len(val) > 1:

            valuelist = []
            for string in val:
                valuelist.append(value_mapper(target, string))
            output3[target] = set_same_order(valuelist)
        else:
            valuelist = []
            for value in val:
                if value.lower() == 'iphone':
                    output3['deviceBrands'] = ["Apple"]
                    output3['deviceTypes'] = ["mobile"]

                elif value.lower() == 'macbook':
                    output3['deviceBrands'] = ["Apple"]
                    output3['deviceTypes'] = ["pc"]

                else:
                    valuelist.append(value_mapper(target, value))
                    output3[target] = valuelist

    for target in output3:
        if len(output3[target]) > 1 and "unspecified" in output3[target]:
            output3[target].remove("unspecified")

    if "referralType" in output3 and output3["referralType"] == [
        "unspecified"]:
        if "referralDomain" in output3 and output3["referralDomain"] == [
            "unspecified"]:

            del output3["referralType"]

    elif "referralType" in output3 and output3["referralType"] not in [
        ["unspecified"], ["unrecognized"]]:
        # only add new referralDomain when no other unspecified values,
        # except visitorId
        if all(v != ["unspecified"] for k, v in output3.items() if
               k != "visitorId"):
            output3.update({"referralDomain": ["unspecified"]})

    if "deviceTypes" in output3 and output3["deviceTypes"] == ["unspecified"]:
        if "deviceBrands" in output3 and output3["deviceBrands"] == [
            "unspecified"]:

            del output3["deviceTypes"]

    return output2, output3


def set_same_order(valuelist):
    seen = set()
    seen_add = seen.add
    return [x for x in valuelist if not (x in seen or seen_add(x))]


def postprocess_ne_predictions(question, prediction):
    output1 = map_labels_to_dictionary(question, prediction)
    entities_default_value, output2 = map_ne_db_strings(output1)
    return entities_default_value, output2


def identify_named_entities(question, model_path):
    model_path = model_path

    # print('loading model....')
    loaded_model = pickle.load(open(model_path, 'rb'))

    tuples = [list(zip(question.tokens, question.tags, question.lemmas))]

    # print('featurizing...')
    features = [train2features(i) for i in tuples]

    # print('doing predictions....')
    prediction = loaded_model.predict(features)
    entities_default_value, output = postprocess_ne_predictions(question,
                                                                prediction[0])

    return entities_default_value, output


def evaluate_saved_model(path_to_model):
    dataset = get_annotation_tuples(
        "c:/users/sande/documents/taglayer/iwt_project/data/raw"
        "/questions_NER.csv")
    _, test = train_test_split(dataset, test_size=0.2, random_state=78)

    print('featurizing test set....')
    X_test = [train2features(s) for s in test]
    y_test = [train2labels(s) for s in test]

    print('loading model....')
    loaded_model = pickle.load(open(path_to_model, 'rb'))
    y_pred = loaded_model.predict(X_test)

    labels = list(loaded_model.classes_)
    labels.remove('O')
    sorted_labels = sorted(labels, key=lambda name: (name[1:], name[0]))

    print(metrics.flat_classification_report(
        y_test, y_pred, labels=sorted_labels, digits=3
    ))


def get_annotation_tuples(path_to_train_data):
    # print(path_to_train_data)

    df = pd.read_csv(path_to_train_data, 'rb', engine="python", delimiter=';',
                     dtype=str)

    dataset = []
    sent = []

    for index, row in df.iterrows():

        doc = nlp(row['word'])
        lemma = doc[0].lemma_

        tuple = (row['word'], row['pos'], lemma, row['entity'])
        if tuple != ('nan', 'nan', 'nan', 'nan'):
            sent.append(tuple)
        else:
            dataset.append(sent.copy())
            sent.clear()

    return dataset


def train_and_test(path_to_train_data, model_path):
    dataset = get_annotation_tuples(path_to_train_data)
    train, test = train_test_split(dataset, test_size=0.2, random_state=8)

    print('featurizing train set....')
    X_train = [train2features(s) for s in train]
    y_train = [train2labels(s) for s in train]

    print('featurizing test set....')
    X_test = [train2features(s) for s in test]
    y_test = [train2labels(s) for s in test]

    #  print('training model....')
    crf = sklearn_crfsuite.CRF(
        algorithm='lbfgs',
        c1=0.05,
        c2=0.001,
        max_iterations=100,
        all_possible_transitions=True
    )
    crf.fit(X_train, y_train)

    # print('dumping.....')
    pickle.dump(crf, open(model_path, 'wb'))
    y_pred = crf.predict(X_test)

    labels = list(crf.classes_)
    labels.remove('O')
    sorted_labels = sorted(labels, key=lambda name: (name[1:], name[0]))

    print(metrics.flat_classification_report(
        y_test, y_pred, labels=sorted_labels, digits=2
    ))


def sklearn_crossval():
    dataset = get_annotation_tuples(
        "c:/users/sande/documents/taglayer/iwt_project/data/raw"
        "/questions_NER.csv")

    random.seed(5)
    random.shuffle(dataset)

    crf = sklearn_crfsuite.CRF(
        algorithm='lbfgs',
        c1=0.05,
        c2=0.001,
        max_iterations=100,
        all_possible_transitions=True
    )

    print('\ndoing crossval...')

    questions = [train2tokens(question) for question in dataset]
    predictions = [train2labels(prediction) for prediction in dataset]

    scores = cross_val_score(crf, questions, predictions, cv=5)
    print("SKLEARN Crossval Score for shuffled data: ", np.mean(scores))


def train_and_cross_validate():
    dataset = get_annotation_tuples(
        "c:/users/sande/documents/taglayer/iwt_project/data/raw"
        "/questions_NER.csv")

    crf = sklearn_crfsuite.CRF(
        algorithm='lbfgs',
        c1=0.05,
        c2=0.001,
        max_iterations=100,
        all_possible_transitions=True
    )

    num_iterations = 5
    train_groups = [dataset[i::num_iterations] for i in range(num_iterations)]

    allsents = []
    allpreds = []
    alltrues = []

    for iteration in range(len(train_groups)):
        test_set = train_groups[iteration]
        train_set = []
        for group_index, group in enumerate(train_groups):
            if group_index != iteration:
                train_set += group
        # now we have a test test and train set for each iteration

        for tuple in test_set:

            sentence = str(' '.join(tup[0] for tup in tuple))
            allsents.append(sentence)

        print('featurizing..... ', iteration + 1)
        X_train = [train2features(s) for s in train_set]
        y_train = [train2labels(s) for s in train_set]

        X_test = [train2features(s) for s in test_set]
        y_test = [train2labels(s) for s in test_set]

        print('fitting....', iteration + 1)
        crf.fit(X_train, y_train)

        labels = list(crf.classes_)
        labels.remove('O')
        sorted_labels = sorted(labels, key=lambda name: (name[1:], name[0]))

        print('\npredicting on test questions....', iteration + 1)
        y_pred = crf.predict(X_test)
        for p in y_pred:
            allpreds.append(p)
        for t in y_test:
            alltrues.append(t)

        print(metrics.flat_classification_report(
            y_test, y_pred, labels=sorted_labels, digits=3
        ))

    print('Printing all errors in cross validation.....')
    count = 1
    for x, i, j in zip(allsents, alltrues, allpreds):
        if i != j:
            count += 1
            print(count, "       ", ''.join(tup[0] for tup in x))
            print("gold: ", i)
            print("pred: ", j, '\n')

    print(metrics.flat_classification_report(
        alltrues, allpreds, labels=sorted_labels, digits=3
    ))


if __name__ == "__main__":

    # print("Training a new model on random 80% of annotated sentences...")
    # train_and_test("c:/users/sande/documents/taglayer/iwt_project/data/raw
    # /questions_NER.csv",
    # "c:/users/sande/documents/taglayer/iwt_project/models/november_29.crfsuite")

    loaded_model = "c:/users/sande/documents/taglayer/iwt_project/models/november_29.crfsuite"

    print("Doing SKLEARN crossval ...")
    sklearn_crossval()

    print("Doing manual crossval with 5 folds...")
    train_and_cross_validate()
