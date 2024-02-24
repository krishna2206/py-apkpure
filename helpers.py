import os
import re


class Helpers:
    # http://greenbytes.de/tech/tc2231/
    @staticmethod
    def filename_from_headers(headers):
        if isinstance(headers, str):
            headers = headers.splitlines()
        if isinstance(headers, list):
            headers = dict([x.split(':', 1) for x in headers])
        cdisp = headers.get("Content-Disposition")
        if not cdisp:
            return None
        cdtype = cdisp.split(';')
        if len(cdtype) == 1:
            return None
        if cdtype[0].strip().lower() not in ('inline', 'attachment'):
            return None
        # several filename params is illegal, but just in case
        fnames = [x for x in cdtype[1:] if x.strip().startswith('filename=')]
        if len(fnames) > 1:
            return None
        name = fnames[0].split('=')[1].strip(' \t"')
        name = os.path.basename(name)
        if not name:
            return None
        return name

    @staticmethod
    def set_icon_res(icon_url, res=None):
        try:
            res_param = re.findall("w=[0-9]*", icon_url)[0]
        except IndexError:
            return icon_url
        else:
            if res is not None:
                return icon_url.replace(res_param, f"w={res}")
            return icon_url
        
    @staticmethod
    def clean_value(value):
        return value.replace("\n", "").strip()