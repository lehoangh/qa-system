import warnings

from pymongo import MongoClient

warnings.simplefilter("ignore", DeprecationWarning)
import pprint

client = MongoClient()
base = client['visits']
db = base.visits

print(db.count())

pprint.pprint(db.find_one({"domain": "brunel.nl"}))


"""
count = 0
for visit in db.find():
    count += 1
    if len(visit['conversion']) > 0:
        print(count, visit['conversion'])


print('done. len=', count)
"""
# unique_visitors = []
# for visit in db.find():
#     unique_visitorsvisit['visitorId']

db_a = db.aggregate([
    {"$match": {"domain": "brunel.nl"}},
    {"$group": {"_id": "$visitorId",
                "layers": {"$addToSet": "$layerId"}}}
])

db = db.find({"domain" : "brunel.nl"})

count = 0
layersset = []
for i in list(db):
    if i.get("layerId"):
        if i["layerId"] not in layersset:
            layersset.append(i["layerId"])

        count += 1

print(count)
print(set(layersset))

