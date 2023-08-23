import requests
from gensim.models import LdaModel
from gensim.corpora import Dictionary
from gensim.models.coherencemodel import CoherenceModel
from gensim.utils import simple_preprocess

import json

from crawler.link import Link
from crawler.parse import CrawlResult
from crawler.root_urls import ROOT_URLS

root_url_domains = {Link.from_url(x["url"]).domain() for x in ROOT_URLS}
if __name__ == "__main__":

    obj = json.load(open("dump.json", "r"))
    training = []
    # Train an LDA model
    for url in obj:
        text = CrawlResult.model_validate_json(obj[url])

        if text.link.domain() in root_url_domains:
            print("Text good domain", text.link.domain())
            training.append(simple_preprocess(text.content))

    common_dictionary = Dictionary(training)
    common_corpus = [common_dictionary.doc2bow(text) for text in training]

    lda_model = LdaModel(corpus=common_corpus, id2word=common_dictionary)

    scores = []
    for url in obj:
        text = json.loads(obj[url])

        if text:
            words = simple_preprocess(text["content"])
            texts = [words]
            bows = [common_dictionary.doc2bow(text) for text in texts]

            coherence_model = CoherenceModel(
                model=lda_model, texts=texts, corpus=bows, coherence='u_mass')

            # Calculate UMass coherence scores
            coherence_scores = coherence_model.get_coherence_per_topic()
            scores.append((sum(coherence_scores) / len(coherence_scores), url))
            print("Coherence scores for ", url, " are ", sum(
                coherence_scores) / len(coherence_scores))
    scores = sorted(scores, key=lambda k: k[0])

    print(scores)
