import gensim
import nltk
from bertopic import BERTopic
from bertopic.representation import KeyBERTInspired
from gensim import corpora
from gensim.models import LdaModel
from gensim.parsing.preprocessing import preprocess_string
from typing import Optional, List, Iterator
import string
from datetime import datetime

from gensim.utils import simple_preprocess
from nltk.corpus import stopwords
from prisma import models


stop_words = stopwords.words('english')
stop_words.extend(['from', 'subject', 're', 'edu', 'use'])
def preprocess(doc):
    data_words = gensim.utils.simple_preprocess(doc, deacc=True)
    # remove stop words
    data_words = remove_stopwords(data_words)
    return data_words


def sent_to_words(sentences):
    for sentence in sentences:
        yield()
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
    cleaned_text = cleaned_text.translate(str.maketrans("", "", r"""#$%&'*+<=>@[\]^_`{|}~"""))

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

def cluster_documents_with_bertopic(pages: List[models.Page], num_topics: int = 20):
    # Create a list of document content
    documents = [filter_text(page.content) for page in pages]
    documents = [overlapping_windows(x) for x in documents]
    documents = [x for y in documents for x in y]

    # Create BERTopic model
    # Create your representation model
    representation_model = KeyBERTInspired()

    # Use the representation model in BERTopic on top of the default pipeline
    model = BERTopic(representation_model=representation_model, min_topic_size=5)

    # Fit the model on the documents
    topics, probabilities = model.fit_transform(documents)

    # Get topic descriptions
    topic_descriptions = model.get_topic_info()


    return topic_descriptions