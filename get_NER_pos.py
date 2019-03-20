import pandas as pd
import spacy

en = spacy.load("en")

path_to_train_data = "c:/users/sande/documents/taglayer/iwt_project/data/raw" \
                     "/questions_raw_new.csv"
df = pd.read_csv(path_to_train_data, engine="python", delimiter=';', dtype=str)
df.columns = ['question']

questions = df['question']

all_tags = []
for question in questions:
    doc = en(question)
    tokens_per_question = [t.orth_ for t in doc]
    tags_per_question = [t.tag_ for t in doc]
    if tokens_per_question[:2] == ["What", "s"] and tags_per_question[:2] == [
        "WP", "VBZ"]:
        tokens_per_question = ["Whats"] + tokens_per_question[2:]
        tags_per_question = ["WP"] + tags_per_question[2:]

    for tok, tag in zip(tokens_per_question, tags_per_question):
        all_tags.append((tok, tag, 'O'))
    all_tags.append(('', '', 'O'))

print(all_tags)

df2 = pd.DataFrame(all_tags)
print(df2.head())
df2.to_csv(
    'c:/users/sande/documents/taglayer/iwt_project/data/raw'
    '/NER_train_questions_new.csv',
    index=0, sep=";", header=["word", "pos", "entity"])
