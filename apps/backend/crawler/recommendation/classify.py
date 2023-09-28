import json
import os
from collections import defaultdict

import psycopg
import numpy as np
from psycopg.rows import dict_row
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.svm import SVR, LinearSVR
from sklearn.metrics import mean_absolute_error, r2_score
from dotenv import load_dotenv
load_dotenv()

# Connect to PostgreSQL
conn = psycopg.connect(os.environ['DATABASE_URL'])

# Create a cursor

# Step 1: Data Preparation
# Load embeddings and page_rank scores
embeddings_data = []  # List to store embeddings for each page
page_rank_scores = []  # List to store page_rank scores for each page

# Fetch data from the database
cur = conn.cursor(row_factory=dict_row)
cur.execute('SELECT p.url, e.vec, p.page_rank as page_rank FROM vecs."Embeddings" e INNER JOIN "Page" p ON e.url = p.url WHERE e.index <= 5 AND p.created_at <= timestamp \'2023-09-26\' ORDER BY e.index asc LIMIT 1500000')
rows = cur.fetchall()
json.dump(rows, open("rows.json", "w+"))
rows = json.load(open("rows.json", "r"))
embeddings_url = defaultdict(list)
page_rank_dict = {}
for row in rows:
    # Assuming embeddings are stored as a comma-separated string
    embeddings = np.fromstring(row['vec'][1:-1], sep=',')
    embeddings_url[row['url']].append(embeddings)

    page_rank_dict[row['url']] = row['page_rank']

for url, embeddings in embeddings_url.items():

    if len(embeddings) < 3:
        print(f"Skipping {url}")
        continue
    embeddings = np.mean(embeddings[0:3], axis=0)
    embeddings_data.append(embeddings)
    page_rank_scores.append(page_rank_dict[url])

# Step 2: Split the Data
X_train, X_test, y_train, y_test = train_test_split(
    embeddings_data, page_rank_scores, test_size=0.15, random_state=45)

n_components = 32  # Adjust the number of components as needed
pca = PCA(n_components=n_components)
X_train = pca.fit_transform(X_train)
X_test = pca.transform(X_test)

# Step 3: Feature Engineering (if needed)
# No specific feature engineering needed since you're using embeddings.

# Step 4: Model Training
svm_model = LinearSVR()
svm_model.fit(X_train, y_train)

# Step 5: Model Evaluation
y_pred = svm_model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
print(f"Mean Absolute Error: {mae}")
print(f"R-squared: {r2}")
