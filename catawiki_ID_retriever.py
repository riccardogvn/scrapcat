from tqdm import tqdm
import json
import requests
import os
import json
import requests
from bs4 import BeautifulSoup as bs
from sortedcontainers import SortedSet
import logging
import time
from datetime import datetime
from tempfile import NamedTemporaryFile
from setup.config import LIST_OF_EXPERTS, CATEGORIES_OK, CATEGORIES_NOT_OK, LIST_OF_OBJECTS, DICT_OF_IDS, CATA_LOTS

def objects_ids(CATEGORIES_OK,CATEGORIES_NOT_OK,LIST_OF_OBJECTS,DICT_OF_IDS,logger,max_number=100000000,nonpartial=True,sleept=0.1):


    def check_status_code(url,session):
        response = session.head(url, allow_redirects=True, timeout=20)

        return response.status_code,response.url

    with requests.Session() as session:
        with open(DICT_OF_IDS, 'r') as f:
            objs = json.load(f)
        with open(CATEGORIES_OK, 'r') as tt:
            titlesok = json.load(tt)
            initial_titles = titlesok.copy()
        with open(CATEGORIES_NOT_OK, 'r') as nott:
            titlesnot = json.load(nott)
            initial_titlesnot = titlesnot.copy()
        nobj = objs['no']
        objn = set(objs['yes'])
        ob404 = set(objs['404'])

        '''
        for number in tqdm(range(nobj, max_number-nobj)):
            if number not in objn and number not in ob404:
                a = len(ob404)
                url = f'https://catawiki.com/en/l/{number}'
                status_code, status_url = check_status_code(url,session)
                if status_code == 404:
                    ob404.append(number)
                if '/c/' in status_url:
                    ob404.append(number)
                if len(ob404) > a:
                    with open(DICT_OF_IDS, 'w') as f:
                        json.dump(objs, f)
                time.sleep(1)
            '''


        for number in tqdm(range(nobj, max_number - nobj)):
            if number in objn or number in ob404:
                pass
            else:
                try:
                    if number not in objn and number not in ob404:
                        a = len(ob404)
                        url = f'https://catawiki.com/en/l/{number}'
                        status_code, status_url = check_status_code(url, session)

                        if status_code == 404:
                            ob404.add(number)
                            if number % 50 == 0:
                                time.sleep(sleept)
                            if nonpartial == True:
                                nobj = number
                        elif '/c/' in status_url:
                            if number % 50 == 0:
                                time.sleep(sleept)
                            ob404.add(number)
                            if nonpartial == True:
                                nobj = number
                        else:
                            if nonpartial == True:
                                if number % 50 == 0:
                                    time.sleep(sleept)
                                try:
                                    response = session.get(f'https://catawiki.com/en/l/{number}', timeout=20)
                                    if response.status_code == 404:
                                        nobj = number
                                        pass

                                    else:
                                        soup = bs(response.content, 'html.parser')
                                        try:
                                            ccc = json.loads(
                                                str(soup.find('script', {'type': 'application/json'}).contents[0]))

                                            for x in ccc['props']['pageProps']['auction']['categories']:
                                                if 'archaeology' in x['title'].lower():
                                                    # objects.append(ccc)
                                                    logger.info(f'{number} approved')
                                                    objn.add(number)
                                                    time.sleep(sleept)
                                                    try:
                                                        soup_beta = bs(session.get(
                                                            f'https://catawiki.com/en/a/{ccc["props"]["pageProps"]["auction"]["id"]}',
                                                            timeout=20).content, 'html.parser')
                                                        ccc_beta = soup_beta.find('div', {
                                                            'data-react-component': 'AuctionListSegment'})['data-props']
                                                        aucy = json.loads(ccc_beta)
                                                        aucy_lots = [x['id'] for x in aucy['results']]
                                                        for aucy_lot in aucy_lots:
                                                            objn.add(aucy_lot)
                                                    except Exception as e:
                                                        logger.error(f"Error processing auction data: {e}")
                                                        pass

                                                    break
                                                elif x['id'] in titlesok:
                                                    # objects.append(ccc)
                                                    logger.info(f'{number} approved')
                                                    objn.add(number)
                                                    time.sleep(sleept)
                                                    try:
                                                        soup_beta = bs(session.get(
                                                            f'https://catawiki.com/en/a/{ccc["props"]["pageProps"]["auction"]["id"]}',
                                                            timeout=20).content, 'html.parser')
                                                        ccc_beta = soup_beta.find('div', {
                                                            'data-react-component': 'AuctionListSegment'})[
                                                            'data-props']
                                                        aucy = json.loads(ccc_beta)
                                                        aucy_lots = [x['id'] for x in aucy['results']]
                                                        for aucy_lot in aucy_lots:
                                                            objn.add(aucy_lot)
                                                            logger.info(f'{number} approved')
                                                    except Exception as e:
                                                        logger.error(f"Error processing auction data: {e}")
                                                        pass
                                                    break
                                                elif x['id'] in titlesnot:
                                                    nobj = number
                                                    pass
                                                '''
                                                else:
                                                    print(x['title'])
                                                    print(number)
                                                    print('\n')
                                                    question = input('this goes in titlesok?\n')
                                                    if question.lower() == 'y':
                                                        titlesok.append(x['id'])
                                                        # objects.append(ccc)
                                                        print(f'{number}went')
                                                        objn.add(number)
                                                        try:
                                                            time.sleep(sleept)
                                                            soup_beta = bs(session.get(
                                                                f'https://catawiki.com/en/a/{ccc["props"]["pageProps"]["auction"]["id"]}',
                                                                timeout=20).content, 'html.parser')
                                                            ccc_beta = soup_beta.find('div', {
                                                                'data-react-component': 'AuctionListSegment'})[
                                                                'data-props']
                                                            aucy = json.loads(ccc_beta)
                                                            aucy_lots = [x['id'] for x in aucy['results']]
                                                            for aucy_lot in aucy_lots:
                                                                objn.add(aucy_lot)
                                                        except Exception as e:
                                                            logger.error(f"Error processing auction data: {e}")
                                                            pass
                                                        break
                                                    else:
                                                        titlesnot.append(x['id'])
                                                        nobj = number

                                                        pass
                                                '''
                                        except Exception as e:
                                            logger.error(f'Error finding application/json. Id escluded: {e}')
                                            nobj = number
                                            pass
                                except Exception as e:
                                    logger.error(f'Error responding. Id escluded: {e}')
                                    nobj = number
                                    pass
                            else:
                                pass

                    else:
                        pass




                    if number % 50 == 0:
                        # Write data to disk every 50 iterations
                        with open(DICT_OF_IDS, 'w') as f:
                            json.dump({'no':nobj,'404':list(ob404),'yes':list(SortedSet(objn))}, f)
                        if initial_titles != titlesok:
                            with open(CATEGORIES_OK, 'w') as tr:
                                json.dump(titlesok, tr)
                        if initial_titlesnot != titlesnot:
                            with open(CATEGORIES_NOT_OK, 'w') as titnot:
                                json.dump(titlesnot, titnot)
                    if number % 1000 == 0:
                        print(f'\n{nobj} is the last NO \n{list(ob404)[-1]} is the last 404 \n{len(list(SortedSet(objn))[-1])} the last count of YES')

                except Exception as e:
                    logger.error(f'Skipping: {number} for {e}')
                    pass

    return objs

def setup_logger(log_file):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Create a file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    # Create a formatter and set it for the file handler
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)

    return logger

def main():
    logger = setup_logger(f'logs/run_{datetime.now().strftime("%d_%m_%y_%H_%M_%S ")}.txt')
    logger.info(f'Starting operation at {datetime.now().strftime("%d/%m/%y %H:%M:%S")}')
    objects_ids(CATEGORIES_OK,CATEGORIES_NOT_OK,LIST_OF_OBJECTS,DICT_OF_IDS,logger)
    logger.info(f'Finished processing at {datetime.now().strftime("%d/%m/%y %H:%M:%S")}')

if __name__ == "__main__":
    main()


'''
def scrapemore(number,session,nobj,objn,titlesok,titlesnot,sleept):
    try:
        response = session.get(f'https://catawiki.com/en/l/{number}', timeout=20)
        if response.status_code == 404:
            nobj = number
            pass

        else:
            soup = bs(response.content, 'html.parser')
            try:
                ccc = json.loads(str(soup.find('script', {'type': 'application/json'}).contents[0]))

                for x in ccc['props']['pageProps']['auction']['categories']:
                    if 'archaeology' in x['title'].lower():
                        #objects.append(ccc)
                        print(f'{number}went')
                        objn.add(number)
                        time.sleep(sleept)
                        try:
                            soup_beta = bs(session.get(f'https://catawiki.com/en/a/{ccc["props"]["pageProps"]["auction"]["id"]}',
                                               timeout=20).content, 'html.parser')
                            ccc_beta = soup_beta.find('div', {'data-react-component':'AuctionListSegment'})['data-props']
                            aucy = json.loads(ccc_beta)
                            aucy_lots = [x['id'] for x in aucy['results']]
                            for aucy_lot in aucy_lots:
                                objn.add(aucy_lot)
                        except:
                            pass

                        break
                    elif x['id'] in titlesok:
                        #objects.append(ccc)
                        print(f'{number}went')
                        objn.add(number)
                        time.sleep(sleept)
                        try:
                            soup_beta = bs(session.get(
                                f'https://catawiki.com/en/a/{ccc["props"]["pageProps"]["auction"]["id"]}',
                                timeout=20).content, 'html.parser')
                            ccc_beta = soup_beta.find('div', {'data-react-component': 'AuctionListSegment'})[
                                'data-props']
                            aucy = json.loads(ccc_beta)
                            aucy_lots = [x['id'] for x in aucy['results']]
                            for aucy_lot in aucy_lots:
                                objn.add(aucy_lot)
                        except:
                            pass
                        break
                    elif x['id'] in titlesnot:
                        nobj = number
                        pass
                    else:
                        print(x['title'])
                        print(number)
                        print('\n')
                        question = input('this goes in titlesok?\n')
                        if question.lower() == 'y':
                            titlesok.append(x['id'])
                            #objects.append(ccc)
                            print(f'{number}went')
                            objn.add(number)
                            try:
                                time.sleep(sleept)
                                soup_beta = bs(session.get(
                                    f'https://catawiki.com/en/a/{ccc["props"]["pageProps"]["auction"]["id"]}',
                                    timeout=20).content, 'html.parser')
                                ccc_beta = soup_beta.find('div', {'data-react-component': 'AuctionListSegment'})[
                                    'data-props']
                                aucy = json.loads(ccc_beta)
                                aucy_lots = [x['id'] for x in aucy['results']]
                                for aucy_lot in aucy_lots:
                                    objn.add(aucy_lot)
                            except:
                                pass
                            break
                        else:
                            titlesnot.append(x['id'])
                            nobj = number

                            pass
            except:
                nobj = number
                pass
    except:
        nobj = number
        pass

    return number,session,nobj,objn,titlesok,titlesnot
'''
'''
time.sleep(1)
                    try:
                        response = session.get(f'https://catawiki.com/en/l/{number}', timeout=20)
                        if response.status_code == 404:
                            nobj = number
                            pass

                        else:
                            soup = bs(response.content, 'html.parser')
                            try:
                                ccc = json.loads(str(soup.find('script', {'type': 'application/json'}).contents[0]))

                                for x in ccc['props']['pageProps']['auction']['categories']:
                                    if 'archaeology' in x['title'].lower():
                                        #objects.append(ccc)
                                        print('went')
                                        objn.add(number)
                                        try:
                                            soup_beta = bs(session.get(f'https://catawiki.com/en/a/{ccc["props"]["pageProps"]["auction"]["id"]}',
                                                               timeout=20).content, 'html.parser')
                                            ccc_beta = soup_beta.find('div', {'data-react-component':'AuctionListSegment'})['data-props']
                                            aucy = json.loads(ccc_beta)
                                            aucy_lots = [x['id'] for x in aucy['results']]
                                            for aucy_lot in aucy_lots:
                                                objn.add(aucy_lot)
                                        except:
                                            pass

                                        break
                                    elif x['id'] in titlesok:
                                        #objects.append(ccc)
                                        print('went')
                                        objn.add(number)
                                        try:
                                            soup_beta = bs(session.get(
                                                f'https://catawiki.com/en/a/{ccc["props"]["pageProps"]["auction"]["id"]}',
                                                timeout=20).content, 'html.parser')
                                            ccc_beta = soup_beta.find('div', {'data-react-component': 'AuctionListSegment'})[
                                                'data-props']
                                            aucy = json.loads(ccc_beta)
                                            aucy_lots = [x['id'] for x in aucy['results']]
                                            for aucy_lot in aucy_lots:
                                                objn.add(aucy_lot)
                                        except:
                                            pass
                                        break
                                    elif x['id'] in titlesnot:
                                        nobj = number
                                        pass
                                    else:
                                        print(x['title'])
                                        print(number)
                                        print('\n')
                                        question = input('this goes in titlesok?\n')
                                        if question.lower() == 'y':
                                            titlesok.append(x['id'])
                                            #objects.append(ccc)
                                            print('went')
                                            objn.add(number)
                                            try:
                                                soup_beta = bs(session.get(
                                                    f'https://catawiki.com/en/a/{ccc["props"]["pageProps"]["auction"]["id"]}',
                                                    timeout=20).content, 'html.parser')
                                                ccc_beta = soup_beta.find('div', {'data-react-component': 'AuctionListSegment'})[
                                                    'data-props']
                                                aucy = json.loads(ccc_beta)
                                                aucy_lots = [x['id'] for x in aucy['results']]
                                                for aucy_lot in aucy_lots:
                                                    objn.add(aucy_lot)
                                            except:
                                                pass
                                            break
                                        else:
                                            titlesnot.append(x['id'])
                                            nobj = number

                                            pass
                            except:
                                nobj = number
                                pass
                    except:
                        nobj = number
                        pass

'''