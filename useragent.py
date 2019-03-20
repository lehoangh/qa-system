#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug  2 11:10:50 2018

@author: lehoa
"""
from ua_parser import user_agent_parser
from user_agents import parse


class Useragent:
    def __init__(self, ua_string):
        self.raw = ua_string
        self.deviceType = None
        self.deviceBrand = None
        self.browserType = None
        self.osType = None
        self.touch = None
        self.res = {}

    def get_device_type(self, user_agent):
        if user_agent.is_mobile is True:
            self.deviceType = "mobile"
        elif user_agent.is_tablet is True:
            self.deviceType = "tablet"
        elif user_agent.is_pc is True:
            self.deviceType = "pc"

    def ua_extract(self, targets_gen):
        parsed_string = user_agent_parser.Parse(self.raw)
        #                print(parsed_string)

        # deviceType
        useragent = parse(self.raw)
        self.get_device_type(useragent)
        # item['deviceType'] = deviceType

        # deviceBrand
        self.deviceBrand = parsed_string['device']['brand']
        # if deviceBrand is not None:
        #     frequency(deviceBrand, device)
        # item['deviceBrand'] = device

        # browserType
        self.browserType = parsed_string['user_agent']['family']
        # frequency(browserType, browser)
        # item['browserType'] = browser

        # osType
        self.osType = parsed_string['os']['family']
        # frequency(osType, osFamilies)
        # item['osType'] = osFamilies
        #
        # # results.append(item.copy())
        # print(100 * '-')
        # return item.copy()

        # touch
        if useragent.is_touch_capable:
            self.touch = True
        else:
            self.touch = False

        mapping = {
            "deviceTypes": self.deviceType, "deviceBrands": self.deviceBrand,
            "browserTypes": self.browserType, "osTypes": self.osType,
            "touch": self.touch
        }

        for target in targets_gen:
            self.res[target] = mapping[target]
        return self.res
        # if target == "deviceTypes":
        #     return self.deviceType
        # elif target == "deviceBrands":
        #     return self.deviceBrand
        # elif target == "browserTypes":
        #     return self.browserType
        # elif target == "osTypes":
        #     return self.osType


#
# item = dict()
#
# # deviceType extraction
# deviceType = dict()
# deviceType['mobile'] = 0
# deviceType['pc'] = 0
# deviceType['tablet'] = 0
#
# # deviceBrands
# device = dict()
#
# # browserTypes
# browser = dict()
#
# # osTypes
# osFamilies = dict()
#
#
#
#
# # calculation the general frequency
# def frequency(key, key_dict):
#     try:
#         key_dict["count"] += 1
#     except KeyError:
#         key_dict["count"] = 1
#
#     if key in key_dict:
#         key_dict[key] += 1
#     else:
#         key_dict[key] = 1
#
#
# # calculation frequency for deviceType (special case)
#     def device_type_freq(user_agent, returndict):
#         try:
#             returndict["count"] += 1
#         except KeyError:
#             returndict["count"] = 1
#
#         if user_agent.is_mobile is True:
#             returndict["mobile"] += 1
#         elif user_agent.is_tablet is True:
#             returndict["tablet"] += 1
#         elif user_agent.is_pc is True:
#             returndict["pc"] += 1
#
#
#
#
# # extracting useragent field
# def useragent_extract(visits, domains):
#     results = list()
#
#     for domain in domains:
#         item = dict()
# #        print('domain: ', domain)
#         item['domain'] = domain
#
#         # deviceType extraction
#         deviceType = dict()
#         deviceType['mobile'] = 0
#         deviceType['pc'] = 0
#         deviceType['tablet'] = 0
#
#         # deviceBrands
#         device = dict()
#
#         # browserTypes
#         browser = dict()
#
#         # osTypes
#         osFamilies = dict()
#
#         # the number of visit no have `useragent` column
#         cnt = 0
#         # print('the amount of records for {} is {}'.format(domain,
# visits.count_documents({'domain': domain})))
#         # domain_records = visits.find({'domain': domain})
#         # for visit in domain_records:
#         for visit in visits:
#             # print('record: ', visit['domain'])
#             if 'useragent' in visit:
# #                print('\n', visit['useragent'])
#                 parsed_string = user_agent_parser.Parse(visit['useragent'])
# #                print(parsed_string)
#
#                 # deviceType
#                 useragent = parse(visit['useragent'])
#                 device_type(useragent, deviceType)
#                 item['deviceTypes'] = deviceType
#
#                 # deviceBrands
#                 deviceBrand = parsed_string['device']['brand']
#                 if deviceBrand is not None:
#                     frequency(deviceBrand, device)
#                 item['deviceBrands'] = device
#
#                 # browserTypes
#                 browserType = parsed_string['user_agent']['family']
#                 frequency(browserType, browser)
#                 item['browserTypes'] = browser
#
#                 # osTypes
#                 osType= parsed_string['os']['family']
#                 frequency(osType, osFamilies)
#                 item['osTypes'] = osFamilies
#             else:
#                 cnt += 1
# #        print('There are ', cnt ,' empty useragent')
#         results.append(item)
#         print('Finished domain {}'.format(domain))
#         print(100 * '-')
#     return results
#
#
#
#
# # output a JSON file
# def json_output(results):
#     print('Starting to write the JSON file')
#     with open(os.path.join(os.getcwd(), 'output.json'), 'w') as outf:
#         json.dump(results, outf)
#     print('Finished all')
#
# def main():
#     visits = connect_db()
#     domains = get_all_domains(visits)
# #    print('Domains: ', domains)
# #    print('Total: ', len(domains))
#     results = useragent_extract(visits, domains)
#     json_output(results)


if __name__ == "__main__":
    # results = dict()
    # # print(useragent_string_extract("Mozilla/5.0 (X11; Ubuntu; Linux
    # x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"), results.copy())
    #
    # results = useragent_string_extract("Mozilla/5.0 (X11; Ubuntu; Linux
    # x86_64; rv:62.0) Gecko/20100101 Firefox/62.0", results.copy())
    # results = useragent_string_extract("Mozilla/5.0 (X11; Ubuntu; Linux
    # x86_64; rv:62.0) Gecko/20100101 Firefox/62.0",
    #                          results.copy())
    # print(results)
    ua_str = "Mozilla/5.0 (Linux; Android 8.0.0; BLA-L29 " \
             "Build/HUAWEIBLA-L29S) AppleWebKit/537.36 (KHTML, like Gecko) " \
             "Chrome/68.0.3440.91 Mobile Safari/537.36"
    ua_exp = Useragent(ua_str)
    print("Before:\n")
    print(ua_exp.deviceType)
    print(ua_exp.deviceBrand)
    print(ua_exp.browserType)
    print(ua_exp.osType)
    print("a. ", ua_exp.ua_extract(["osTypes", "deviceTypes"]))
    print("After:\n")
    print(ua_exp.deviceType)
    print(ua_exp.deviceBrand)
    print(ua_exp.browserType)
    print(ua_exp.osType)
