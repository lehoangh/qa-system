'''
The script has some calculations for postprocessing
'''
import re
from collections import Counter
from datetime import timedelta, datetime

import bson
import numpy as np
import pycountry

from modules.get_reference_target import get_reference_target
from modules.session_calculation import get_cal_by_session_by_uvID
from resources.en.value_mapping import mappings

end_idx = -1
tr_fl_lst = ["bounce", "adBlock", "touch", "returningByVisitors"]
# 1 hour converted into milliseconds
HOUR_MILLI = 1000 * 60 * 60
# SESSION_GAP = 2 hours = 2 * 1000 * 60 * 60 (milliseconds)
SESSION_GAP = 2 * HOUR_MILLI

"""check date value is in the format yyyy-mm-dd or not"""


def check_date_format(date):
    pattern = re.compile(r'\d{4}-\d{2}-\d{2}', re.I)
    date_numeric = [[item for item_date in date for item in item_date if
                     pattern.search(item)]]
    idx_date_numeric = list(
        date.index(item_date) for item_date in date for item in item_date if
        pattern.search(item))
    idx_date_numeric = sorted(set(idx_date_numeric),
                              key=lambda k: idx_date_numeric.index(k))
    # print(idx_date_numeric)
    return date_numeric.copy(), idx_date_numeric


"""find the pattern for target values of referralDomain target"""


def find_pattern(pattern, phrase):
    if isinstance(pattern, int):
        return phrase == pattern
    elif isinstance(phrase, int):
        return phrase == int(pattern)
    elif phrase.count(" ") > 0:
        r = re.compile(r'\b%s\b' % pattern, re.I)
        a = r.search(phrase)
        if a:
            return True
    else:
        r = re.compile(r'^%s*' % pattern, re.I)
        a = r.search(phrase)
        if a:
            return phrase


"""convert seconds into minutes"""


def convert_sec_into_min(seconds):
    """convert seconds into minutes and seconds only"""
    minutes = timedelta(seconds=seconds)
    if (datetime(1, 1, 1) + minutes).strftime("%M") == "00":
        if (datetime(1, 1, 1) + minutes).strftime("%S") >= "10":
            minutes = str((datetime(1, 1, 1) + minutes).strftime("%S seconds"))
        else:
            if seconds > 1:
                minutes = str(seconds) + " " + "seconds"
            elif seconds == float(1):
                minutes = str(seconds) + " " + "second"
            else:
                minutes = str(round(seconds, 2)) + " " + "seconds"
    elif (datetime(1, 1, 1) + minutes).strftime("%M%S") < "1010":
        minutes_part = str((datetime(1, 1, 1) + minutes).minute)
        seconds_part = str((datetime(1, 1, 1) + minutes).second)
        if minutes_part > "1" and seconds_part > "1":
            minutes = minutes_part + " minutes and " + seconds_part + " seconds"
        elif minutes_part > "1" and seconds_part == "1":
            minutes = minutes_part + " minutes and " + seconds_part + " second"
        elif minutes_part == "1" and seconds_part > "1":
            minutes = minutes_part + " minute and " + seconds_part + " seconds"
        elif minutes_part == "1" and seconds_part == "1":
            minutes = minutes_part + " minute and " + seconds_part + " seconds"
    elif (datetime(1, 1, 1) + minutes).strftime("%M") > "10" and (
            datetime(1, 1, 1) + minutes).strftime("%S") < "10":
        minutes_part = str((datetime(1, 1, 1) + minutes).minute)
        seconds_part = str((datetime(1, 1, 1) + minutes).second)
        minutes = minutes_part + " minutes and " + seconds_part + " seconds"
    else:
        minutes = (datetime(1, 1, 1) + minutes).strftime(
            "%M minutes and %S seconds")
    return minutes


"""convert seconds into hours"""


def convert_sec_into_hour(seconds):
    """convert seconds into hours and minutes only"""
    hours = timedelta(seconds=seconds)
    if (datetime(1, 1, 1) + hours).strftime("%H") == "00":
        if (datetime(1, 1, 1) + hours).strftime("%M") >= "10":
            hours = str((datetime(1, 1, 1) + hours).strftime("%M minutes"))
        else:
            if seconds > 1:
                hours = str(seconds) + " " + "seconds"
            else:
                hours = str(seconds) + " " + "second"
    elif (datetime(1, 1, 1) + hours).strftime("%H%M") < "1010":
        hours_part = str((datetime(1, 1, 1) + hours).hour)
        minutes_part = str((datetime(1, 1, 1) + hours).minute)
        if hours_part > "1" and minutes_part > "1":
            hours = hours_part + " hours and " + minutes_part + " minutes"
        elif hours_part > "1" and minutes_part == "1":
            hours = hours_part + " hours and " + minutes_part + " minute"
        elif hours_part == "1" and minutes_part > "1":
            hours = hours_part + " hour and " + minutes_part + " minutes"
        elif hours_part == "1" and minutes_part == "1":
            hours = hours_part + " hour and " + minutes_part + " minute"
    elif (datetime(1, 1, 1) + hours).strftime("%H") > "10" and (
            datetime(1, 1, 1) + hours).strftime("%M") < "10":
        hours_part = str((datetime(1, 1, 1) + hours).hour)
        minutes_part = str((datetime(1, 1, 1) + hours).minute)
        hours = hours_part + " hours and " + minutes_part + " minutes"
    else:
        hours = (datetime(1, 1, 1) + hours).strftime("%H hours and %M minutes")
    return hours


"""round function to float number"""


def round_float_perc(number):
    if number == 0:
        return 0
    elif number > 1:
        return round(number, 2)
    else:
        return round(number, 5)


"""getting full name of countries or languages"""


def get_full_name(key, container, target):
    if isinstance(container, dict):
        if key == "cfCountry":
            return {
                target: {pycountry.countries.get(alpha_2=k).name: v for k, v in
                         container[target].items()
                         if k != "XX" and k}
            }
        elif key == "languages":
            return {
                target: {pycountry.languages.get(alpha_2=k).name: v for k, v in
                         container[target].items() if k}
            }
    elif isinstance(container, list):
        if key == "cfCountry":
            # return ", ".join(i for i in [pycountry.countries.get(
            # alpha_2=item).name for item in container
            #                              if item != "XX" and item][:end_idx])
            return [pycountry.countries.get(alpha_2=item).name for item in
                    container if item != "XX" and item][:end_idx]
        elif key == "languages":
            # return ", ".join(i for i in [pycountry.languages.get(
            # alpha_2=item).name for item in container
            #                              if item][:end_idx])
            return [pycountry.languages.get(alpha_2=item).name for item in
                    container if item][:end_idx]

    else:
        if key == "cfCountry":
            if container != "XX" and container:
                return pycountry.countries.get(alpha_2=container).name
        elif key == "languages":
            return pycountry.languages.get(alpha_2=container).name


"""my converter function to store unknown object into JSON file"""


def my_converter_func(o):
    if isinstance(o, datetime):
        return o.__str__()


"""check list of lists is empty or not"""


def is_empty(a):
    return all([is_empty(b) for b in a]) if isinstance(a, list) else False


"""check length of a list of lists"""
"""getting the length of inside lists"""


def length(a):
    c = 0
    for x in a:
        for _ in x:
            c = c + 1
    return c


"""check if targets is existed or not"""


def is_existed(frame_conds, targets_lst):
    return True if any(
        cond.target in targets_lst for cond in frame_conds) else False


"""calculation the general frequency"""


def frequency(key, key_dict):
    try:
        key_dict["count"] += 1
    except KeyError:
        key_dict["count"] = 1

    if key in key_dict:
        key_dict[key] += 1
    else:
        key_dict[key] = 1


"""return the maximum value with corresponding key of a dictionary"""


def key_with_max_val(d, op, target):
    """ a) create a list of the dict's keys and values;
        b) return the key with the max value and max value"""
    if op == "max":
        v = list(d[j] for j in d.keys() if j not in ["count", None])
        k = list(i for i in d.keys() if i not in ["count", None])
        return k[v.index(max(v))], max(v)
    else:
        sorted_d = sorted(
            {k: v for k, v in d.items() if k not in ["count", None]}.items(),
            key=lambda kv: kv[1])
        # print(sorted_d)
        if target == "referralType":
            return list(np.partition(sorted_d, -2)[-2])
        else:
            # print(list(reversed(np.partition(sorted_d, -2)[-2])))
            return list(reversed(np.partition(sorted_d, -2)[-2]))


"""return the minimum value with corresponding key of a dictionary"""


def key_with_min_val(d):
    """ a) create a list of the dict's keys and values;
        b) return the key with the max value and max value"""
    sorted_d = dict(sorted(d.items(), key=lambda kv: kv[1]))
    v = list(sorted_d[j] for j in sorted_d.keys() if j not in ["count", None])
    minimum = min(v)
    indices = [k for k, v in sorted_d.items() if v == minimum]
    return indices, minimum


"""getting the results for "not" operator"""


def key_with_not_op(d):
    for k, v in d.items():
        if k != "count":
            return k, v


"""return the maximum value in quantity form or percentage form"""


def get_quantity_perc(target, d, qtype, total_pv, func):
    elem = None
    if func == "max":
        elem = key_with_max_val(d, func, target)
    elif func == "min":
        elem = key_with_min_val(d)
    elif func == "second":
        elem = key_with_max_val(d, func, target)
    elif func == "not":
        elem = key_with_not_op(d)
    if qtype == "QUANTITY":
        return elem
    elif qtype == "PERC":
        return (
            elem[0], str(round_float_perc(elem[-1] / total_pv * 100)) + "%")
    elif qtype == "CATEGORY":
        if target in ["cfCountry", "languages"]:
            return get_full_name(key=target, container=elem[0], target=None)
        elif target == "referralType":
            if isinstance(elem[0], list) and len(elem[0]) == 1:
                return mappings[target][elem[0][0]][0].lower()
            elif len(elem) == 2:
                return mappings[target][elem[0]][0].lower()
            else:
                return [mappings[target][i][0].lower() for i in
                        elem[0][:end_idx]]
        else:
            # for checking the `second` operator
            if len(elem) == 2:
                if func == "second":
                    return elem[0]
                else:
                    return "".join(elem[0]) if len(elem[0]) == 1 else elem[0]
            else:
                # only take 3 first element
                return elem[0][:end_idx]
    elif qtype == "yes/no":
        # print("target: ", target)
        sorted_d = sorted(d.items(), key=lambda kv: kv[1], reverse=True)
        # print("sorted_d: ", sorted_d)
        # print(sum(i[1] for i in sorted_d))
        check_lst = list(
            map(lambda x: str(x[0]) == str(target.value[0]), sorted_d))
        # print("check flag: ", check_lst)
        if target.target in ["cfCountry", "languages"]:
            name = get_full_name(target.target, target.value[0], None)
        elif target.target == "referralType":
            name = mappings[target.target][target.value[0]][0]
        else:
            name = target.value[0]
        if target.target in tr_fl_lst:
            # binary valued target
            if name == "unspecified":
                name = "True"
                if func in ["max", ">=", ">"]:
                    return (
                        round_float_perc(sorted_d[0][1] / total_pv * 100) > 50,
                        name, target.target,
                        str(round_float_perc(
                            sorted_d[0][1] / total_pv * 100)) + "%")
                elif func in ["min", "<", "<="]:
                    return (
                        round_float_perc(sorted_d[0][1] / total_pv * 100) < 50,
                        name, target.target,
                        str(round_float_perc(
                            sorted_d[0][1] / total_pv * 100)) + "%")
            else:
                if func in ["max", ">", ">="]:
                    return (
                        round_float_perc(sorted_d[0][1] / total_pv * 100) > 50,
                        name, target.target,
                        str(round_float_perc(
                            sorted_d[0][1] / total_pv * 100)) + "%")
                elif func in ["min", "<", "<="]:
                    return (
                        round_float_perc(sorted_d[0][1] / total_pv * 100) < 50,
                        name, target.target,
                        str(round_float_perc(
                            sorted_d[0][1] / total_pv * 100)) + "%")
        else:
            try:
                # ranking order
                if func == "max":
                    return (
                        check_lst.index(True) == 0, check_lst.index(True) + 1,
                        name, target.target)
                    # str(round_float_perc(d[target.value[0]]/total_pv *
                    # 100)) + "%")
                elif func == "min":
                    return (
                        check_lst.index(True) == sorted_d.index(sorted_d[-1]),
                        check_lst.index(True) + 1, name, target.target)
                    # str(round_float_perc(d[target.value[0]]/total_pv *
                    # 100)) + "%")
                elif func == "second":
                    return (
                        check_lst.index(True) == 1, check_lst.index(True) + 1,
                        name, target.target)
                elif func in [">", ">="]:
                    # always default is compare with 50%
                    # print("test: ", sorted_d[check_lst.index(True)])
                    return (round_float_perc(sorted_d[check_lst.index(True)][
                                                 1] / total_pv * 100) > 50,
                            name, target.target,
                            str(round_float_perc(
                                sorted_d[check_lst.index(True)][
                                    1] / total_pv * 100)) + "%")
                elif func in ["<", "<="]:
                    # always default is compare with 50%
                    return (round_float_perc(sorted_d[check_lst.index(True)][
                                                 1] / total_pv * 100) < 50,
                            name, target.target,
                            str(round_float_perc(
                                sorted_d[check_lst.index(True)][
                                    1] / total_pv * 100)) + "%")
            except ValueError:
                return None


"""get the new dictionary of returningByVisitor"""


def get_returning(lst):
    for item in lst:
        duration = max(item["created"]) - min(item["created"])
        if duration >= timedelta(hours=2):
            item["returningByVisitors"] = "True"
        else:
            item["returningByVisitors"] = "False"
    return lst


"""getting the results depending on pagesPerVisitors or visitTime for two 
qtype MEDIAN and AVERAGE"""


def get_results_format(numbers, target, func):
    if func == "MEDIAN":
        if target == "visitTime":
            return convert_sec_into_min(np.median(numbers))
        else:
            return round_float_perc(np.median(numbers))
    elif func == "AVERAGE":
        if target == "visitTime":
            return convert_sec_into_min(np.average(numbers))
        else:
            return round_float_perc(np.average(numbers))
    else:
        return numbers


"""calculate the number of unique visitors with the conditions of visitTime"""


def get_number_uvt_vt(db_v, domain, date_range, match, op, key):
    # match = date_range.copy()
    # match.update({"domain": domain})
    pipeline = []
    if key == "visitTime":
        pipeline = [{"$match": match},
                    {
                        "$group": {
                            "_id": "$visitorId",
                            "totalVisitTime": {"$sum": "$visitTime"}
                        }
                    },
                    {"$match": {"totalVisitTime": op}},
                    {
                        "$group": {
                            "_id": None, "total": {"$sum": 1}, "details": {
                                "$push": {
                                    "groupby": "$_id",
                                    "sumVT": "$totalVisitTime"
                                }
                            }
                        }
                    },
                    {"$project": {"_id": 0, "total": 1}}]
    elif key == "pagesPerVisitor":
        pipeline = [{"$match": match},
                    {
                        "$group": {
                            "_id": "$visitorId",
                            "totalPagesPerVisitor": {"$sum": 1}
                        }
                    },
                    {"$match": {"totalPagesPerVisitor": op}},
                    {
                        "$group": {
                            "_id": None, "total": {"$sum": 1},
                            "details": {
                                "$push": {
                                    "groupby": "$_id",
                                    "sumPPVT": "$totalPagesPerVisitor"
                                }
                            }
                        }
                    },
                    {"$project": {"_id": 0, "total": 1}}]
    elif key == "returningByVisitors":
        pipeline = [{"$match": match},
                    {
                        "$group": {
                            "_id": "$visitorId",
                            "totalCreatedList": {"$push": "$created"}
                        }
                    },
                    {
                        "$project": {
                            "_id": 1,
                            "min_value": {"$min": "$totalCreatedList"},
                            "max_value": {"$max": "$totalCreatedList"}
                        }
                    },
                    {
                        "$project": {
                            "_id": 1,
                            "diff": {"$subtract": ["$max_value", "$min_value"]}
                        }
                    },
                    {
                        "$project": {
                            "_id": 1,
                            "diff_by_hours": {"$divide": ["$diff", HOUR_MILLI]}
                        }
                    },
                    {"$match": {"diff_by_hours": op}},
                    {"$group": {"_id": None, "total": {"$sum": 1}}},
                    {"$project": {"_id": 0, "total": 1}}]
    db_vt = db_v.aggregate(pipeline)
    # pprint.pprint(list(db_vt))
    try:
        total = list(db_vt)[0]["total"]
    except IndexError:
        total = 0
    # print("total: ", total)
    return total


def get_session(db_v, domain, date_range, match, unique_vt, qtype, question,
                frame):
    group = {
        "_id": "$visitorId",
        "details": {
            "$push": {
                "created": "$created",
            }
        }
    }
    project = {
        "_id": 1,
        "details": 1
    }

    pipeline = [{"$match": match},
                {"$group": group},
                {"$project": project},
                {
                    "$unwind": {
                        "path": "$details",
                        "includeArrayIndex": "arrayIndex"
                    }
                },
                {
                    "$group": {
                        "_id": "$_id",
                        "time_series": {
                            "$push": {
                                "value": "$details.created",
                                "index": "$arrayIndex",
                            }
                        }
                    }
                },
                {
                    "$project": {
                        "session_idx":
                            {
                                "$map": {
                                    "input": "$time_series",
                                    "as": "el",
                                    "in":
                                        {
                                            "$cond": [{
                                                "$gte": [{
                                                    "$abs":
                                                        {
                                                            "$subtract": [
                                                                "$$el.value",
                                                                {
                                                                    "$let": {
                                                                        "vars": {
                                                                            "nextElement": {
                                                                                "$arrayElemAt": [
                                                                                    "$time_series",
                                                                                    {
                                                                                        "$add": [
                                                                                            "$$el.index",
                                                                                            1]
                                                                                    }]
                                                                            }
                                                                        },
                                                                        "in": "$$nextElement.value"
                                                                    }
                                                                }]
                                                        }
                                                },
                                                    SESSION_GAP]
                                            },
                                                "$$el.index", -1]
                                        }
                                }
                            }
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "vID": "$_id",
                            "session": "$session_idx"
                        }
                    }
                },
                {"$project": {"_id": 1, "session": 1}},
                {
                    "$project": {
                        "_id.vID": 1,
                        "number_of_session": {
                            "$add": [{
                                "$size": {
                                    "$filter": {
                                        "input": "$_id.session",
                                        "as": "index",
                                        "cond": {"$gte": ["$$index", 0]}
                                    }
                                }
                            }, 1]
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None, "total_session": {
                            "$sum":
                                "$number_of_session"
                        }, "returners": {
                            "$push": {
                                "$gt": [
                                    "$number_of_session", 1]
                            }
                        }
                    }
                },
                {
                    "$project": {
                        "_id": 0, "total_session": 1,
                        "total_returners": {
                            "$size": {
                                "$filter": {
                                    "input": "$returners",
                                    "as": "item",
                                    "cond": {"$eq": ["$$item", True]}
                                }
                            }
                        }
                    }
                }]

    db_sess = db_v.aggregate(pipeline, allowDiskUse=True)

    if qtype == "QUANTITY":
        return list(db_sess)[0]["total_session"]
    elif qtype == "PERC":
        rnge = date_range.copy()
        rnge.update({"domain": domain})
        pipeline_tot = [{"$match": rnge},
                        {"$group": group},
                        {"$project": project},
                        {
                            "$unwind": {
                                "path": "$details",
                                "includeArrayIndex": "arrayIndex"
                            }
                        },
                        {
                            "$group": {
                                "_id": "$_id",
                                "time_series": {
                                    "$push": {
                                        "value": "$details.created",
                                        "index": "$arrayIndex",
                                    }
                                }
                            }
                        },
                        {
                            "$project": {
                                "session_idx":
                                    {
                                        "$map": {
                                            "input": "$time_series",
                                            "as": "el",
                                            "in":
                                                {
                                                    "$cond": [{
                                                        "$gte": [{
                                                            "$abs":
                                                                {
                                                                    "$subtract": [
                                                                        "$$el.value",
                                                                        {
                                                                            "$let": {
                                                                                "vars": {
                                                                                    "nextElement": {
                                                                                        "$arrayElemAt": [
                                                                                            "$time_series",
                                                                                            {
                                                                                                "$add": [
                                                                                                    "$$el.index",
                                                                                                    1]
                                                                                            }]
                                                                                    }
                                                                                },
                                                                                "in": "$$nextElement.value"
                                                                            }
                                                                        }]
                                                                }
                                                        },
                                                            SESSION_GAP]
                                                    },
                                                        "$$el.index", -1]
                                                }
                                        }
                                    }
                            }
                        },
                        {
                            "$group": {
                                "_id": {
                                    "vID": "$_id",
                                    "session": "$session_idx"
                                }
                            }
                        },
                        {"$project": {"_id": 1, "session": 1}},
                        {
                            "$project": {
                                "_id.vID": 1,
                                "number_of_session": {
                                    "$add": [{
                                        "$size": {
                                            "$filter": {
                                                "input": "$_id.session",
                                                "as": "index",
                                                "cond": {
                                                    "$gte": ["$$index", 0]
                                                }
                                            }
                                        }
                                    }, 1]
                                }
                            }
                        },
                        {
                            "$group": {
                                "_id": None, "total_session": {
                                    "$sum":
                                        "$number_of_session"
                                }, "returners": {
                                    "$push": {
                                        "$gt": [
                                            "$number_of_session", 1]
                                    }
                                }
                            }
                        },
                        {
                            "$project": {
                                "_id": 0, "total_session": 1,
                                "total_returners": {
                                    "$size": {
                                        "$filter": {
                                            "input": "$returners",
                                            "as": "item",
                                            "cond": {"$eq": ["$$item", True]}
                                        }
                                    }
                                }
                            }
                        }]

        total_session_tot = list(db_v.aggregate(pipeline_tot,
                                                allowDiskUse=True))[0][
            "total_session"]
        total_session_cond = list(db_sess)[0]["total_session"]
        return str(round_float_perc(total_session_cond / total_session_tot *
                                    100)) + "%"
    elif qtype == "COMPARISON":
        return list(db_sess)[0]["total_session"]
    elif qtype == "AVERAGE":
        if all(x.target in ["visitorId", "session"] for x in frame.conditions):
            return round_float_perc(list(db_sess)[0]["total_session"] /
                                    unique_vt)
        elif all(x.target in ["pageviews", "session"] for x in
                 frame.conditions):
            rnge = date_range.copy()
            rnge.update({"domain": domain})
            total_pv = db_v.count_documents(rnge)
            return round_float_perc(
                total_pv / list(db_sess)[0]["total_session"])


"""take the database of visit time / pages per visitor based on session, 
2-hour gap"""


def get_vt_ppv_by_session(db_v, domain, date_range, match, field, unique_vt,
                          qtype, question, frame):
    if field == "visitTime":
        match.update({field: {"$exists": True, "$nin": ["", None]}})
    match.update({"created": {"$exists": True, "$nin": ["", None]}})
    group = {}
    project = {}
    session_result = None

    if field == "session":
        session_result = get_session(db_v, domain, date_range, match,
                                     unique_vt, qtype, question, frame)
    else:
        if field == "visitTime":
            group = {
                "_id": "$visitorId",
                "details": {
                    "$push": {
                        "created": "$created",
                        field: "$" + field
                    }
                }
            }
            project = {
                "_id": 1,
                "details": 1
            }
        elif field in ["pagesPerVisitor", "pageviews"]:
            group = {
                "_id": "$visitorId",
                "details": {
                    "$push": {
                        "created": "$created",
                        field: {"$sum": 1}
                    }
                }
            }
            project = {
                "_id": 1,
                "details": 1
            }

        variable = "$details." + field

        pipeline = [{"$match": match},
                    {"$group": group},
                    {"$project": project},
                    {
                        "$unwind": {
                            "path": "$details",
                            "includeArrayIndex": "arrayIndex"
                        }
                    },
                    {
                        "$group": {
                            "_id": "$_id",
                            "time_series": {
                                "$push": {
                                    "value": "$details.created",
                                    "index": "$arrayIndex",
                                    "field": variable
                                }
                            }
                        }
                    },
                    {
                        "$project": {
                            "time_series.field": 1,
                            "session_idx":
                                {
                                    "$map": {
                                        "input": "$time_series",
                                        "as": "el",
                                        "in":
                                            {
                                                "$cond": [{
                                                    "$gte": [{
                                                        "$abs":
                                                            {
                                                                "$subtract": [
                                                                    "$$el.value",
                                                                    {
                                                                        "$let": {
                                                                            "vars": {
                                                                                "nextElement": {
                                                                                    "$arrayElemAt": [
                                                                                        "$time_series",
                                                                                        {
                                                                                            "$add": [
                                                                                                "$$el.index",
                                                                                                1]
                                                                                        }]
                                                                                }
                                                                            },
                                                                            "in": "$$nextElement.value"
                                                                        }
                                                                    }]
                                                            }
                                                    },
                                                        SESSION_GAP]
                                                },
                                                    "$$el.index", -1]
                                            }
                                    }
                                }
                        }
                    },
                    {
                        "$group": {
                            "_id": "$_id", "details": {
                                "$push": {
                                    "visitTime": "$time_series.field",
                                    "session_idx": "$session_idx"
                                }
                            }
                        }
                    },
                    {"$project": {"_id": 1, "details": 1}}]

        # print(pipeline)
        db_vt = db_v.aggregate(pipeline, allowDiskUse=True)
        # pprint.pprint(list(db_vt))
        session_result = get_cal_by_session_by_uvID(db_vt, unique_vt, qtype)

    return session_result


"""check visitTime or pagesPerVisitor in total or in session"""


def check_in_total_in_session(phrase):
    found_total = find_pattern(pattern="total|alltime|all time|sum",
                               phrase=phrase)
    if found_total:
        return "TOTAL"
    else:
        found_session = find_pattern(pattern="session|sesion|browser",
                                     phrase=phrase)
        if found_session:
            return "SESSION"

    return None


"""return the special case: visitTime, pagesPerVisitor, pageviews"""


def get_vt_ppv(question, entities_before_mapping, db_v, domain, date_range,
               match, key, qtype, total_pv, unique_visitor_lst, total_doc,
               total_uvt, check_pv, frame):
    if not total_uvt:
        total_uvt = len(db_v.distinct("visitorId"))
    if key.target == "session":
        return get_vt_ppv_by_session(db_v, domain, date_range, match,
                                     key.target, total_uvt, qtype, question,
                                     frame)
    elif key.target == "pageviews":
        check = check_in_total_in_session(phrase=question)
        if check and check == "SESSION":
            by_session = get_vt_ppv_by_session(db_v, domain, date_range, match,
                                               key.target, total_uvt, qtype,
                                               question, frame)
            if qtype in ["QUANTITY", "CATEGORY"]:
                return get_results_format(by_session, key.target, "AVERAGE")
            elif qtype == "PERC":
                return str(round_float_perc(by_session)) + "%"
            else:
                return get_results_format(by_session, key.target, qtype)
        elif check and check == "TOTAL":
            numbers = [sum(x["_id"]["pagesPerVisitor"]) for x in
                       unique_visitor_lst]
            if qtype in ["MEDIAN", "AVERAGE"]:
                return get_results_format(numbers, key.target, qtype)
            elif qtype == "QUANTITY":
                if entities_before_mapping.get("visitorId"):
                    return get_results_format(numbers, key.target, "AVERAGE")
                else:
                    return total_pv
            elif qtype == "PERC":
                return str(round_float_perc(
                    total_pv / total_doc * 100)) + "%" if total_doc else None
            else:
                return get_results_format(numbers, key.target, "AVERAGE")
        else:
            numbers = [sum(x["_id"]["pagesPerVisitor"]) for x in
                       unique_visitor_lst]
            by_session = get_vt_ppv_by_session(db_v, domain, date_range, match,
                                               key.target, total_uvt, qtype,
                                               question, frame)
            if qtype in ["MEDIAN", "AVERAGE"]:
                return (
                    {"total": get_results_format(numbers, key.target, qtype)},
                    {
                        "session": get_results_format(by_session, key.target,
                                                      qtype)
                    },
                    "unspecified")
            elif qtype == "QUANTITY":
                if entities_before_mapping.get("visitorId"):
                    return ({
                                "total": get_results_format(numbers,
                                                            key.target,
                                                            "AVERAGE")
                            },
                            {
                                "session": get_results_format(by_session,
                                                              key.target,
                                                              "AVERAGE")
                            }, "unspecified")
                else:
                    return total_pv
            elif qtype == "PERC":
                return ({
                            "total": str(round_float_perc(
                                total_pv / total_doc * 100)) + "%" if
                            total_doc else None
                        },
                        {"session": str(round_float_perc(by_session)) + "%"},
                        "unspecified")
            else:
                return (
                    {
                        "total": get_results_format(numbers, key.target,
                                                    "AVERAGE")
                    },
                    {
                        "session": get_results_format(
                            get_vt_ppv_by_session(db_v, domain, date_range,
                                                  match, key.target, total_uvt,
                                                  "AVERAGE", question, frame),
                            key.target, "AVERAGE")
                    },
                    "unspecified")

    elif key.target == "returningByVisitors":
        if qtype == "QUANTITY":
            return len(list(filter(lambda x: x[key.target] == key.value[0],
                                   unique_visitor_lst)))
        elif qtype == "PERC":
            refer_target = get_reference_target(question,
                                                entities_before_mapping)
            if refer_target == key.target:
                if key.value[0] == "True":
                    op = {"$gte": 2}
                else:
                    op = {"$lt": 2}
                total_uvt_cond = get_number_uvt_vt(db_v, domain, date_range,
                                                   match, op, refer_target)
                return str(round_float_perc(
                    len(list(filter(lambda x: x[key.target] == key.value[0],
                                    unique_visitor_lst))) / total_uvt_cond *
                    100)) + "%"
            else:
                return str(round_float_perc(
                    len(list(filter(lambda x: x[key.target] == key.value[0],
                                    unique_visitor_lst))) / total_uvt *
                    100)) + "%"
        elif qtype in ["MEDIAN", "AVERAGE"]:
            if check_pv == "pageviews":
                filtered_lst = list(
                    filter(lambda x: x[key.target] == key.value[0],
                           unique_visitor_lst))
                numbers = [x["pagesPerVisitor"] for x in filtered_lst]
                return get_results_format(numbers, check_pv, qtype)
    else:
        if key.operator == "<" and len(key.value) == 1:
            if qtype == "QUANTITY":
                # use a convert function in here
                return len(list(
                    filter(lambda x: sum(x["_id"][key.target]) < int(key.value[
                                                                         0]),
                           unique_visitor_lst)))
            elif qtype == "PERC":
                refer_target = get_reference_target(question,
                                                    entities_before_mapping)
                op = {"$lt": int(key.value[0])}
                if refer_target == key.target:
                    total_uvt_cond = get_number_uvt_vt(db_v, domain,
                                                       date_range, op,
                                                       refer_target)
                    return str(round_float_perc(len(list(
                        filter(lambda x: sum(x["_id"][key.target]) < int(
                            key.value[0]),
                               unique_visitor_lst))) / total_uvt_cond *
                                                100)) + "%"
                else:
                    return str(round_float_perc(len(list(
                        filter(lambda x: sum(x["_id"][key.target]) < int(
                            key.value[0]),
                               unique_visitor_lst))) / len(
                        unique_visitor_lst) * 100)) + "%"
            elif qtype == "CATEGORY":
                return list(filter(lambda x: sum(x["_id"][key.target]) < int(
                    key.value[0]),
                                   unique_visitor_lst))
            elif qtype in ["MEDIAN", "AVERAGE"]:
                if check_pv == "pageviews":
                    filtered_lst = list(
                        filter(lambda x: sum(x["_id"][key.target]) < int(
                            key.value[0]),
                               unique_visitor_lst))
                    numbers = [sum(x["_id"]["pagesPerVisitor"]) for x in
                               filtered_lst]
                    return get_results_format(numbers, check_pv, qtype)
                else:
                    numbers = [sum(x["_id"][key.target]) for x in list(
                        filter(
                            lambda x: x["_id"][key.target] < int(key.value[0]),
                            unique_visitor_lst))]
                    return get_results_format(numbers, key.target, qtype)
            elif qtype == "COMPARISON":
                k_dct = key.operator + key.value[0]
                return {
                    k_dct: str(round_float_perc(len(list(
                        filter(lambda x: sum(x["_id"][key.target]) < int(
                            key.value[0]),
                               unique_visitor_lst))) / len(
                        unique_visitor_lst) * 100)) + "%"
                }

        elif key.operator == "<=" and len(key.value) == 1:
            if qtype == "QUANTITY":
                return len(list(
                    filter(lambda x: sum(x["_id"][key.target]) <= int(
                        key.value[0]),
                           unique_visitor_lst)))
            elif qtype == "PERC":
                refer_target = get_reference_target(question,
                                                    entities_before_mapping)
                op = {"$lte": int(key.value[0])}
                if refer_target == key.target:
                    total_uvt_cond = get_number_uvt_vt(db_v, domain,
                                                       date_range, op,
                                                       refer_target)
                    return str(round_float_perc(len(list(
                        filter(lambda x: sum(x["_id"][key.target]) <= int(
                            key.value[0]),
                               unique_visitor_lst))) / total_uvt_cond *
                                                100)) + "%"
                else:
                    return str(round_float_perc(len(list(
                        filter(lambda x: sum(x["_id"][key.target]) <= int(
                            key.value[0]),
                               unique_visitor_lst))) / len(
                        unique_visitor_lst) * 100, 2)) + "%"
            elif qtype == "CATEGORY":
                return list(
                    filter(lambda x: sum(x["_id"][key.target]) <= int(
                        key.value[0]),
                           unique_visitor_lst))
            elif qtype in ["MEDIAN", "AVERAGE"]:
                if check_pv == "pageviews":
                    filtered_lst = list(
                        filter(lambda x: sum(x["_id"][key.target]) <= int(
                            key.value[0]),
                               unique_visitor_lst))
                    numbers = [x["pagesPerVisitor"] for x in filtered_lst]
                    return get_results_format(numbers, check_pv, qtype)
                else:
                    numbers = [x[key.target] for x in list(
                        filter(lambda x: sum(x["_id"][key.target]) <= int(
                            key.value[0]),
                               unique_visitor_lst))]
                    return get_results_format(numbers, key.target, qtype)
            elif qtype == "COMPARISON":
                k_dct = key.operator + key.value[0]
                return {
                    k_dct: str(round_float_perc(len(list(
                        filter(lambda x: sum(x["_id"][key.target]) <= int(
                            key.value[0]),
                               unique_visitor_lst))) / len(
                        unique_visitor_lst) * 100)) + "%"
                }

        elif key.operator == ">" and len(key.value) == 1:
            if qtype == "QUANTITY":
                return len(list(
                    filter(lambda x: sum(x["_id"][key.target]) > int(key.value[
                                                                         0]),
                           unique_visitor_lst)))
            elif qtype == "PERC":
                refer_target = get_reference_target(question,
                                                    entities_before_mapping)
                op = {"$gt": int(key.value[0])}
                if refer_target == key.target:
                    total_uvt_cond = get_number_uvt_vt(db_v, domain,
                                                       date_range, op,
                                                       refer_target)
                    return str(round_float_perc(len(list(
                        filter(lambda x: sum(x["_id"][key.target]) > int(
                            key.value[0]),
                               unique_visitor_lst))) / total_uvt_cond *
                                                100)) + "%"
                else:
                    return str(round_float_perc(len(list(
                        filter(lambda x: sum(x["_id"][key.target]) > int(
                            key.value[0]),
                               unique_visitor_lst))) / len(
                        unique_visitor_lst) * 100)) + "%"
            elif qtype == "CATEGORY":
                return list(filter(lambda x: sum(x["_id"][key.target]) > int(
                    key.value[0]),
                                   unique_visitor_lst))
            elif qtype in ["MEDIAN", "AVERAGE"]:
                if check_pv == "pageviews":
                    filtered_lst = list(
                        filter(lambda x: sum(x["_id"][key.target]) > int(
                            key.value[0]),
                               unique_visitor_lst))
                    numbers = [x["pagesPerVisitor"] for x in filtered_lst]
                    return get_results_format(numbers, check_pv, qtype)
                else:
                    numbers = [x[key.target] for x in list(
                        filter(lambda x: sum(x["_id"][key.target]) > int(
                            key.value[0]),
                               unique_visitor_lst))]
                    return get_results_format(numbers, key.target, qtype)
            elif qtype == "COMPARISON":
                k_dct = key.operator + key.value[0]
                return {
                    k_dct: str(round_float_perc(len(list(
                        filter(lambda x: sum(x["_id"][key.target]) > int(
                            key.value[0]),
                               unique_visitor_lst))) / len(
                        unique_visitor_lst) * 100)) + "%"
                }

        elif key.operator == ">=" and len(key.value) == 1:
            if qtype == "QUANTITY":
                return len(list(
                    filter(lambda x: sum(x["_id"][key.target]) >= int(
                        key.value[0]),
                           unique_visitor_lst)))
            elif qtype == "PERC":
                refer_target = get_reference_target(question,
                                                    entities_before_mapping)
                op = {"$gte": int(key.value[0])}
                if refer_target == key.target:
                    total_uvt_cond = get_number_uvt_vt(db_v, domain,
                                                       date_range, op,
                                                       refer_target)
                    return str(round_float_perc(len(list(
                        filter(lambda x: sum(x["_id"][key.target]) >= int(
                            key.value[0]),
                               unique_visitor_lst))) / total_uvt_cond *
                                                100)) + "%"
                else:
                    return str(round_float_perc(len(list(
                        filter(lambda x: sum(x["_id"][key.target]) >= int(
                            key.value[0]),
                               unique_visitor_lst))) / len(
                        unique_visitor_lst) * 100)) + "%"
            elif qtype == "CATEGORY":
                return list(
                    filter(lambda x: sum(x["_id"][key.target]) >= int(
                        key.value[0]),
                           unique_visitor_lst))
            elif qtype in ["MEDIAN", "AVERAGE"]:
                if check_pv == "pageviews":
                    filtered_lst = list(
                        filter(lambda x: sum(x["_id"][key.target]) >= int(
                            key.value[0]),
                               unique_visitor_lst))
                    numbers = [sum(x["_id"]["pagesPerVisitor"]) for x in
                               filtered_lst]
                    return get_results_format(numbers, check_pv, qtype)
                else:
                    numbers = [sum(x["_id"][key.target]) for x in list(
                        filter(lambda x: int(key.value[0]) <= sum(x["_id"][
                                                                      key.target]) <=
                                         int(key.value[1]),
                               unique_visitor_lst))]
                    return get_results_format(numbers, key.target, qtype)
            elif qtype == "COMPARISON":
                k_dct = key.operator + key.value[0]
                return {
                    k_dct: str(round_float_perc(len(list(
                        filter(lambda x: sum(x["_id"][key.target]) <= int(
                            key.value[0]),
                               unique_visitor_lst))) / len(
                        unique_visitor_lst) * 100)) + "%"
                }

        elif len(key.value) == 1 and key.value[0] != "unspecified":
            if qtype == "QUANTITY":
                return len(list(
                    filter(lambda x: x["_id"][key.target] == int(key.value[0]),
                           unique_visitor_lst)))
            elif qtype == "PERC":
                refer_target = get_reference_target(question,
                                                    entities_before_mapping)
                op = {"$eq": int(key.value[0])}
                if refer_target == key.target:
                    total_uvt_cond = get_number_uvt_vt(db_v, domain,
                                                       date_range, match, op,
                                                       refer_target)
                    return str(round_float_perc(len(list(
                        filter(lambda x: x["_id"][key.target] == int(
                            key.value[0]),
                               unique_visitor_lst))) / total_uvt_cond *
                                                100)) + "%"
                # elif refer_target:
                #     total_uvt_cond = get_number_uvt_vt(db_v, domain,
                #                                        date_range, match, op,
                #                                        key.target)
                #     return str(round_float_perc(len(list(
                #         filter(lambda x: x[key.target] == int(key.value[0]),
                #                unique_visitor_lst))) / total_uvt_cond *
                #                                 100)) + "%" if \
                #         total_uvt_cond > 0 else str(float(0)) + "%"
                else:
                    return str(round_float_perc(len(list(
                        filter(lambda x: x["_id"][key.target] == int(
                            key.value[0]),
                               unique_visitor_lst))) / len(
                        unique_visitor_lst) * 100)) + "%"
            elif qtype == "CATEGORY":
                return list(
                    filter(lambda x: x["_id"][key.target] == int(key.value[0]),
                           unique_visitor_lst))
            elif qtype in ["MEDIAN", "AVERAGE"]:
                if check_pv == "pageviews" and key.value != ["unspecified"]:
                    filtered_lst = list(
                        filter(lambda x: x["_id"][key.target] == int(
                            key.value[0]),
                               unique_visitor_lst))
                    numbers = [x["pagesPerVisitor"] for x in filtered_lst]
                    return get_results_format(numbers, check_pv, qtype)
                else:
                    if key.value == ["unspecified"]:
                        numbers = [x["_id"][key.target] for x in
                                   unique_visitor_lst]
                    else:
                        numbers = [x["_id"][key.target] for x in list(filter(
                            lambda x: x["_id"][key.target] == int(
                                key.value[0]),
                            unique_visitor_lst))]
                    return get_results_format(numbers, key.target, qtype)

        elif len(key.value) == 2 and qtype not in ["COMPARISON", "yes/no"]:
            if qtype == "QUANTITY":
                return len(list(filter(
                    lambda x: min(list(map(int, key.value))) <= sum(
                        x["_id"][key.target])
                              <= max(list(map(int, key.value))),
                    unique_visitor_lst)))
            elif qtype == "PERC":
                refer_target = get_reference_target(question,
                                                    entities_before_mapping)
                op = {
                    "$gte": min(list(map(int, key.value))),
                    "$lte": max(list(map(int, key.value)))
                }
                if refer_target == key.target:
                    total_uvt_cond = get_number_uvt_vt(db_v, domain,
                                                       date_range, op,
                                                       refer_target)
                    return str(
                        round_float_perc(len(list(filter(
                            lambda x: min(list(map(int, key.value))) <= sum(
                                x["_id"][key.target])
                                      <= max(list(map(int, key.value))),
                            unique_visitor_lst))) / total_uvt_cond * 100)) + \
                           "%"
                else:
                    return str(round_float_perc(len(list(filter(
                        lambda x: min(list(map(int, key.value))) <= sum(x[
                                                                            "_id"][
                                                                            key.target])
                                  <= max(list(map(int, key.value))),
                        unique_visitor_lst))) / total_pv * 100)) + "%"
            elif qtype == "CATEGORY":
                return list(filter(
                    lambda x: min(list(map(int, key.value))) <= sum(x["_id"][
                                                                        key.target]) <=
                              max(list(map(int, key.value))),
                    unique_visitor_lst))
            elif qtype in ["MEDIAN", "AVERAGE"]:
                if check_pv == "pageviews":
                    filtered_lst = list(filter(
                        lambda x: min(list(map(int, key.value))) <= sum(x[
                                                                            "_id"][
                                                                            key.target]) <=
                                  max(list(map(int, key.value))),
                        unique_visitor_lst))
                    numbers = [sum(x["_id"]["pagesPerVisitor"]) for x in
                               filtered_lst]
                    return get_results_format(numbers, check_pv, qtype)
                else:
                    numbers = [sum(x["_id"][key.target]) for x in list(
                        filter(lambda x: min(list(map(int, key.value))) <=
                                         sum(x["_id"][key.target]) <=
                                         max(list(map(int, key.value))),
                               unique_visitor_lst))]
                    return get_results_format(numbers, key.target, qtype)
            elif qtype == "COMPARISON":
                k_dct = key.operator + key.value[0]
                return {
                    k_dct: str(round_float_perc(len(
                        list(filter(lambda x: min(list(map(int, key.value))) <=
                                              sum(x["_id"][key.target]) <=
                                              max(list(map(int, key.value))),
                                    unique_visitor_lst))) / len(
                        unique_visitor_lst) * 100)) + "%"
                }

        else:
            check = check_in_total_in_session(phrase=question)
            if check and check == "SESSION":
                by_session = get_vt_ppv_by_session(db_v, domain, date_range,
                                                   match, key.target,
                                                   total_uvt, qtype,
                                                   question, frame)
                if qtype in ["QUANTITY", "CATEGORY"]:
                    return get_results_format(by_session, key.target,
                                              "AVERAGE")
                elif qtype == "PERC":
                    return str(round_float_perc(by_session)) + "%"
                else:
                    return get_results_format(by_session, key.target, qtype)
            elif check and check == "TOTAL":
                if check_pv == "pageviews":
                    numbers = [sum(x["_id"]["pagesPerVisitor"]) for x in
                               unique_visitor_lst]
                    if qtype in ["MEDIAN", "AVERAGE"]:
                        return get_results_format(numbers, check_pv, qtype)
                    elif qtype == "PERC":
                        return str(round_float_perc(
                            len(unique_visitor_lst) / total_uvt * 100)) + "%"
                    else:
                        return get_results_format(numbers, check_pv, "AVERAGE")
                else:
                    numbers = [sum(x["_id"][key.target]) for x in
                               unique_visitor_lst if
                               sum(x["_id"][key.target]) != float(0)]
                    if qtype in ["MEDIAN", "AVERAGE"]:
                        return get_results_format(numbers, key.target, qtype)
                    elif qtype == "PERC":
                        return str(round_float_perc(
                            len(unique_visitor_lst) / total_uvt * 100)) + "%"
                    else:
                        return get_results_format(numbers, key.target,
                                                  "AVERAGE")
            else:
                if check_pv == "pageviews":
                    numbers = [sum(x["_id"]["pagesPerVisitor"]) for x in
                               unique_visitor_lst]
                    if qtype in ["MEDIAN", "AVERAGE"]:
                        by_total = get_results_format(numbers, check_pv, qtype)
                    elif qtype == "PERC":
                        by_total = str(round_float_perc(
                            len(unique_visitor_lst) / total_uvt * 100)) + "%"
                    else:
                        by_total = get_results_format(numbers, check_pv,
                                                      "AVERAGE")
                    avg_by_session = get_vt_ppv_by_session(db_v, domain,
                                                           date_range, match,
                                                           check_pv, total_uvt,
                                                           qtype, question,
                                                           frame)
                    by_session = get_results_format(avg_by_session, check_pv,
                                                    qtype)
                else:
                    numbers = [sum(x["_id"][key.target]) for x in
                               unique_visitor_lst if
                               sum(x["_id"][key.target]) != float(0)]
                    if qtype in ["MEDIAN", "AVERAGE"]:
                        by_total = get_results_format(numbers, key.target,
                                                      qtype)
                    elif qtype == "PERC":
                        by_total = str(round_float_perc(
                            len(unique_visitor_lst) / total_uvt * 100)) + "%"
                    else:
                        by_total = get_results_format(numbers, key.target,
                                                      "AVERAGE")
                    avg_by_session = get_vt_ppv_by_session(db_v, domain,
                                                           date_range, match,
                                                           key.target,
                                                           total_uvt, qtype,
                                                           question, frame)
                    by_session = get_results_format(avg_by_session, key.target,
                                                    "AVERAGE")

                return (
                    {"total": by_total}, {"session": by_session},
                    "unspecified")


"""calculation of returning visitors for comparison and yes/no question"""


def get_number_of_returning_vt_comp_yes_no(domain, date_rnge, target, value,
                                           db_v):
    rnge = date_rnge.copy()
    rnge.update({"domain": domain})
    tmp = dict()
    for d in db_v.find(rnge):
        if d["visitorId"] not in tmp:
            # tmp[d["visitorId"]] = {k: v for k, v in d.items() if k not in
            # ["visitorId", "visitTime"]}
            tmp[d["visitorId"]] = dict()
            tmp[d["visitorId"]]["visitorId"] = d["visitorId"]
            # tmp[d["visitorId"]]["pagesPerVisitor"] = 1
            # if d.get("visitTime"):
            #     tmp[d["visitorId"]]["visitTime"] = d["visitTime"]
            # else:
            #     tmp[d["visitorId"]]["visitTime"] = 0
            if d.get("created"):
                tmp[d["visitorId"]]["created"] = [d["created"], ]
        else:
            # tmp[d["visitorId"]]["pagesPerVisitor"] += 1
            # # take the total/sum of visitTime values
            # if d.get("visitTime"):
            #     tmp[d["visitorId"]]["visitTime"] += d["visitTime"]
            if d.get("created"):
                tmp[d["visitorId"]]["created"].append(d["created"])

    db_by_id = list(tmp.values())

    db_by_id = get_returning(db_by_id)

    total_uvt_cond = len(list(filter(lambda x: x[target] == value, db_by_id)))

    return total_uvt_cond


"""getting the results for the comparison questions"""


def get_results_comparison_questions(dicto, target, total_uniquevisitors,
                                     cond_target, db_v, domain, date_range,
                                     frame):
    # print("dicto: ", dicto)
    res_dict = dict()

    if isinstance(dicto, list):
        res_dict[target] = get_vt_ppv(cond_target, "COMPARISON",
                                      db_v.count_documents(date_range), dicto,
                                      None, None, None)

    else:

        if target not in res_dict:
            res_dict[target] = dict()

        for key, value in dicto.items():
            if target == "visitorId":
                if key not in res_dict[target]:
                    res_dict[target][key] = len(value)
            elif target in ["pageviews", "session"]:
                range = date_range.copy()
                if key not in res_dict[target]:
                    if cond_target == "referralDomain" and key.find(".") == -1:
                        pattern = re.compile("^" + key + "*", re.I)
                        regex = bson.regex.Regex.from_native(pattern)
                        regex.flags ^= re.UNICODE
                        val = regex
                        range.update({"domain": domain, cond_target: val})
                        # res_dict[target][key] = db_v.count_documents(range)
                    else:
                        range.update({"domain": domain, cond_target: value})

                    if target == "pageviews":
                        res_dict[target][key] = db_v.count_documents(range)
                    else:
                        count_session_key = get_session(db_v, domain,
                                                        date_range, range,
                                                        total_uniquevisitors,
                                                        "COMPARISON", "",
                                                        frame)
                        res_dict[target][key] = count_session_key
            # other targets to match, but until now, don't know
            else:
                # print("target: ", target)
                # print("key: ", key)
                # print("cond target: ", cond_target)
                for item in value:
                    """avoid "conversion" key now, will be fixed if having 
                    conversion"""
                    if not isinstance(item[cond_target], list):
                        frequency(key=item[cond_target],
                                  key_dict=res_dict[target])

        # print(res_dict)
        if target == "visitorId":
            # print(total_uniquevisitors)
            res_dict = {
                target: {key: str(
                    round_float_perc(value / total_uniquevisitors * 100)) + "%"
                         for key, value in res_dict[target].items() if
                         key != "count"}
            }
            if cond_target in ["cfCountry", "languages"]:
                res_dict = get_full_name(key=cond_target, container=res_dict,
                                         target=target)
            elif cond_target == "referralType":
                tmp = {
                    target: {mappings[cond_target][key][0]: value for
                             key, value in res_dict[target].items()}
                }
                res_dict = tmp
        elif target == "pageviews":
            total_pv = db_v.count_documents(date_range)
            res_dict = {
                target: {
                    key: str(round_float_perc(value / total_pv * 100)) + "%"
                    for key, value in res_dict[target].items() if
                    key != "count"}
            }
            if cond_target in ["cfCountry", "languages"]:
                res_dict = get_full_name(key=cond_target, container=res_dict,
                                         target=target)
            elif cond_target == "referralType":
                tmp = {
                    target: {mappings[cond_target][key][0].lower(): value for
                             key, value in res_dict[target].items()}
                }
                res_dict = tmp
        elif target == "returningByVisitors":
            # take the value of target "returningByVisitors"
            value = list(i[target] for k, v in dicto.items() for i in v)
            total_uvt_cond = get_number_of_returning_vt_comp_yes_no(domain,
                                                                    date_range,
                                                                    target,
                                                                    "True",
                                                                    db_v)
            # res_dict = str(round_float_perc(total_uvt_cond /
            # total_uniquevisitors * 100)) + "%"
            res_dict = total_uvt_cond
            # res_dict = {target: {key: str(round_float_perc(total_uvt_cond
            # / total_uniquevisitors * 100)) + "%"
            #                      for key, value in res_dict[target].items(
            # ) if key != "count"}}
            if cond_target in ["cfCountry", "languages"]:
                res_dict = get_full_name(key=cond_target, container=res_dict,
                                         target=target)
            elif cond_target == "referralType":
                tmp = {
                    target: {mappings[cond_target][key][0].lower(): value for
                             key, value in res_dict[target].items()}
                }
                res_dict = tmp
        elif target:
            res_dict = {
                target: {key: str(
                    round_float_perc(value / total_uniquevisitors * 100)) + "%"
                         for key, value in res_dict[target].items() if
                         key != "count"}
            }
            if cond_target in ["cfCountry", "languages"]:
                res_dict = get_full_name(key=cond_target, container=res_dict,
                                         target=target)
            elif cond_target == "referralType":
                tmp = {
                    target: {mappings[cond_target][key][0].lower(): value for
                             key, value in res_dict[target].items()}
                }
                res_dict = tmp
        else:
            res_dict = {
                target: {key: str(round_float_perc(
                    value / res_dict[target]["count"] * 100)) + "%"
                         for key, value in res_dict[target].items() if
                         key != "count"}
            }
            if cond_target in ["cfCountry", "languages"]:
                res_dict = get_full_name(key=cond_target, container=res_dict,
                                         target=target)
            elif cond_target == "referralType":
                tmp = {
                    target: {mappings[cond_target][key][0]: value for
                             key, value in res_dict[target].items()}
                }
                res_dict = tmp
    return res_dict


"""getting the results for the yes/no questions"""


def get_results_yes_no_questions(db_v, target, cmp, domain, date_range, qtype):
    # print("target: ", target)
    # print("cmp: ", cmp)
    rnge = date_range.copy()
    rnge.update({"domain": domain})
    total_pv = db_v.count_documents(rnge)
    total_uvt = len(db_v.distinct("visitorId", rnge))
    # print("total uvt cond: ", total_uvt)
    """create a database of each value of cmp conditions based on visitorId"""
    tmp = dict()
    db_by_id = list()
    target_dict = dict()
    res = None
    # if cmp:
    if target.target == "returningByVisitors":
        for d in db_v.find(rnge):
            if d["visitorId"] not in tmp:
                # tmp[d["visitorId"]] = {k: v for k, v in d.items() if k not
                #  in ["visitorId", "visitTime"]}
                if cmp:
                    tmp[d["visitorId"]] = {cmp.target: d[cmp.target]}
                else:
                    tmp[d["visitorId"]] = dict()
                tmp[d["visitorId"]]["visitorId"] = d["visitorId"]
                tmp[d["visitorId"]]["pagesPerVisitor"] = 1
                # if d.get("visitTime"):
                #     tmp[d["visitorId"]]["visitTime"] = d["visitTime"]
                # else:
                #     tmp[d["visitorId"]]["visitTime"] = 0
                if d.get("created"):
                    tmp[d["visitorId"]]["created"] = [d["created"], ]
            else:
                tmp[d["visitorId"]]["pagesPerVisitor"] += 1
                # # take the total/sum of visitTime values
                # if d.get("visitTime"):
                #     tmp[d["visitorId"]]["visitTime"] += d["visitTime"]
                if d.get("created"):
                    tmp[d["visitorId"]]["created"].append(d["created"])

        db_by_id = list(tmp.values())

        db_by_id = get_returning(db_by_id)
        # if cmp:
        db_by_id = list(
            filter(lambda x: x[target.target] == target.value[0], db_by_id))
        # else:
        #     db_by_id = db_by_id

        # print("db by id 1: ", db_by_id[20:25])

        if cmp:
            lst_v = [v for item in db_by_id for k, v in item.items() if
                     k == cmp.target]
        else:
            lst_v = [v for item in db_by_id for k, v in item.items() if
                     k == target.target]
        target_dict = Counter(lst_v)
        # print("target_dict 1: ", sum(target_dict.values()))

        if target.operator:
            res = get_quantity_perc(target, target_dict, qtype, total_uvt,
                                    target.operator)
    else:
        # the case target.target is always "visitorId", if not, it will be
        # used with referral target
        # like perc combination
        if cmp.target in tr_fl_lst and cmp.target != "returningByVisitors":
            if target.target not in ["visitorId", "pageviews",
                                     "pagesPerVisitor"]:
                rnge.update({target.target: target.value[0], cmp.target: True})
            else:
                rnge.update({cmp.target: True})
            target_dict = {"True": len(db_v.distinct("visitorId", rnge))}
        elif cmp.target not in ["returningByVisitors", "pagesPerVisitor",
                                "visitTime"]:
            if target.target not in ["visitorId", "pageviews",
                                     "pagesPerVisitor"]:
                rnge.update({target.target: target.value[0]})
            # else:
            #     rnge = rnge
            unique_value_lst = db_v.distinct(cmp.target)
            for k in unique_value_lst:
                if k:
                    tmp_rnge = rnge.copy()
                    tmp_rnge.update({cmp.target: k})
                    target_dict[k] = len(db_v.distinct("visitorId", tmp_rnge))
            # target_dict = {k: len(db_v.distinct("visitorId",
            # tmp_rnge.update({cmp.target: k}))) for k in unique_value_lst}
        else:
            for d in db_v.find(rnge):
                if d["visitorId"] not in tmp:
                    tmp[d["visitorId"]] = dict()
                    tmp[d["visitorId"]] = {k: [v] for k, v in d.items() if
                                           k not in ["visitorId", "visitTime"]}
                    tmp[d["visitorId"]]["visitorId"] = d["visitorId"]
                    tmp[d["visitorId"]]["pagesPerVisitor"] = 1

                    if d.get("created"):
                        tmp[d["visitorId"]]["created"] = [d["created"], ]
                else:
                    tmp[d["visitorId"]]["pagesPerVisitor"] += 1

                    if d.get("created"):
                        tmp[d["visitorId"]]["created"].append(d["created"])

            db_by_id = list(tmp.values())

            db_by_id = get_returning(db_by_id)

            if cmp.target in tr_fl_lst and cmp.target != "returningByVisitors":
                db_by_id = list(
                    filter(lambda x: x[cmp.target] == True, db_by_id))
            elif not cmp.operator:
                db_by_id = list(
                    filter(lambda x: x[cmp.target] == cmp.value[0], db_by_id))
            else:
                db_by_id = db_by_id.copy()

            # print("after: ", db_by_id[20:25])

            # targets with values as a list of values when creating a db by id
            if cmp.operator and cmp.target not in ["returningByVisitors",
                                                   "pagesPerVisitor"]:
                # lst_v = [i for vid, item in tmp.items() for k,
                # v in item.items() for i in v if k == cmp.target]
                lst_v = list()
                for vid, value in tmp.items():
                    for k, v in value.items():
                        if k == cmp.target:
                            for i in v:
                                lst_v.append(i)
                # lst_v = [i for vid, value in tmp.items() for k,
                # v in value.items() for i in v if k == cmp.target]
            elif cmp.target == "returningByVisitors":
                lst_v = [v for item in db_by_id for k, v in item.items() if
                         k == cmp.target and str(v) == cmp.value[0]]
            else:  # other targets
                lst_v = [v for item in db_by_id for k, v in item.items() if
                         k == cmp.target]
                # lst_v = [v for item in db_by_id for k, v in item.items()
                # if k == target.target]
            target_dict = Counter(lst_v)
        # print(target_dict)
        # print("target_dict 1: ", sum(target_dict.values()))

    if cmp.operator:
        # print("cmp: ", cmp)
        # print("target dict: ", target_dict)
        # print("total uvt: ", total_uvt)
        if cmp.target == "returningByVisitors":
            res = get_quantity_perc(cmp, target_dict, qtype, total_uvt,
                                    cmp.operator)
        else:
            res = get_quantity_perc(cmp, target_dict, qtype, total_uvt,
                                    cmp.operator)

    else:
        if target.operator and db_by_id:
            res = get_quantity_perc(cmp, target_dict, qtype,
                                    sum(target_dict.values()), target.operator)
        elif target_dict[cmp.value[0]] > 0:

            if cmp.target in ["cfCountry", "languages"]:
                name = get_full_name(cmp.target, cmp.value[0], None)
            elif cmp.target == "referralType":
                name = mappings[target.target][target.value[0]][0]
            else:
                name = cmp.value[0]
            return (True, name, cmp.target,
                    str(round_float_perc(target_dict[cmp.value[0]] /
                                         len(db_v.distinct(target.target,
                                                           rnge)) * 100)) +
                    "%")
        elif cmp.target in tr_fl_lst and cmp.target != "returningByVisitors":
            if cmp.value[0] == "unspecified" and target_dict["True"] > 0:
                return (True, "True", cmp.target,
                        str(round_float_perc(target_dict["True"] /
                                             len(db_v.distinct(target.target,
                                                               rnge)) *
                                             100)) + "%")

    return res


"""check two dicts are equal or not"""


def is_equal(a, b):
    if len(a) != len(b):
        return False

    for x, y in zip(a.items(), b.items()):
        # idx 0 is key type, idx 1 is value type
        if x[0] == y[0] and x[1] not in y[1]:
            return False

    return True


if __name__ == "__main__":
    a1 = {'deviceTypes': 'mobile', 'osTypes': 'iOS'}
    a2 = {'deviceTypes': 'pc', 'osTypes': 'iOS'}
    b = {"deviceTypes": ["mobile", "pc"], "osTypes": ["iOS"]}
    print(is_equal(a1, b))
    print(is_equal(a2, b))
