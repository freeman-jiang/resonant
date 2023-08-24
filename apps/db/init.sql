CREATE TABLE links (
  id SERIAL PRIMARY KEY,
  text TEXT NOT NULL,
  url TEXT NOT NULL,
  parent_url TEXT NOT NULL,
  depth FLOAT DEFAULT 0 NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE articles (
  id SERIAL PRIMARY KEY,
  link_id INT REFERENCES links(id),
  title TEXT,
  date TEXT,
  author TEXT,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE article_outbound_links (
  PRIMARY KEY (article_id, link_id),
  article_id INT REFERENCES articles(id),
  link_id INT REFERENCES links(id)
);