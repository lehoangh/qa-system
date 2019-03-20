import re

from modules.text import Text

"""regex pattern definition"""
percent_pattern = "percent|percentage|%| rate| rating|what part|perc|part " \
                  "of|conversion rate|bounce rate|bouncing rate|ratio |share"
quantity_pattern = "how many|howmany|how " \
                   "much|howmuch|number|amount|total|count "
category_pattern = 'best| all |which|what is|what|where'
median_pattern = 'median'
average_pattern = 'mean|average|avg|per visitor|per visit'
quantity_pattern_2 = 'pageviews|referrals|referals|refferrals|visitors|users' \
                     '|time|many'
comparison_pattern = " or not|than |compared| or "
trend_pattern = "which day|which date|which week|which month|which " \
                "year|increase|increasing|decrease|decreasing|trend|" \
                "evolution|evolve|progress|overview|per day|per date|per " \
                "week|per month|per year|daily|" \
                "weekly|monthly|yearly|annual|when " \
                "did|brief|distribution|over time|chart|over|highest|lowest"

"""deciding on the question type"""


def get_questiontype(question):
    question_string = question.raw.lower()
    question_type = None

    t = re.findall(trend_pattern, question_string)
    if t:
        question_type = "TREND"
    else:
        m = re.findall(median_pattern, question_string)
        if m != []:
            question_type = "MEDIAN"
        else:
            A = re.findall(average_pattern, question_string)
            if A != []:
                question_type = "AVERAGE"
            else:
                P = re.findall(percent_pattern, question_string)
                if P != []:
                    question_type = "PERC"
                else:
                    Q = re.findall(quantity_pattern, question_string)
                    if Q != []:
                        question_type = "QUANTITY"
                    else:
                        com = re.findall(comparison_pattern, question_string)
                        if " or not" in com:
                            com.remove(" or not")
                        if com != []:
                            question_type = "COMPARISON"

                        else:
                            C = re.findall(category_pattern, question_string)
                            if C != []:
                                question_type = "CATEGORY"

                            else:
                                tags = question.tags

                                """checking for yes/no questions, excluding 
                                "Give me" structures"""
                                if tags[0].startswith("VB") and tags[
                                    1] != 'PRP' and len(tags) >= 4:
                                    question_type = "yes/no"
                                    return question_type


                                elif ',' in tags:
                                    id = tags.index(',')
                                    id += 1
                                    tags_after_comma = tags[id:]

                                    if tags_after_comma[0].startswith("VB") \
                                            and \
                                            tags_after_comma[
                                                1] != 'PRP' and len(tags) >= 4:
                                        question_type = "yes/no"
                                        return question_type

                                    else:
                                        question_type = "QUANTITY"
                                        return question_type

                                    """ if not found a yes/no sequence"""
                                else:
                                    tags_as_string = " ".join(tags)
                                    pos_patterns = ["RBS JJ XX", "RBS JJ NN",
                                                    "RBS VBN NN", "RBS VBN RB",
                                                    "RBS VBG NN",
                                                    "RBS VBG VBG", "JJS JJ NN"]

                                    # These are patterns for finding
                                    # CATEGORY structures with an operator

                                    for pattern in pos_patterns:
                                        if pattern in tags_as_string:
                                            question_type = "CATEGORY"
                                            return question_type

                                    q2 = re.findall(quantity_pattern_2,
                                                    question_string)
                                    if q2 != []:
                                        question_type = "QUANTITY"

                                        """ if not matching anything...give 
                                        default """
                                    else:
                                        question_type = "QUANTITY"

    return question_type


if __name__ == "__main__":
    questions = ["Are the most visitors returning or nah?"]
    for question in questions:
        question = Text(question, "en")
        question.preprocess()
        print(get_questiontype(question))
