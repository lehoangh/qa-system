import pandas as pd
from nltk import word_tokenize

from resources.en.value_mapping import value_mapper

"""first part"""

# path_to_train_data = os.path.join("..", "data/raw/questions_NER.csv")
path_to_train_data = "c:/users/sande/documents/taglayer/iwt_project/data/raw" \
                     "/questions_NER.csv"

df = pd.read_csv(path_to_train_data, 'rb', engine="python", delimiter=';',
                 dtype=str)

dataset = []
sent = []

for index, row in df.iterrows():
    tuple = (row['word'], row['pos'], row['entity'])
    if tuple != ('nan', 'nan', 'nan'):
        sent.append(tuple)
    else:
        dataset.append(sent.copy())
        sent.clear()
TOTALsentences = []
TOTALpredictions = []

for lst in dataset:
    sentence = []
    sentenceprediction = []
    for tup in lst:
        sentenceprediction.append(tup[2])
        sentence.append(tup[0])
    sentence = ' '.join(sentence)
    TOTALpredictions.append(sentenceprediction)
    TOTALsentences.append(sentence)

"""second part"""

for sentenceprediction, sentence in zip(TOTALpredictions, TOTALsentences):
    targets = ['visitorId', 'pageviews', 'bounce', 'adblock', 'deviceTypes',
               'deviceBrands', 'browserTypes', 'osTypes',
               'returningByVisitors',
               'cfCountry', 'languages', 'visitTime', 'conversion',
               'referralType',
               'referralDomain', 'touch', 'pagesPerVisitor']
    output = {}
    for target in targets:
        output[target] = list()

    extra = ''
    num = 0
    for tok, label in zip(word_tokenize(sentence), sentenceprediction):
        num += 1

        if label != 'O':
            if label.startswith('B'):
                label = label.replace('B-', '')
                if label in targets:
                    extra = tok

                try:
                    if sentenceprediction[num].startswith('I'):
                        pass
                    else:
                        output[label].append(extra)

                except IndexError:
                    pass


            elif label.startswith('I'):
                label = label.replace('I-', '')
                extra += ' ' + tok
                output[label].append(extra)
                extra = ''
            else:
                output[label].append(extra)

    output2 = {}
    for key, val in output.items():
        if output[key] != []:
            output2[key] = val

    for target in output2:
        val = output2[target]

        if len(val) > 1:

            valuelist = []
            for string in val:
                valuelist.append(value_mapper(target, string))
            output2[target] = valuelist
        else:
            valuelist = []
            for value in val:
                valuelist.append(value_mapper(target, value))
                output2[target] = valuelist

    print(output2)
