from flask import Flask, request, jsonify
from flask_cors import CORS
import redis
import os
import json

app = Flask(__name__)
CORS(app)

# Redis Connection
# We use environment variables for configuration
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

@app.route('/vote', methods=['POST'])
def vote():
    """
    Receives a vote and pushes it to the Redis queue.
    Does NOT write to the database directly.
    """
    data = request.get_json()
    vote_option = data.get('vote')

    if vote_option not in ['option_a', 'option_b']:
        return jsonify({'error': 'Invalid vote option'}), 400

    # Push to Redis List (Queue)
    try:
        data_string = json.dumps({'vote': vote_option})
        r.rpush('votes', data_string)
        return jsonify({'status': 'queued', 'message': 'Vote received and queued!'})
    except redis.exceptions.ConnectionError:
        return jsonify({'error': 'Redis unavailable'}), 503

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
