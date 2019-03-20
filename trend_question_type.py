"""The script for testing the TREND question type"""
import calendar
import datetime
import pprint
import re

import bson
import pandas as pd
import plotly
import plotly.graph_objs as go

from ipa.frame import Frame, Condition
from ipa.postprocess import connect_db, ipa_columns, tr_fl_lst, date_selection
from modules.calculations import is_existed, check_date_format
import plotly.graph_objs as go

db_v = connect_db()
# print(db_v.count_documents({}))
domain = "brunel.nl"


def get_start_and_end_date_from_calendar_week(year, calendar_week):
    sunday = datetime.datetime.strptime(f'{year}-{calendar_week}-0',
                                        "%Y-%W-%w").date()
    return sunday.strftime("%Y-%m-%d"), (sunday + datetime.timedelta(
        days=6)).strftime("%Y-%m-%d")


def get_mongo_targets_trend(frame, date_rnge):
    # print("date range: ", date_rnge)
    match = dict()
    match["domain"] = domain
    match.update(date_rnge.copy())
    # print(match)

    project = dict()
    project["_id"] = 0
    project["visitorId"] = 1

    if is_existed(frame.conditions, "returningByVisitors"):
        if not date_rnge:
            match["created"] = {"$nin": ["", None]}
        project["created"] = 1
    if any(cond_item.value == ["unrecognized"] for cond_item in
           frame.conditions):
        return None
    elif all(cond_item.value == ["unrecognized"] for cond_item in
             frame.conditions):
        return None
    else:
        for cond_item in frame.conditions:
            if cond_item.target in ipa_columns:
                if cond_item.target == "referralDomain":
                    if cond_item.value != ["unspecified"]:
                        val_lst = list()
                        for val in cond_item.value:
                            if "." not in val:
                                pattern = re.compile("^" + val + "*", re.I)
                                regex = bson.regex.Regex.from_native(pattern)
                                regex.flags ^= re.UNICODE
                                val_lst.append(regex)
                            else:
                                val_lst.append(val)
                        match[cond_item.target] = {"$in": val_lst}
                    project[cond_item.target] = 1
                if cond_item.target == "visitTime" and "unspecified" not in \
                        cond_item.value:
                    match[cond_item.target] = {"$nin": ["", None]}
                    project[cond_item.target] = 1
                elif cond_item.value != [
                    "unspecified"] and cond_item.target != "referralDomain":
                    if len(cond_item.value) > 1:
                        match[cond_item.target] = {"$in": cond_item.value}
                        project[cond_item.target] = 1
                    else:
                        # take the value of target
                        match[cond_item.target] = cond_item.value[0]
                        project[cond_item.target] = 1
                elif cond_item.target in tr_fl_lst:
                    if cond_item.operator == "not":
                        match[cond_item.target] = False
                    else:
                        match[cond_item.target] = True
                    project[cond_item.target] = 1
                else:
                    project[cond_item.target] = 1
    # print("match query: ", match)
    # print("projection: ", project)

    return match


def set_title(entities_default_value):
    title_list = []
    for key in entities_default_value:
        if key not in ['visitorId', 'pageviews', 'session']:
            title_list.append(entities_default_value[key])

    if len(title_list) > 1:
        prefix = "Specifications: "
    elif len(title_list) == 1:
        prefix = "Specification: "
    else:
        prefix = ''

    title = ', '.join([''.join(i) for i in title_list])
    chart_title = prefix + title

    return chart_title


"""set the x-label name corresponding to each different type"""


def set_xlabel(name, df):
    if name == "date":
        xaxis = dict(
            title="Period"
        )
    else:
        tickvals = []
        ticktext = []
        if name == "weekday":
            tickvals = df[name].tolist()
            ticktext = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday",
                        "Friday", "Saturday"]
        elif name == "week":
            df[["first", "last"]] = df[name].apply(lambda row:
                                                   pd.Series(
                                                       get_start_and_end_date_from_calendar_week(
                                                           datetime.datetime.now().year,
                                                           row)))
            tickvals = df[name].tolist()
            # ticktext = [(i, j) for i, j in zip(df["first"].tolist(),
            #                                    df["last"].tolist())]
            ticktext = df["first"].tolist()
        elif name == "month":
            tickvals = df[name].tolist()
            ticktext = [calendar.month_name[i] for i in tickvals]

        xaxis = dict(
            title='Period',
            tickvals=tickvals,
            ticktext=ticktext
        )

    return xaxis


"""detect the limitation on the x-axis (by week, month, day/date, weekday, 
year)"""


def detect_key_to_limit(date, question):
    pattern_weekday = re.compile(r'\bweekday|week day|day of week\b', re.I)
    pattern_week = re.compile(r'\bweek|weekly\b', re.I)
    pattern_month = re.compile(r'\bmonth|monthly\b', re.I)
    pattern_year = re.compile(r'\byear|yearly|annual\b', re.I)

    found_weekday = [pattern_weekday.search(i) for item in date for i in item]
    found_week = [pattern_week.search(i) for item in date for i in item]
    found_month = [pattern_month.search(i) for item in date for i in item]
    found_year = [pattern_year.search(i) for item in date for i in item]

    if found_weekday and all(i not in [None, [], ''] for i in found_weekday)\
            or pattern_weekday.search(question):
        key = "WEEKDAY"
    elif found_week and all(i not in [None, [], ''] for i in found_week) or \
            pattern_week.search(question):
        key = "WEEK"
    elif found_month and all(i not in [None, [], ''] for i in found_month) \
            or pattern_month.search(question):
        key = "MONTH"
    elif found_year and all(i not in [None, [], ''] for i in found_year) or \
            pattern_year.search(question):
        key = "YEAR"
    else:
        key = "DATE"

    return key


def pipeline_struction(key, match, variable, total_pv, total_uvt):
    name = key.lower()
    pipeline = []
    condition = {}

    if key == "WEEKDAY":
        condition = {"$dayOfWeek": "$created"}
    elif key == "WEEK":
        condition = {"$week": "$created"}
    elif key == "MONTH":
        condition = {"$month": "$created"}
    elif key == "YEAR":
        condition = {"$year": "$created"}

    if key == "DATE":
        pipeline = [{"$match": match},
                    {
                        "$project": {
                            "visitorId": "$visitorId",
                            "year": {"$year": "$created"},
                            "month": {"$month": "$created"},
                            "day": {"$dayOfMonth": "$created"}
                        }
                    },
                    {
                        "$group": {
                            "_id": {
                                "year": "$year", "month": "$month",
                                "day": "$day"
                            },
                            "uniqueVisitor": {
                                "$addToSet": "$" + variable
                            },
                            "count_pv": {"$sum": 1}
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            name: {
                                "$dateFromParts": {
                                    "year": "$_id.year", "month": "$_id.month",
                                    "day": "$_id.day"
                                }
                            },
                            "count_pv": 1,
                            "count_uvtID": {"$size": "$uniqueVisitor"},
                            "percentage_pv": {
                                "$concat": [{
                                    "$substr": [
                                        {
                                            "$multiply": [{
                                                "$divide": [
                                                    "$count_pv", {
                                                        "$literal":
                                                            total_pv
                                                    }]
                                            }, 100]
                                        }, 0, 3]
                                }, "",
                                    "%"]
                            },
                            "percentage_uvtID": {
                                "$concat": [{
                                    "$substr": [
                                        {
                                            "$multiply": [{
                                                "$divide": [
                                                    {
                                                        "$size":
                                                            "$uniqueVisitor"
                                                    }, {
                                                        "$literal":
                                                            total_uvt
                                                    }]
                                            }, 100]
                                        }, 0,
                                        3]
                                }, "",
                                    "%"]
                            }
                        }
                    },
                    {"$sort": {name: 1}}]
    else:
        pipeline = [{"$match": match},
                    {
                        "$project": {
                            "visitorId": "$visitorId",
                            name: condition,
                        }
                    },
                    {
                        "$group": {
                            "_id": {
                                name: "$" + name
                            },
                            "uniqueVisitor": {
                                "$addToSet": "$" + variable
                            },
                            "count_pv": {"$sum": 1}
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            name: "$_id." + name,
                            "count_pv": 1,
                            "count_uvtID": {"$size": "$uniqueVisitor"},
                            "percentage_pv": {
                                "$concat": [{
                                    "$substr": [
                                        {
                                            "$multiply": [{
                                                "$divide": [
                                                    "$count_pv", {
                                                        "$literal":
                                                            total_pv
                                                    }]
                                            }, 100]
                                        }, 0, 3]
                                }, "",
                                    "%"]
                            },
                            "percentage_uvtID": {
                                "$concat": [{
                                    "$substr": [
                                        {
                                            "$multiply": [{
                                                "$divide": [
                                                    {
                                                        "$size":
                                                            "$uniqueVisitor"
                                                    }, {
                                                        "$literal":
                                                            total_uvt
                                                    }]
                                            }, 100]
                                        }, 0,
                                        3]
                                }, "",
                                    "%"]
                            }
                        }
                    },
                    {"$sort": {name: 1}}]

    return name, pipeline


def trend_visualization(db_v, frame, match, date_idx,
                        entities_default_value, question):
    print("match query: ", match)
    print("test date: ", frame.date)
    if match:
        total_uvt = len(db_v.distinct("visitorId", match))
        total_pv = db_v.count_documents(match)
    else:
        match = {}
        total_uvt = len(db_v.distinct("visitorId", {}))
        total_pv = db_v.count_documents({})
    # print("The number of total unique visitors satisfied the conditions: ",
    #  total_uvt)
    cond_sp = list(
        filter(lambda x: "unspecified" not in x.value, frame.conditions))
    try:
        variable = list(filter(lambda x: x not in cond_sp, frame.conditions))[
            0].target
    except IndexError:
        variable = "visitorId"
    # print(variable)

    key = detect_key_to_limit(frame.date, question)

    name, pipeline = pipeline_struction(key, match, variable, total_pv,
                                        total_uvt)

    db = list(db_v.aggregate(pipeline=pipeline))
    pprint.pprint(list(db))
    # print(sum(item["count"] for item in list(db)))

    """set the title name"""
    title = set_title(entities_default_value)
    df = pd.DataFrame(db)

    """set the x-axis label"""
    xaxis = set_xlabel(name, df)

    pprint.pprint(df.head())

    """plotting"""
    if any(key == "visitorId" for key, value in
           entities_default_value.items()) or variable == "visitorId":
        data = [go.Bar(
            x=df[name],
            y=df["count_uvtID"],
            # fill='tozeroy'
            # fill='tonexty',
            # line=dict(
            #   color='rgb(30, 100, 300)',
            # )
        )]
    else:
        data = [go.Bar(  # or Scatter, then use following variables too
            x=df[name],
            y=df["count_pv"],
            # fill='tozeroy'
            # fill='tonexty',
            # line=dict(
            #   color='rgb(30, 100, 300)',
            # )
        )]

    if 'pageviews' in entities_default_value and 'visitorId' not in entities_default_value:
        titlename = 'Amount of pageviews'
    elif 'session' in entities_default_value and 'visitorId' not in entities_default_value:
        titlename = 'Amount of sessions'
    else:
        titlename = 'Amount of visitors'

    layout = go.Layout(
        title=title,
        yaxis=dict(
            title=titlename,
        ),
        xaxis=xaxis
    )

    plotly.offline.plot(
        {
            'data': data,
            'layout': layout
        },
        auto_open=True)

    return db



def get_trend_result(frame, entities_default_value, question):
    date_numeric, date_idx = check_date_format(frame.date)
    # print(date_numeric)
    date_range = date_selection(date_numeric)
    # print(date_range)
    match = get_mongo_targets_trend(frame, date_rnge=date_range)
    trend_visualization(db_v, frame, match, date_idx,
                        entities_default_value, question)


if __name__ == "__main__":
    frame = Frame()

    frame.question_type, frame.date, frame.conditions = (
        'TREND', [],
        [Condition(target='visitorId', operator=None, value=['unspecified']),
         Condition(target='cfCountry', operator=None, value=['BE'])])

    get_trend_result(frame, entities_default_value)
