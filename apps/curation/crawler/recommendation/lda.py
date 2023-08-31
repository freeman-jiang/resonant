import json
import os

import gensim
import load_dotenv
import nltk
import numpy as np
import psycopg
import pytest
from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired
from gensim import corpora
from gensim.models import LdaModel
from typing import Optional, List, Iterator

from nltk.corpus import stopwords
from prisma import models
from psycopg.rows import class_row

stop_words = stopwords.words('english')
stop_words.extend(['from', 'subject', 're', 'edu', 'use'])


def preprocess(doc):
    data_words = gensim.utils.simple_preprocess(doc, deacc=True)
    # remove stop words
    data_words = remove_stopwords(data_words)
    return data_words


def sent_to_words(sentences):
    for sentence in sentences:
        yield ()


def remove_stopwords(texts):
    return [word for word in texts if word not in stop_words]


def cluster_documents_with_lda(pages: List[models.Page], num_topics: int = 20, num_top_words: int = 10):
    # Preprocess all page content and combine into a single list
    all_processed_content = [preprocess(page.content) for page in pages]

    # Create a dictionary
    dictionary = corpora.Dictionary(all_processed_content)

    # Create a corpus
    corpus = [dictionary.doc2bow(doc) for doc in all_processed_content]

    # Train LDA model
    lda_model = LdaModel(corpus, num_topics=num_topics, id2word=dictionary)

    # Get topic descriptions
    all_topic_descriptions = []
    for topic_id in range(num_topics):
        topic_words = lda_model.show_topic(topic_id, topn=num_top_words)
        topic_words = [word for word, _ in topic_words]
        topic_description = " ".join(topic_words)
        all_topic_descriptions.append(topic_description)

    return all_topic_descriptions


def filter_text(s):
    import re
    cleaned_text = re.sub(r'\n|http[s]?://\S+', ' ', s)
    cleaned_text = cleaned_text.translate(
        str.maketrans("", "", r"""#$%&'*+<=>@[\]^_`{|}~"""))

    return cleaned_text


def overlapping_windows(s: str) -> Iterator[str]:
    arr: list[str] = nltk.word_tokenize(s)
    # Generate overlapping windows of size 512 of arr
    count = 0
    for i in range(0, len(arr), 220):
        count += 1

        if count >= 15:
            break
        yield ' '.join(arr[i:i + 250])


class PageWithVec(models.Page):
    vec: str

    def npvec(self):
        # Convert vec string into list
        li = json.loads(self.vec)
        return np.array(li)


def cluster_documents_with_bertopic(pages: List[PageWithVec]):
    # Create a list of document content
    # documents = [filter_text(page.content) for page in pages]
    # documents = [overlapping_windows(x) for x in documents]
    # documents = [x for y in documents for x in y]
    documents = [page.content for page in pages]
    embeddings = np.vstack([x.npvec() for x in pages])

    # Create BERTopic model
    # Create your representation model
    representation_model = KeyBERTInspired()

    # Use the representation model in BERTopic on top of the default pipeline
    model = BERTopic(representation_model=representation_model,
                     min_topic_size=15, embedding_model="all-mpnet-base-v2")

    # Fit the model on the documents
    model.fit(documents, embeddings)

    # topic_distr, topic_token_distr = model.approximate_distribution(documents, calculate_tokens=True)

    # Run the visualization with the original embeddings
    model.visualize_documents(
        documents, embeddings=embeddings).write_html("a.html")

    return 5


@pytest.mark.asyncio
async def test_lda():
    load_dotenv.load_dotenv()
    db = psycopg.connect(os.environ['DATABASE_URL'])

    cursor = db.cursor(row_factory=class_row(PageWithVec))
    pages = cursor.execute("""WITH pages AS (SELECT * FROM "Page" LIMIT 700)
SELECT * FROM pages INNER JOIN "vecs"."Embeddings" ON pages.url = "vecs"."Embeddings".url WHERE index < 10 ORDER BY pages.url, index
""").fetchall()

    print(cluster_documents_with_bertopic(pages))

    return
