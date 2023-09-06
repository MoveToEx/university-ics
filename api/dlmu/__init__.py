import json
import datetime
import time
import browser_cookie3 as bc
from bs4 import BeautifulSoup as bs
import js2py
import re
import requests
import base64
from Crypto.Cipher import DES

class_time = [
    None, (8, 0), (8, 50), (10, 0), (10, 50), (13, 30),
    (14, 20), (15, 30), (16, 20), (18, 0), (18, 50)
]


class API:
    def __init__(self):
        self.args = {
            'username': '',
            'password': '*',
        }
        self.geo = [
            (r'学汇楼', (38.868859, 121.527693)),
            (r'德济楼', (38.867199, 121.527789)),
            (r'励志楼', (38.866902, 121.529855)),
            (r'尚德楼', (38.867470, 121.530445)),
            (r'扬帆楼', (38.865717, 121.529046)),
            (r'四海楼', (38.867085, 121.528287)),
            (r'百川楼', (38.867694, 121.527149)),
            (r'游泳馆', (38.870818, 121.530099)),
            (r'数理楼', (38.869364, 121.532405)),
            (r'体育馆', (38.870361, 121.531165))
        ]
        self.session = requests.Session()

    def pad(text):
        if isinstance(text, str):
            text = text.encode()
        n = len(text) % 8
        if n == 0:
            n = 8
        return text + n.to_bytes(1, 'little') * n

    def find_geo(self, location):
        for i in self.geo:
            if re.search(i[0], location):
                return i[1]

    def fetch(self):
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Referer": "https://id.dlmu.edu.cn/login"
        }

        res = bs(self.session.get('https://id.dlmu.edu.cn/login').text, 'html.parser')

        crypto = res.select_one('#login-croypto').text

        print('key =', crypto)

        des = DES.new(base64.b64decode(crypto), DES.MODE_ECB)

        cipher = base64.b64encode(des.encrypt(API.pad(self.args['password'])))

        print('cipher =', cipher)

        form_data = {
            'username': self.args['username'],
            'type': res.select_one('#current-login-type').text,
            '_eventId': 'submit',
            'geolocation': '',
            'execution': res.select_one('#login-page-flowkey').text,
            'captcha_code': '',
            'croypto': crypto,
            'password': cipher
        }

        res = self.session.post('https://id.dlmu.edu.cn/login', data=form_data, allow_redirects=False)

        if res.status_code == 401:
            raise Exception('failed when logging in')
        elif res.status_code == 302:
            print('successfully logged in')

            self.session.get('https://hall.dlmu.edu.cn')
            print('session refreshed')

        data = []
            
        res = self.session.get('http://jw.xpaas.dlmu.edu.cn/eams/courseTableForStd.action')
        sid = re.search(r'semesterCalendar\({empty:"false",onChange:"",value:"(.*)"},"searchTable\(\)"\)', res.text).group(1)

        print('current semester id =', sid)

        body = {
            'ignoreHead': 1,
            'setting.kind': 'std',
            'startWeek': '',
            'semester.id': sid,
            'ids': ''
        }
        schedule = []
        self.session.headers.update({
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "http://jw.xpaas.dlmu.edu.cn",
            "Referer": "http://jw.xpaas.dlmu.edu.cn/eams/courseTableForStd.action"
        })

        res = self.session.get('http://jw.xpaas.dlmu.edu.cn/eams/courseTableForStd.action')

        body['ids'] = re.search(r'bg\.form\.addInput\(form,"ids","(.*)"\);', res.content.decode()).group(1)

        print('schedule id =', body['ids'])

        res = self.session.post('http://jw.xpaas.dlmu.edu.cn/eams/courseTableForStd!courseTable.action', data=body)

        src = bs(res.content.decode(), 'html.parser').select_one('#ExportA > script').string

        with open("./api/dlmu/underscore-esm.min.js", encoding='utf8') as f:
            js = f.read()

        res = self.session.get('http://jw.xpaas.dlmu.edu.cn/eams/static/scripts/course/TaskActivity.js?v3.21&_=' + str(time.time() * 1e3))

        js += res.content.decode('utf8') + re.sub(r"fillTable\(table0,\d*,\d*,\d*\);", "", src) + """
function(){
    ans = []
    for (var i = 0; i < 70; i++) {
        table0.activities[i].forEach(function(x) {
            var t = {
                "name": x.courseName.replace(/\s/g, ''),
                "teacher": x.teacherName,
                "location": x.roomName,
                "weeks": x.vaildWeeks,
                "weekday": Math.ceil((Number(i) + 1) / 10),
                "from": Number(i) % 10 + 1,
                "to": Number(i) % 10 + 1
            };
            var adj = ans.filter(function(w) {
                return w.weekday == t.weekday && Math.abs(w.from - t.from) == 1 && w.name == t.name;
            });
            if (adj.length) {
                ans.forEach(function(w, i) {
                    if (w.weekday == t.weekday && w.name == t.name) {
                        if (w.from < t.from) {
                            ans[i].to = t.to;
                        }
                        else if (w.from > t.from) {
                            ans[i].from = t.from;
                        }
                    }
                });
            }
            else {
                ans.push(t);
            }
        });
    }
    return ans;
}
"""
        data = js2py.eval_js(js)()

        for it in data:
            event = {
                "name": re.search(r'(.*)\(\d*\..{2}\)', it['name']).group(1),
                "teacher": it['teacher'],
                "location": it['location'],
                "weeks": [x for x in range(len(it['weeks'])) if it['weeks'][x] == '1'],
                "weekday": it['weekday'],
                "geo": "",
                "time": {
                    "from": datetime.timedelta(hours=class_time[it['from']][0], minutes=class_time[it['from']][1]),
                    "to": datetime.timedelta(hours=class_time[it['to']][0], minutes=class_time[it['to']][1] + 45)
                },
                "ext": []
            }
            geo = self.find_geo(it['location'])
            if geo:
                event['geo'] = "%f,%f" % (geo[0], geo[1])
                event['ext'].append({
                    "name": "X-APPLE-STRUCTURED-LOCATION",
                    "value": "geo:" + str(geo[0]) + ',' + str(geo[1]),
                    "parameters": {
                        "VALUE": "URI",
                        "X-TITLE": it['location']
                    }
                })
            schedule.append(event)
        return schedule

    def starting_date(self) -> datetime.datetime:
        self.session.headers.update({
            'Accept': 'application/json, text/plain, */*',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://hall.dlmu.edu.cn/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        })
        res = self.session.get('https://hall.dlmu.edu.cn/portal/api/v1/api/http/43')
        data = json.loads(res.text)
        
        if data['code'] != 200:
            raise Exception(data['error'])
        print('current semester starts at', data['data']['KSSJ'])

        ans = datetime.datetime.strptime(data['data']['KSSJ'], '%Y-%m-%d %H:%M:%S')
        ans += datetime.timedelta(hours=-12)
        return ans
