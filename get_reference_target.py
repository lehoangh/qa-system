import spacy

from modules.text import Text


def step_through_tree(index, targets, doc):
    head_token = doc[index].head
    print("=>", head_token.orth_)
    if index == head_token.i:
        print("Arrived at top of sentence. No target found.")
        for tok in head_token.subtree:
            if tok.orth_ in targets:
                return tok.orth_
        return None
    elif head_token.orth_ in targets:
        return head_token.orth_
    else:
        return step_through_tree(head_token.i, targets, doc)


def find_idx_punct(lst_subtree):
    idx = len(lst_subtree)
    for item in lst_subtree:
        if item.dep_ == "punct":
            idx = item.i
    return idx


def find_subj(sentence_obj, dicto):
    cond_sp = {k: v for k, v in dicto.items() if k != "visitorId"}
    # print("sp: ", cond_sp)

    # nlp = spacy.load("en")
    # doc = nlp(sentence_obj)
    res = None
    for chunk in sentence_obj.noun_chunks:
        # print(chunk.text, chunk.root.text, chunk.root.dep_,
        #       chunk.root.head.text)
        if chunk.root.dep_ == "nsubj":
            res = [key for key, value in cond_sp.items() if value[0] in \
                   chunk.text]
        elif chunk.root.dep_ == "iobj" and not res:
            res = [key for key, value in cond_sp.items() if value[0] in \
                   chunk.text]
        elif chunk.root.dep_ == "dobj" and not res:
            res = [key for key, value in cond_sp.items() if value[0] in
                   chunk.text]

    return res


def get_reference_target(sentence, dicto):
    res = None

    if len(dicto) > 1:
        sentence_obj = Text(sentence, "en")
        sentence_obj.preprocess_further()
        # print(sentence_obj.raw)

        cond_sp = {k: v for k, v in dicto.items() if k != "visitorId"}
        # print("sp: ", cond_sp)
        if len(cond_sp) > 2:
            nlp = spacy.load("en")
            doc = nlp(sentence_obj.raw)
            root = [tok for tok in doc if tok.head == tok][0]
            # print("CHECK: ", root)
            try:
                subject = list(root.lefts)[0]
                # print("subject: ", subject.text, subject.text.strip(
                # ).count(" "),
                # subject.pos_, subject.tag_)
                if subject.tag_ == "WP":
                    subject = list(root.rights)[0]
            except IndexError:
                subject = list(root.rights)[0]

            # print("CHECK 1: ", subject)
            # try:
            #     print(list(root.lefts)[0])
            # except IndexError:
            #     pass
            ref_value = None

            idx = find_idx_punct(list(subject.subtree))

            for descendant in list(subject.subtree)[:idx]:
                # print("descendant: ", descendant)
                for sp, value in cond_sp.items():
                    # print(descendant.text, descendant.dep_, descendant.head,
                    # descendant.head.dep_)
                    if descendant.dep_ != "dobj" and descendant.head.dep_ \
                            not in [
                        "relcl", "ROOT"] and descendant.text in value[0]:
                        ref_value = descendant.text
                    elif not ref_value:
                        if descendant.dep_ == "dobj" and descendant.text in \
                                value[0]:
                            ref_value = descendant.text
                        elif descendant.head.dep_ == "pobj" and \
                                descendant.text in \
                                value[0]:
                            ref_value = descendant.text
                        elif not ref_value:
                            """finding the right subtree"""
                            subject_right = list(root.rights)[0]
                            idx = find_idx_punct(list(subject_right.subtree))
                            for descendant_r in list(subject_right.subtree)[
                                                :idx]:
                                # print("descendant_r: ", descendant_r)
                                # print(descendant_r.text, descendant_r.dep_,
                                #       descendant_r.head,
                                # descendant_r.head.dep_)
                                for sp, value in cond_sp.items():
                                    if descendant_r.dep_ != "dobj" and \
                                            descendant_r.head.dep_ not in [
                                        "relcl",
                                        "ROOT"] and descendant_r.text in \
                                            value[0]:
                                        ref_value = descendant_r.text
                                    elif not ref_value:
                                        if descendant_r.dep_ == "dobj" and \
                                                descendant_r.text in \
                                                value[0]:
                                            ref_value = descendant_r.text
                                        elif descendant_r.head.dep_ == \
                                                "pobj" and \
                                                descendant_r.text in \
                                                value[0]:
                                            ref_value = descendant_r.text

            # print("ref value: ", ref_value)
            if ref_value:
                for np in list(sentence_obj.noun_chunks):
                    # print("np: ", np)
                    if ref_value not in np.text.split(" ") and len(
                            np) > 1 and all(
                            word not in ["percent", "percentage", "perc"] for
                            word in
                            np.text.split(" ")) and not ref_value.isdigit():
                        try:
                            res = \
                                list(k for k, v in cond_sp.items() if
                                     ref_value not in v[0])[0]
                        except IndexError:
                            pass
            if not res:
                if not ref_value:
                    res = find_subj(sentence_obj, dicto)
                    if isinstance(res, list):
                        res = res[0]
                else:
                    res = \
                    list(k for k, v in cond_sp.items() if ref_value in v[0])[0]

            # for np in list(sentence_obj.noun_chunks):
            #     print("np: ", np)
            #     for sp, value in cond_sp.items():
            #         print("0: ", value[0])
            #         if any(word in value[0] for word in np.text.split(" ")):
            #
            #             print("find: ", {sp: value})
            #             if not flag:
            #                 res = sp
            #                 flag = True
            #
            # if not res:
            #     nlp = spacy.load("en")
            #     doc = nlp(sentence_obj.raw)
            #     for tok in doc:
            #         # print(tok.text, tok.dep_, tok.head)
            #         if tok.dep_ == "ROOT":
            #             root_idx = [t.orth_ for t in doc].index(tok.text)
            #             # print(root_idx)
            #             targets = [i[0] for i in cond_sp.values()]
            #             # print(targets)
            #             outp = step_through_tree(root_idx, targets, doc)
            #             print(outp)
            #             res = list(k for k, v in cond_sp.items() if v[0]
            # != outp)[0]

    return res


if __name__ == "__main__":
    dicto = {
        'visitorId': ['users'], 'deviceTypes': ['mobile'],
        'cfCountry': ['american']
    }
    question = "What percent of mobile users is american?"
    print(get_reference_target(question, dicto))
    print("_____________________")
    question = "What percent of american users use mobile?"
    print(get_reference_target(question, dicto))
    print("_____________________")
    question = "What is the percentage that american users use mobile?"
    print(get_reference_target(question, dicto))
    print("_____________________")
    question = "What is the percentage of people who use mobile are american?"
    print(get_reference_target(question, dicto))
    print("_____________________")
    question = "For mobile users, percent of american?"
    print(get_reference_target(question, dicto))
    print("_____________________")
    question = "For social media users, percent of american"
    dicto = {
        'visitorId': ['users'], 'cfCountry': ['american'],
        'referralType': ['social media']
    }
    print(get_reference_target(question, dicto))
    print("_____________________")
    question = "What is the percentage of people who come from google speak " \
               "english"
    dicto = {
        'visitorId': ['people'], 'languages': ['english'],
        'referralDomain': ['google']
    }
    print(get_reference_target(question, dicto))
    print("_____________________")
    question = "What is the percentage of people who stay longer than 2 " \
               "minutes speak english"
    dicto = {
        'visitorId': ['people'], 'languages': ['english'],
        'visitTime': ['2 minutes']
    }
    print(get_reference_target(question, dicto))
    print("_____________________")
    question = "what percent of people who stayed 1 minute are american"
    dicto = {
        'visitorId': ['people'], 'cfCountry': ['american'],
        'visitTime': ['1 minute']
    }
    print(get_reference_target(question, dicto))
    print("_____________________")
    # question = "what percent of people who stayed between 1 minute and 2
    # minutes are germany"
    question = "what percent of people stayed between 1 minute and 2 minutes " \
               "" \
               "" \
               "are germany"
    dicto = {
        'visitorId': ['people'], 'cfCountry': ['germany'],
        'visitTime': ['1 minute', '2 minutes']
    }
    print(get_reference_target(question, dicto))
    print("_____________________")
    question = "what percent of people who stayed 5 pages are germany"
    dicto = {
        'visitorId': ['people'], 'pageviews': ['pages'],
        'cfCountry': ['germany'], 'pagesPerVisitor': ['5']
    }
    print(get_reference_target(question, dicto))
    print("_____________________")
    question = "what percent of returning visitors use mobile"
    dicto = {
        'visitorId': ['visitors'], 'deviceTypes': ['mobile'],
        'returningByVisitors': ['returning']
    }
    print(get_reference_target(question, dicto))
    print("_____________________")
    question = "is any american user use mobile"
    dicto = {
        'visitorId': ['user'], 'deviceTypes': ['mobile'],
        'cfCountry': ['american']
    }
    print(get_reference_target(question, dicto))
    print("_____________________")
    question = "is any mobile users come from american"
    dicto = {
        'visitorId': ['users'], 'deviceTypes': ['mobile'],
        'cfCountry': ['american']
    }
    print(get_reference_target(question, dicto))
    print("_____________________")
    question = "are there more american users use mobile on nov 3?"
    dicto = {
        'visitorId': ['users'], 'deviceTypes': ['mobile'],
        'cfCountry': ['american']
    }
    print(get_reference_target(question, dicto))
    print("_____________________")
    question = "are there anyone from american who use mobile on nov 3?"
    dicto = {'deviceTypes': ['mobile'], 'cfCountry': ['american']}
    print(get_reference_target(question, dicto))
    print("_____________________")
    question = "what is the percent of people use mobile and stayed 3 minutes"
    dicto = {
        'visitorId': ['people'], 'deviceTypes': ['mobile'],
        'visitTime': ['3 minutes']
    }
    print(get_reference_target(question, dicto))
    print("_____________________")
