import json

from langchain.chat_models import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.schema import AIMessage
from langchain.schema.runnable import RunnableConfig

from test import articles

model = ChatAnthropic(model_name="claude-2", max_tokens_to_sample=4096)

prompt = ChatPromptTemplate.from_messages([
    ("human", " Article Title: '{title}'. Article Content: {content}."
              "Come up with five quotes (between 60 and 100 words) directly from the source article that are INTERESTING and RELEVANT and BEST SUMMARIZE THE ARTICLE."
              "Follow the length requirements exactly."
              "Format the response as a JSON list[string]. Do not output anything else. Use only exact quotations."
     )
])

quote_chain = prompt | model

ranking_prompt = ChatPromptTemplate.from_messages([
    ("human", "You are an interested reader. The title is {title}, content is {content}. The quotes are: {quotes}."
              "Now, rank each quote based on how much it hooks the reader in (interestingness) and relevance from 0 to 20."
              "JSON Output: List[Object(interestingness: int, relevance: int, quote: str)]. Do NOT output anything else. Only output JSON."),
    AIMessage(content = "[")
])

ranking_chain = ranking_prompt | model
def process_article_batch(articles: list[dict]):
    config = RunnableConfig(max_concurrency=1)
    result = []

    quote_responses = quote_chain.batch(articles, config = config)

    ranking_inputs = [dict(**article, quotes = quotes) for article, quotes in zip(articles, quote_responses)]

    ranking_outputs = ranking_chain.batch(ranking_inputs, config = config)
    for output in ranking_outputs:
        response = '[' + output.content
        print(response)
        result.append(json.loads(response))
    return result

print(process_article_batch(articles[0:1]))
# chain = prompt | model | StrOutputParser()
#
# airesponse = chain.batch(articles)
#
# prompt.append(airesponse)
# prompt.append(HumanMessage(
#     content = "Now, rank each excerpt based on how much it hooks the reader in (interestingness) and relevance from 0 to 20. Output: List[Object(interestingness: int, relevance: int)]"
# ))
#
# chain = prompt | model
#
# response = chain.invoke(articles[0])
#
# print(response.content)
# print(airesponse.content)