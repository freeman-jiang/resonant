from crawler.experiment.metrics import get_readability_metrics
from crawler.root_urls import ROOT_URLS

BAD_URLS = ["https://www.linkedin.com/in/marcyun", "https://www.detroitnews.com/story/sports/mlb/tigers/2023/08/22/tigers-even-series-with-cubs-andy-ibanez-has-career-night-with-two-homers/70649505007/",
            'https://www.cnbc.com/2021/03/14/stripe-valued-at-95-billion-in-600-million-funding-round.html', 'https://companiesmarketcap.com/coinbase/marketcap/',
            'https://www.prsa.org/_Publications/magazines/0802news1.asp',
            'https://schwartzpr.de/en/', 'https://www.albawaba.com/editorchoice/alb-arabic-computer-programming-language-understands-calligraphy-861614',
'https://www.forbes.com/sites/investor-hub/2023/08/22/nvidia-stock-earnings-forecast-what-to-watch/?sh=3a52ec4830fb',
            'https://www.forbes.com/sites/jahlselassie/2023/07/28/can-50-really-put-a-student-on-the-road-to-college/?sh=32eb6e4cbc4f',
            'https://www.forbes.com/sites/robertfarrington/2023/07/10/5-financial-tips-for-college-kids-to-follow-before-moving-into-dorms-next-month/?sh=5b52e7dd6403'
'https://www.sciencedirect.com/journal/finance-research-letters'
            ]

import numpy as np
GOOD_URLS = [x["url"] for x in ROOT_URLS]

if __name__ == "__main__":
    import nltk

    nltk.download('punkt')
    nltk.download('stopwords')
    from crawler.link import Link

    good = []
    bad = []
    for url in GOOD_URLS:
        good.append(get_readability_metrics(Link(url=url, text="", parent_url = "")).hlr)

    print("BAD URLS")
    for url in BAD_URLS:
        result = get_readability_metrics(Link(url=url, text="", parent_url = ""))

        if result:
            bad.append(result.hlr)

    print(np.mean(good), np.std(good))
    print(np.mean(bad), np.std(bad))
    print("Done!")