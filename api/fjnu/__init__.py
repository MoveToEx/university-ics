import requests
import json
from parse import parse
import execjs
import time
from datetime import timedelta as td
from bs4 import BeautifulSoup as bs
import re

class_time = {
    "旗山校区": [None, (8, 20), (9, 15), (10, 20), (11, 15), (14, 0), (14, 55),
             (15, 50), (16, 45), (18, 30), (19, 25), (20, 20), (21, 15)],
    "仓山校区": [None, (8, 00), (8, 55), (10, 00), (10, 55), (14, 0), (14, 55),
             (15, 50), (16, 45), (18, 30), (19, 25), (20, 20), (21, 15)]
}

duration = 45

class API:
    def __init__(self):
        self.args = {
            "uid": "",
            "password": "*",
            "year": "",
            "semester": ""
        }
        with open("./api/fjnu/encrypt.min.js", "r") as f:
            self.encryptor = execjs.compile(f.read())

    def fetch(self):
        s = requests.Session()
        semester = [None, 3, 12, 16][int(self.args['semester'])]
        ts = int(time.time() * 1e3)
        data = {
            "language": "zh_CN"
        }

        # Init CSRF token
        res = s.get('https://jwglxt.fjnu.edu.cn/jwglxt/xtgl/login_slogin.html')
        data['csrftoken'] = bs(res.content.decode('utf8'), 'html.parser').find('input', { "name": "csrftoken" }).attrs['value']
        
        s.headers = {
            "Origin": "https://jwglxt.fjnu.edu.cn",
            "Referer": "https://jwglxt.fjnu.edu.cn/jwglxt/xtgl/login_slogin.html",
        }

        print("csrk token =", data['csrftoken'])

        # Encrypt
        res = s.get('https://jwglxt.fjnu.edu.cn/jwglxt/xtgl/login_getPublicKey.html?time=' + str(ts))
        rsa_arg = json.loads(res.content.decode('utf8'))

        data['yhm'] = self.args['uid']
        data['mm'] = self.encryptor.call('encrypt', self.args['password'], rsa_arg['modulus'], rsa_arg['exponent'])

        print("key =", rsa_arg['exponent'], rsa_arg['modulus'])

        # Login
        res = s.post('https://jwglxt.fjnu.edu.cn/jwglxt/xtgl/login_slogin.html?time=' + str(ts), data = data)

        if res.content.decode('utf8').find('不正确') != -1:
            raise ValueError("Invalid user ID or password.")
        
        print("successfully logged in")

        res = s.post('https://jwglxt.fjnu.edu.cn/jwglxt/kbcx/xskbcx_cxXsgrkb.html?gnmkdm=N253508&layout=default&su=' + self.args['uid'], data={
            "xnm": self.args['year'],
            "xqm": semester,
            "kzlx": "ck"
        })

        print("fetched schedule descriptor")

        content = json.loads(res.content.decode('utf8'))['kbList']

        res = []

        # 写后端的傻逼我囸你妈

        for it in content:
            _ = parse("{}-{}", it['jcs'])
            if not _:
                raise NotImplementedError("Unimplemented class index format: " + it['jcs'])
            _class = [int(_[0]), int(_[1])]
            campus = it['xqmc']

            weeks = []
            for s in it['zcd'].split(','):
                s = s.strip()
                if re.match(r"\d*-\d*周\(.*\)", s):
                    _ = parse("{}-{}周({})", s)
                    if _[2] == '单':
                        weeks = weeks + [x for x in range(int(_[0]), int(_[1]) + 1) if x % 2 == 1]
                    elif _[2] == '双':
                        weeks = weeks + [x for x in range(int(_[0]), int(_[1]) + 1) if x % 2 == 0]
                    else:
                        raise Exception("?")
                elif re.match(r"\d*-\d*周", s):
                    _ = list(map(int, parse("{}-{}周", s)))
                    weeks = weeks + list(range(_[0], _[1] + 1))
                elif re.match(r"\d*周", s):
                    _ = parse("{}周", s)
                    weeks.append(int(_[0]))
                else:
                    raise NotImplementedError("Unsupported week index format: " + s)


            res.append({
                "name": it['kcmc'],
                "teacher": it['xm'],
                "location": it['cdmc'],
                "time": {
                    "from": td(hours=class_time[campus][_class[0]][0], minutes=class_time[campus][_class[0]][1]),
                    "to": td(hours=class_time[campus][_class[1]][0], minutes=class_time[campus][_class[1]][1] + duration)
                },
                "weeks": weeks,
                "weekday": int(it['xqj']),
                'geo': '',
                'ext': []
            })
        return res
