import time

from pymongo import MongoClient

from modules.lang import lang_extract
from modules.useragent import Useragent

visitsdburi = 'mongodb://localhost:27017'
visitsdbstr = 'visits'
ipadbstr = "ipa_db"
domain = "brunel.nl"
ipaDB = MongoClient(visitsdburi)[ipadbstr]["ipa"]

"""connect the visits database"""


def connect_db():
    print('Connecting database ' + 10 * '.')
    client = MongoClient(visitsdburi)[visitsdbstr]
    db_v = client['visits']
    print('Finished')
    print(100 * '-')
    return db_v


"""select some useful columns for the IPA DB"""


def column_selection_from_DB_v(db_v):
    columns = ["created", "visitorId", "domain", "cfCountry", "bounce",
               "adBlock", "referralDomain", "referralType", "visitTime",
               "conversion", "layerId", "useragent", "page"]
    domain = "brunel.nl"
    match = {"domain": domain}
    project = {col: 1 for col in columns}

    DB = list(db_v.find(match, project))
    return DB


"""parsing useragent and page columns to take different columns"""


def process_ua_lang(DB):
    ua_str = "useragent"
    ua_lst = ["deviceTypes", "deviceBrands", "browserTypes", "osTypes",
              "touch"]
    pg_str = "page"
    for visit in DB:
        if visit.get(ua_str):
            ua_parsing = Useragent(ua_string=visit[ua_str]).ua_extract(
                targets_gen=ua_lst)
            visit.pop(ua_str)
            visit.update(ua_parsing)
        if visit.get(pg_str):
            pg_parsing = dict()
            pg_parsing["languages"] = lang_extract(domain=domain,
                                                   page=visit[pg_str])
            visit.pop(pg_str)
            visit.update(pg_parsing)

    return DB


"""combine the document and create a database"""


def create_ipa_db(DB):
    if ipaDB.count_documents({}) > 0:
        ipaDB.drop()
        ipaDB.insert_many(DB)
    else:
        ipaDB.insert_many(DB)


def main():
    db_v = connect_db()
    DB = column_selection_from_DB_v(db_v)
    start_time_perf = time.perf_counter()
    start_time_proc = time.process_time()
    DB = process_ua_lang(DB)
    print("The processing time for parsing 1 [min]: ",
          (time.perf_counter() - start_time_perf) / 60)
    print("The processing time for parsing 2 [min]: ",
          (time.process_time() - start_time_proc) / 60)
    print("length of total pageviews: ", db_v.count_documents({}))
    create_ipa_db(DB)
    print("The total time 1 [min]: ",
          (time.perf_counter() - start_time_perf) / 60)
    print("The total time 2 [min]: ",
          (time.process_time() - start_time_proc) / 60)


if __name__ == "__main__":
    main()
