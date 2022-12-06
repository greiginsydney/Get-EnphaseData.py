# -*- coding: utf-8 -*-
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
# This script is part of our solar monitoring project. See:
# https://github.com/greiginsydney/Get-EnphaseData.py
# https://greiginsydney.com/get-enphasedata-py
# https://greiginsydney.com/category/prtg/


# from *WINDOWS* call as python ./Get-EnphaseData.py '{\"host\":\"<IP>"}'
# e.g. C:\Get-EnphaseData\python> &"C:\Program Files (x86)\PRTG Network Monitor\python\python" ./Get-EnphaseData.py '{\"host\":\"http://<IP>"}'


import json
import re           # for the regex replacement (sub)
import requests     # for the web call to Enphase
import sys
from requests.auth import HTTPDigestAuth

#Customise this with your own credentials:
username = 'envoy'
password = '12345'

if __name__ == "__main__":
    try:
        url = ''
        if len(sys.argv) > 1:
            args = json.loads(sys.argv[1])
            # Check for 'host' and 'params' keys in the passed JSON, with params taking precedence:
            # (We strip any http or https prefix, but there's no other validation)
            for i in ("host", "params"):
                if args.get(i):
                    url = re.sub("https?:", "", args[i]).strip().strip('/')
            result = {'prtg': {'text' : "This sensor queries %s" % url}}
        if len(url) == 0:
            result = {'prtg': {'text' : 'Unsufficient or bad arguments', 'error' : {'args' : sys.argv}}}
            print(json.dumps(result))
            sys.exit(1)
        try:
            response = None
            query = "http://" + url + "/api/v1/production/inverters"
            response = requests.get(query, timeout=20, auth=HTTPDigestAuth(username, password))
            response.raise_for_status() #Throws a HTTPError if we didn't receive a 2xx response
            jsonResponse = json.loads(response.text)

            if jsonResponse:
                result['prtg'].update({'result': []})
                
                result['prtg']['result'].append(
                    {'Channel' : 'panel count',
                    'Value' : len(jsonResponse),
                    'Unit' : 'Custom',
                    'CustomUnit' : 'Count',
                    'Float' : 0,
                    'ShowChart' : 0,
                    'ShowTable' : 0,
                    'primary' : 1
                    })

                panelMax = 0
                panelMin = 10000

                for eachPanel in jsonResponse:
                    result['prtg']['result'].append(
                        {'Channel' : eachPanel['serialNumber'],
                        'Value' : eachPanel['lastReportWatts'],
                        'Unit' : 'Custom',
                        'CustomUnit' : 'Watts',
                        'Float' : 0,
                        'ShowChart' : 1,
                        'ShowTable' : 1
                        })
                    if eachPanel['lastReportWatts'] > panelMax: panelMax = eachPanel['lastReportWatts']
                    if eachPanel['lastReportWatts'] < panelMin: panelMin = eachPanel['lastReportWatts']

                result['prtg']['result'].append(
                    {'Channel' : 'panel range',
                    'Value' : (panelMax - panelMin),
                    'Unit' : 'Custom',
                    'CustomUnit' : 'Watts',
                    'Float' : 0,
                    'ShowChart' : 0,
                    'ShowTable' : 0,
                    })


        except requests.exceptions.Timeout as e:
            result = {'prtg': {'text' : 'Remote host timeout error', 'error' : "%s" % str(e)}}
        except requests.exceptions.ConnectionError as e:
            result = {'prtg': {'text' : 'Remote host connection error', 'error' : "%s" % str(e)}}
        except requests.exceptions.HTTPError as e:
            result = {'prtg': {'text' : 'Remote host HTTP error', 'error' : "%s" % str(e)}}
        except requests.exceptions.TooManyRedirects as e:
            result = {'prtg': {'text' : 'Remote host Too Many Redirects error', 'error' : "%s" % str(e)}}
        except Exception as e:
            result = {'prtg': {'text' : 'Unhandled error', 'error' : "%s" % str(e)}}
            
    except Exception as e:
        result = {'prtg': {'text' : 'Python Script execution error', 'error' : "%s" % str(e)}}

    print('')
    print(json.dumps(result))

# References:
# ValueCustomUnits: C:\Program Files (x86)\PRTG Network Monitor\python\Lib\site-packages\prtg\sensor\CustomUnits.py
