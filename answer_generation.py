import os
import random
import re

import spintax

from modules.calculations import get_full_name


def read_answers_from_file():
    answers = {}
    with open(os.path.join("..", "data/answers/answers.tsv"), 'r') as i:
        for line in i:
            line = line.strip().split("\t")
            variables = line[:-1]
            answer = line[-1]
            question_type, answer_type = variables
            if question_type not in answers:
                answers[question_type] = {}
            if answer_type not in answers[question_type]:
                answers[question_type][answer_type] = {}

            # get targets from answer
            fields = re.findall("<.*?>", answer)
            ignore = ["<RESULT>", "<RESULT_REF>", "<NUM>", "<BOOL>", "<DATE>",
                      "<DATE_REF>", "<INDEX>"]
            targets = [field for field in fields if field not in ignore]
            targets = list(set(targets))
            targets.sort()

            targets_string = "_".join(targets)
            # print(targets_string)
            if targets_string not in answers[question_type][answer_type]:
                answers[question_type][answer_type][targets_string] = []

            answers[question_type][answer_type][targets_string].append(answer)

    return answers


def get_targets_from_frame(frame):
    all_targets = [{cond.target: cond.value} for cond in frame.conditions]
    targets_frame_list = []

    for d in all_targets:
        for target in d:
            if len(d[target]) == 1:
                target = '<' + target + '>'
                targets_frame_list.append(target)
                target_other = None
                target_REF = None
                value_other = None
                value_REF = None


            elif len(d[target]) == 2:
                #print("your values: ", d[target])
                for key, value in d.items():
                    target_other = '<' + key + '>'
                    value_other = d[target][1]
                    targets_frame_list.append(target_other)
                    target_REF = '<' + key + '_REF>'
                    targets_frame_list.append(target_REF)
                    value_REF = d[target][0]

    targets_frame_list.sort()
    if len(targets_frame_list) > 1 and '<visitorId>' in targets_frame_list:
        targets_frame_list.remove('<visitorId>')
    if '<pageviews>' in targets_frame_list and '<pagesPerVisitor>' in \
            targets_frame_list:
        targets_frame_list.remove('<pageviews>')
    targets = "_".join(targets_frame_list)

    #print('frame targets: ', targets)

    return targets, target_other, target_REF, value_other, value_REF


def generate_answer(answers, frame, result, date_string, question):
    memory = None
    did_date_comparison = False

    dicto = frame.map_target_values()

    if type(result) == int:
        answer_type = 'INT'
    elif 'float' in str(type(result)):
        answer_type = "FLOAT"
    elif type(result) == str and "%" in result:
        answer_type = "FLOAT"
    elif type(result) == list:
        answer_type = "LST"
    elif type(result) == tuple:
        answer_type = "TUPLE"
    elif type(result) == dict:
        answer_type = "DICT"
    elif 'second' in str(result):
        answer_type = "TIME"
    else:
        answer_type = 'STR'

    print("Answer Type:", answer_type)

    targets, target_other, target_REF, value_other, value_REF = get_targets_from_frame(frame)
    # print('possible answers: ', answers[frame.question_type][answer_type][targets], '\n\n') # join targets here

    try:
        answer = random.choice(answers[frame.question_type][answer_type][targets])
        answer = spintax.spin(answer)


    except KeyError:
        if answer_type == "TUPLE" and result[2] == 'unspecified':
            answer = ""

        elif len(targets) > 1:
            template = "The answer is <OUTPUT>"
            template = template.replace('<OUTPUT>', str(result))
            return template, None
        else:

            return "Rephrase your question, please! I am afraid I don't understand.", None


    """replacing RESULT"""

    """category list"""
    if type(result) == list:
        if None in result:
            result.remove(None)
        if len(result) == 2:
            selection = ' and '.join(result), ' only'
        elif len(result) == 3:
            selection = result[0], ', ', result[1], ' and ', result[2]
        elif len(result) == 4:
            selection = result[0], ', ', result[1], ', ', result[2], ' and ', \
                        result[3]
        elif len(result) > 4:

            selection = result[0], ', ', result[1], ', ', result[2], ' and ', str(len(result) - 3), ' others'
            memory = 'full value list', ', '.join(result), selection

        else:
            return "Sorry, I do not have that information.", None

        answer = answer.replace("<RESULT>", ''.join(selection))

        """target value comparison"""
    elif type(result) == dict:
        if len(result) == 1:
            try:
                operator = \
                [item.operator for item in frame.conditions if item.operator][
                    0]
            except IndexError:
                operator = None
            check_flags = True
            for targets, compares in result.items():
                name_lst = list(compares.keys())
                perc_lst = list(compares.values())
                perc_flt = [float(item.split("%")[0]) for item in perc_lst]
            RESULT_REF = perc_lst[0]
            RESULT = perc_lst[1]

            assumption_made = re.findall('than', question)
            assumption_2 = re.findall('compared to', question)

            if assumption_made or assumption_2:
                if operator == '>':
                    if perc_flt[0] > perc_flt[1]:
                        answer = answer.replace("<BOOL>", "Yep, ")
                    else:
                        answer = answer.replace("<BOOL>", "Nope, ")
                elif operator == '<':
                    if perc_flt[0] < perc_flt[1]:
                        answer = answer.replace("<BOOL>", "Yep, ")
                    else:
                        answer = answer.replace("<BOOL>", "Nope, ")
            else:
                answer = answer.replace("<BOOL>", "")

            answer = answer.replace("<RESULT>", RESULT)
            answer = answer.replace("<RESULT_REF>", RESULT_REF)


        elif len(result) == 2:
            memory = 'unknown memory stuff here, answer gen line +-180', tuple(result.values())


        """yes/no with and without operator, binary and ranking"""

    elif type(result) == tuple and len(result) == 4:
        try:
            operator = \
            [item.operator for item in frame.conditions if item.operator][0]
        except IndexError:
            operator = None

        if operator:

            if type(result[1]) == str:
                """binary with operator"""

                if str(result[0]) == "True":
                    answer = answer.replace("<BOOL>", "That's right, ")
                elif str(result[0]) == "False":
                    if operator == "max" or operator == ">":
                        answer = answer.replace("<BOOL>", "Nope, only ")
                    else:
                        answer = answer.replace("<BOOL>", "No, ")
                else:
                    answer = "Something went wrong... Try splitting up your " \
                             "question, because I'm a little confused :/"

                print(result[-1])
                answer = answer.replace("<RESULT>", result[-1])

            elif type(result[1]) == int:
                """ranking with operator"""

                if str(result[0]) == "True":
                    answer = answer.replace("<BOOL>", "Correct! ")
                elif str(result[0]) == "False":
                    answer = answer.replace("<BOOL>", "Not really! ")
                else:
                    answer = "How embarassing... I'm afraid I do not " \
                             "understand the question. Try splitting it up!"

                if str(result[1]) == '1':
                    answer = answer.replace('<INDEX>', '')
                elif str(result[1]).endswith('1'):
                    answer = answer.replace('<INDEX>', str(result[1]) + 'st ')
                elif str(result[1]).endswith('2'):
                    answer = answer.replace('<INDEX>', str(result[1]) + 'nd ')
                elif str(result[1]).endswith('3'):
                    answer = answer.replace('<INDEX>', str(result[1]) + 'rd ')
                else:
                    answer = answer.replace('<INDEX>', str(result[1]) + 'th ')

        else:

            """without operator"""
            if str(result[0]) == "True":
                answer = answer.replace('<BOOL>', "Sure they do! ")
                template = 'was the <INDEX>most common'
                template_new = "was good for " + str(result[-1])

                answer = answer.replace(template, template_new)
                answer = answer.replace("<RESULT>", str(result[-1]))

            elif str(result[0]) == "False":
                answer = "Negative."

        """date comparison"""
    elif type(result) == tuple and len(result) == 2:

        try:
            operator = \
            [item.operator for item in frame.conditions if item.operator][0]
        except IndexError:
            operator = None

        #print(operator)

        RESULT_REF = result[0]
        RESULT = result[1]
        if any(item == "The database doesn't have this information" for item in
               result):
            return "The database doesn't have this information.", None

        assumption_made = re.findall('than', question)
        assumption_2 = re.findall('compared to', question)

        if assumption_made or assumption_2:
            if operator == '>':
                if result[0] > result[1]:
                    answer = answer.replace("<BOOL>", "Yep, ")
                else:
                    answer = answer.replace("<BOOL>", "Nope, ")
            elif operator == '<':
                if result[0] < result[1]:
                    answer = answer.replace("<BOOL>", "Yep, ")
                else:
                    answer = answer.replace("<BOOL>", "Nope, ")

        else:
            answer = answer.replace("<BOOL>", "")

        answer = answer.replace("<RESULT>", str(RESULT))
        answer = answer.replace("<RESULT_REF>", str(RESULT_REF))

        answer = answer.replace("<DATE_REF>", date_string[0])
        answer = answer.replace("<DATE>", date_string[1])

        did_date_comparison = True


    elif type(result) == tuple and 'unspecified' in result:
        memory = "visittime period clarification", result

        """percent, quantity or category string"""
    elif type(result) == str or type(result) == int:
        answer = answer.replace("<RESULT>", str(result))

    else:
        answer = answer.replace("<RESULT>", str(result))

    """replacing operators and values"""
    if "OPERATOR" in answer:
        operator = [item.operator for item in frame.conditions if
                    item.operator]
        if operator:
            operator = operator[0]
            answer = answer.replace("OPERATOR", revert_map(operator))
        else:
            answer = answer.replace("OPERATOR", "")

    answer = answer.replace("<visitorId>", '')
    answer = answer.replace("<pageviews>", '')

    if "<cfCountry>" in answer:
        if len(dicto['cfCountry']) == 1:
            if dicto['cfCountry'][0] == "unspecified":
                answer = answer.replace('<cfCountry>', '')
            else:
                answer = answer.replace('<cfCountry>',
                                        get_full_name("cfCountry",
                                                      dicto['cfCountry'][0],
                                                      None))
        elif len(dicto['cfCountry']) == 2:
            answer = answer.replace("<cfCountry_REF>", name_lst[0])
            answer = answer.replace("<cfCountry>", name_lst[1])

    if "<languages>" in answer:
        if len(dicto['languages']) == 1:
            if dicto['languages'][0] == "unspecified":
                answer = answer.replace('<languages>', '')
            else:
                answer = answer.replace('<languages>',
                                        get_full_name("languages",
                                                      dicto['languages'][0],
                                                      None))
        elif len(dicto['languages']) == 2:
            answer = answer.replace("<languages_REF>", name_lst[0])
            answer = answer.replace("<languages>", name_lst[1])

    if "<deviceTypes>" in answer:
        if len(dicto['deviceTypes']) == 1:
            if dicto['deviceTypes'][0] == "unspecified":
                answer = answer.replace('<deviceTypes>', '')
            else:
                answer = answer.replace('<deviceTypes>',
                                        dicto['deviceTypes'][0])
        elif len(dicto['deviceTypes']) == 2:
            answer = answer.replace("<deviceTypes_REF>", name_lst[0])
            answer = answer.replace("<deviceTypes>", name_lst[1])

    if "<deviceBrands>" in answer:
        if len(dicto['deviceBrands']) == 1:
            if dicto['deviceBrands'][0] == "unspecified":
                answer = answer.replace('<deviceBrands>', '')
            else:
                answer = answer.replace('<deviceBrands>',
                                        dicto['deviceBrands'][0])
        elif len(dicto['deviceBrands']) == 2:
            answer = answer.replace("<deviceBrands_REF>", name_lst[0])
            answer = answer.replace("<deviceBrands>", name_lst[1])

    if "<browserTypes>" in answer:
        if len(dicto['browserTypes']) == 1:
            if dicto['browserTypes'][0] == "unspecified":
                answer = answer.replace('<browserTypes>', '')
            else:
                answer = answer.replace('<browserTypes>',
                                        dicto['browserTypes'][0])
        elif len(dicto['browserTypes']) == 2:
            answer = answer.replace("<browserTypes_REF>", name_lst[0])
            answer = answer.replace("<browserTypes>", name_lst[1])

    if "<osTypes>" in answer:
        if len(dicto['osTypes']) == 1:
            if dicto['osTypes'][0] == "unspecified":
                answer = answer.replace('<osTypes>', '')
            else:
                answer = answer.replace('<osTypes>', dicto['osTypes'][0])
        elif len(dicto['osTypes']) == 2:
            answer = answer.replace("<osTypes_REF>", name_lst[0])
            answer = answer.replace("<osTypes>", name_lst[1])

    if "<conversion>" in answer:
        answer = answer.replace("<conversion>", "convert")
    if "<touch>" in answer:
        answer = answer.replace("<touch>", "touch screen")
    if "<bounce>" in answer:
        answer = answer.replace("<bounce>", "bounce")
    if "<adBlock>" in answer:
        answer = answer.replace("<adBlock>", "adblock")

    if "<referralType>" in answer:
        if len(dicto['referralType']) == 1:
            if dicto['referralType'][0] == "unspecified":
                answer = answer.replace('<referralType>', '')
            else:
                answer = answer.replace('<referralType>',
                                        revert_map(dicto['referralType'][0]))
        elif len(dicto['referralType']) == 2:
            answer = answer.replace("<referralType_REF>", name_lst[0])
            answer = answer.replace("<referralType>", name_lst[1])

    if "<referralDomain>" in answer:
        if len(dicto['referralDomain']) == 1:
            if dicto['referralDomain'][0] == "unspecified":
                answer = answer.replace('<referralDomain>', '')
            else:
                answer = answer.replace('<referralDomain>',
                                        dicto['referralDomain'][0])
        elif len(dicto['referralDomain']) == 2:
            answer = answer.replace("<referralDomain_REF>", name_lst[0])
            answer = answer.replace("<referralDomain>", name_lst[1])

    if "<returningByVisitors>" in answer:
        answer = answer.replace("<returningByVisitors>",
                                revert_map(dicto['returningByVisitors'][0]))

    if "<visitTime>" in answer:
        if len(dicto['visitTime']) == 1:
            if dicto['visitTime'][0] == "unspecified":
                answer = answer.replace('<visitTime>', '')
            else:
                answer = answer.replace('<visitTime>',
                                        revert_map(dicto['visitTime'][0]))
        elif len(dicto['visitTime']) == 2:
            answer = answer.replace("<visitTime_REF>", revert_map(name_lst[0]))
            answer = answer.replace("<visitTime>", revert_map(name_lst[1]))

    if "<pagesPerVisitor>" in answer:
        if len(dicto['pagesPerVisitor']) == 1:
            if dicto['pagesPerVisitor'][0] == "unspecified":
                answer = answer.replace('<pagesPerVisitor>', '')
            else:
                answer = answer.replace('<pagesPerVisitor>',
                                        dicto['pagesPerVisitor'][0])
        elif len(dicto['pagesPerVisitor']) == 2:
            answer = answer.replace("<pagesPerVisitor_REF>", name_lst[0])
            answer = answer.replace("<pagesPerVisitor>", name_lst[1])

    """ adding the date string """
    if did_date_comparison == False:
        if date_string:
            answer = add_date_to_answer(date_string, answer)

    return answer, memory


def revert_map(mappedvalue):
    revert = {
        'unspecified': '',
        'BE': 'Belgium',
        'DE': 'Germany',
        'US': 'The Unites States',
        'NL': 'The Netherlands',
        'nl': 'Dutch',
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'mobile': 'mobile device',
        'pc': 'pc',
        'tablet': 'tablet',
        1: 'direct',
        2: 'internal',
        3: 'social media',
        4: 'search engine',
        5: 'email',
        7: 'Android App',
        8: 'advertisement',
        'True': 'returning',
        'False': 'first time',
        '10': '10 seconds',
        '20': '20 seconds',
        '30': '30 seconds',
        '60': 'one minute',
        '120': 'two minutes',
        '180': 'three minutes',
        '240': 'four minutes',
        '300': 'five minutes',
        '600': '10 minutes',
        '900': '15 minutes',
        'max': 'most',
        'min': 'least',
        '>': 'more than',
        '<': 'less than',
        'second': 'second most',
        'all': 'only',
        'IE': 'Internet Explorer'
    }

    try:
        return revert[mappedvalue]
    except KeyError:
        return mappedvalue


def add_date_to_answer(date_string, answer):
    date_string = ' ' + date_string[0].lower() + '.'
    answer = rreplace(answer, '.', date_string, 1)
    return answer


def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


if __name__ == "main":
    print(read_answers_from_file())
