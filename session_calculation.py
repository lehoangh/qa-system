from statistics import median, mean

INVALID_VALUE = 0


"""the function to calculate visit time/pages per visitors according to 
sessions for each unique users"""
def get_cal_by_session_by_uvID(db_uvID, uvt, qtype):
    session = list()
    session_vt = dict()

    for visitor in list(db_uvID):
        session_vt["_id"] = visitor["_id"]
        session_vt["session"] = list()
        idx = list(
            filter(lambda x: x != -1, visitor["details"][0]["session_idx"]))
        total = INVALID_VALUE
        if idx:
            # print("id: ", visitor["_id"])
            idx.append(-1)
            prev = 0
            last = 0
            for index in idx:
                last = index
                if last < len(visitor["details"][0][
                                  "visitTime"]) and prev < last + 1:
                    total = sum(
                        visitor["details"][0]["visitTime"][prev:last + 1])
                elif last == -1:
                    total = sum(visitor["details"][0]["visitTime"][prev:])
                if total > INVALID_VALUE:
                    session_vt["session"].append(total)
                if last != -1:
                    prev = last + 1
                else:
                    prev = prev
                # print("length: ", len(visitor["details"][0]["visitTime"]))
                # print("prev: ", prev)
                # print("last: ", last)
        else:
            total = sum(visitor["details"][0]["visitTime"])
            if total > INVALID_VALUE:
                session_vt["session"].append(total)

        session.append(session_vt.copy())

    # pprint.pprint(session)

    # filter out the empty session list
    session = list(filter(lambda x: x["session"], session))

    by_session = list()

    for visitor in session:
        avg_by_visitor_by_session = {}
        avg_by_visitor_by_session["_id"] = visitor["_id"]
        avg_by_visitor_by_session["avg"] = mean(visitor["session"])
        avg_by_visitor_by_session["median"] = median(visitor["session"])
        avg_by_visitor_by_session["count"] = len(visitor["session"])

        by_session.append(avg_by_visitor_by_session)

    # pprint.pprint(by_session)

    session_result = 0

    if qtype == "MEDIAN":
        # median of VisitorVisitTime per each session
        session_result = median(
            [value for visitor in by_session for key, value in visitor.items()
             if key == "median"])
    elif qtype in ["AVERAGE", "CATEGORY", "QUANTITY"]:
        # average of VisitorVisitTime per each session
        session_result = sum(
            [value for visitor in by_session for key, value in visitor.items()
             if key == "avg"]) / uvt
    elif qtype == "PERC":
        session_result = sum(
            [value for visitor in by_session for key, value in visitor.items()
             if key == "count"]) / uvt * 100
    # elif qtype == "QUANTITY":
    #     session_result = len(session_lst)

    return session_result
