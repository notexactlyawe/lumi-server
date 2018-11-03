from flask import Flask
import redis

app = Flask(__name__)
redis_inst = redis.StrictRedis(host='localhost', port=6379, db=0)
redis_inst.set('led_colour', 'red')

@app.route('/colour')
def get_led_colour():
    return redis_inst.get('led_colour')

if __name__ == "__main__":
    app.run(port=3000, debug=True)
