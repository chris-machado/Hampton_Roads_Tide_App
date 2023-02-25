from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json, time
from datetime import datetime


def lambda_handler(event, context):
    # TODO implement
    DATA = call_tide_api()
    url = 'http://ec2-18-233-120-8.compute-1.amazonaws.com:8080/post'
    DATA_str = json.dumps(DATA)
    payload = DATA_str.encode("utf-8")
    headers = {"Content-Type": "application/json"}
    
    response = make_request(url, data=payload, headers=headers)

    return {
        'statusCode': 200,
        'body': json.dumps('Sucess')
    }

def call_tide_api():
    tide_stations = {
        "Sewells Point": "8638610",
        "Money Point" : "8639348",
        "Chesapeake Bay Bridge Tunnel" : "8638901", 
        "Kiptopeke" : "8632200",
        "Yorktown" : "8637689"  
    }
    base_url = 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?date=latest&time_zone=gmt&units=english&format=json&product=water_level&datum=MLLW&station='
    data = []
    for identifier in tide_stations.values():
        api_url = base_url + identifier
        with urlopen(api_url) as url:
            ob = json.loads(url.read().decode())
            new_ob = {}
            if 'error' in ob.keys():
#                new_ob[identifier] = ob['error']
                 continue
            else:
                new_ob['id'] = ob['metadata']['id']
                new_ob['time'] = ob['data'][0]['t']
                new_ob['name'] = ob['metadata']['name']
                new_ob['lat'] = ob['metadata']['lat']
                new_ob['lon'] = ob['metadata']['lon']
                new_ob['water_level'] = ob['data'][0]['v']
                new_ob['s'] = ob['data'][0]['s']
                new_ob['q'] = ob['data'][0]['q']
                new_ob['ttl-purge'] = str(datetime.timestamp(datetime.now())+345600)
                data.append(new_ob)    
    return data
    
def make_request(url, headers, data):
    request = Request(url, headers=headers or {}, data=data)
    try:
        with urlopen(request, timeout=10) as response:
            print(response.status)
            return response.read(), response
    except HTTPError as error:
        print(error.status, error.reason)
    except URLError as error:
        print(error.reason)
    except TimeoutError:
        print("Request timed out")