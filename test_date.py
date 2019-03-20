"""
This script is for testing the functionality of the time module
"""
import os

import pandas as pd

from ipa.get_date import get_date


def test_date():
    path_to_train_data = os.path.join("..", "data/raw/questions_date.csv")
    df = pd.read_csv(path_to_train_data, sep=",", header=0, index_col=False,
                     encoding="utf-8")
    df.columns = ["question", "date", "index"]
    print(df.head())

    df[["predicted_date_string", "predicted_date", "predicted_index"]] = df[
        "question"].apply(
        lambda row: pd.Series(get_date(row)))

    correct = 0
    correct_total = 0
    total_dates = 0
    total_dates_predicted = 0
    for question, date, index, predicted_date, predicted_index in zip(
            df["question"], df["date"], df["index"],
            df["predicted_date"], df["predicted_index"]):
        # if date != "[]" and not predicted_date:
        if date != "[]":
            total_dates += 1
        # precision = actual no date, predict have date
        # if date == "[]" and len(predicted_date) > 0:
        #     total_date_predicted += 1
        if date == str(predicted_date):
            correct_total += 1
        if predicted_date:
            total_dates_predicted += 1
            if date == str(predicted_date):
                correct += 1
            else:
                print(question, date, predicted_date)
                print("---------------------------------")

    print("the number of total goal dates: ", correct_total)
    print("the number of correct date with goal dates are existed: ", correct)
    print("the number of total date: ", total_dates)
    print(
        "the number of wrong predicted date, no date actually but have date "
        "in prediction: ",
        total_dates_predicted)
    print("the total number of questions: ", len(df["question"]))
    accuracy = round(correct_total / len(df["question"]), 2)
    recall = round(correct / total_dates, 2)
    precision = round(correct / total_dates_predicted, 2)
    print("Recall:", recall)
    print("Precision:", precision)
    print('F1 score:', round(2 * precision * recall / (precision + recall), 2))

    print("Accuracy:", accuracy)
    assert accuracy > 0.95


if __name__ == "__main__":
    test_date()
