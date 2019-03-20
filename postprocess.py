import re
import warnings
from collections import Counter

import bson
import pycountry
from dateutil.parser import parse as time_parser
from pymongo import MongoClient

from ipa.frame import Frame, Condition
from modules.calculations import length, is_empty, is_existed, frequency, \
    get_quantity_perc, get_vt_ppv, round_float_perc, \
    find_pattern, get_results_comparison_questions, \
    get_results_yes_no_questions, check_date_format, get_session
from modules.get_reference_target import get_reference_target
from resources.en.value_mapping import mappings

warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("error", RuntimeWarning)

ipadburi = 'mongodb://localhost:27017'
ipadbstr = 'ipa_db'

domain = "brunel.nl"
mongo_columns = ['referralType', 'adBlock', 'visitTime', 'referralDomain',
                 'cfCountry', 'bounce', 'conversion',
                 "created"]
useragent_targets = ['deviceBrands', 'deviceTypes', 'touch', 'osTypes',
                     'browserTypes']
page_targets = ['languages']
special_targets = ["visitTime", "pagesPerVisitor", "pageviews",
                   "returningByVisitors", "session"]
tr_fl_lst = ["adBlock", "touch", "bounce", "returningByVisitors"]
ipa_columns = ['referralType', 'adBlock', 'visitTime', 'referralDomain',
               'cfCountry', 'bounce', 'conversion',
               "created", 'deviceBrands', 'deviceTypes', 'touch', 'osTypes',
               'browserTypes', "languages", "layerId"]

# 1 hour converted into milliseconds
HOUR_MILLI = 1000 * 60 * 60
# SESSION_GAP = 2 hours = 2 * 1000 * 60 * 60 (milliseconds)
SESSION_GAP = 2 * HOUR_MILLI

# personalized layers variable
personalized_layers = ['5b56e394073cdf0c3792c5d6',
                       'all_visitors/url_param/all_other_scenarios/abtesting'
                       '/abtesting__0__50']

""" Step 0: connect the database IPA DB """


def connect_db():
    client = MongoClient(ipadburi)[ipadbstr]
    db_v = client['ipa']
    return db_v


""" Step 1: date range selection """


def date_selection(date):
    """extracting the database corresponding with the date of frame"""
    date_rnge = {}

    if not is_empty(date):
        date_numeric, idx_date_numeric = check_date_format(date)
        if date_numeric:
            if length(date_numeric) == 2:
                try:
                    date_rnge = {
                        "created": {
                            "$gte": time_parser(
                                str(date_numeric[0][0]) + 'T00:00:00Z'),
                            "$lte": time_parser(
                                str(date_numeric[0][1]) + 'T00:00:00Z'),
                        }
                    }
                except IndexError:
                    date_rnge = {
                        "created": {
                            "$gte": time_parser(
                                str(date_numeric[0][0]) + 'T00:00:00Z'),
                            "$lte": time_parser(
                                str(date_numeric[-1][0]) + 'T00:00:00Z'),
                        }
                    }
                # print("date_range:", date_rnge)
            elif length(date_numeric) == 1:
                date_rnge = {
                    "created": {
                        "$gte": time_parser(
                            str(date_numeric[0][0]) + 'T00:00:00Z'),
                        "$lte": time_parser(
                            str(date_numeric[0][0]) + 'T23:59:59Z'),
                    }
                }
                # print("date_range 2: ", date_rnge)

    return date_rnge


""" Step 2.1: DB limitation by Mongo targets, IPA DB columns"""


def get_mongo_targets(db_v, frame, date_rnge):
    match = dict()
    match["domain"] = domain
    match.update(date_rnge.copy())

    project = dict()
    project["_id"] = 0
    project["visitorId"] = 1

    if is_existed(frame.conditions, "returningByVisitors"):
        if not date_rnge:
            match["created"] = {"$nin": ["", None], "$exists": True}
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
                        match[cond_item.target] = {
                            "$in": val_lst,
                            "$exists": True, "$nin": ["", None]
                        }
                    project[cond_item.target] = 1
                if cond_item.target == "visitTime":
                    match[cond_item.target] = {
                        "$nin": ["", None],
                        "$exists": True
                    }
                    project[cond_item.target] = 1
                elif cond_item.value != [
                    "unspecified"] and cond_item.target not in \
                        ["referralDomain", "layerId"]:
                    if len(cond_item.value) > 1:
                        match[cond_item.target] = {
                            "$in": cond_item.value,
                            "$exists": True, "$nin": ["", None]
                        }
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
                elif cond_item.target == "layerId":
                    if "personalized" in cond_item.value:
                        match[cond_item.target] = {"$in": personalized_layers}
                    elif "not_personalized" in cond_item.value:
                        personalized_layers.append("")
                        personalized_layers.append(None)
                        match[cond_item.target] = {
                            "$nin": personalized_layers,
                            "$exists": True
                        }
                    else:
                        match[cond_item.target] = {
                            "$exists": True, "$nin": ["", None]
                        }
                    project[cond_item.target] = 1
                else:
                    project[cond_item.target] = 1
    # print("match query: ", match)
    # print("projection: ", project)

    # DB = list(db_v.find(match, project).rewind())

    # print("length of total documents: ", len(DB))

    return match, project


""" Step 2.2. Limitation by Mongo targets and limitation by values by calling 
step 2"""


def create_limited_DB(db_v, frame, date_rnge):
    match, project = get_mongo_targets(db_v, frame, date_rnge)

    return match, project


"""  Step 3: get basic numbers """


def get_basic_numbers(db_v, match, date_range):
    new_range = date_range.copy()
    new_range.update({"domain": domain})
    total_uniquevisitors = len(db_v.distinct("visitorId", new_range))
    total_pageviews = db_v.count_documents({})
    total_pageviews_cond = db_v.count_documents(match)
    # visitorlist = []
    # if isinstance(DB, Cursor):
    #     for dicto in DB.rewind():
    #         visitorlist.append(dicto['visitorId'])
    # else:
    #     for dicto in DB:
    #         visitorlist.append(dicto["visitorId"])
    #
    # uniquevisitors = set(
    #     visitorlist)  # a set with all unique ID's for the whole visits db
    total_uniquevisitors_cond = len(db_v.distinct("visitorId", match))

    return total_uniquevisitors, total_pageviews, \
           total_uniquevisitors_cond, total_pageviews_cond


""" Step 4: create a database by unique visitorId and take the output 
    dictionary of frequencies of each value for targets """


def get_db_by_id(match, project, db_v, frame_conds):
    """new approach to create a unique visitor database"""
    db_by_id = list()
    pipeline = []
    group = {"_id": "$visitorId"}
    unwind = dict()

    """check if whether visitTime target or not"""
    check_vt_pvv = False
    if any(cond.target in special_targets for cond in frame_conds):
        check_vt_pvv = True

    if check_vt_pvv:
        group.update({
            "details": {
                "$push": {
                    "created": "$created",
                    "visitTime": "$visitTime",
                    "pagesPerVisitor": {"$sum": 1}
                }
            }
        })

        project.update({"details": 1})
    else:
        for key, value in project.items():
            if key not in ["visitorId", "_id", "visitTime", "created"]:
                group.update({key: {"$push": "$" + key}})
                unwind = "$" + key
        # condition_group = {"field": {"$push": "$" + key for key, value in
        #                          project.items(
        #
        # ) if key not in ["visitorId", "_id", "visitTime", "created"]}}
        # print(condition_group)
        # group.update(condition_group)
        # project.update({"field": 1})

    # print(match)
    # print(project)
    # print(group)

    """create a dictionary of unique visitor/pagesPerVisitors with their 
    features"""
    if check_vt_pvv:
        pipeline = [{"$match": match},
                    {"$project": project},
                    {"$group": group},
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
                                    "visitTime": "$details.visitTime",
                                    "pagesPerVisitor":
                                        "$details.pagesPerVisitor"
                                }
                            }
                        }
                    },
                    {
                        "$project": {
                            "time_series.visitTime": 1,
                            "time_series.pagesPerVisitor": 1,
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
                    # {
                    #     "$group": {
                    #         "_id": "$_id", "details": {
                    #             "$push": {
                    #                 "visitTime": "$time_series.visitTime",
                    #                 "pagesPerVisitor":
                    #                     "$time_series.pagesPerVisitor",
                    #                 "session_idx": "$session_idx"
                    #             }
                    #         }
                    #     }
                    # },
                    {
                        "$group": {
                            "_id": {
                                "vID": "$_id",
                                "visitTime": "$time_series.visitTime",
                                "pagesPerVisitor":
                                    "$time_series.pagesPerVisitor",
                                "session": "$session_idx"
                            }
                        }
                    },
                    {
                        "$project": {
                            "_id": 1, "details": 1, "returningByVisitors":
                                {
                                    "$cond": [{
                                        "$gt": [{
                                            "$add": [{
                                                "$size": {
                                                    "$filter": {
                                                        "input":
                                                            "$_id.session",
                                                        "as": "index",
                                                        "cond": {
                                                            "$gte": ["$$index",
                                                                     0]
                                                        }
                                                    }
                                                }
                                            }, 1]
                                        }, 1]
                                    }, "True", "False"]
                                }
                        }
                    }]
    else:
        if unwind:
            pipeline = [{"$match": match},
                        {"$project": project},
                        {"$group": group},
                        {"$unwind": unwind}]
        else:
            pipeline = [{"$match": match},
                        {"$project": project},
                        {"$group": group}]

    if pipeline:
        db_by_id = list(db_v.aggregate(pipeline, allowDiskUse=True))

    results = dict()
    sp_cond = list(
        filter(
            lambda x: x.value != ["unspecified"] and x.target != "visitTime",
            frame_conds))

    # if isinstance(limited_db_lst, Cursor):
    #     limited_db_lst = list(limited_db_lst.rewind())
    # else:
    #     limited_db_lst = limited_db_lst
    #
    # results = dict()
    # sp_cond = list(
    #     filter(
    #         lambda x: x.value != ["unspecified"] and x.target != "visitTime",
    #         frame_conds))
    #
    # """check if whether visitTime target or not"""
    # check_vt_pvv = False
    # if any(cond.target in special_targets for cond in frame_conds):
    #     check_vt_pvv = True
    #
    # """create a dictionary of unique visitor/pagesPerVisitors with their
    # features"""
    # if check_vt_pvv:
    #     # print("sp cond: ", len(sp_cond))
    #     tmp = dict()
    #     for d in list(limited_db_lst):
    #         if d["visitorId"] not in tmp:
    #             tmp[d["visitorId"]] = {k: v for k, v in d.items() if
    #                                    k not in ["visitorId", "visitTime"]}
    #             tmp[d["visitorId"]]["visitorId"] = d["visitorId"]
    #             tmp[d["visitorId"]]["pagesPerVisitor"] = 1
    #             if d.get("visitTime"):
    #                 tmp[d["visitorId"]]["visitTime"] = d["visitTime"]
    #             else:
    #                 tmp[d["visitorId"]]["visitTime"] = 0
    #             if d.get("created"):
    #                 tmp[d["visitorId"]]["created"] = [d["created"], ]
    #         else:
    #             tmp[d["visitorId"]]["pagesPerVisitor"] += 1
    #             # take the total/sum of visitTime values
    #             if d.get("visitTime"):
    #                 tmp[d["visitorId"]]["visitTime"] += d["visitTime"]
    #             if d.get("created"):
    #                 tmp[d["visitorId"]]["created"].append(d["created"])
    #
    #     db_by_id = list(tmp.values())
    #
    #     if any("returningByVisitors" in item for item in frame_conds):
    #         db_by_id = get_returning(db_by_id)
    #
    #     # print(db_by_id[20:25])
    #     if any(i.target == "returningByVisitors" for i in sp_cond):
    #         for spc in sp_cond:
    #             if spc.target == "returningByVisitors":
    #                 db_by_id = list(
    #                     filter(lambda x: x[spc.target] == spc.value[0],
    #                            db_by_id))
    #         # print("new db: ", db_by_id[20:25])
    #         # filtering by unique visitorId
    #         db_by_id = list({dicto["visitorId"]: dicto for dicto in
    #                          list(db_by_id)}.values())
    # else:
    #     # print("length of limited db:", list(limited_db_lst)[20:25])
    #     # filtering by unique visitorId
    #     db_by_id = list({dicto["visitorId"]: dicto for dicto in
    #                      list(limited_db_lst)}.values())
    #
    # # print("length of unique visitors:", len(db_by_id))
    #

    # print("sp cond: ", sp_cond)

    for db_item in db_by_id:
        if sp_cond:
            for cond_item in sp_cond:
                if cond_item.operator:
                    if db_item.get(cond_item.target):
                        if cond_item.target not in results:
                            results[cond_item.target] = dict()
                        else:
                            frequency(db_item[cond_item.target],
                                      results[cond_item.target])
        else:
            for cond_item in frame_conds:
                if cond_item.operator or cond_item.target in tr_fl_lst:
                    if db_item.get(cond_item.target):
                        if cond_item.target not in results:
                            results[cond_item.target] = dict()
                        else:
                            frequency(db_item[cond_item.target],
                                      results[cond_item.target])

    # print("Finished filtering, waiting for results")
    # print(results)

    return db_by_id, results


""" Step 5: check question type for last processing  """


def get_results(question, entities_before_mapping, match, frame, db_by_id,
                target_dict, db_v, total_uniquevisitors, total_pageviews,
                total_uniquevisitors_cond, total_pageviews_cond, date_range):
    cond_op_vid = list(filter(lambda x: x.operator and x.target == "visitorId",
                              frame.conditions))
    cond_op = list(filter(lambda x: x.operator, frame.conditions))
    cond_val = list(
        filter(lambda x: x.operator is None and x.target in special_targets,
               frame.conditions))
    remaining_cond = list(filter(lambda
                                     x: x not in cond_op and x not in
                                        cond_val and x not in cond_op_vid,
                                 frame.conditions))
    # print(cond_op_vid)
    # print(cond_op)
    # print(cond_val)
    # print(remaining_cond)

    res = None

    if any(item.target == "conversion" for item in frame.conditions):
        res = "Not found"
    else:
        if frame.question_type not in ["COMPARISON", "yes/no"]:
            if cond_op_vid:
                for cond in cond_op_vid:
                    if cond.operator == "max":
                        if cond_val:
                            for cond_v in cond_val:
                                res = get_quantity_perc(cond_v.target,
                                                        target_dict[
                                                            cond_v.target],
                                                        frame.question_type,
                                                        total_pageviews,
                                                        cond.operator)
                    elif cond.operator == "min":
                        if cond_val:
                            for cond_v in cond_val:
                                res = get_quantity_perc(cond_v.target,
                                                        target_dict[
                                                            cond_v.target],
                                                        frame.question_type,
                                                        total_pageviews,
                                                        cond.operator)
                    elif not cond.operator:
                        if cond_val:
                            for cond_v in cond_val:
                                res = get_vt_ppv(question,
                                                 entities_before_mapping,
                                                 db_v, domain, date_range,
                                                 match, cond_v,
                                                 frame.question_type,
                                                 total_pageviews, db_by_id,
                                                 None, None,
                                                 None, frame)
            elif cond_op:
                for cond in cond_op:
                    if cond.operator == "max":
                        if target_dict:
                            res = get_quantity_perc(cond.target,
                                                    target_dict[cond.target],
                                                    frame.question_type,
                                                    total_pageviews,
                                                    cond.operator)
                        else:
                            target_list = list(
                                map(lambda x: x[cond.target], db_by_id))
                            count_dict = Counter(target_list)
                            res = get_quantity_perc(cond.target, count_dict,
                                                    frame.question_type,
                                                    total_pageviews,
                                                    cond.operator)
                    elif cond.operator == "min":
                        if target_dict:
                            res = get_quantity_perc(cond.target,
                                                    target_dict[cond.target],
                                                    frame.question_type,
                                                    total_pageviews,
                                                    cond.operator)
                        else:
                            target_list = list(
                                map(lambda x: x[cond.target], db_by_id))
                            count_dict = Counter(target_list)
                            res = get_quantity_perc(cond.target, count_dict,
                                                    frame.question_type,
                                                    total_pageviews,
                                                    cond.operator)
                    elif cond.operator == "all":
                        res_lst = list(
                            {item[cond.target]: item[cond.target] for item in
                             db_by_id if item[cond.target]}.values())
                        if cond.target == "cfCountry":
                            res = [pycountry.countries.get(alpha_2=item).name
                                   for item in res_lst if
                                   item != "XX" and item]
                        elif cond.target == "languages":
                            res = [pycountry.languages.get(alpha_2=item).name
                                   for item in res_lst if item]
                        elif cond.target == "referralType":
                            res = [mappings[cond.target][i][0].lower() for i in
                                   res_lst]
                        else:
                            res = res_lst
                    elif cond.operator == "second":
                        if target_dict:
                            res = get_quantity_perc(cond.target,
                                                    target_dict[cond.target],
                                                    frame.question_type,
                                                    total_pageviews,
                                                    cond.operator)
                        else:
                            target_list = list(
                                map(lambda x: x[cond.target], db_by_id))
                            count_dict = Counter(target_list)
                            res = get_quantity_perc(cond.target, count_dict,
                                                    frame.question_type,
                                                    total_pageviews,
                                                    cond.operator)
                    elif cond.operator == "not":
                        res = get_quantity_perc(cond.target,
                                                target_dict[cond.target],
                                                frame.question_type,
                                                total_pageviews, cond.operator)
                    elif cond.operator in [">", "<", ">=", "<="]:
                        if any(item.target == "pageviews" for item in
                               frame.conditions):
                            res = get_vt_ppv(question, entities_before_mapping,
                                             db_v, domain, date_range,
                                             match, cond, frame.question_type,
                                             total_pageviews, db_by_id, None,
                                             None, "pageviews", frame)
                        else:
                            res = get_vt_ppv(question, entities_before_mapping,
                                             db_v, domain, date_range,
                                             match, cond, frame.question_type,
                                             total_pageviews, db_by_id, None,
                                             None, None, frame)
            elif cond_val:
                for cond in cond_val:
                    if frame.question_type == "CATEGORY":
                        res = get_vt_ppv(question, entities_before_mapping,
                                         db_v, domain, date_range, match, cond,
                                         frame.question_type, total_pageviews,
                                         db_by_id, None, None, None, frame)
                        """let's check here"""
                        # if res and remaining_cond:
                        #     for cond in remaining_cond:
                        #         if cond.target != "visitorId":
                        #             if cond.target == "pageviews":
                        #                 res = list(
                        #                     {item["pagesPerVisitor"]: item[
                        # "pagesPerVisitor"] for item in res}.values())
                        #             else:
                        #                 res = list({item[cond.target]:
                        # item[cond.target] for item in res}.values())
                        #             if cond.target in ["cfCountry",
                        # "languages"]:
                        #                 res = get_full_name(cond.target,
                        # res, None)
                        #             elif cond.target == "referralType":
                        #                 res = list(mappings[cond.target][
                        # i][0] for i in res)

                    else:
                        if any(item.target in ["pageviews",
                                               "returningByVisitors"] for item
                               in frame.conditions):
                            """can be deleted"""
                            res = get_vt_ppv(question, entities_before_mapping,
                                             db_v, domain, date_range,
                                             match, cond,
                                             frame.question_type,
                                             total_pageviews_cond, db_by_id,
                                             total_pageviews,
                                             total_uniquevisitors,
                                             "pageviews", frame)
                        else:
                            res = get_vt_ppv(question, entities_before_mapping,
                                             db_v, domain, date_range,
                                             match, cond,
                                             frame.question_type,
                                             total_pageviews_cond, db_by_id,
                                             total_pageviews,
                                             total_uniquevisitors, None, frame)
            else:
                if total_uniquevisitors == 0 or any(
                        item.target == "conversion" for item in
                        frame.conditions):
                    res = "The database doesn't have this information"
                else:
                    if frame.question_type == "QUANTITY":
                        if any(x.target == "visitTime" for x in
                               frame.conditions):
                            cond = list(filter(lambda x: x.target ==
                                                         "visitTime",
                                               frame.conditions))[0]
                            res = get_vt_ppv(question, entities_before_mapping,
                                             db_v, domain, date_range,
                                             match, cond,
                                             frame.question_type,
                                             total_uniquevisitors_cond,
                                             db_by_id, total_pageviews,
                                             total_uniquevisitors, None, frame)
                        else:
                            res = total_uniquevisitors_cond
                    elif frame.question_type == "PERC":
                        # refer_target is a target to be divided by
                        refer_target = get_reference_target(question,
                                                            entities_before_mapping)
                        if refer_target:
                            refer_cond = {cond.target: cond.value[0] for cond
                                          in
                                          frame.conditions if
                                          cond.target == refer_target}
                            if refer_target == "referralDomain":
                                pattern = re.compile(
                                    "^" + refer_cond[refer_target] + "*", re.I)
                                regex = bson.regex.Regex.from_native(pattern)
                                regex.flags ^= re.UNICODE
                                refer_cond[refer_target] = regex

                            res = str(round_float_perc(
                                total_uniquevisitors_cond / len(
                                    db_v.distinct("visitorId",
                                                  refer_cond)) * 100)) + "%"
                        else:
                            if total_uniquevisitors_cond != \
                                    total_uniquevisitors:
                                res = str(
                                    round_float_perc(
                                        total_uniquevisitors_cond /
                                        total_uniquevisitors * 100)) + "%"
                            else:
                                res = str(round_float_perc(
                                    total_uniquevisitors_cond / len(
                                        db_v.distinct("visitorId",
                                                      {})) * 100)) + "%"
                    elif frame.question_type == "CATEGORY":
                        if remaining_cond:
                            try:
                                cond_r = list(filter(lambda
                                                         x: x.target !=
                                                            "visitorId" and
                                                            "unspecified" in
                                                            x.value,
                                                     remaining_cond))[0]
                                res_lst = list(val for val in {
                                    item[cond.target]: item[cond.target] for
                                    item in
                                    db_by_id
                                    for cond in remaining_cond if
                                    cond.target != "visitorId" and
                                    "unspecified"
                                    in cond.value}.values()
                                               if val)
                                if cond_r.target == "cfCountry":
                                    res = [pycountry.countries.get(
                                        alpha_2=item).name for item in res_lst
                                           if
                                           item != "XX" and item]
                                elif cond_r.target == "languages":
                                    res = [pycountry.languages.get(
                                        alpha_2=item).name for item in res_lst
                                           if item]
                                elif cond_r.target == "referralType":
                                    res = [
                                        mappings["referralType"][i][0].lower()
                                        for i in res_lst if i != 9]
                                else:
                                    res = res_lst
                            # no cond_r, maybe frame is incorrect, raise the
                            # IndexError due to "0" index
                            except IndexError:
                                pass

        elif frame.question_type == "COMPARISON":
            # comparison for two values of targets, not for comparing time
            if len(frame.conditions) == 1:
                if len(frame.conditions[0].value) != 2:
                    rnge = date_range.copy()
                    rnge.update({"domain": domain})

                    # compare two dates
                    if frame.conditions[0].target == "visitorId":
                        res = len(db_v.distinct("visitorId", rnge))
                    elif frame.conditions[0].target == "pageviews":
                        res = db_v.count_documents(rnge)
                    elif frame.conditions[0].target == "returningByVisitors":
                        res = len(db_by_id)
                    elif frame.conditions[0].target in tr_fl_lst:
                        rnge.update({frame.conditions[0].target: True})
                        res = db_v.count_documents(rnge)
                    else:
                        if "unspecified" not in frame.conditions[0].value:
                            rnge.update({
                                frame.conditions[0].target:
                                    frame.conditions[0].value[0]
                            })
                        res = len(db_v.distinct("visitorId", rnge))
                elif len(frame.conditions[0].value) == 2:
                    pattern_dict = {
                        value: list(filter(lambda x: find_pattern(value, x[
                            frame.conditions[0].target]), db_by_id)) for
                        value in
                        frame.conditions[0].value if value != "unrecognized"}
                    res = get_results_comparison_questions(pattern_dict,
                                                           "visitorId",
                                                           total_uniquevisitors,
                                                           frame.conditions[
                                                               0].target,
                                                           db_v, domain,
                                                           date_range)
            elif len(frame.conditions) == 2 and any(
                    "unspecified" not in x.value and len(x.value) == 1 for x in
                    frame.conditions):
                # date comparison
                cond_cmp = list(
                    filter(lambda x: len(x.value) == 1 and x.value[
                        0] != "unspecified" or x.target in tr_fl_lst,
                           frame.conditions))
                if cond_cmp:
                    rnge = date_range.copy()
                    rnge.update({"domain": domain})

                    # compare two dates
                    if cond_cmp[0].target == "visitorId":
                        res = len(db_v.distinct("visitorId", rnge))
                    elif cond_cmp[0].target == "pageviews":
                        res = db_v.count_documents(rnge)
                    elif cond_cmp[0].target == "returningByVisitors":
                        res = len(db_by_id)
                    elif cond_cmp[0].target in tr_fl_lst:
                        rnge.update({cond_cmp[0].target: True})
                        res = db_v.count_documents(rnge)
                    else:
                        rnge.update({cond_cmp[0].target: cond_cmp[0].value[0]})
                        res = len(db_v.distinct("visitorId", rnge))
            else:
                cond_cmp = list(
                    filter(lambda x: len(x.value) > 1 or x.operator,
                           frame.conditions))
                # print("cond_cmp: ", cond_cmp)
                if len(cond_cmp) == 2:
                    # need to process here for two operator
                    save_cmp = cond_cmp.copy()
                    cond_cmp = list(filter(
                        lambda x: x.operator in ["max", "min"] or len(
                            x.value) == 2, save_cmp))
                    # print(cond_cmp)
                    # cond_usp = list(filter(lambda x: x.operator not in [
                    # "max", "min"], save_cmp))

                    cond_usp = [item for item in save_cmp if
                                item not in cond_cmp]
                    # print(cond_usp)
                else:
                    cond_usp = list(
                        filter(
                            lambda x: x not in cond_cmp and x.target not in (
                                    ["visitorId", "conversion", "pageviews",
                                     "returningByVisitors"] + tr_fl_lst or len(
                                x.value) == 1), frame.conditions))
                # print("after, cond cmp: ", cond_cmp)
                # print("cond usp: ", cond_usp)
                rnge = date_range.copy()
                if cond_usp and cond_cmp:
                    for cmp, usp in zip(cond_cmp, cond_usp):
                        # if usp.target in ["visitTime", "pagesPerVisitor"]:
                        #     # print(get)
                        #     pattern_dict = {}
                        # else:
                        # if usp.operator:
                        #     usp = Condition(target=usp.target,
                        # operator=None, value=usp.value)
                        # print(usp)
                        pattern_dict = {value: list(
                            filter(
                                lambda x: find_pattern(value, x[cmp.target]),
                                db_by_id)) for
                            value in
                            cmp.value if value != "unrecognized"}
                        if cond_usp[0].target not in ["visitorId",
                                                      "returningByVisitor",
                                                      "pageviews",
                                                      "pagesPerVisitor",
                                                      "session"]:
                            rnge.update({
                                "domain": domain,
                                cond_usp[0].target: cond_usp[0].value[0]
                            })
                            total_uvt_usp = len(db_v.distinct("visitorId",
                                                              rnge))
                        else:
                            if cond_usp[0].target == "session":
                                total_uvt_usp = get_session(db_v, domain,
                                                            date_range,
                                                            {},
                                                            total_uniquevisitors,
                                                            frame.question_type,
                                                            question)

                            else:
                                rnge.update({"domain": domain})
                                total_uvt_usp = len(db_v.distinct(
                                    "visitorId", rnge))
                        # print(total_uvt_usp)
                        res = get_results_comparison_questions(pattern_dict,
                                                               usp.target,
                                                               total_uvt_usp,
                                                               cmp.target,
                                                               db_v, domain,
                                                               date_range)
                elif not cond_usp and cond_cmp:
                    cond_usp = list(
                        filter(lambda x: x not in cond_cmp and x.target in (
                                ["visitorId", "pageviews",
                                 "returningByVisitors"] + tr_fl_lst),
                               frame.conditions))
                    """if no having other targets, but visitorId, please 
                    choose it as the target"""
                    if cond_usp:
                        # print("cond_usp: ", cond_usp)
                        if cond_cmp:
                            # if cond_cmp[0].target == "pagesPerVisitor" and
                            # target_dict:
                            #     res = get_vt_ppv(cond_cmp[0],
                            # frame.question_type, total_uniquevisitors_cond,
                            #  target_dict, None, None, None)
                            # else:
                            for cmp, usp in zip(cond_cmp, cond_usp):
                                if cmp.target in ["visitTime",
                                                  "pagesPerVisitor"]:
                                    res = get_results_comparison_questions(
                                        db_by_id, usp.target,
                                        total_uniquevisitors,
                                        cmp,
                                        db_v, domain, date_range)
                                else:
                                    pattern_dict = {
                                        value: list(filter(
                                            lambda x: find_pattern(value, x[
                                                cmp.target]), db_by_id))
                                        for value in cmp.value if
                                        value != "unrecognized"}
                                    res = get_results_comparison_questions(
                                        pattern_dict, usp.target,
                                        total_uniquevisitors, cmp.target,
                                        db_v, domain, date_range)
                    else:
                        """if having only a condition with two values, 
                        the default is depending on visitorId key"""
                        pattern_dict = {
                            value: list(filter(lambda x: find_pattern(value, x[
                                cond_cmp[0].target]), db_by_id))
                            for value in cond_cmp[0].value if
                            value != "unrecognized"}
                        res = get_results_comparison_questions(pattern_dict,
                                                               "visitorId",
                                                               total_uniquevisitors,
                                                               cond_cmp[
                                                                   0].target,
                                                               db_v, domain,
                                                               date_range)
                else:
                    # compare two dates
                    res = len(db_by_id)

        elif frame.question_type == "yes/no":
            if any(x.operator and x.target != "visitorId" for x in
                   frame.conditions):
                cond_cmp = list(
                    filter(
                        lambda x: x.operator or all(i not in x.value for i in
                                                    ["unspecified", "True",
                                                     "False"]),
                        frame.conditions))
                if len(cond_cmp) == 2:
                    cond_ref = list(filter(lambda x: not x.operator, cond_cmp))
                    cond_cmp = list(
                        filter(lambda x: x not in cond_ref, cond_cmp))
                else:
                    # cond_ref = list(filter(lambda x: x not in cond_cmp and
                    # x.target in (["visitorId", "pageviews",
                    # "returningByVisitors"] + tr_fl_lst), frame.conditions))
                    cond_ref = list(
                        filter(lambda
                                   x: x not in cond_cmp and "unspecified" not
                                      in x.value,
                               frame.conditions))
                # print("check: ", cond_cmp)
                # print("check 2: ", cond_ref)
            else:
                # no operator
                cond_cmp = list(filter(lambda x: (len(
                    x.value) == 1 and x.value not in [["unspecified"], [
                    "unrecognized"], ["True"], ["False"]] and x.target not in (
                                                          ["visitorId",
                                                           "pageviews",
                                                           "returningByVisitors"] + tr_fl_lst)) or
                                                 x.operator and x.target !=
                                                 "visitorId",
                                       frame.conditions))
                # cond_cmp_op = list(filter(lambda x: x.operator,
                # frame.conditions))
                cond_ref = list(filter(
                    lambda x: x.target in (["pageviews",
                                            "returningByVisitors"] +
                                           tr_fl_lst) and x not in cond_cmp,
                    frame.conditions))
                # print("cond cmp: ", cond_cmp)
                # print("cond ref: ", cond_ref)
            if cond_cmp:
                # if len(cond_cmp) > 1:
                #     print("test thu: ", get_reference_target(question,
                #
                # entities_before_mapping))
                if cond_ref and any(x.target == "returningByVisitors" for x in
                                    frame.conditions):
                    res = get_results_yes_no_questions(db_v, cond_ref[0],
                                                       cond_cmp[0], domain,
                                                       date_range,
                                                       frame.question_type)
                elif cond_ref:
                    res = get_results_yes_no_questions(db_v, cond_ref[0],
                                                       cond_cmp[0], domain,
                                                       date_range,
                                                       frame.question_type)
                else:
                    if any(x.target == "returningByVisitors" for x in
                           frame.conditions) and len(
                        frame.conditions) > 1 and cond_cmp[
                        0].target != "returningByVisitors":
                        cond_ref = list(
                            filter(lambda x: x.target == "returningByVisitors",
                                   frame.conditions))
                        cond_cmp = list(
                            filter(lambda x: x not in cond_ref, cond_cmp))
                        res = get_results_yes_no_questions(db_v, cond_ref[0],
                                                           cond_cmp[0], domain,
                                                           date_range,
                                                           frame.question_type)
                    else:
                        cond_ref = Condition(target="visitorId", operator=None,
                                             value=["unspecified"])
                        # print("date range: ", date_range)
                        res = get_results_yes_no_questions(db_v, cond_ref,
                                                           cond_cmp[0], domain,
                                                           date_range,
                                                           frame.question_type)
                # need to find the way for combination of two or three
                # targets without returningByVisitors or visitorId
                # for example, question = Do Americans people still use laptop?
            else:
                if cond_ref:
                    if any(x.target == "returningByVisitors" for x in
                           frame.conditions):
                        res = get_results_yes_no_questions(db_v, cond_ref[0],
                                                           None, domain,
                                                           date_range,
                                                           frame.question_type)
                    else:
                        # if only one condition, add a stuff condition to be
                        # considered as a reference
                        cond_tmp = Condition(target="visitorId", operator=None,
                                             value=["unspecified"])
                        res = get_results_yes_no_questions(db_v, cond_tmp,
                                                           cond_ref[0], domain,
                                                           date_range,
                                                           frame.question_type)
            # operator = list(filter(lambda x: x.operator, frame.conditions))
            # if any(x.target == "returningByVisitors" for x in
            # frame.conditions):
            #     res = get_results_yes_no_questions(db_v,
            # "returningByVisitors", cond_cmp[0], domain, date_range,
            # frame.question_type)
            # elif cond_cmp:
            #     res = get_results_yes_no_questions(db_v, "visitorId",
            # cond_cmp[0], domain, date_range, frame.question_type)

    return res


"""This function for testing when you run this Python file: python 
postprocess.py"""


def get_postprocess_inside(question, entities_before_mapping, frame):
    # frame.conditions = [Condition(target='deviceTypes', operator="max",
    # value=['unspecified'])]

    # frame.conditions = [Condition(target='deviceTypes', operator=None,
    # value=['tablet'])]

    # frame.conditions = [Condition(target='deviceTypes', operator=None,
    # value=['mobile'])]

    # frame.conditions = [Condition(target='deviceTypes', operator="min",
    # value=['unspecified'])]

    # frame.conditions = [Condition(target='deviceTypes', operator="second",
    # value=['unspecified'])]

    # frame.conditions = [Condition(target='osTypes', operator=None, value=[
    # 'Linux'])]

    # frame.conditions = [Condition(target='osTypes', operator="max", value=[
    # 'unspecified'])]

    # frame.conditions = [Condition(target='osTypes', operator=None, value=[
    # 'Windows'])]

    # frame.conditions = [Condition(target='osTypes', operator="min", value=[
    # 'unspecified'])]

    # frame.conditions = [Condition(target='osTypes', operator="max", value=[
    # 'unspecified'])]

    # frame.conditions = [Condition(target='pageviews', operator=None,
    # value=['unspecified'])]

    # frame.conditions = [Condition(target='pagesPerVisitor', operator=None,
    # value=['unspecified'])]

    # frame.conditions = [Condition(target='languages', operator="max",
    # value=['unspecified'])]

    # frame.conditions = [Condition(target='languages', operator=None,
    # value=['es'])]

    # frame.conditions = [Condition(target='languages', operator=None,
    # value=['fr'])]

    # frame.conditions = [Condition(target='languages', operator=None,
    # value=['nl'])]

    # frame.conditions = [Condition(target='browserTypes', operator="max",
    # value=['unspecified'])]

    # frame.conditions = [Condition(target='browserTypes', operator=None,
    # value=['Chrome'])]

    # frame.conditions = [Condition(target='browserTypes', operator=None,
    # value=['Safari'])]

    # frame.conditions = [Condition(target='browserTypes', operator=None,
    # value=['Firefox'])]

    # frame.conditions = [Condition(target='browserTypes', operator="second",
    #  value=['unspecified'])]

    # frame.conditions = [Condition(target='deviceBrands', operator="max",
    # value=['unspecified'])]

    # frame.conditions = [Condition(target='deviceBrands', operator="all",
    # value=['unspecified'])]

    # frame.conditions = [Condition(target='deviceBrands', operator=None,
    # value=['Apple'])]

    # frame.conditions = [Condition(target='deviceBrands', operator=None,
    # value=['Sony'])]

    # frame.conditions = [Condition(target='deviceBrands', operator="min",
    # value=['unspecified'])]

    # frame.conditions = [Condition(target='deviceBrands', operator=None,
    # value=['Asus'])]

    # frame.conditions = [Condition(target='deviceBrands', operator=None,
    # value=['Apple'])]

    # frame.conditions = [Condition(target='deviceBrands', operator="max",
    # value=['unspecified'])]

    # frame.conditions = [Condition(target='adBlock', operator=None, value=[
    # 'unspecified'])]

    # frame.conditions = [Condition(target='touch', operator=None, value=[
    # 'unspecified'])]

    # frame.conditions = [Condition(target='cfCountry', operator="max",
    # value=['unspecified']),
    #                     Condition(target='bounce', operator=None, value=[
    # 'unspecified'])]

    # frame.conditions = [Condition(target='returningByVisitor',
    # operator=None, value=['True'])]

    # frame.conditions = [Condition(target='referralType', operator=None,
    # value=[5])]

    # frame.conditions = [Condition(target='referralDomain', operator=None,
    # value=["google", "linkedin.com"])]

    # frame.conditions = [Condition(target='pageviews', operator=None,
    # value=['unspecified']),
    #                     Condition(target='pagesPerVisitor', operator=None,
    # value=['4', '2'])]

    # frame.conditions = [Condition(target='pageviews', operator=None,
    # value=['unspecified']),
    #                     Condition(target='pagesPerVisitor', operator=None,
    # value=["unspecified"])]

    # frame.conditions = [Condition(target='pageviews', operator=None,
    # value=['unspecified'])]

    # frame.conditions = [Condition(target='visitorId', operator=None,
    # value=['unspecified']),
    #                     Condition(target='cfCountry', operator=None,
    # value=['FR', 'US']),
    #                     Condition(target="deviceTypes", operator=None,
    # value=["mobile"])]
    # frame.conditions = [Condition(target='visitorId', operator=None,
    # value=['unspecified']),
    #                     Condition(target='cfCountry', operator=None,
    # value=['FR']),
    #                     Condition(target="deviceTypes", operator=None,
    # value=["mobile"])]
    # frame.conditions = [Condition(target="deviceTypes", operator=None,
    # value=["mobile"])]

    # frame.conditions = [Condition(target='visitorId', operator=None,
    # value=['unspecified']),
    #                     Condition(target='cfCountry', operator=None,
    # value=['FR', 'US']),
    #                     Condition(target="deviceTypes", operator=None,
    # value=["mobile"]),
    #                     Condition(target="osTypes", operator=None, value=[
    # "iOS"])]
    # frame.conditions = [Condition(target="touch", operator=None, value=[
    # "unspecified"])]
    # frame.conditions = [Condition(target="touch", operator=None, value=[
    # "unspecified"])]

    # frame.conditions = [Condition(target="returningByVisitor",
    # operator=None, value=["False"])]

    # frame.conditions = [Condition(target='visitorId', operator=None,
    # value=['unspecified']),
    #                     Condition(target='cfCountry', operator=None,
    # value=["unspecified"])]

    # frame.conditions = [Condition(target='visitorId', operator=None,
    # value=['unspecified']),
    #                     Condition(target='cfCountry', operator="all",
    # value=["unspecified"])]

    # frame.conditions = [Condition(target='visitorId', operator=None,
    # value=['unspecified']),
    #                     Condition(target='cfCountry', operator="second",
    # value=["unspecified"])]

    ##################Okay
    # frame.conditions = [Condition(target='visitorId', operator='max',
    # value=['unspecified']),
    #                     Condition(target='cfCountry', operator=None,
    # value=['FR', "US"])]

    # frame.conditions = [Condition(target="deviceTypes", operator=None,
    # value=["mobile"]),
    #                     Condition(target="osTypes", operator=None, value=[
    # "iOS"])]

    # frame.conditions = [Condition(target='visitorId', operator=None,
    # value=['unspecified']),
    #                     Condition(target='cfCountry', operator="max",
    # value=["unspecified"])]

    # frame.conditions = [Condition(target='visitorId', operator=None,
    # value=['unspecified']),
    #                     Condition(target='cfCountry', operator="min",
    # value=["unspecified"])]

    # frame.conditions = [Condition(target="touch", operator=None, value=[
    # "unspecified"])]
    # frame.conditions = [Condition(target="bounce", operator=None, value=[
    # "unspecfied"])]

    # frame.conditions = [Condition(target='visitorId', operator=None,
    # value=['unspecified']),
    #                     Condition(target='languages', operator=None,
    # value=['FR', 'EN']),
    #                     Condition(target="deviceTypes", operator=None,
    # value=["mobile"]),
    #                     Condition(target="osTypes", operator=None, value=[
    # "iOS"]),
    #                     Condition(target="visitTime", operator="<", value=[
    # "12"])]

    # frame.conditions = [Condition(target="languages", operator=None,
    # value=["FR", "EN"])]

    # frame.conditions = [Condition(target='visitorId', operator=None,
    # value=['unspecified']),
    #                     Condition(target='cfCountry', operator=None,
    # value=['unspecified']),
    #                     Condition(target="deviceTypes", operator=None,
    # value=["mobile"]),
    #                     Condition(target="osTypes", operator=None, value=[
    # "iOS"]),
    #                     Condition(target="visitTime", operator="<", value=[
    # "12"])]

    # frame.conditions = [Condition(target='visitorId', operator=None,
    # value=['unspecified']),
    #                     Condition(target='cfCountry', operator=None,
    # value=['FR', 'US']),
    #                     Condition(target="deviceTypes", operator=None,
    # value=["mobile"]),
    #                     Condition(target="pageviews", operator=None,
    # value=["unspecified"])]

    print("Frame is: ", frame.print_frame())

    db_v = connect_db()
    # print(type(db_v))
    # print(db_v.count_documents({}))
    date_rnge = date_selection(frame.date)
    match, project = create_limited_DB(db_v, frame, date_rnge)
    db_by_id, processed_db = get_db_by_id(match, project, db_v,
                                          frame.conditions)
    if db_by_id:
        total_uniquevisitors, total_pageviews, \
        total_uniquevisitors_cond, total_pageviews_cond = get_basic_numbers(
            db_v, match, date_rnge)
        # print("outside", total_uniquevisitors_cond)
        # print("processed_db: ", processed_db[20:25])

        # print("The total number of pageviews {}".format(
        # db_v.count_documents({})))
        # print("db by id: ", db_by_id[20:25])
        # print("processed id: ", processed_db)

        res = get_results(question, entities_before_mapping, match, frame,
                          db_by_id, processed_db, db_v, total_uniquevisitors,
                          total_pageviews, total_uniquevisitors_cond,
                          total_pageviews_cond, date_rnge)
    else:
        res = "The database doesn't have this information"

    return res


def get_postprocess(db_v, question, entities_before_mapping, frame):
    # print("The total number of pageviews {}".format(db_v.count_documents({
    # })))
    # print("Frame is: ", frame.print_frame())
    if frame.conditions:
        date_rnge = date_selection(frame.date)
        match, project = create_limited_DB(db_v, frame, date_rnge)
        db_by_id, processed_db = get_db_by_id(match, project, db_v,
                                              frame.conditions)
        if db_by_id:
            # print("db by id: ", db_by_id[20:25])
            # print("processed id: ", processed_db)
            # with open("test_1.json", "w") as outf1:
            #     json.dump(db_by_id, outf1)
            # with open("test_2.json", "w") as outf2:
            #     json.dump(processed_db, outf2)
            total_uniquevisitors, total_pageviews, \
            total_uniquevisitors_cond, total_pageviews_cond = \
                get_basic_numbers(
                    db_v, match, date_rnge)
            res = get_results(question, entities_before_mapping, match, frame,
                              db_by_id, processed_db, db_v,
                              total_uniquevisitors,
                              total_pageviews, total_uniquevisitors_cond,
                              total_pageviews_cond, date_rnge)
            return res, True
        else:
            return "The database doesn't have this information", False
    else:
        return "Cannot detect any target", False


if __name__ == '__main__':
    frame = Frame()

    frame.question_type = "COMPARISON"
    frame.date = [[]]
    frame.conditions = [
        Condition(target='osTypes', operator=">", value=['Windows', 'iOS'])]
    frame.question_type = "yes/no"
    frame.date = [[]]
    frame.conditions = [
        Condition(target='visitorId', operator=None, value=['unspecified']),
        Condition(target='returningByVisitors', operator=">", value=['True'])]
    frame.conditions = [
        Condition(target='visitorId', operator=None, value=['unspecified']),
        Condition(target='cfCountry', operator=">", value=['US'])]
    frame.question_type, frame.date, frame.conditions = (
        'yes/no', [],
        [Condition(target='visitorId', operator=None, value=['unspecified']),
         Condition(target='osTypes', operator=None, value=['Linux']),
         Condition(target='cfCountry', operator="max", value=['NL'])])
    frame.question_type, frame.date, frame.conditions = (
        'yes/no', [],
        [Condition(target='returningByVisitors', operator=None,
                   value=['True']),
         Condition(target='cfCountry', operator="max", value=['FR'])])
    frame.question_type, frame.date, frame.conditions = (
        'yes/no', [["2018-09-23"]],
        [Condition(target='visitorId', operator=None, value=['unspecified']),
         Condition(target='deviceTypes', operator=None, value=['mobile']),
         Condition(target='cfCountry', operator="max", value=['US'])])
    frame.question_type, frame.date, frame.conditions = (
        'CATEGORY', [],
        [Condition(target='referralType', operator=None, value=[4]),
         Condition(target='referralDomain', operator="max",
                   value=['unspecified'])]
    )
    question = "What percent of mobile users is american?"
    entities_before_mapping = {
        'visitorId': ['users'], 'deviceTypes': ['mobile'],
        'cfCountry': ['american']
    }
    frame.question_type, frame.date, frame.conditions = (
        'PERC', [],
        [Condition(target='visitorId', operator=None, value=['unspecified']),
         Condition(target='deviceTypes', operator=None, value=['mobile']),
         Condition(target='cfCountry', operator=None, value=['US'])])

    frame.question_type, frame.date, frame.conditions = (
        'yes/no', [['2018-10-15']],
        [Condition(target='visitorId', operator='>', value=['unspecified']),
         Condition(target='deviceTypes', operator=None, value=['mobile']),
         Condition(target='cfCountry', operator=None, value=['US'])])

    question = "are more sessions from google than from facebook?"
    # question = "how many sessions from google"
    question = "What percent is personalised?"
    question = "how many page per browser"
    question = "What percent is personalised?"
    question = "How many were on the personalised layer?"
    question = "how many Belgians saw personalised website?"
    frame.question_type, frame.date, frame.conditions = (
        'COMPARISON', [],
        [Condition(target='session', operator=None, value=['unspecified']),
         Condition(target='referralDomain', operator=None, value=['google',
                                                                  'facebook'
                                                                  ])])
    # frame.question_type, frame.date, frame.conditions = (
    #     'QUANTITY', [],
    #     [Condition(target='session', operator=None, value=['unspecified']),
    #      Condition(target='referralDomain', operator=None, value=[
    #          'facebook'])])
    frame.question_type, frame.date, frame.conditions = (
        'AVERAGE', [],
        [Condition(target='pageviews', operator=None, value=['unspecified']),
         Condition(target='session', operator=None, value=['unspecified'])])

    # frame.question_type, frame.date, frame.conditions = (
    #     'AVERAGE', [],
    #     [Condition(target='session', operator=None, value=['unspecified']),
    #      Condition(target='visitorId', operator=None, value=[
    # 'unspecified'])])

    frame.question_type, frame.date, frame.conditions = ('QUANTITY', [], [
        Condition(target='returningByVisitors', operator=None,
                  value=['True'])])
    frame.question_type, frame.date, frame.conditions = ('PERC', [], [
        Condition(target='layerId', operator=None,
                  value=['personalized'])])
    frame.question_type, frame.date, frame.conditions = ('QUANTITY', [], [
        Condition(target='layerId', operator=None,
                  value=['personalized'])])
    # frame.question_type, frame.date, frame.conditions = ('QUANTITY', [], [
    #     Condition(target='layerId', operator=None,
    #               value=['personalized']),
    # Condition(target="cfCountry", operator=None, value=["BE"])])
    # frame.question_type, frame.date, frame.conditions = ('QUANTITY', [], [
    #     Condition(target='layerId', operator=None,
    #               value=['unspecified'])])
    frame.question_type, frame.date, frame.conditions = ('CATEGORY', [], [
        Condition(target='layerId', operator="max",
                  value=['personalized'])])
    frame.question_type, frame.date, frame.conditions = ('CATEGORY', [], [
        Condition(target='cfCountry', operator="max",
                  value=['unspecified'])])
    frame.question_type, frame.date, frame.conditions = ('CATEGORY', [], [
        Condition(target='cfCountry', operator="max",
                  value=['unspecified']),
        Condition(target='deviceType', operator=None,
                  value=['mobile'])
    ])
    frame.question_type, frame.date, frame.conditions = ('QUANTITY', [],
                                                         [Condition(
                                                             target='visitorId',
                                                             operator=None,
                                                             value=[
                                                                 'unspecified']),
                                                             Condition(
                                                                 target='cfCountry',
                                                                 operator=None,
                                                                 value=['US']),
                                                             Condition(
                                                                 target='visitTime',
                                                                 operator='<=',
                                                                 value=[
                                                                     '60'])])
    print(get_postprocess_inside(question, entities_before_mapping, frame))
