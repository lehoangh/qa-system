import re

from word2number import w2n

from modules.text import Text

mappings = {
    'browserTypes': {
        'unspecified': ['Browser', 'Browsertype', 'Browsertypes',
                        'Browser Types', 'Browsers', "Browser Type"],
        'Edge': ['Edge'],
        'Chrome': ['Google Chrome', 'Chrome'],
        'Chrome Mobile': ['Chrome Mobile', 'Mobile Chrome'],
        'Firefox': ['Mozilla', 'Firefox', 'Mozilla Firefox'],
        'Safari': ['Safari'],
        'Mobile Safari': ['Mobile Safari', 'Safari Mobile'],
        'IE': ['Explorer', 'IE', 'Internet Explorer', 'Internet'],
        'Google Bot': ['Google Bot'],
        'Samsung Internet': ['Samsung Internet', 'Samsung Browser']
    },
    'deviceTypes': {
        'unspecified': ['Devicetype', 'Device Type', 'Type', 'Device',
                        'Devicetypes', 'Device Types'],
        'pc': ['Laptop', 'Pc', 'Laptops', 'PCs', 'PC'],
        'mobile': ['Smart Phone', 'Smartphone', 'Phone', 'Mobile Phone',
                   'Mobile', 'Cellphone', 'Cell Phone'],
        'tablet': ['Tablet']
    },
    'deviceBrands': {
        'unspecified': ['Devicebrand', 'Brand', 'Brands', 'Devicebrands',
                        'Device Brands', 'Device Brand'],
        'Apple': ['Apple'],
        'Samsung': ['Samsung'],
        'Spider': ['Spider'],
        'Acer': ['Acer', 'Acer Device'],
        'Asus': ['Asus', 'Asus Device'],
        'Huawei': ['Huawei'],
        'LG': ['LG', 'L.G.'],
        'Nokia': ['Nokia'],
        'Sony': ['Sony Ericsson', 'Ericsson', 'Sony'],
        'Generic_Android': ['Generic Android', 'Android'],
        'Motorola': ['Motorola'],
        'Lenovo': ['Lenovo'],
        'HP': ['HP', 'Hp'],
        'HTC': ['Htc'],
        'Generic': ['Generic'],
        'XiaoMi': ['Xiaomi']
    },
    'osTypes': {
        'unspecified': ['OS', 'Operating System', 'OsType', 'Operating Sys',
                        'Os', 'Operatingsystem', 'Operating Systems',
                        'Systems'],
        'iOS': ['Ios', 'IOS'],
        'Windows': ['Windows'],
        'Linux': ['Linux'],
        'Android': ['Android'],
        'Mac OS X': ['Mac X', 'Mac OS X'],
        'Ubuntu': ['Ubuntu'],
    },
    'cfCountry': {
        'unspecified': ['Country', 'Where', 'Place', 'Countries',
                        'Nationality', 'Nationalities', 'Places',
                        'Destination', 'Destinations', 'Location'],
        'BE': ['Be', 'Belgium', 'Bel', 'Belgian', 'Belgians'],
        'US': ['Us', 'United States', 'The United States', 'U.S.', 'The US',
               'The USA', 'USA', 'U.S.A.', 'The States', 'America', 'Murica',
               'American', 'Americans'],
        'PT': ['Pt', 'Portugal', 'Portugese', 'Portuguese'],
        'NL': ['Nl', 'Netherlands', 'The Netherlands', 'Dutch'],
        'BR': ['Br', 'Brazil', 'Brasil', 'Brasilian', 'Brazilian',
               'Brazilians', 'Brasilians'],
        'DE': ['De', 'Germany', 'German', 'Germans'],
        'FR': ['Fr', 'France', 'French'],
        'IT': ['It', 'Italy', 'Italian', 'Italians'],
        'JP': ['Jp', 'Japan', 'Japanese', 'The Land Of The Rising Sun',
               'land of the rising sun'],
        'BH': ['Bh', 'Bahrain'],
        'IE': ['Ie', 'Ireland', 'Irish'],
        'BZ': ['Bz', 'Belize'],
        'CA': ['Ca', 'Canada', 'Canadian', 'Canadese', 'Canadians'],
        'HK': ['Hk', 'Hong Kong'],
        'ES': ['Es', 'Spain', 'Mallorca', 'Spanish'],
        'VN': ['Vn', 'Vietnam', 'Viet Nam', 'Vietnamese'],
        'IN': ['In', 'India', 'Indian', 'Indians'],
        'MX': ['Mx', 'Mexico', 'Mexican', 'Mexicans'],
        'CN': ['Cn', 'China', 'Chinese'],
        'RU': ['Ru', 'Russia', 'Russian', 'Russian Federation', 'Putinland',
               'Russians'],
        'CO': ['Co', 'Colombia', 'Colombian', 'Colombians'],
        'EC': ['Ec', 'Ecuador', 'Ecuadoreans', 'Ecuadorean'],
        'CR': ['Cr', 'Costa Rica'],
        'DK': ['Dk', 'Denmark', 'Danish'],
        'PL': ['Pl', 'Poland', 'Polish'],
        'NO': ['No', 'Norway', 'Norwegian', 'Norwegians'],
        'SG': ['Sg', 'Singapore', 'Singaporean', 'Singaporeans'],
        'GR': ['Gr', 'Greece', 'Grecian', 'Grecians', 'Greek', 'Greeks'],
        'GB': ['Gb', 'Great-Britain', 'United Kingdom', 'UK', 'The UK',
               'Great Britain', 'Britain', 'England', 'British', 'English'],
        'NZ': ['Nz', 'New Zealand'],
        'EG': ['Eg', 'Egypt', 'Egyptian', 'Egyptians'],
        'FI': ['Fi', 'Finland', 'Finnish'],
        'AU': ['Au', 'Australia', 'Australian', 'Australians'],
        'HU': ['Hu', 'Hungary', 'Hungarian', 'Hungarians'],
        'CZ': ['Cz', 'Czech Republic', 'Czech'],
        'AT': ['At', 'Austria', 'Austrian', 'Austrians'],
        'LU': ['Lu', 'Luxemburg', 'Luxembourg'],
        'SE': ['Se', 'Sweden', 'Swedish'],
        'PA': ['Panama']
    },
    "languages": {
        'unspecified': ['Language', 'Lang', 'Speak', 'Languages'],
        'ar': ['Ar', 'Arabic'],
        'bs': ['Bs', 'Bosnian'],
        'zh': ['Zh', 'Chinese'],
        'cs': ['Cs', 'Czech'],
        'hr': ['Hr', 'Croatian'],
        'da': ['Da', 'Danish'],
        'en': ['En', 'English'],
        'nl': ['Nl', 'Dutch'],
        'de': ['De', 'German'],
        'fr': ['Fr', 'French'],
        'fi': ['Fi', 'Finnish'],
        'el': ['El', 'Greek'],
        'hi': ['Hi', 'Hindi'],
        'he': ['He', 'Hebrew'],
        'hu': ['BZ', 'Hungarian'],
        'it': ['It', 'Italian'],
        'ja': ['Ja', 'Japanese'],
        'lu': ['Lu', 'Lithuanian'],
        'no': ['No', 'Norwegian'],
        'ps': ['Ps', 'Polish'],
        'pt': ['Pt', 'Portuguese'],
        'ru': ['Ru', 'Russian'],
        'es': ['Es', 'Spanish'],
        'sv': ['Sv', 'Swedish'],
        'tr': ['Tr', 'Turkish'],
        'vi': ['Vi', 'Vietnamese']
    },
    "referralType": {
        'unspecified': ['Referral', 'Referral Type', 'ReferralType',
                        'Referral', 'Referraltype', 'Type', 'Types',
                        'Referraltypes', 'Referral Types'],
        1: ['Direct', 'Direct Referral', 'Direct Referring',
            'Direct Referrals'],
        2: ['Internal', 'Internal Referral', 'Internal Referring',
            'Internal Referrals'],
        5: ['Email', 'Email Referral', 'Email Referring', 'E-mail',
            'E-mail Referral', 'Email Referrals'],
        3: ['Social Media', 'Social', 'Social Referral',
            'Social Media Referral', 'Social Referrals',
            'Social Media Referrals'],
        4: ['Search Engine', 'Search Engine Referral',
            'Search Engine Referrals', 'Engine', 'Search Engines'],
        8: ['Advertising', 'Advertisement', 'Advertisement Referral',
            'Advertisement Referrals', 'Advertising Referrals',
            'Advertisement Referring', 'Ad Referral', 'Ad Referrals'],
        7: ['Android', 'Android Referral', 'Android App Referrals',
            'Android App Referring']
    },

    "pagesPerVisitor": {
        'unspecified': ['Page', 'Pages', 'Views'],
        '1': ['Homepage', 'Single', 'One']
    },
    "visitTime": {
        "unspecified": ['Time', 'Long', 'Duration', 'Length', 'Visiting Time',
                        'Visittime', 'Visit Time']
    },
    "referralDomain": {
        'unspecified': ['Referral', 'Referral Domain', 'Referraldomain',
                        'Referraldomains', 'Domain', 'Website', 'Domains',
                        'Websites', 'Referral Domains', 'Referrals',
                        'Referral Domains', 'Referrer']
    },
    "returningByVisitors": {
        'True': ['Come Back', 'Return', 'Returning', 'Came Back', 'Returned',
                 'Returners', 'Returner'],
        'False': ['New', 'First Time', 'First Timers']
    }

}


def value_mapper(target, string):
    singlevalue = string.title().strip()
    #print('single value: ', singlevalue)

    result = "unspecified"

    if target == "visitTime" and [k for (k, v) in mappings[target].items() if
                                  singlevalue in v] != ["unspecified"]:
        time_phrase = "([^\s]+)(\s+)(minutes?|seconds?|secs?|mins?)"
        time_pattern = re.compile(time_phrase, flags=re.I)
        matches = time_pattern.search(singlevalue)
        if matches:
            number = None
            matches_phrase = matches.group()
            first_part = matches_phrase.split(" ")[0]
            second_part = matches_phrase.split(" ")[1]
            text_obj = Text(second_part, "en")
            text_obj.preprocess()
            if any(item in text_obj.lemmas for item in ["minute", "min"]):
                if first_part.isdigit():
                    number = int(first_part) * 60
                elif first_part.lower() == 'a':
                    number = 60
                else:
                    number = w2n.word_to_num(first_part.lower()) * 60

            elif any(item in text_obj.lemmas for item in ["second", "sec"]):
                if first_part.isdigit():
                    number = int(first_part)
                elif first_part.lower() == 'a':
                    number = 1
                else:
                    number = w2n.word_to_num(first_part.lower())
        # else:
        # if the case is `between 2 and 5 minutes` or `between 2 and 5
        # secs`, the singlevalue is 2, how to detect
        # 2 is 2 minutes or 2 secs?, need to regexp the question

        try:
            return str(number)
        except UnboundLocalError:
            pass

    elif target == "pagesPerVisitor":
        if singlevalue.lower() in ["homepage", "homepages", 'a', "single",
                                   "home"]:
            number = 1
        elif singlevalue.isdigit():
            number = int(singlevalue)
        else:
            number = w2n.word_to_num(singlevalue.lower())
        result = str(number)


    elif target == 'referralDomain':
        if singlevalue in mappings['referralDomain']['unspecified']:
            result = 'unspecified'
        else:
            result = singlevalue.lower()

    elif target == 'visitorId' or target == 'pageviews':
        result = 'unspecified'


    else:
        try:
            for key in mappings[target]:
                if singlevalue in mappings[target][key]:
                    result = key
                    return result
                else:
                    result = 'unrecognized'
        except KeyError:
            result = 'unspecified'

    return result


if __name__ == "__main__":
    print(value_mapper(target="referralType", value="email"))
