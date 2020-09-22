import csv
import json
import re
import requests


GEOCODE_URL = 'https://geocoder.api.here.com/6.2/geocode.json?app_id=h22Tqd5BRr2wYpQWuWFt&app_code=9Jr1aviAP89DAdyU0l0pGA&searchtext='
GEOCODE_MIN_SCORE = 80
DATA_CSV = 'address_partial_OES_short.csv'
#DATA_CSV = 'testfailurecase.csv'

class Uncertain(Exception):
    pass


def get_addresses():
    with open(DATA_CSV, 'r') as csvfile:
        data = [row for row in csv.reader(csvfile.read().splitlines())]
        print(data)
        print(data[1])
        return {int(row[0]): row[1] for row in data[1:]}  


def sanitize_address(address):
    # Remove suite/number/space, e.g. 123 Main St #A1 Chico, CA
    # Otherwise API won't come back with any results
    return address.replace('#','unit ')


def geocode(address):
    address = sanitize_address(address)
    addrForQuery = address.replace(' ','+')
    aptQuery = '&additionaldata=IncludeMicroPointAddresses,true' # this is needed for apartment number

    try:
        #print(GEOCODE_URL + addrForQuery + aptQuery)
        res = requests.get(GEOCODE_URL + addrForQuery + aptQuery)
        res.raise_for_status()
        js = res.json()
        
        newAddr = 'unknown'
        
        try:
            newAddr = js['Response']['View'][0]['Result'][0]['Location']['Address']['Label']
            if js['Response']['View'][0]['Result'][0]['MatchLevel'] != 'houseNumber':
                newAddr = 'null'
        except IndexError:
            newAddr = 'null'
            pass

        return newAddr
        
    except requests.exceptions.RequestException as e:
        raise ValueError('Bad request: ' + str(e))
    

if __name__ == '__main__':
    count = 0
    breakdown = {
        'certain': 0,
        'manually_reviewed': 0,
        'match': 0,
        'mismatch': 0,
        'uncertain': 0,
        'unverified': 0,
    }
    with open('address_outcome.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['intake no', 'old address', 'new address'])
        id_to_address = get_addresses()

        for intake_num, oldAddr in get_addresses().items():
            print(oldAddr)
            try:
                newAddress = geocode(oldAddr)
            except Uncertain as e:
                status = 'Uncertain ({})'.format(e)
            except ValueError as e:
                status = 'Error ({})'.format(e)
        
            writer.writerow([intake_num, oldAddr, newAddress])
            f.flush()