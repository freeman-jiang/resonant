from typing import Optional

import numpy as np

from crawler.recommendation.embedding import model

from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from pydantic import BaseModel


class MetricsResult(BaseModel):
    avg_sentence_length: float
    avg_word_length: float
    ttr: float
    hlr: float


def get_readability_metrics(text: str) -> Optional[MetricsResult]:
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
        avg_sentence_length=avg_sentence_length,
        avg_word_length=avg_word_length,
        hlr=hlr,
        ttr=ttr
    )




