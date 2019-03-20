"""
find date and the indices of date in the question
return: date_string, date_out, index_out
        date_string: list of date's strings (in letters/characters/string
        format)
        date_out: list of date's strings (in numeric format yyyy-mm-dd)
        index_out: list of date's indices
"""
import datetime
import re
from datetime import timedelta

import datefinder
import parsedatetime

import modules.date_module as date_module
from modules.date_module import cal_duration, find_date_parser, \
    cal_duration_ner_special, get_date_ner_from_spacy, \
    get_date_from_datefinder_lib, \
    get_date_from_pdt_lib, get_date_from_season_period, add_prep_date_string
from modules.text import Text

# maximum of month word (september) + 2 spaces before and after and 1
# character/letter
MAX_LENGTH = 13
MIN_LENGTH = 9


def get_date(question):
    day_out = list()
    index_out = list()
    date_spacy = list()

    df = datefinder.DateFinder()
    cal = parsedatetime.Calendar()

    q_obj = Text(question, "en")
    q_obj.preprocess()

    doc = date_module.en(question)

    df1, idf1 = get_date_from_datefinder_lib(question, key=None)
    # print(df1, idf1)
    if df1 and len(df1) == 2:
        pattern = re.compile(
            r"\b(between)\b\s+[a-z0-9\s?]+\b(and|or)\b\s+[a-z0-9\s?]+", re.I)
        is_date_found = pattern.search(question)
        if is_date_found is not None:
            date_string = is_date_found.group()
            date_spacy.append(date_string)

            for i in range(len(df1)):
                day_out.append([df1[i].strftime(date_module.date_format)])
            index_out.append(idf1)
        else:
            # for i in range(len(df1)):
            #     day_out.append([df1[i].strftime(date_module.date_format)])
            # index_out.append(idf1)
            date_spacy, _ = get_date_ner_from_spacy(question)
            # print(date_spacy)

            if idf1[0][1] - idf1[0][0] > MAX_LENGTH and idf1[1][1] - idf1[1][
                0] > MAX_LENGTH:
                for i in range(len(df1)):
                    day_out.append([df1[i].strftime(date_module.date_format)])
                index_out.append(idf1)
            elif any(idf1[i][1] - idf1[i][0] >= MAX_LENGTH for i in
                     range(len(idf1))):
                for i in range(len(df1)):
                    day_out.append([df1[i].strftime(date_module.date_format)])
                index_out.append(df1)
            elif not date_spacy:
                for date_string, index, _ in df.extract_date_strings(question):
                    for idx in idf1:
                        if index == idx:
                            # print({tok.i: tok.idx for tok in doc})
                            for tok in doc:
                                if tok.idx == index[0] + 1 and q_obj.tags[
                                    tok.i - 1] == "IN":
                                    prep_idx = tok.i
                            date_spacy.append(
                                add_prep_date_string(doc, prep_idx,
                                                     date_string))
                for i in range(len(df1)):
                    day_out.append([df1[i].strftime(date_module.date_format)])
                index_out.append(idf1)
            else:
                time_phrase_lst = cal.nlp(question)
                for item in time_phrase_lst:
                    day = item[0]
                    if day.year > date_module.now.year:
                        day = datetime.datetime(date_module.now.year,
                                                day.month, day.day)
                    status_flag = item[1]
                    idx = (item[2], item[3])
                    time_phrase = item[-1]
                    if status_flag == 1:
                        # day_string, _ = get_date_ner_from_spacy(question)
                        day_out, index_out = cal_duration(day, time_phrase,
                                                          question, day_out,
                                                          index_out, idx)
            # return day_string, day_out, index_out

    else:
        df_str, df2, idf2 = get_date_from_pdt_lib(question, key=None)
        # print(date_module.months_list_abbr)
        if df_str and len(df2) == 2 and any(item.lower() in df_str for item in
                                            date_module.months_list_abbr):
            prep = ''
            for tok, tag in zip(q_obj.tokens, q_obj.tags):
                if tag == "IN":
                    prep = tok
            for item in df_str:
                date_spacy.append(prep + " " + item)
            for day, day_str, idx in zip(df2, date_spacy, idf2):
                day_out, index_out = cal_duration(day, day_str, question,
                                                  day_out, index_out, idx)
        else:

            """
            finding the pattern "between ... and ..."
            """
            date_string, date_noun_chks, idx_tuple = find_date_parser(question)
            # print("NER: ", date_noun_chks)
            # print("index outside: ", idx_tuple)
            if date_noun_chks:
                day_list = list()
                for item in date_noun_chks:
                    """
                    return: (time, status_flag, begin_index, end_index)
                    type: tuples
                    """
                    day = list(datefinder.find_dates(item))[0]
                    day = day.strftime(date_module.date_format)
                    day_list.append(day)
                day_out.append(day_list)
                index_out.append(idx_tuple)
                date_spacy.append(date_string)
                # print("1. ", date_spacy)
            else:
                date_df, index_df = get_date_from_datefinder_lib(question,
                                                                 key=None)
                # print(date_df, index_df)
                # print(len(date_df), len(index_df))
                date_spacy, index_spacy = get_date_ner_from_spacy(question)
                # print(date_spacy, index_spacy)

                if date_df and len(date_df) == 1 and date_spacy:
                    # print(index_df[0][1] - index_df[0][0])
                    if (index_df[0][1] - index_df[0][
                        0] - 1) > MAX_LENGTH or any(
                            item.lower() in q_obj.tokens for item in
                            date_module.months_list_abbr):
                        if abs(index_df[0][0] - index_spacy[0][0]) != 1:
                            for date_string, index, \
                                _ in df.extract_date_strings(
                                    question):
                                if index == index_df[0]:
                                    for ent in doc.ents:
                                        if ent.label_ == "DATE":
                                            idx_start = ent.start
                                            date_string = add_prep_date_string(
                                                doc, idx_start, date_string)
                                    # print("date string: ", date_string)
                                    text_obj = Text(date_string, "en")
                                    text_obj.preprocess()
                                    # print(text_obj.tags)
                                    if text_obj.tags[0] == "IN":
                                        date_spacy.pop(0)
                                        date_spacy.append(date_string)
                        day_out.append(
                            [date_df[0].strftime(date_module.date_format)])
                        index_out.append(index_df[0])
                    elif any(i in question for i in ["-", "/"]):
                        day_out.append(
                            [date_df[0].strftime(date_module.date_format)])
                        index_out.append(index_df[0])
                    else:
                        if date_spacy:
                            for phrase, idx in zip(date_spacy, index_spacy):
                                if phrase.count(" ") > 1:
                                    # """detect expressions of weeks"""
                                    week_expression = """((last|past)\s+([
                                    ^\s]+)\s+(weeks?|days?|months?)|([
                                    ^\s]+)\s+(weeks?|days?|months?)\s+ago)"""
                                    week_pattern = re.compile(week_expression,
                                                              re.I)
                                    week_matches = week_pattern.search(phrase)
                                    if week_matches:
                                        day_out, index_out = \
                                            cal_duration_ner_special(
                                            day_out, index_out, phrase, idx,
                                            key="spacy")
                                    else:
                                        date_df = get_date_from_datefinder_lib(
                                            phrase, key="spacy")
                                        day_out, index_out = cal_duration(
                                            date_df, phrase, question, day_out,
                                            index_out, idx)
                                        # if date_df:
                                        #     day_out.append([
                                        # date_df.strftime(
                                        # date_module.date_format)])
                                        #     index_out.append(idx)
                                else:
                                    year_pattern = r"\d{4}"
                                    year_pattern = re.compile(year_pattern,
                                                              re.I)
                                    if year_pattern.search(
                                            phrase) and phrase.count(" ") == 1:
                                        date_df = get_date_from_datefinder_lib(
                                            phrase, key="spacy")
                                        first_day, last_day = \
                                            date_module.cal_first_last_day_a_year(
                                            date_df, date_module.date_format)
                                        day_out.append([first_day, last_day])
                                        index_out.append(idx)
                                    else:
                                        date_pdt = get_date_from_pdt_lib(
                                            phrase, key="spacy")
                                        day_out, index_out = cal_duration(
                                            date_pdt, phrase, question,
                                            day_out, index_out, idx)

                                        # first_day = date_pdt.strftime(
                                        # date_module.date_format)
                                        # last_day =
                                        # date_module.cal_last_day_a_month(
                                        # date_pdt, date_module.date_format)
                                        # day_out.append([first_day, last_day])
                                        # index_out.append(idx)


                        else:
                            """
                            from datefinder library
                            return: (date, index)
                            type: generator
                            """
                            time_lst = datefinder.find_dates(question,
                                                             index=True)
                            # print("check thu: ", list(time_lst))
                            """
                            from parsedatetime library
                            return: (time, status_flag, begin_index, end_index)
                            type: tuple
                            """
                            cal = parsedatetime.Calendar()

                            start = date_module.now.timetuple()
                            time_struct = cal.nlp(question, start)
                            # print("time struct: ", time_struct)

                            if time_struct:
                                for item in time_struct:
                                    status_flag = item[1]
                                    # print("flag: ", status_flag)
                                    # the returned type is not `time` type (
                                    # 1: DATE, 2: DURATION,
                                    # read documentation for more details)
                                    if status_flag == 1:
                                        day = item[0]
                                        index = (item[2], item[3])
                                        if day.day > date_module.now.day:
                                            duration_day = (
                                                                       day -
                                                                       date_module.now).days + 1
                                            # print("duration day: ",
                                            # duration_day)
                                            first_day = (
                                                        date_module.now -
                                                        timedelta(
                                                    days=duration_day)).strftime(
                                                date_module.date_format)
                                            last_day = (
                                                date_module.now).strftime(
                                                date_module.date_format)
                                            day_out.append(
                                                [first_day, last_day])
                                            index_out.append(index)
                                        elif day.year > date_module.now.year:
                                            day = datetime.datetime(
                                                date_module.now.year,
                                                day.month, day.day)
                                            # print("day lon hon bay gio ve
                                            # nam: ", day)

                                            time_phrase = item[4]
                                            # print(time_phrase)
                                            day_out, index_out = cal_duration(
                                                day, time_phrase, question,
                                                day_out, index_out, index)
                                    elif status_flag == 3:
                                        day = item[0].strftime(
                                            date_module.date_format)
                                        day_out.append([day])
                                        index = (item[2], item[3])
                                        index_out.append(index)
                            else:
                                """the special cases are no specified date, 
                                but the semantic of the question
                                is about day, week, month, year"""
                                day_out, index_out = cal_duration_ner_special(
                                    day_out, index_out, question, index_out,
                                    key=None)


                elif date_df and len(date_df) == 1 and not date_spacy:
                    if any(item.lower() in q_obj.tokens for item in
                           date_module.months_list):
                        if ((index_df[0][1] - index_df[0][0]) >= MIN_LENGTH and
                                index_df[0][1] - index_df[0][
                                    0] <= MAX_LENGTH and not date_spacy
                                or any(item.lower() in q_obj.tokens for item in
                                       date_module.months_list_abbr)):
                            for date_string, index, \
                                _ in df.extract_date_strings(
                                    question):
                                if index == index_df[0]:
                                    # print({tok.i: tok.idx for tok in doc})
                                    for tok in doc:
                                        if tok.idx == index[0] + 1 and \
                                                q_obj.tags[tok.i - 1] == "IN":
                                            date_spacy.append(
                                                add_prep_date_string(doc,
                                                                     tok.i,
                                                                     date_string))
                                    day_out.append([date_df[0].strftime(
                                        date_module.date_format)])
                                    index_out.append(index_df[0])
                    elif any(i in question for i in ["-", "/"]):
                        day_out.append(
                            [date_df[0].strftime(date_module.date_format)])
                        index_out.append(index_df[0])
                else:
                    if date_spacy:
                        for phrase, idx in zip(date_spacy, index_spacy):
                            if phrase.count(" ") > 1:
                                date_df = get_date_from_datefinder_lib(phrase,
                                                                       key="spacy")
                                if date_df:
                                    day_out.append([date_df.strftime(
                                        date_module.date_format)])
                                    index_out.append(idx)
                                else:
                                    date_pdt = get_date_from_pdt_lib(phrase,
                                                                     key="spacy")
                                    if date_pdt:
                                        day_out, index_out = cal_duration(
                                            date_pdt, phrase, question,
                                            day_out, index_out, idx)
                                    else:
                                        day_out, index_out = \
                                            cal_duration_ner_special(
                                            day_out, index_out, phrase, idx,
                                            key="spacy")
                            else:
                                year_pattern = r"\d{4}"
                                year_pattern = re.compile(year_pattern, re.I)
                                if year_pattern.search(phrase):
                                    date_df = get_date_from_datefinder_lib(
                                        phrase, key="spacy")
                                    first_day, last_day = \
                                        date_module.cal_first_last_day_a_year(
                                        date_df,
                                        date_module.date_format)
                                    day_out.append([first_day, last_day])
                                    index_out.append(idx)
                                elif any(season in phrase for season in
                                         date_module.seasons_period):
                                    day_out, index_out = \
                                        get_date_from_season_period(
                                        day_out, index_out, phrase, idx)
                                else:
                                    date_pdt = get_date_from_pdt_lib(phrase,
                                                                     key="spacy")
                                    day_out, index_out = cal_duration(date_pdt,
                                                                      phrase,
                                                                      question,
                                                                      day_out,
                                                                      index_out,
                                                                      idx)

                                    # first_day = date_pdt.strftime(
                                    # date_module.date_format)
                                    # last_day =
                                    # date_module.cal_last_day_a_month(
                                    # date_pdt, date_module.date_format)
                                    # day_out.append([first_day, last_day])
                                    # index_out.append(idx)


                    else:
                        """
                        from datefinder library
                        return: (date, index)
                        type: generator
                        """
                        time_lst = datefinder.find_dates(question, index=True)
                        # print("check thu: ", list(time_lst))
                        """
                        from parsedatetime library
                        return: (time, status_flag, begin_index, end_index)
                        type: tuple
                        """
                        cal = parsedatetime.Calendar()

                        start = date_module.now.timetuple()
                        time_struct = cal.nlp(question, start)
                        # print("time struct: ", time_struct)

                        if time_struct:
                            for item in time_struct:
                                status_flag = item[1]
                                # print("flag: ", status_flag)
                                # the returned type is not `time` type (1:
                                # DATE, 2: DURATION, read documentation for
                                # more details)
                                if status_flag == 1:
                                    day = item[0]
                                    index = (item[2], item[3])
                                    if day.day > date_module.now.day:
                                        duration_day = (
                                                                   day -
                                                                   date_module.now).days + 1
                                        # print("duration day: ", duration_day)
                                        first_day = (
                                                    date_module.now -
                                                    timedelta(
                                                days=duration_day)).strftime(
                                            date_module.date_format)
                                        last_day = (date_module.now).strftime(
                                            date_module.date_format)
                                        day_out.append([first_day, last_day])
                                        index_out.append(index)
                                    elif day.year > date_module.now.year:
                                        day = datetime.datetime(
                                            date_module.now.year, day.month,
                                            day.day)

                                        time_phrase = item[4]
                                        # print(time_phrase)
                                        for token in doc:
                                            if token.pos_ == "ADP" and \
                                                    token.tag_ == "IN" and \
                                                    token.text not in time_phrase:
                                                date_string = token.text + " " + time_phrase.strip()
                                        if date_string not in date_spacy:
                                            date_spacy.append(date_string)
                                        day_out, index_out = cal_duration(day,
                                                                          time_phrase,
                                                                          question,
                                                                          day_out,
                                                                          index_out,
                                                                          index)
                                elif status_flag == 3:
                                    day = item[0].strftime(
                                        date_module.date_format)
                                    day_out.append([day])
                                    index = (item[2], item[3])
                                    index_out.append(index)
                        else:
                            """the special cases are no specified date, but the semantic of the question
                            is about day, week, month, year"""
                            day_out, index_out = cal_duration_ner_special(
                                day_out, index_out, question, None, key=None)

    # print(date_spacy, day_out, index_out)

    return date_spacy, day_out, index_out


if __name__ == "__main__":
    # print(get_date("how many bouncers did I have last month"))
    # print(get_date("how many bouncers did I have this month"))
    # print(get_date("how many visitors come in august"))
    # print(get_date("how many visitors between apr 23 and 27"))
    # print(get_date("how many visitors now"))
    # print(get_date("how many visitors by now"))
    # print(get_date("how much people turned adblock on for this site in august and september?"))
    # print(get_date("Did many people convert between the 3rd and 10th of august?"))
    # print(get_date("Were most of the visitors last month from France?"))
    # print(get_date("Average pages for people who stay at least 20 seconds"))
    # print(get_date("did i have more american users on september 10th and october 14th "))
    # print(get_date("What referraltype was most prominent last week?"))
    # print(get_date("Since a month ago, how much visitors were there?"))
    # print(get_date("Please tell me the number of those who came on Chrome in the past weeks,"))
    # print(get_date("What is the average time of a visit this year"))
    # print(get_date("total amount of conversions since two weeks ago,"))
    # print(get_date("which device was most commonly used since start of summer?"))
    # print(get_date("Tell me how many pageviews we had the past three months,"))
    # print(get_date("how many enable adblock when visiting in the past 20 days?"))
    # print(get_date("show me visits over a period of 43 days,"))
    # print(get_date("perc of new sessions on 12 mar?"))
    # print(get_date("amount of returning visitors over weeks for the last year"))
    # print(get_date("pageviews last week compared to the week before?"))
    # print(get_date("number of pageviews in October 2017"))
    # print(get_date("How many pages do visitors visit on average on the 1st of may?"))
    # print(get_date("Of all devices, which one was the second most popular in march?"))
    # print(get_date("What was the most popular browser in august?"))
    # print(get_date("what was the median visit time on 20th of october 2017"))
    # print(get_date("How many visitors did I have in september?"))
    # print(get_date("How many users stayed more than a minute in 2017?"))
    # print(get_date("Did many people convert between the 3rd and 10th of august?"))
    # print(get_date("Are there more users in september 18th or in october 4th"))
    print(get_date(
        "how is the general trend in september to my american users who referred from social media"))

    question = input()
    while question != 'q':
        print(get_date(question))
        question = input()
