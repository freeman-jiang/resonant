import random

import requests
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from nltk.stem import WordNetLemmatizer

url = 'https://curius.app/api/passageSearch'

headers = {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Cookie': '_ga=GA1.1.1515636949.1695874520; G_ENABLED_IDPS=google; G_AUTHUSER_H=1; token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MzYwMCwiaWF0IjoxNjk1ODc4NTM2LCJleHAiOjE3MjczMjQxMzZ9.B79if_lbVHN60mQvbVJy4da1CDiKV8QSboMyc-nsOdI; jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MzYwMCwiaWF0IjoxNjk1ODc4NTM2LCJleHAiOjE3MjczMjQxMzZ9.B79if_lbVHN60mQvbVJy4da1CDiKV8QSboMyc-nsOdI; _ga_QC76Y27GM4=GS1.1.1698029340.4.0.1698029340.0.0.0; mp_6f4de78898d87a1c8d7b7c5bd8b97049_mixpanel=%7B%22distinct_id%22%3A%203600%2C%22%24device_id%22%3A%20%2218adc17fc32254-08ec09cdfd1521-18525634-16a7f0-18adc17fc33fa5%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22%24user_id%22%3A%203600%7D',
    'Pragma': 'no-cache',
    'Referer': 'https://curius.app/henry-nguyen',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MzYwMCwiaWF0IjoxNjk1ODc4NTM2LCJleHAiOjE3MjczMjQxMzZ9.B79if_lbVHN60mQvbVJy4da1CDiKV8QSboMyc-nsOdI',
    'content-type': 'application/json',
    'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
}

def scrape_search_term(search):
    params = {'query': search}

    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data.get('links', []), search
    else:
        print(f"Request failed for search term '{search}' with status code: {response.status_code}")
        return [], search

count = 0
def print_links(future):
    global count
    links, search = future.result()
    print("Links for search term:", search, count)
    for link in links:
        print(link['link'])

if __name__ == "__main__":
    searched_words = set()
    lemmatizer = WordNetLemmatizer()

    with open("total.txt", "rb") as searched:
        for line in searched.readlines():
            line = line.decode('ascii', errors = 'ignore')
            if line.startswith("Links for search term:"):
                word = line.split(' ')[-1]
                searched_words.add(word.lower().strip())

    with open("/usr/share/dict/words", "r") as file_words:
        word_list = [word.lower().strip() for word in file_words.readlines()]

    tasks = 0
    random.shuffle(word_list)
    with ProcessPoolExecutor(max_workers=50) as executor:  # Adjust the number of workers as needed
        for word in word_list:
            word = lemmatizer.lemmatize(word)

            if word in searched_words:
                continue
            else:
                searched_words.add(word)

            tasks += 1
            print("Task", tasks)
            links = executor.submit(scrape_search_term, word)
            links.add_done_callback(print_links)

    # You can add more processing or handling of the links if needed.
