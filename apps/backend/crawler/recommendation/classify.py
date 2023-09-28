import os

import psycopg
import numpy as np
from psycopg.rows import dict_row
from sklearn.model_selection import train_test_split
from sklearn.svm import SVR
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

cur.execute('SELECT p.url, AVG(e.vec) as vec, AVG(p.page_rank) as page_rank FROM vecs."Embeddings" e INNER JOIN "Page" p ON e.url = p.url WHERE e.index <= 6 GROUP BY p.url LIMIT 10000')
rows = cur.fetchall()
for row in rows:
    embeddings = np.fromstring(row['vec'][1:-1], sep=',')  # Assuming embeddings are stored as a comma-separated string
    embeddings_data.append(embeddings)
    page_rank_scores.append(row['page_rank'])

# Step 2: Split the Data
X_train, X_test, y_train, y_test = train_test_split(embeddings_data, page_rank_scores, test_size=0.2, random_state=45)

# Step 3: Feature Engineering (if needed)
# No specific feature engineering needed since you're using embeddings.

# Step 4: Model Training
svm_model = SVR()
svm_model.fit(X_train, y_train)

# Step 5: Model Evaluation
y_pred = svm_model.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
print(f"Mean Absolute Error: {mae}")
print(f"R-squared: {r2}")

# Commit changes to the database
conn.commit()

# Close the cursor and the connection
cur.close()
conn.close()