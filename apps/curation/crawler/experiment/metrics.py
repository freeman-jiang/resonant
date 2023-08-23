from typing import Optional

import requests
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from pydantic import BaseModel

from crawler.link import Link
from crawler.parse import parse_html


class MetricsResult(BaseModel):
    url: Link
    avg_sentence_length: float
    avg_word_length: float
    ttr: float
    hlr: float


def get_readability_metrics(link: Link) -> Optional[MetricsResult]:
    response = requests.get(link.url)
    crawl_result = parse_html(
        response.content.decode('utf-8', errors='ignore'), link)

    if not crawl_result:
        return None
    text = crawl_result.content

    # Tokenize text
    sentences = sent_tokenize(text)
    words = word_tokenize(text)

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    words = [word.lower() for word in words if word.isalnum()
             and word.lower() not in stop_words]

    # Calculate average sentence length and average word length
    avg_sentence_length = sum(len(word_tokenize(sentence))
                              for sentence in sentences) / len(sentences)
    avg_word_length = sum(len(word) for word in words) / len(words)

    # Calculate TTR (Type-Token Ratio)
    ttr = len(set(words)) / len(words)

    # Calculate Hapax Legomena Ratio (HLR)
    fdist = FreqDist(words)
    hapax_count = len(fdist.hapaxes())
    hlr = hapax_count / len(words)

    return MetricsResult(
        url=link,
        avg_sentence_length=avg_sentence_length,
        avg_word_length=avg_word_length,
        hlr=hlr,
        ttr=ttr
    )
