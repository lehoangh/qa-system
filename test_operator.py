import ast
# from ipa.get_target_and_value import get_target_and_value
import json

import pandas as pd

from ipa.get_operator import find_operator, map_operator

"""DELETE THE FILES YOU DONT NEED IN THE DATA/ANNOTATED DIRECTORY"""


def convert():
    f = "c:/users/sande/documents/taglayer/iwt_project/data/raw" \
        "/questions_NER_operator.json"
    a = "c:/users/sande/documents/taglayer/iwt_project/data/raw" \
        "/questions_question_type.csv"
    with open(f) as i:
        records = json.load(i)

    for record in records:
        record["operator"] = ast.literal_eval(
            record["operator"].replace('“', '"').replace('”', '"'))

    with open(
            "c:/users/sande/documents/taglayer/iwt_project/data/raw"
            "/questions_NER_operator2.json",
            "w") as o:
        json.dump(records, o)


def test_operators():
    # path_to_train_data = "c:/users/sande/documents/taglayer/iwt_project
    # /data/raw/questions_NER_operator.tsv"
    # df = pd.read_csv(path_to_train_data, encoding = "utf-8", sep = '\t')
    # df.columns = ['index', 'question', 'operator', 'NERoutput']
    # pattern = 'second most|most|do least|the least|more than|or more|less
    # than|or less|at least'
    # ops = re.findall(pattern, question.lower())
    # print('counter:', get_target_and_value.counter)
    # "data/raw/questions_NER_operator.json"), orient='records'
    qtypes = pd.read_csv(
        "c:/users/sande/documents/taglayer/iwt_project/data/raw"
        "/questions_question_type.csv",
        encoding="latin1", engine="python", delimiter=';', dtype=str)
    qtypes.columns = ['question', 'qtype']
    qtype = qtypes['qtype']

    with(open(
            "c:/users/sande/documents/taglayer/iwt_project/data/raw"
            "/questions_NER_operator2.json",
            "rb")) as t:
        data = json.load(t)

    correct = 0
    correct_negative = 0
    empty_dicts = 0
    total_ops = 0
    total_ops_predicted = 0
    for qt, dicto in zip(qtype, data):
        question = dicto['question']
        NERoutput = dicto['NERoutput']

        for key in NERoutput:
            if NERoutput[key] == ["unspecified", "unspecified"]:
                NERoutput[key] = ["unspecified"]

        gold_operator_dict = dicto['operator']
        if len(gold_operator_dict) > 0:
            total_ops += 1

        found_operators = find_operator(question)

        if len(found_operators) > 1:
            print("Here are more operators in one sentence:", found_operators)

        if found_operators == [] and len(gold_operator_dict) == 0:
            correct_negative += 1

        if len(found_operators) == 1:
            total_ops_predicted += 1

            for found_operator in found_operators:
                predicted_operator_dict = map_operator(question,
                                                       found_operator,
                                                       NERoutput, qt)
                if not predicted_operator_dict:
                    print(predicted_operator_dict)
                    print(found_operator)
                    print(NERoutput)
                    print(qt)

                if predicted_operator_dict == gold_operator_dict:
                    correct += 1

                else:
                    print("INCORRECTLY FOUND: ", question, "PRED:",
                          predicted_operator_dict, "GOLD:", gold_operator_dict,
                          found_operator)

        if found_operators == [] and len(gold_operator_dict) > 0:
            print("DID NOT FIND:", gold_operator_dict, ", FOR: ", question,
                  NERoutput)

    recall = correct / total_ops
    precision = correct / total_ops_predicted

    print("Acc:", (correct + correct_negative) / len(data))

    print("Recall:", recall)
    print("Precision:", precision)
    print('F score:', 2 * precision * recall / (precision + recall))


test_operators()
