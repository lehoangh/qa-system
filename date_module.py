import calendar
import re
import string
from datetime import timedelta, datetime

import datefinder
import parsedatetime
import spacy
from datefinder import DateFinder
from word2number import w2n

from modules.text import Text

months_list_fullname = list(calendar.month_name)
months_list_abbr = list(calendar.month_abbr)
months_list = months_list_fullname + months_list_abbr
months_list = list(filter(None, months_list))

weekday_list = list(calendar.day_name) + list(calendar.day_abbr)

en = spacy.load("en")

date_format = "%Y-%m-%d"
now = datetime.now()
time_unit = ["week", "month", "year", "day"]

ordinal_word = DateFinder.DIGITS_MODIFIER_PATTERN
days_pattern = DateFinder.DAYS_PATTERN
months_pattern = DateFinder.MONTHS_PATTERN
unit_pattern = 'day|week|month|year'

mapping = {
    "first": 1, "second": 2, "third": 3, "fourth": 4, "forth": 4, "fifth": 5,
    "sixth": 6
}

SECONDS_A_DAY = 24 * 3600

seasons_period = ["spring", "summer", "autumn", "winter"]

cal = parsedatetime.Calendar()


def cal_first_day_a_month(day, date_format):
    first_day = day.replace(day=1).strftime(date_format)
    return first_day


def cal_last_day_a_month(day, date_format):
    last_day = day.replace(
        day=calendar.monthrange(day.year, day.month)[1]).strftime(date_format)
    return last_day


def cal_first_last_day_a_year(day, date_format):
    first_day = day.date().replace(month=1, day=1).strftime(date_format)
    last_day = day.date().replace(month=12, day=31).strftime(date_format)
    return first_day, last_day


def cal_first_last_day_by_week(day, date_format, number):
    if datetime.date(now.year, now.month, now.day) - datetime.date(day.year,
                                                                   day.month,
                                                                   day.day) \
            == datetime.timedelta(days=7 * number) and number != 1:
        # print("True")
        first_day = day.strftime(date_format)
        last_day = now.strftime(date_format)
    else:
        if number == 1:
            first_day = (day - timedelta(days=day.weekday())).strftime(
                date_format)
            last_day = (day - timedelta(days=day.weekday()) + timedelta(
                days=6)).strftime(date_format)
        elif number > 1:
            # """if prefer only business days, i.e. as monday to friday,
            # uncomment"""
            # first_day = (day - timedelta(days=day.weekday())).strftime(
            # date_format)
            # last_day = (day - timedelta(days=day.weekday()) + timedelta(
            # days=6 + 7 * (number - 1))).strftime(date_format)
            first_day = (day - timedelta(days=7 * (number - 1))).strftime(
                date_format)
            last_day = (day + timedelta(days=6)).strftime(date_format)
    return first_day, last_day


def cal_month_ago(day, date_format):
    first_day = day.strftime(date_format)
    last_day = now.strftime(date_format)
    return first_day, last_day


def cal_first_last_day_duration_by_days(day, date_format, number):
    first_day = (day - timedelta(days=number)).strftime(date_format)
    last_day = day.strftime(date_format)
    return first_day, last_day


def cal_past(day, date_format, text_nlp):
    number = None
    for item in text_nlp.lemmas:
        if item not in time_unit and item not in ["ago", "last", "past"]:
            try:
                number = w2n.word_to_num(item)
            except ValueError:
                # default is 4 weeks duration in the past,
                # but the day variable is the day of last week.
                number = 4
        elif item == "week" and number:
            # print("number = ", number)
            first_day, last_day = cal_first_last_day_by_week(day, date_format,
                                                             number)
        elif item == "day" and number:
            first_day, last_day = cal_first_last_day_duration_by_days(day,
                                                                      date_format,
                                                                      number)
    return first_day, last_day


def find_date_parser(question):
    # between number and number month word
    # find the phrase `between ... and ... `
    pattern = re.compile(
        r"\b(between)\b\s+[a-z0-9\s?]+\b(and)\b\s+[a-z0-9\s?]+", re.I)
    is_date_found = pattern.search(question)
    new_str = list()
    start_idx = None
    end_idx = None
    date_string = ''
    # print(is_date_found)
    if is_date_found is not None:
        num_word = list()
        date_found = is_date_found.group()
        # print("date found: ", date_found)
        time_obj = Text(date_found, "en")
        time_obj.preprocess()
        start_idx = is_date_found.start()
        end_idx = is_date_found.end()
        # print("index: ", start_idx, end_idx)
        date_string = Text(is_date_found.group(0), "en")
        date_string.preprocess()
        date_string = " ".join(
            item for item, tag in zip(date_string.tokens, date_string.tags) if
            tag != ".")
        # print("date string: ", date_string)
        if any(j.lower() in time_obj.tokens for j in months_list):
            for item in time_obj.tokens:
                if item not in ["between", "and", "the",
                                "of"] and item not in string.punctuation:
                    if item.title() in months_list:
                        month_word = item
                    else:
                        num_word.append(item)
            for item in num_word:
                new_str.append(item + " " + month_word)
    return date_string, new_str, (start_idx, end_idx)


def cal_duration_ner_special(day_out, index_out, sentence, idx, key="spacy"):
    if key == "spacy":
        text_nlp = Text(sentence, "en")
        text_nlp.preprocess()
        if sentence == "the week before":
            first_day = now - timedelta(days=now.weekday()) - timedelta(
                days=14)
            last_day = (first_day + timedelta(days=6)).strftime(date_format)
            first_day = first_day.strftime(date_format)
            day_out.append([first_day, last_day])
        elif "past year" in sentence:
            day = cal.nlp("last year")[0][0]
            first_day, last_day = cal_first_last_day_a_year(day, date_format)
            day_out.append([first_day, last_day])
        elif "weeks" in sentence:
            day = cal.nlp("last weeks")[0][0]
            # print("day is: ", day)
            # print(type(day))
            first_day, last_day = cal_past(day, date_format, text_nlp=text_nlp)
            day_out.append([first_day, last_day])
        elif "days" in sentence:
            day = now
            # text_nlp = Text(sentence, "en")
            # text_nlp.preprocess()
            first_day, last_day = cal_past(day, date_format, text_nlp=text_nlp)
            day_out.append([first_day, last_day])
        else:
            day_out.append([sentence])

        index_out.append(idx)
    elif not key:
        en = spacy.load("en")
        doc = en(sentence)
        for ent in doc.ents:
            # print(ent.text, ent.start_char, ent.end_char, ent.label_)
            if ent.label_ == "DATE":
                if "past year" in ent.text:
                    day = cal.nlp("last year")[0][0]
                    first_day, last_day = cal_first_last_day_a_year(day,
                                                                    date_format)
                    day_out.append([first_day, last_day])
                elif "past weeks" in ent.text:
                    day = cal.nlp("last weeks")
                    text_nlp = Text(sentence, "en")
                    text_nlp.preprocess()
                    first_day, last_day = cal_past(day, date_format,
                                                   text_nlp=text_nlp)
                    day_out.append([first_day, last_day])
                else:
                    day_out.append([ent.text])

                index_out.append((ent.start_char, ent.end_char))
        if any("weekday" in token.text for token in doc):
            for token in doc:
                if token.text == "weekday":
                    day_out.append([token.text])
                    index_out.append((sentence.index(token.text),
                                      sentence.index(token.text) + len(
                                          token.text)))

    return day_out.copy(), index_out.copy()


def cal_duration_ner(question):
    en = spacy.load("en")
    doc = en(question)
    day_tmp = list()
    index_tmp = list()
    for ent in doc.ents:
        # print(ent.text, ent.start_char, ent.end_char, ent.label_)
        if ent.label_ == "DATE":
            # print(ent.label_)
            day_tmp.append([ent.text])
            index_tmp.append((ent.start_char, ent.end_char))

    # print("NER DATE: ", day_tmp)

    return day_tmp, index_tmp


def find_specific_date(day, index, day_out, index_out, question, date_tmp,
                       index_tmp):
    DATES_PATTERN = """({ordinal_word})(\\s+)({unit_pattern}|{days_pattern})"""
    DATES_PATTERN = DATES_PATTERN.format(ordinal_word=ordinal_word,
                                         unit_pattern=unit_pattern,
                                         days_pattern=days_pattern)
    DATES_REGEX = re.compile(DATES_PATTERN, re.I)
    # print(DATES_REGEX)
    if date_tmp:
        for tmp in date_tmp:
            kq_lst = list(datefinder.find_dates(tmp[0], index=True))
            matches = DATES_REGEX.search(tmp[0])
            # print("match: ", matches)
            # print("kq lst: ", kq_lst)
            # the format "the second day/week/month of ..."
            if matches and kq_lst:
                day, index = zip(*kq_lst)
                day = day[0]
                index = index[0]
                if day and index:
                    if matches.group(3) == "day":
                        word = matches.group(1)
                        number = mapping[word]
                        day = day.replace(day=number).strftime(date_format)
                if day not in day_out and index not in index_out:
                    day_out.append([day])
                    index_out.append(index)
            # the format "the second of ..."
            elif not matches and kq_lst:
                DATES_PATTERN2 = """({ordinal_word})(\\s+)(of)(\\s+)({
                months_pattern})"""
                DATES_PATTERN2 = DATES_PATTERN2.format(
                    ordinal_word=ordinal_word, months_pattern=months_pattern)
                DATES_REGEX2 = re.compile(DATES_PATTERN2, re.I)
                matches2 = DATES_REGEX2.search(tmp[0])
                if matches2:
                    # print(matches2)
                    # kq_lst2 = datefinder.find_dates(tmp[0], index=True)
                    day, index = zip(*kq_lst)
                    # print(day)
                    day = day[0].strftime(date_format)
                    index = index[0]
                    if day not in day_out and index not in index_out:
                        day_out.append([day])
                        index_out.append(index)
                # the status flag is 1, meaning that it is the DATE
                elif not matches2 and kq_lst:
                    # print("kq lst: ", kq_lst)
                    MONTHS_PATTERN = """({months_pattern})(\\s+)(?P<year>[
                    0-9][0-9][0-9][0-9]|[a-z+])"""
                    MONTHS_PATTERN = MONTHS_PATTERN.format(
                        months_pattern=months_pattern)
                    MONTHS_REGEX = re.compile(MONTHS_PATTERN, re.I)
                    months_matches = MONTHS_REGEX.search(tmp[0])
                    # print(MONTHS_PATTERN)
                    if months_matches:
                        first_day = day.replace(day=1).strftime(date_format)
                        last_day = cal_last_day_a_month(day, date_format)
                        if [first_day, last_day] not in day_out:
                            day_out.append([first_day, last_day])
                            index_out.append(index)
                    else:
                        day, index = zip(*kq_lst)
                        day = day[0].strftime(date_format)
                        index = index[0]
                        if day not in day_out and index not in index_out:
                            day_out.append([day])
                            index_out.append(index)
                # the specific format such as "the 1st sep"
                else:
                    first_day = day.strftime(date_format)
                    last_day = cal_last_day_a_month(day, date_format)
                    if [first_day, last_day] not in day_out:
                        day_out.append([first_day, last_day])
                        index_out.append(index)

            elif not kq_lst:
                first_day = day.strftime(date_format)
                last_day = cal_last_day_a_month(day, date_format)
                if [first_day, last_day] not in day_out:
                    day_out.append([first_day, last_day])
                    index_out.append(index)
    else:
        matches = DATES_REGEX.search(question)
        if matches:
            kq_lst = list(datefinder.find_dates(question, index=True))
            if kq_lst:
                day, index = zip(*kq_lst)
                day = day[0]
                index = index[0]
                if day and index:
                    if matches.group(3) == "day":
                        word = matches.group(1)
                        number = mapping[word]
                        day = day.replace(day=number).strftime(date_format)
                if day not in day_out and index not in index_out:
                    day_out.append([day])
                    index_out.append(index)
        else:
            first_day = day.strftime(date_format)
            last_day = cal_last_day_a_month(day, date_format)
            if [first_day, last_day] not in day_out:
                day_out.append([first_day, last_day])
                index_out.append(index)
    # print("day out o day: ", day_out)

    return day_out.copy(), index_out.copy()


def cal_duration(day, time_phrase, question, day_out, index_out, index):
    text_nlp = Text(time_phrase, "en")
    text_nlp.preprocess()
    # print(text_nlp.lemmas)
    # """detect expressions of weeks"""
    # week_expression = r"
    #     (last|past)\s+([^\s]+)\s+weeks?|
    #     ([^\s]+)\s+weeks?\s+ago
    # "
    # week_pattern = re.compile(week_expression, re.I)
    # print(week_pattern.search(time_phrase))
    day_expr = r"([^\s]+)\s+days?"
    day_regexp = re.compile(day_expr, re.I)
    if "this month" in time_phrase:
        # calculate the first day
        first_day = cal_first_day_a_month(day, date_format)
        last_day = day.strftime(date_format)
        day_out.append([first_day, last_day])
        index_out.append(index)
    elif "last month" in time_phrase:
        # calculate the last day
        first_day = day.strftime(date_format)
        last_day = cal_last_day_a_month(day, date_format)
        day_out.append([first_day, last_day])
        index_out.append(index)
    elif any(item in time_phrase.lower() for item in
             ["last year", "this year", "the past year", "the last year",
              "this year vs last year"]):
        if time_phrase.lower() == "this year vs last year":
            day = cal.nlp("this year")[0][0]
            first_day, last_day = cal_first_last_day_a_year(day, date_format)
            day_out.append([first_day, last_day])
            index_out.append(index)
            day = cal.nlp("last year")[0][0]
            first_day, last_day = cal_first_last_day_a_year(day, date_format)
            day_out.append([first_day, last_day])
            index_out.append(index)
        else:
            first_day, last_day = cal_first_last_day_a_year(day, date_format)
            day_out.append([first_day, last_day])
            index_out.append(index)
    elif any(item in time_phrase for item in ["last week", "this week"]):
        # print(day)
        first_day, last_day = cal_first_last_day_by_week(day, date_format,
                                                         number=1)
        day_out.append([first_day, last_day])
        index_out.append(index)
    elif "a month ago" in time_phrase.lower():
        first_day, last_day = cal_month_ago(day, date_format)
        day_out.append([first_day, last_day])
        index_out.append(index)
    elif "weeks" in time_phrase and "ago" in time_phrase:
        # print("day = ", day)
        first_day, last_day = cal_past(day, date_format, text_nlp)
        day_out.append([first_day, last_day])
        index_out.append(index)
    elif any(word.title() in months_list for word in
             time_phrase.strip().split()):
        day_tmp, index_tmp = cal_duration_ner(question)
        # print(day_tmp)
        # print("test: ", all(word not in time_unit for word in day_tmp))
        if find_specific_date(day, index, day_out, index_out, question,
                              day_tmp, index_tmp) \
                and all(word not in time_unit for word in day_tmp):
            day_out, index_out = find_specific_date(day, index, day_out,
                                                    index_out, question,
                                                    day_tmp, index_tmp)

    elif day_regexp.search(time_phrase):
        day = now
        text_nlp = Text(time_phrase, "en")
        text_nlp.preprocess()
        first_day, last_day = cal_past(day, date_format, text_nlp)
        day_out.append([first_day, last_day])
        index_out.append(index)
    elif time_phrase.strip().title() not in months_list and not day:
        # print("question: ", question)
        # day = day.strftime(date_format)
        day_out.append([time_phrase])
        index_out.append(index)
    # elifcal_duration_ner(question):
    #     print("chay vao day: ", cal_duration_ner(question))
    elif any(item.lower() in time_phrase for item in weekday_list):
        if day > now:
            day = (day - timedelta(days=7)).strftime(date_format)
        else:
            day = day.strftime(date_format)
        day_out.append([day])
        index_out.append(index)
    else:
        day = day.strftime(date_format)
        day_out.append([day])
        index_out.append(index)

    return day_out.copy(), index_out.copy()


"""adding the preposition on the date string"""


def add_prep_date_string(doc, start_idx, phrase):
    # start_token_index = ent.start
    start_token_index = start_idx
    previous_index = start_token_index - 1
    if previous_index >= 0:
        previous_token = doc[previous_index]
        if previous_token.pos_ == "ADP" and previous_token.tag_ == "IN" and \
                previous_token.text not in phrase:
            # date_string = previous_token.text + " " + ent.text
            date_string = previous_token.text + " " + phrase
        else:
            # date_string = ent.text
            date_string = phrase
    else:
        # date_string = ent.text
        date_string = phrase

    return date_string


def get_date_ner_from_spacy(sentence):
    doc = en(sentence)
    date_spacy = list()
    index_spacy = list()
    pattern_format = r'\s+(and|or|than)\s+'
    pattern_re = re.compile(pattern_format, re.I)
    check_first_idx = False
    for ent in doc.ents:
        # print("inside: ", ent.text, ent.label_)
        if ent.label_ == "DATE":
            # print("ent text: ", ent.text)
            index_spacy.append((ent.start_char, ent.end_char))
            # print("index total: ", index_spacy)

            if pattern_re.search(ent.text):
                first_phrase = ent.text[:pattern_re.search(ent.text).start()]
                second_phrase = ent.text[pattern_re.search(ent.text).end():]
                # print("check: ", first_phrase, second_phrase)
                date_string = add_prep_date_string(doc, ent.start,
                                                   first_phrase)
                date_spacy.append(date_string)
                date_string = add_prep_date_string(doc, ent.start,
                                                   second_phrase)
                date_spacy.append(date_string)
            else:
                if not check_first_idx:
                    idx_start = ent.start
                    check_first_idx = True
                date_string = add_prep_date_string(doc, idx_start, ent.text)
                date_spacy.append(date_string)

    return date_spacy, index_spacy


def get_date_from_datefinder_lib(sentence, key):
    date_df = None
    index_df = None
    if key == "spacy":
        date_df = list(datefinder.find_dates(sentence, index=False))
        if date_df:
            date_df = date_df[0]
        return date_df
    elif not key:
        kq = list(datefinder.find_dates(sentence, index=True))
        if kq:
            date_df, index_df = zip(*kq)
            if date_df:
                date_df = date_df

            return date_df, index_df
        else:
            return date_df, index_df


def get_date_from_pdt_lib(sentence, key):
    cal = parsedatetime.Calendar()
    if key == "spacy":
        date_pdt = cal.nlp(sentence)
        if date_pdt:
            for item in date_pdt:
                date_pdt = item[0]
                if date_pdt.year > now.year:
                    date_pdt = date_pdt.replace(year=now.year)
        return date_pdt
    elif not key:
        date_pdt = cal.nlp(sentence)
        date_str = list()
        date_lst = list()
        idx_pdt = list()
        if date_pdt and len(date_pdt) == 2 and all(
                item[1] == 1 for item in date_pdt):
            for item in date_pdt:
                idx_pdt.append((item[2], item[3]))
                date_str.append(item[-1].strip())
                if item[0].year > now.year:
                    date_lst.append(item[0].replace(year=now.year))
        return date_str, date_lst, idx_pdt


def get_date_from_season_period(day_out, index_out, sentence, idx):
    if "spring" in sentence.lower():
        first_day = datetime.date(now.year, 3, 21).strftime(date_format)
        last_day = datetime.date(now.year, 6, 20).strftime(date_format)
    elif "summer" in sentence.lower():
        first_day = datetime.date(now.year, 6, 21).strftime(date_format)
        last_day = datetime.date(now.year, 9, 20).strftime(date_format)
    elif "autumn" in sentence.lower():
        first_day = datetime.date(now.year, 9, 21).strftime(date_format)
        last_day = datetime.date(now.year, 12, 20).strftime(date_format)
    else:
        first_day = datetime.date(now.year - 1, 12, 21).strftime(date_format)
        last_day = datetime.date(now.year, 3, 20).strftime(date_format)
    day_out.append([first_day, last_day])
    index_out.append(idx)

    return day_out, index_out
