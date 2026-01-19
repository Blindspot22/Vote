import redis
import psycopg2
import os
import json
import time

# Configuration
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
DB_HOST = os.environ.get('DB_HOST', 'db')
DB_NAME = os.environ.get('DB_NAME', 'postgres')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')

def get_redis_connection():
    try:
        return redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
    except Exception as e:
        print(f"Error connecting to Redis: {e}")
        return None

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Error connecting to DB: {e}")
        return None

def main():
    print("Worker started...")
    
    # Wait for Redis
    r = None
    while not r:
        r = get_redis_connection()
        if not r:
            time.sleep(2)

    # Main Loop
    while True:
        try:
            # Blocking pop from 'votes' list
            # Returns a tuple ('votes', value)
            item = r.blpop('votes', timeout=0)
            if item:
                queue_name, data_string = item
                data = json.loads(data_string)
                vote_option = data.get('vote')
                
                print(f"Processing vote: {vote_option}")

                # Save to DB
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor()
                    # Initialize table if not exists (ideally done in migration script, but keeping it simple here)
                    cur.execute("CREATE TABLE IF NOT EXISTS votes (option TEXT PRIMARY KEY, vote_count INTEGER);")
                    cur.execute("INSERT INTO votes (option, vote_count) VALUES ('option_a', 0) ON CONFLICT (option) DO NOTHING;")
                    cur.execute("INSERT INTO votes (option, vote_count) VALUES ('option_b', 0) ON CONFLICT (option) DO NOTHING;")
                    
                    cur.execute("UPDATE votes SET vote_count = vote_count + 1 WHERE option = %s", (vote_option,))
                    conn.commit()
                    cur.close()
                    conn.close()
                    
                    # Invalidate Cache so Result Service fetches fresh data
                    try:
                        r.delete("poll_results")
                        print("Cache invalidated.")
                    except Exception as e:
                        print(f"Error invalidating cache: {e}")

                    print("Vote saved.")
                else:
                    print("DB connection failed, pushing back to queue (simplified)")
                    # In real app, handle retries carefully
                    
        except Exception as e:
            print(f"Error in worker loop: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
