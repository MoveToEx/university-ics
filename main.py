import getpass
import datetime
import argparse
import uuid
import icalendar as ics
import importlib as il

parser = argparse.ArgumentParser()

parser.add_argument('module')
parser.add_argument('-o', '--output', help='output file', default='output.ics')
parser.add_argument('-v', '--verbose', action='store_true', help='pint debug info')
parser.add_argument('-d', '--start_date', help='starting date of current semester, yyyy/mm/dd')

args = parser.parse_args()
cal = ics.Calendar()
api = il.import_module('api.' + args.module).API()

cal['dtstart'] = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
cal['summary'] = "CLASS SCHEDULE"
cal['prodid'] = "DLMU-ics"

def debug(*s):
    if args.verbose:
        print(*s)

for key in api.args:
    if api.args[key] == "":
        api.args[key] = input(key + '=')
    elif api.args[key] == "*":
        api.args[key] = getpass.getpass(key)

data = api.fetch()
week = 0
count = 0

if 'starting_date' in dir(api):
    t = api.starting_date()
elif not args.start_date:
    s = input("date(default=2022/8/29)=")
    if len(s):
        t = datetime.datetime.strptime(s, '%Y/%m/%d')
    else:
        t = datetime.datetime(2022, 8, 29)
    print('----------')
else:
    t = datetime.datetime.strptime(args.start_date, '%Y/%m/%d')

for i in range(365):
    if i % 7 == 0:
        week += 1
    debug("date index:", i, t)
    for it in data:
        if week in it['weeks'] and i % 7 + 1 == it['weekday']:
            count = count + 1
            debug("\t", it['name'], it['time']['from'], it['time']['to'])

            event = ics.Event()

            # Mandatory
            event['dtstamp'] = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
            event['dtstart'] = (t + it['time']['from']).strftime("%Y%m%dT%H%M%S")
            event['dtend'] = (t + it['time']['to']).strftime("%Y%m%dT%H%M%S")
            event['uid'] = str(uuid.uuid4()).upper()

            # Optional
            event['summary'] = it['name']
            event['description'] = '授课教师: ' + it['teacher']
            
            if it['location']:
                event['location'] = it['location']

            if it['geo']:
                event['geo'] = it['geo']

            if it['ext']:
                for item in it['ext']:
                    event.add(**item)

            cal.add_component(event)
    t += datetime.timedelta(days=1)

print(count, "events in total")
print("writing output to", args.output, "...")

with open(args.output, 'wb') as f:
    f.write(cal.to_ical())

print("success")