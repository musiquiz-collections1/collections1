import re

def html_entity_to_unicode(s):
    # Replace HTML numeric entities like &#8203; with the corresponding unicode character
    def replace_entity(match):
        code = match.group(1)
        try:
            return chr(int(code))
        except Exception:
            return match.group(0)
    return re.sub(r'&#(\d+);', replace_entity, s)
