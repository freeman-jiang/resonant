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

    topic_distr, _ = model.approximate_distribution(DOC, window = 10, stride = 3)
    viz = model.visualize_distribution(topic_distr[0])
    viz.write_html("b.html")

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
    pages = cursor.execute("""WITH pages AS (SELECT * FROM "Page" LIMIT 1500)
SELECT * FROM pages INNER JOIN "vecs"."Embeddings" ON pages.url = "vecs"."Embeddings".url WHERE index < 4 ORDER BY pages.url, index
""").fetchall()

    print(cluster_documents_with_bertopic(pages))

    return


DOC = """
In the last few weeks it’s become clear to me how silly it is that I am so afraid to share this on the blog and in my life. It’s not healthy to feel guilt for listening to your own body– I should be thanking myself, not telling myself I’ve done something wrong. I have “sinned.”

When it comes to veganism, that is.


When I created this blog over a year ago, I identified with being a plant-based vegan. As the months wore on and I learned more about health, the body and dietary labels, I started believing less in the label of “veganism” and more in listening to my body. I ate a cruelty-free plant-based diet because it felt good to me, my body felt nourished and fueled, I experienced no stomach problems, I was eating the most ethical and compassionate diet for animals/the earth, and my mind was clear and content.

I was vegan, and it worked.

Then around November my body started telling me things. My roasted veggies and quinoa for dinner were not satisfying me like they once had, and my green smoothies for breakfast were giving me stomach aches and making me feel bloated and overly full. I was shocked! This plant-based lifestyle I had so adored and built my career around was “failing” me… Or so I believed.

I spent the next several months ignoring my body’s internal cues. I longed to try new things that looked and sounded good to me, but ethically I couldn’t do it. I had done so much research, read so many books, watched so many documentaries and personally connected with so many vegans and those against eating animal protein, and I believed wholeheartedly in the lifestyle. I felt that I knew better than to eat animal protein. I was educated, I had will power, and I loved being vegan.

That’s what I kept telling myself. And most days, I believed it. Other days, I knew that I was going to have to eat a bowl of veggies the size of a monster truck to fill me up. Some days, I could hardly eat at all because my biochemistry was so thrown off. Some days, I had wild and ravenous sugar cravings that took over my mind and hindered me from focusing on anything else.


I also started fearing a LOT of things when it came to food. Having grown up with a notoriously sensitive stomach, I already avoided wheat, fried foods, sauces, oil, flour of any type, some legumes and many grains. Then I started reading about raw foods, digestion, food combining, the space at which meals should be eaten apart from each other, and the dangers of even all-natural fructose. (And let’s not forget my bout with 80/10/10 raw veganism.)

I started living in a bubble of restriction. Entirely vegan, entirely plant-based, entirely gluten-free, oil-free, refined sugar-free, flour-free, dressing/sauce-free, etc. and lived my life based off of when I could and could not eat and what I could and could not combine. There is nothing wrong with any of those things (many of them are great, actually!!) but my body didn’t feel GOOD & I wasn’t listening to it.

Does that sound crazy to you?

Yeah, it sounds crazy to me too. My wake up call came when one of my best friends was in town and we went to get smoothies at Juice Press before spending the day in Central Park. We went to Juice Press because I was the difficult one– I was very limited when it came to breakfast foods, and my friends suggested Juice Press knowing it would make things easier on everyone.

I knew which juice I wanted long before we headed over… A green juice with a tiny bit of apple but not their green juice with more apple juice because that one was too sugary. (If you’re familiar with JP, I wanted ‘Series B’.) We got there, and they didn’t have it. I stared at the juices and smoothies and raw food for a good 15 minutes, panicking, because I had no idea how I was going to navigate this setback. By this time my two friends already had their smoothies and were nearly done with them. Since they’ve known me forever and they know my issues with decision making… They were patient.


Eventually my roomie Katie suggested we walk to a different Juice Press location, a mile out of our way, to get the juice I wanted. I was so relieved… Or so I convinced myself. My stomach was in knots because I had hardly eaten for days, and my body wasn’t sure it could even walk a mile without any sustenance. And we were at a raw food juice bar! A place where everything on the menu was vegan! I should NOT have been feeling so limited and so helpless.

We walked, I got my juice, sipped it, and was still starving. I needed FOOD & I wasn’t allowing myself to have it for 5 billion reasons in my head that are hard to explain but you’re starting to get the picture.

Things continued to spiral downward for a few more weeks… When my mom and sister were in town, I don’t think I enjoyed a single meal with them. I ate before or after seeing them, panicked that the food at the restaurants we were going to was going to make me feel like crap and throw off my system.

I was also addicted to juice cleanses. I felt that if I cleansed my body like I had done successfully so many times in the past, these cravings and hunger pains and disordered habits would go away.


I knew I had disordered eating habits, but until I was willing to admit I had developed some variation of an eating disorder I wasn’t going to be able to do anything about it. One night over dinner with my dear friend Tara, someone who I owe every ounce of my realization to… I started to accept it. It kind of came to me all at once – entirely shocking and strangely unsurprising at the same time.

Then I continued to accept it. And I cannot tell you how freeing that was.

I’m not writing about it because I think it’s normal to share such personal aspects of one’s life in such a public place… I actually think it’s very abnormal, and it is counterintuitive for me to be doing this. I’m writing about it because I value you as my readers and friends tremendously, and I think it’s time we ditch the labels.


It’s time to advocate a lifestyle that doesn’t involve restriction, labeling or putting ourselves into a box. I am extremely passionate about eating ethically and eating whole, plant-based foods from the earth. My original passion for health stemmed from learning about real foods and how they affect our bodies versus chemically-produced and factory farmed disgustingness that is not food.

But that doesn’t mean that living life in moderation is a sin. It’s a beautiful thing… To accept moderation, to accept balance, to allow for happiness and growth and change and fluctuation. Life is an ebb and flow, and our bodies and our mindsets evolve! It is okay to embrace that, and it’s detrimental to our health and our well being not to.

My body was trying to speak to me for many months and I did not listen. As a result, I grew extremely deficient in a variety of vitamins and hormones and knocked myself way out of whack. I injured my ankle doing something that would have never injured me in the past, I lost my period for several months and I experienced a major lack of energy. I ignored my body’s internal cues… And that wasn’t cool.

So, long story short, I am reevaluating my diet. I’m saying goodbye to the labels. I’ve tried organic farm fresh eggs and wild fish from the local farmer’s market. I had some sashimi from an organic restaurant that I very much trust. All in the last couple of weeks. This is terrifying for me and extremely out of my comfort zone after living under the vegan umbrella for so long, but I’m doing it for my physical and mental health.


I am getting help in other areas too, and I am beyond okay with admitting that. I have always been a huge advocate of therapy and getting to know oneself on a deeper label, and I feel very lucky to be connecting with myself in a whole new way.

This doesn’t mean you are going to see me at a hole in the wall burger joint eating cheeseburgers and downing milkshakes. I still believe in ethical, sustainable food that comes from as close to the earth as possible… Farm raised, locally grown and as organic as can be. I am still against factory farming and the lies that the food industry hides behind, and I still love animals and am as passionate about their rights as ever before.

I am simply taking my health into my own hands, and I am encouraging you to do the same. My philosophy has shifted, and rightfully so. When I came up with the name The Blonde Vegan I was a full-fledged vegan girl who was still in college and had just discovered plant-based eating and was totally enamored by it.

Plants are amazing! Vegetables, fruits, grains, nuts and legumes are beautiful foods from the earth and should be incorporated into as many meals as possible throughout the day. But that’s not ALL that is out there. Some of us need more in order to fuel or bodies properly– especially those of us with extreme “all or nothing” personalities like my own.

Vegan diets can absolutely work if you’re eating a balanced diet. One example, my friend Katie has been vegan for 12 years and lives an extremely healthy lifestyle. She is balanced, and has not experienced the restrictive aspects of the diet like I did. I know countless other people who thrive off of a plant-based diet. I did, for quite some time. And I absolutely respect anyone who chooses that lifestyle. I still think it’s amazing. But sometimes, in some bodies, things change and we have to pay attention to that.

That’s the point… we are all different!


I have changed, and I ask for your support and acceptance, which I can most assuredly tell you I will give to all of you. ❤

That being said… I’m in the market for a new blog name. I am heart broken about this because The Blonde Vegan has become an extension of who I am, and it will always be a part of me. But as I move my brand forward I do not want to confuse people about my philosophy and what I stand for. As a health coach, I want to help other people learn to eat in the best possible way for their bodies. I want to work with people who have developed “orthorexia,” as I have, and I don’t believe TBV will serve me as a name for those purposes.

Love to all of you. Please share your thoughts with me on all of this. It feels good to be honest, but it’s freaking terrifying. Love to my vegans and love to everyone else– I am still the same compassionate girl I was yesterday, last month and last year.

*ADDENDUM: I have written a memoir about my transition experience, Breaking Vegan, that is now available for pre-order. It will be out in November. Email me the preorder receipt of your book to get added to the TBB Tribe email list. The book is about my eating disorder journey, and has a balance guide + 25 healthy, whole foods recipes.

"""