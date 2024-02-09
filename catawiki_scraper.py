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
from tempfile import NamedTemporaryFile
from cata_config import LIST_OF_EXPERTS, CATEGORIES_OK, CATEGORIES_NOT_OK, LIST_OF_OBJECTS, DICT_OF_IDS, CATA_LOTS

def cata_soup(category,id,timeout=20,parser='html.parser'):
    soup = bs(requests.get(f'https://catawiki.com/en/{category}/{id}',timeout).content,parser)
    return soup

def scrape_expert(id):
    soup = cata_soup('e',id)
    if 'Experts at Catawiki' in soup.find('title').string:
        pass
    else:
        result = json.loads(soup.find('script', {'type':'application/json'}).contents[0])['props']['pageProps']['expertData']
        return result

def scrape_experts(LIST_OF_EXPERTS):
    with open(LIST_OF_EXPERTS,'r') as list_of_experts:
        experts = json.load(list_of_experts)
    ids = []
    noexp = []
    for element in experts:
        ids.append(element['id'])
    ids = list(set(ids))
    for number in tqdm(range(ids[-1],ids[-1]+500)):
        if number not in ids:
            try:
                output = scrape_expert(number)
                if output:
                    experts.append(output)
            except:
                noexp.append(number)
                pass
    with open(LIST_OF_EXPERTS,'w') as experts_write:
        json.dump(experts,experts_write)

    return experts

def update_categories(LIST_OF_EXPERTS,CATEGORIES_OK,CATEGORIES_NOT_OK):
    categories = dict()
    with open(LIST_OF_EXPERTS,'r') as ex:
        experts = json.load(ex)
    for x in experts:
        cat = x['category']
        id = cat['id']
        name = cat['name']
        categories[id] = name

    with open(CATEGORIES_OK,'r') as categories_ok:
        interesting_categories = json.load(categories_ok)
    with open(CATEGORIES_NOT_OK,'r') as categories_not_ok:
        not_interesting_categories = json.load(categories_not_ok)

    for k, v in categories.items():
        print(v)
        if k in interesting_categories:
            pass
        elif k in not_interesting_categories:
            pass
        else:
            question = input(f'is {v} interesting? y or n')
            if question.lower() == 'y':
                interesting_categories.append(k)
            else:
                not_interesting_categories.append(k)

    with open(CATEGORIES_OK,'w') as categories_write:
        json.dump(interesting_categories,categories_write)
    with open(CATEGORIES_NOT_OK,'w') as categories_not_write:
        json.dump(not_interesting_categories, categories_not_write)

def objects_ids(CATEGORIES_OK,CATEGORIES_NOT_OK,LIST_OF_OBJECTS,DICT_OF_IDS,max_number=100000000,nonpartial=True,sleept=0.1):
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
                                                    print(f'{number}went')
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
                                                    except:
                                                        pass

                                                    break
                                                elif x['id'] in titlesok:
                                                    # objects.append(ccc)
                                                    print(f'{number}went')
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

                except:
                    pass



    return objs

def scraper_catawiki(DICT_OF_IDS,CATA_LOTS):
    logger = setup_logger('catawiki_scraper_log.txt')

    with open(DICT_OF_IDS, 'r') as doi:
        objects = json.load(doi)
    try:
        with open(CATA_LOTS, 'r') as lotscata:
            catawiki_scrapers = json.load(lotscata)
        with open(CATA_LOTS, 'r') as lotscata:
            initial_scrapers = json.load(lotscata)
    except FileNotFoundError:
        catawiki_scrapers = {}
        logger.error(f"File {DICT_OF_IDS} not found")

    sellers = catawiki_scrapers.get('sellers',[])
    scraped = catawiki_scrapers.get('scraped',[])
    scraper = catawiki_scrapers.get('scraper',{})
    not_working = catawiki_scrapers.get('not_working',[])

    for element in tqdm(objects['yes']):
        if element in catawiki_scrapers['scraped']:
            pass
        else:
            response = requests.get(f'https://catawiki.com/en/l/{element}', timeout=20)
            response.raise_for_status()
            soup = bs(response.content, 'html.parser')
            try:
                script_content = soup.find('script', {'type': 'application/json'}).contents[0]
                ccc = json.loads(script_content)
                if 'lotDetailsData' not in ccc['props']['pageProps']:
                    print(f'Lot data not found for {element}')
                    not_working.append(element)
                else:

                    lot_data = ccc['props']['pageProps']['lotDetailsData']
                    seller = lot_data['sellerInfo']

                    if seller not in sellers:
                        sellers.append(seller)

                    whole_lot = ccc['props']['pageProps']
                    scraped.append(whole_lot['lotId'])
                    # Store lot details without creating a circular reference
                    scraper[whole_lot['lotId']] = whole_lot
            except Exception as e:
                logger.error(f"An error occurred while processing lot {element}: {e}")
                not_working.append(element)
                pass

        catawiki_scrapers['sellers'] = sellers
        catawiki_scrapers['scraper'] = scraper
        catawiki_scrapers['scraped'] = scraped
        catawiki_scrapers['not_working'] = not_working

        if catawiki_scrapers != initial_scrapers:
            with NamedTemporaryFile('w', delete=False) as temp_file:
                json.dump(catawiki_scrapers, temp_file)
        else:
            logger.info('No changes')

        if catawiki_scrapers != initial_scrapers:
            try:
                os.replace(temp_file.name, CATA_LOTS)

            except Exception as e:
                logger.error(f'Failed to write data to {CATA_LOTS}: {e}')


    return catawiki_scrapers

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

def catawiki_buyers(CATA_LOTS):
    with open(CATA_LOTS, 'r') as f:
        scrapers = json.load(f)

    scraped_owners = scrapers['sellers']

    new_owners = []

    for owner in tqdm(scraped_owners):
        # Initialize tot_feedbacks with existing feedbacks if any, to avoid duplicates
        tot_feedbacks = owner.get('feedbacks', [])
        # Create a set of composite keys for existing feedbacks
        existing_feedback_keys = {(f['order_reference'], f['created_at'], f['author_name']) for f in tot_feedbacks}
        number = 1
        control = True

        while control:
            api_page = f"https://catawiki.com/feedback/api/v2/sellers/{owner['id']}/feedbacks?page={number}"
            try:
                response = requests.get(api_page, timeout=20)
                feeds = response.json()

                if feeds and len(feeds['feedbacks']) > 0:
                    for feedback in feeds['feedbacks']:
                        feedback_key = (feedback['order_reference'], feedback['created_at'], feedback['author_name'])
                        if feedback_key not in existing_feedback_keys:
                            tot_feedbacks.append(feedback)
                            existing_feedback_keys.add(feedback_key)

                    # Assuming pagination should continue until no new feedbacks are found
                    number += 1
                else:
                    control = False
            except requests.RequestException as e:
                print(f"Request failed: {e}")
                control = False

        owner['feedbacks'] = tot_feedbacks
        new_owners.append(owner)

    scrapers['sellers'] = new_owners

    with open(CATA_LOTS, 'w') as f:
        json.dump(scrapers, f)

    return scrapers

def scrapemore(number,session,nobj,objn,titlesok,titlesnot):
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
                        print(f'\n{number} added to Yes')
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
                        print(f'\n{number} added to Yes')
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
                            print(f'\n{number} added to Yes')
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

    return number,session,nobj,objn,titlesok,titlesnot


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