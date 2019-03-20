import spacy
from spacy.symbols import *

# en = spacy.load("en")
# en = spacy.load("en_core_web_lg")

en = spacy.load("en")


def pos_tag(text):
    doc = en(text)
    tokens = [t.orth_ for t in doc]
    tags = [t.tag_ for t in doc]
    lemmas = [t.lemma_ for t in doc]

    if tokens[:2] == ["What", "s"] and tags[:2] == ["WP", "VBZ"]:
        tokens = ["Whats"] + tokens[2:]
        tags = ["WP"] + tags[2:]
        lemmas = ["Whats"] + lemmas[2:]

    return tokens, tags, lemmas


def preprocess(text):
    doc = en(text)
    tokens = [t.orth_ for t in doc if not t.is_punct]
    pos = [t.tag_ for t in doc]
    lemmas = [t.lemma_ for t in doc]
    tok_tup_lst = list()

    entities = {}
    for entity in doc.ents:
        entity_type = entity.label_
        entity_text = entity.text
        if entity_type not in entities:
            entities[entity_type] = []
        entities[entity_type].append(entity_text)

    # sub tree (e.g. the second most popular of languages, browser types)
    subtree = [t.subtree for t in doc]

    # noun phrases: the adv/adj nouns (e.g. the most popular languages)
    np_with_adj = list()
    # np_labels = set([nsubj, nsubjpass, dobj, iobj, pobj])
    np_labels = {nsubj, nsubjpass, dobj, iobj, pobj}
    for word in doc:
        if word.dep in np_labels:
            np_with_adj = list(word.subtree)

    # noun chunks
    noun_chunks = doc.noun_chunks

    # (text, tag, pos) tuples of tokens
    for tok in doc:
        tok_tup_lst.append((tok.text, tok.lemma_, tok.tag_, tok.pos_))

    return (tokens, pos, lemmas, entities, subtree, noun_chunks, np_with_adj,
            tok_tup_lst)


preprocess('Who is Barack Obama?')
