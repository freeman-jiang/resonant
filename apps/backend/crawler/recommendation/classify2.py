import json
import os

import psycopg
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LinearRegression
from dotenv import load_dotenv
from sklearn.svm import LinearSVR

load_dotenv()

# Connect to PostgreSQL
conn = psycopg.connect(os.environ['DATABASE_URL'])


# Function to fetch data from the database
def fetch_data():
    conn = psycopg.connect(
        os.environ['DATABASE_URL']
    )
    cur = conn.cursor()

    query = """
    SELECT p.content, p.page_rank
    FROM "Page" p
    WHERE p.created_at <= timestamp '2023-09-26'
    """

    cur.execute(query)
    results = cur.fetchall()

    cur.close()
    conn.close()

    return results


# Fetch data from the database
data = fetch_data()
json.dump(data, open("data.json", "w+"))
data = json.load(open("data.json", "r"))
# Separate content and page_rank scores
content = [row[0] for row in data if row[1] is not None]
page_rank = [row[1] for row in data if row[1] is not None]

# Split the data into training and testing sets
content_train, content_test, page_rank_train, page_rank_test = train_test_split(content, page_rank, test_size=0.2,
                                                                                random_state=42)

# Text preprocessing (e.g., TF-IDF vectorization)
tfidf_vectorizer = TfidfVectorizer()
content_train_tfidf = tfidf_vectorizer.fit_transform(content_train)
content_test_tfidf = tfidf_vectorizer.transform(content_test)

# Create and train an ML model (e.g., Linear Regression)
model = LinearSVR()
model.fit(content_train_tfidf, page_rank_train)

# Make predictions on the test set
page_rank_pred = model.predict(content_test_tfidf)

# Evaluate the model (you can use appropriate metrics for regression)
# For example, mean squared error (MSE)
from sklearn.metrics import mean_squared_error, r2_score

mse = mean_squared_error(page_rank_test, page_rank_pred)
r2 = r2_score(page_rank_test, page_rank_pred)

print(f"R-squared: {r2}")

print(f"Mean Squared Error: {mse}")
