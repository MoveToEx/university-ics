import datetime
import time
import browser_cookie3 as bc
import bs4
import js2py
import re
import requests

class_time = [
    None, (8, 0), (8, 50), (10, 0), (10, 50), (13, 30), (14,
                                                         20), (15, 30), (16, 20), (18, 0), (18, 50)
]


class DLMUApi:
    def __init__(self):
        self.args = {}
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

    def find_geo(self, location):
        for i in self.geo:
            if re.search(i[0], location):
                return i[1]

    def fetch(self):
        data = []
        body = {
            'ignoreHead': 1,
            'setting.kind': 'std',
            'startWeek': '',
            'semester.id': '37',
            'ids': ''
        }
        schedule = []
        js = ""
        s = requests.Session()
        s.cookies = bc.load('dlmu.edu.cn')
        s.headers = {
            "Accept": "*/*",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "http://jw.xpaas.dlmu.edu.cn",
            "Referer": "http://jw.xpaas.dlmu.edu.cn/eams/courseTableForStd.action",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }

        res = s.get('http://jw.xpaas.dlmu.edu.cn/eams/courseTableForStd.action')

        body['ids'] = re.search(
            r'bg.form.addInput\(form,"ids","(.*)"\);', res.content.decode()).group(1)

        res = s.post(
            'http://jw.xpaas.dlmu.edu.cn/eams/courseTableForStd!courseTable.action', data=body)

        src = bs4.BeautifulSoup(res.content.decode(), 'html.parser').select_one(
            '#ExportA > script').string

        with open("./underscore-esm.min.js", encoding='utf8') as f:
            js = f.read()

        res = s.get(
            'http://jw.xpaas.dlmu.edu.cn/eams/static/scripts/course/TaskActivity.js?v3.21&_=' + str(time.time() * 1e3))

        js = js + res.content.decode('utf8') + re.sub("fillTable\\(table0,\\d*,\\d*,\\d*\\);", "", src) + """
function get() {
    ans = []
    for (var i in table0.activities) {
        if (table0.activities[i][0]) {
            var t = {
                "name": table0.activities[i][0].courseName,
                "teacher": table0.activities[i][0].teacherName,
                "location": table0.activities[i][0].roomName,
                "weeks": table0.activities[i][0].vaildWeeks,
                "weekday": Math.ceil((Number(i) + 1) / 10),
                "index": Number(i) % 10 + 1
            };
            ans.push(t);
        }
    }
    return ans;
}
get
"""
        data = js2py.eval_js(js)()

        for i in data:
            event = {
                "name": re.search(r'(.*)\(\d*\.\d*\)', i['name']).group(1),
                "teacher": i['teacher'],
                "location": i['location'],
                "weeks": [x for x in range(len(i['weeks'])) if i['weeks'][x] == '1'],
                "weekday": i['weekday'],
                "time": {
                    "from": datetime.timedelta(hours=class_time[i['index']][0], minutes=class_time[i['index']][1]),
                    "to": datetime.timedelta(hours=class_time[i['index']][0], minutes=class_time[i['index']][1] + 45)
                },
                "ext": []
            }
            geo = self.find_geo(i['location'])
            if geo:
                event['ext'].append({
                    "name": "X-APPLE-STRUCTURED-LOCATION",
                    "value": "geo:" + str(geo[0]) + ',' + str(geo[1]),
                    "param": {
                        "VALUE": "URI",
                        "X-TITLE": i['location']
                    }
                })
            schedule.append(event)
        return schedule
