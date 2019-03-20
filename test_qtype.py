import pandas as pd
from ipa.text import Text

from ipa.get_questiontype import get_questiontype


def test_questiontypes():
    path_to_train_data = "c:/users/sande/documents/taglayer/iwt_project/data" \
                         "/raw/questions_question_type.csv"
    df = pd.read_csv(path_to_train_data, engine="python", delimiter=';',
                     dtype=str)
    df.columns = ['question', 'question_type']

    correct = 0
    for question, question_type in zip(df["question"], df["question_type"]):
        question = Text(question, "en")
        question.preprocess()
        predicted_type = get_questiontype(question)

        if predicted_type == question_type:
            correct += 1
        else:
            print(question.raw, predicted_type, question_type)

    accuracy = correct / len(df["question"])

    print("Accuracy:", accuracy)
    assert accuracy > 0.99


test_questiontypes()
