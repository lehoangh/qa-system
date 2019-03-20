"""
The function to extract the language code from the url of the website
"""

# default libraries
import re

# custom files
from resources.en.lang_data import lang
from resources.en.lang_default import default_lang

default_code = 'nl'


# The function to extract language from url
def lang_extract(domain, page):
    # FIX CODE for extracting language code
    if domain == 'pharmamarket.be':
        k = re.search(r'\_([a-zA-Z]+)', page)

        # group(1) for result is only 'nl', not contains '_'
        if k and lang.get(k.group(1)):
            code = k.group(1)
            return code
        else:
            # return lang[default_code]
            return default_lang[domain]
    else:
        # ** OTHER DOMAINS
        # the url having formats: .be/nl-be/ or :8002/nl-be/
        k = re.search(r'(\.([a-zA-Z]+)|\:\d+)\/(\w{2})-(\w{2})\/', page)
        if k and lang.get(k.group(3)):
            code = k.group(3)
            # OR code = k.group(0).split('-')[0].split('/')[1]
            return code
        else:
            # the url having formats: .be/nl or :8002/nl or .be/te-koop
            k = re.search(r'(\.([a-zA-Z]+)|\:\d+)\/([a-zA-Z\-\_]+)', page)
            if k and lang.get(k.group(3)):
                code = k.group(3)
                return code
            else:
                # return lang[default_code]
                return default_lang[domain]
