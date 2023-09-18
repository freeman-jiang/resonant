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


def cosine(A, B):
    from numpy.linalg import norm
    return np.dot(A, B)/(norm(A)*norm(B))


def coherence(text: str):
    vecs = model.embed(text, stride=35, size=42)

    cosine_distances = []
    for v in range(vecs.shape[0] - 1):
        cosine_distances.append(cosine(vecs[v], vecs[v+1]))

    return np.median(cosine_distances)


def test_coherence():
    a = coherence(""" The UK’s National Air Traffic Service (NATS) said in two statements that airspace remained open but that it had been forced to apply air traffic flow restrictions to maintain safety. “We are currently experiencing a technical issue and have applied traffic flow restrictions to maintain safety,” NATS said. “Engineers are working to find and fix the fault.” The fault meant that flight plans have to be input into the system manually, slowing down the volume that can be processed by humans compared to those done automatically by computer. It was identified and fixed around three hours after the public was first alerted, but had created a backlog of delays and disruptions for passengers. NATS handles 2.5 million flights per year across the UK’s main 15 airports. Jake Smith, 31, said he had been held on the tarmac on board his British Airways flight from Porto, Portugal, for almost 50 minutes and said crew had advised passengers the wait could be at least another 40 minutes. """)
    b = coherence("""We miss the old seminars and conferences. While we wait for those to happen again, we’ve decided to organize a seminar series ourselves. Most talks will probably be about behavioral science, but we are figuring things out as we go. The one thing that all talks will have in common is that all three of us are interested in listening. We are hoping that you might be interested also. To receive the links required to attend these seminars, please sign up here Subscribe (this mailing list is independent of the blog's; you need to subscribe even if you get Colada blog alerts) The plan is to let the speakers focus on the presentation, and the three of us will act as moderators, passing along some of the audience’s questions to the speakers. To try out a format that's more interactive than the standard virtual seminar, we will attempt a format in which roughly 8-10 people can be seen and heard from during the entirety of the presentation (e.g., to interject questions, to laugh at jokes, to frown at bad puns, etc.). These people will include the three of us, a few folks chosen by the speaker, and maybe a couple of additional folks chosen by us. If this doesn’t work well, we will stop doing it. Some of our invitees may present research on methods, but this is not a methods seminar series. It is very broadly an interdisciplinary behavioral research seminar series. Seminars will be about an hour long (and never more than an hour), and will take place at 12:00 pm Eastern (6 pm Barcelona) on Fridays. Our first talk will be this Friday, April 24th. We are very grateful to the incomparable Yoel Inbar for agreeing to be our first speaker. His talk is titled, “Attitudes Towards Genetically Engineered Food and Other Controversial Scientific Technologies.” Thus far our schedule is as follows: 4/24: Yoel Inbar (Department of Psychology, University of Toronto) 5/1: Don Moore (Department of Management of Organizations, Berkeley Haas) 5/8: Nina Strohminger (Department of Legal Studies & Business Ethics, The Wharton School) Going forward, all relevant seminar information, including the speaker schedule, as well as talk titles and abstracts, will be posted here:""")
    print(a)
    print(b)
