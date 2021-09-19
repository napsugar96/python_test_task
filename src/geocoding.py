import http.client
import json
import urllib.parse


def get_geocode(address: str) -> str:
    connection = http.client.HTTPConnection('api.positionstack.com')

    params = urllib.parse.urlencode({
        'access_key': '7599c1f38d5552eaef628551bf9e05ae',
        'query': address,
        'limit': 1,
    })

    connection.request('GET', '/v1/forward?{}'.format(params))
    response = connection.getresponse()
    return response.read()


def get_location(response: str) -> (str, str): # longitude, latitude
    json_string = response.decode('utf-8')
    try:
        json_obj = json.loads(json_string)
    except ValueError as error:
        print(error)
        return None, None

    if 'data' in json_obj and len(json_obj['data']) != 0:
        return json_obj['data'][0]['longitude'], json_obj['data'][0]['latitude']
    else:
        print('problem with geocoder api response')
        return None, None
