import asyncio
from datetime import datetime, timedelta
import logging
from time import time

import concurrent.futures
from aiohttp import ClientSession, ClientConnectorError


today = datetime.today()


async def request(url: str):
    async with ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.ok:
                    return await resp.json()
                logging.error(f"Error status: {resp.status} for {url}")
                return None
        except ClientConnectorError as err:
            logging.error(f"Connection error: {str(err)}")
            return None


def pb_handler(result):
    data = result
    usd_sale = None
    usd_buy = None
    eur_sale = None
    eur_buy = None
    
    for item in data['exchangeRate']:
        if item['currency'] == 'EUR':
            eur_sale = item['saleRateNB']
            eur_buy = item['purchaseRateNB']
            
    for item in data['exchangeRate']:
        if item['currency'] == 'USD':
            usd_sale = item['saleRateNB']
            usd_buy = item['purchaseRateNB']
    
    dict_pb = {
        data['date']: {'EUR': {
            'sale': eur_sale,
            'buy': eur_buy
        },
            'USD': {
                'sale': usd_sale,
                'buy': usd_buy
            }
        }
    }
    
    return dict_pb


def nbu_handler(result):
    usd, = list(filter(lambda el: el["cc"] == "USD", result))
    eur, = list(filter(lambda el: el["cc"] == "EUR", result))
    dict_nbu = {
        usd['exchangedate']: {'EUR': {
            'rate': eur['rate']
            # 'buy' : eur['buy']
        },
            'USD': {
                'rate': usd['rate']
                # 'buy' : usd['buy']
            }
        }
    }
    
    return dict_nbu


def api_pb():
    list_api_pb = []
    for i in range(10):
        date = (today - timedelta(days=i)).strftime("%d.%m.%Y")
        API_PB = f'https://api.privatbank.ua/p24api/exchange_rates?json&date={date}'
        list_api_pb.append(API_PB)
    return list_api_pb


def api_nbu():
    list_api_nbu = []
    for i in range(10):
        date = (today - timedelta(days=i)).strftime("%Y%m%d")
        API_NBU = f'https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?date={date}&json'
        list_api_nbu.append(API_NBU)
    return list_api_nbu


async def get_exchange(url, handler):
    result = await request(url)
    if result:
        return handler(result)
    return "Failed to retrieve data"


def fetch_urls_with_executor(urls, handler):
    with concurrent.futures.ProcessPoolExecutor() as executor:
        loop = asyncio.get_event_loop()
        tasks = [loop.create_task(get_exchange(url, handler)) for url in urls]
        results = loop.run_until_complete(asyncio.gather(*tasks))
    return results


if __name__ == '__main__':
    start_time = time()
    
    l_api_pb = api_pb()
    l_api_nbu = api_nbu()

    result_list_pb = fetch_urls_with_executor(l_api_pb, pb_handler)
    result_list_nbu = fetch_urls_with_executor(l_api_nbu, nbu_handler)

    print(result_list_pb)
    print(result_list_nbu)
    
    end_time = time()
    print(end_time - start_time)
    