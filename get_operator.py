"""rule based operator detector"""
import re

import spacy

en = spacy.load("en")

"""two functions for getting and mapping the operator"""


def find_operator(question):
    # pattern = r'\b(second most|all|before|than before|of all|a lot
    # of|prefer|majority|further than|no more
    # than|most|best|increase|highest|mostly|lowest|under|longer
    # than|least|more than|or more|less than|within|or less|at least|at
    # least once)\b'
    pattern = r'\b(more|rather than|at least once|all|at least|second ' \
              r'most|before|than before|a lot of|of ' \
              r'all|prefer|majority|minority|further than|no more ' \
              r'than|most|best|increase|highest|mostly|lowest|under|longer ' \
              r'than|least|more than|or more|week before|less than|within|or ' \
              r'less|less)\b'

    ops = re.findall(pattern, question.lower())
    removals = ['of all', 'week before', 'at least once', 'than before']
    for op in ops:
        if op in removals:
            ops.remove(op)

    return ops


def map_operator(question, operator, NER_output, qtype):
    comparatives = ['more', 'less than', 'rather than', 'increase', 'before',
                    'further than', 'or less',
                    'no more than', 'under', 'within', 'or more', 'more than',
                    'at least', 'longer than', 'less']

    if operator in comparatives:
        for target in NER_output:
            if 'visitTime' in NER_output and 'pagesPerVisitor' not in \
                    NER_output:
                return {'visitTime': operator_mapper(operator)}

            elif 'pagesPerVisitor' in NER_output and 'visitTime' not in \
                    NER_output:
                return {'pagesPerVisitor': operator_mapper(operator)}

            elif 'visitTime' not in NER_output and 'pagesPerVisitor' not in \
                    NER_output:
                return {target: operator_mapper(operator)}
                # return {target : '////'}
                # comparative but not visittime or pagespervisitor

            elif 'visitTime' in NER_output and 'pagesPerVisitor' in NER_output:
                # """operatorsplit = operator.split()
                #
                # if operatorsplit[0] == 'or' or operatorsplit[0] == 'at':
                #     operator = operatorsplit[1]
                # elif operatorsplit[1] == 'than':
                #     operator = operatorsplit[0]
                # values = []
                # targets = []
                # for i in NER_output:
                #     values.append([string for string in NER_output[i]])
                # find_head(question, operator, values)"""
                return {
                    target: "combining visittime and pagespervisitor...need "
                            "extra postprocessing"
                }


            elif 'returningByVisitors' in NERoutput:
                return {target: operator_mapper(operator)}


    else:

        ignore = ['pageviews', 'visitorId']

        if len(NER_output) > 1:

            for target in NER_output:

                if target not in ignore:

                    if NER_output[target] == ['unspecified']:
                        return {target: operator_mapper(operator)}

                    else:

                        if qtype in ["yes/no", "COMPARISON"]:
                            if "unspecified" in NER_output[target]:
                                NER_output[target].remove('unspecified')

                            return {target: operator_mapper(operator)}
        elif len(NER_output) == 1:
            for target in NER_output:

                return {target: operator_mapper(operator)}


def operator_mapper(operator):
    mappings = {
        'max': ["highest", "majority", "a lot of", "best", "most", "a lot of",
                "prefer", "max", 'mostly', 'the most'],
        'min': ["lowest", "least", 'min', 'the least', 'do least', 'minority'],
        'second': ["second most"],
        '>': ['more than', 'rather than', 'further than', 'increase',
              'or more', 'longer than', 'at least', 'more'],
        '<': ['less than', 'within', 'no more than', 'before', 'under',
              'or less', 'at most', 'less'],
        'all': ['all', 'the various', 'the different']
    }

    for key in mappings:
        if operator in mappings[key]:
            return key


"""two functions for dependency parsing
def step_through_tree(index, values, doc):
    head_token = doc[index].head
    print("headtoken: ",head_token)
    if index == head_token.i:
        print("Arrived at top of sentence. No target found.")
        return None

    else:
        for value in values:
            if value != ['unspecified']:
                print("value: ", value)
                if head_token.orth_ in value:
                    return head_token.orth
                else:
                    return step_through_tree(head_token.i, values, doc)

def find_head(question, operator, values):
    #print("Operator:", operator)
    doc = en(question)
    operator_index = [t.orth_ for t in doc].index(operator)
    print(operator_index)
    head = step_through_tree(operator_index, values, doc)
    return head
"""
