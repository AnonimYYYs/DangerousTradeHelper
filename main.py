from requests import get as r_get
import json
from datetime import datetime
from datetime import timedelta

# GLOBAL VARS TO CHANGE
currentSystemName = 'Gliese 58'
minSellPrice = 20000  # crd
searchSize = 50  # ly (if sphere -> size is radius(0;100) | if cube -> size is length of side (0;200)
minStockAmount = 40  # T
carrierUpdateTime = 1  # hours
stationUpdateTime = 16  # hours
searchType = 'sphere'  # 'cube'|'sphere'
minProfit = 10000  # crd

def requestSystemsCubeList(centerSysName, size=100):
    if size > 200:
        size = 200
    url = f'https://www.edsm.net/api-v1/cube-systems?systemName={centerSysName}&size={size}'
    jObj = json.loads(r_get(url).text)
    print(f'--> data about systems in cube around {centerSysName} is gathered /{type(jObj)}')
    return jObj

def requestSystemsSphereList(centerSysName, radius=50):
    if radius > 100:
        radius = 100
    url = f'https://www.edsm.net/api-v1/sphere-systems?systemName={centerSysName}&radius={radius}'
    jObj = json.loads(r_get(url).text)
    print(f'--> data about systems in sphere around {centerSysName} is gathered /{type(jObj)}')
    return jObj

def requestSystemStationsInfo(systemName):
    url = f'https://www.edsm.net/api-system-v1/stations?systemName={systemName}'
    jObj = json.loads(r_get(url).text)
    print(f'--> data about stations into {systemName} is gathered /{type(jObj)}')
    return jObj.get('stations', [])

def requestMarketCommoditiesInfo(marketId):
    url = f'https://www.edsm.net/api-system-v1/stations/market?marketId={marketId}'
    jObj = json.loads(r_get(url).text)
    print(f'--> data about comms in market#{marketId} is gathered /{type(jObj)}')
    return jObj['commodities']



if __name__ == '__main__':
    commsList = []
    # getting systems in radius
    if searchType == 'cube':
        systems = requestSystemsCubeList(currentSystemName, searchSize)
    else:
        systems = requestSystemsSphereList(currentSystemName, searchSize)
    for row in systems:
        row.pop('bodyCount')
        # getting stations of each system
        stations = requestSystemStationsInfo(row['name'])

        # filter stations that have refreshed less than given time
        stations = [st for st in stations if st['haveMarket'] is True]
        stations = [
            st for st in stations if
            (datetime.now() - datetime.strptime(st['updateTime']['market'], '%Y-%m-%d %H:%M:%S') <
             timedelta(hours=carrierUpdateTime) and st['type'] == 'Fleet Carrier') or
            (datetime.now() - datetime.strptime(st['updateTime']['market'], '%Y-%m-%d %H:%M:%S') <
             timedelta(hours=stationUpdateTime) and st['type'] != 'Fleet Carrier')
        ]
        for st in stations:
            # getting all commodities of station
            commodities = requestMarketCommoditiesInfo(st['marketId'])

            # foreach commodity searching for best selling price
            for com in commodities:
                # if sold on market with good price
                if com['sellPrice'] > minSellPrice:
                    # if already on commodities list -> compare with best one
                    isExist = False
                    for sell in commsList:
                        if sell['name'] == com['name']:
                            isExist = True
                            # if better than best -> change
                            if com['sellPrice'] != 0 and sell['sellPrice'] < com['sellPrice']:
                                sell['sellPrice'] = com['sellPrice']
                                sell['sellStationName'] = st['name']
                                sell['sellSystemName'] = row['name']
                    # add if new commodity
                    if not isExist:
                        commsList.append({
                            'name': com['name'],
                            'sellPrice': com['sellPrice'],
                            'sellStationName': st['name'],
                            'sellSystemName': row['name'],
                            'buyPrice': -1,
                            'buyStationName': '---',
                            'buySystemName': '---'
                        })
                com.pop('id')
                com.pop('stockBracket')

            st['commodities'] = commodities
        row['stations'] = stations



    # deleting systems without good stations
    systems = [d for d in systems if len(d['stations']) != 0]


    # gathering best buying from station info for each
    for myComm in commsList:
        for sys in systems:
            for market in sys['stations']:
                for comms in market['commodities']:
                    if comms['name'] == myComm['name']:
                        if (comms['buyPrice'] != 0 and comms['stock'] >= minStockAmount and
                                (comms['buyPrice'] < myComm['buyPrice'] or myComm['buyPrice'] == -1)):
                            myComm['buyPrice'] = comms['buyPrice']
                            myComm['buyStationName'] = market['name']
                            myComm['buySystemName'] = sys['name']
        myComm['profit'] = myComm['sellPrice'] - myComm['buyPrice'] if myComm['buyPrice'] != -1 else -1


    # deleting low profit roots
    commsList = [com for com in commsList if com['profit'] > minProfit]

    # deleting unnecessary elements in json
    for d in systems:
        for st in d['stations']:
            st.pop('id', '')
            st.pop('type', '')
            st.pop('allegiance', '')
            st.pop('government', '')
            st.pop('economy', '')
            st.pop('secondEconomy', '')
            st.pop('haveMarket', '')
            st.pop('haveShipyard', '')
            st.pop('haveOutfitting', '')
            st.pop('otherServices', '')
            st.pop('controllingFaction', '')
            st.pop('updateTime')
    print('---------------------------------------------------------------------------')
    print(f'systems amount: {len(systems)}')
    # print(json.dumps(systems, indent=2))
    # for d in systems:
    #     print(d)
    print('---------------------------------------------------------------------------')
    print(f'sellings amount:{len(commsList)}')
    sellList = sorted(commsList, key=lambda k: k['profit'])
    # for s in sellList:
    #     print(s)
    print(json.dumps(sellList, indent=2))