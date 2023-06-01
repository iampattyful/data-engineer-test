from sanic import Sanic
from sanic.response import json
import psycopg2

app = Sanic("Voting-System")
conn = psycopg2.connect(dbname='voting_system',
                        user='postgres', password='postgres', host='localhost')


@app.route('/vote', methods=['POST'])
async def vote(request):
    try:
        feature_id = request.json['feature_id']
    except KeyError:
        return json({'success': False, 'message': 'Missing feature ID in request body'}, status=400)

    try:
        feature_id = int(feature_id)
    except (ValueError, TypeError):
        return json({'success': False, 'message': 'Invalid feature ID'}, status=400)

    cur = conn.cursor()
    cur.execute("SELECT id FROM features WHERE id = %s", (feature_id,))
    result = cur.fetchone()

    if not result:
        return json({'success': False, 'message': 'Invalid feature ID'}, status=400)

    cur.execute(
        "UPDATE features SET vote_count = vote_count + 1 WHERE id = %s", (feature_id,))
    cur.execute("INSERT INTO votes (feature_id) VALUES (%s)", (feature_id,))
    conn.commit()
    cur.close()

    return json({'success': True, 'message': 'Voted successfully'})


@app.route('/result', methods=['GET'])
async def result(request):
    cur = conn.cursor()
    cur.execute("SELECT name, vote_count FROM features")
    rows = cur.fetchall()
    result = {'features': []}
    for row in rows:
        feature = {'name': row[0], 'cumulative_vote_count': row[1]}
        result['features'].append(feature)
    cur.execute(
        "SELECT COUNT(*) FROM votes WHERE created_at > NOW() - INTERVAL '10 minutes'")
    total_votes_last_10_min = cur.fetchone()[0]
    cur.close()
    if total_votes_last_10_min is None:
        total_votes_last_10_min = 0
    result['total_votes_last_10_min'] = total_votes_last_10_min
    return json(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
