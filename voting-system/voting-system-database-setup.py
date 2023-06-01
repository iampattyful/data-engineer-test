import psycopg2

# Connect to PostgreSQL
conn = psycopg2.connect(dbname='voting_system',
                        user='postgres', password='postgres', host='localhost')

# Create the 'features' table to store product feature names and vote counts
cur = conn.cursor()
cur.execute('''
CREATE TABLE features
(
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    vote_count INTEGER NOT NULL DEFAULT 0
)
''')
conn.commit()

# Insert initial data into the 'features' table
cur.execute("INSERT INTO features (name) VALUES ('P1_chatbot')")
cur.execute("INSERT INTO features (name) VALUES ('P2_user_generated_content')")
cur.execute("INSERT INTO features (name) VALUES ('P3_personalized_push')")
conn.commit()

# Create the 'votes' table to store individual votes with timestamps
cur.execute('''
CREATE TABLE votes
(
    id SERIAL PRIMARY KEY,
    feature_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
)
''')
conn.commit()

# Close the cursor and connection
cur.close()
conn.close()
