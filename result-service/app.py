from flask import Flask, jsonify
from flask_cors import CORS
import psycopg2
import redis
import os
import json
import time

app = Flask(__name__)
CORS(app)

# Redis Connection for Caching
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
# Result Service only reads, but sometimes sets cache
try:
    r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
except Exception as e:
    r = None
    print(f"Redis connection failed: {e}")

def get_db_connection():
    """Connect to the Postgres database with retries."""
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(
                host=os.environ.get('DB_HOST', 'db'),
                database=os.environ.get('DB_NAME', 'postgres'),
                user=os.environ.get('DB_USER', 'postgres'),
                password=os.environ.get('DB_PASSWORD', 'postgres')
            )
            return conn
        except psycopg2.OperationalError:
            retries -= 1
            time.sleep(1)
    return None

@app.route('/results', methods=['GET'])
def get_results():
    # 1. Try Cache
    if r:
        try:
            cached_results = r.get("poll_results")
            if cached_results:
                print("Returning cached results")
                return jsonify(json.loads(cached_results))
        except redis.exceptions.ConnectionError:
            pass

    # 2. Query Database (Cache Miss)
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database unavailable'}), 503

    cur = conn.cursor()
    try:
        print("Querying Database")
        cur.execute("SELECT option, vote_count FROM votes")
        votes = cur.fetchall()
        results_dict = {row[0]: row[1] for row in votes}
        
        response = {
            'option_a': results_dict.get('option_a', 0),
            'option_b': results_dict.get('option_b', 0)
        }

        # 3. Update Cache (TTL 10 seconds to prevent stale data staying forever if invalidation fails)
        if r:
            try:
                r.set("poll_results", json.dumps(response), ex=10)
            except Exception as e:
                print(f"Failed to cache results: {e}")

        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
