from modules.preprocess import pos_tag, preprocess


class Text:

    def __init__(self, raw_string, language):
        self.raw = raw_string
        self.language = language
        self.pos = None
        self.tokens = None
        self.lemmas = None
        self.entities = None
        self.subtree = None
        self.noun_chunks = None
        self.np_with_adj = None
        self.tok_tup_lst = None

    def preprocess(self):
        self.tokens, self.tags, self.lemmas = pos_tag(self.raw)

    def preprocess_further(self):
        self.tokens, self.pos, self.lemmas, self.entities, self.subtree, \
        self.noun_chunks, self.np_with_adj, self.tok_tup_lst = preprocess(
            self.raw)


if __name__ == "__main__":
    text = Text("Whats the number of visitors?", "en")
    text.preprocess()
    print(text.tokens)
    print(text.tags)
