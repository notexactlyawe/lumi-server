from flask import Flask
import redis
from datetime import time, datetime, timedelta

app = Flask(__name__)
redis_inst = redis.StrictRedis(host='localhost', port=6379, db=0)
redis_inst.set('led_colour', 'red')

def store_next_event(event_date):
    '''
    Get event date as a string and store it in the redis databse
    '''
    redis_inst.set('next_event', event_date)

def change_led_colour():
    '''
    Returns an LED colour depending on the amount of time left till the next meeting
    '''
    next_event_date_string = str(redis_inst.get('next_event')).strip('b\'')

    event_date = datetime.strptime(next_event_date_string, '%Y:%M:%d')
    time_30_mins = timedelta(seconds=30*60)
    time_now = datetime.now()

    if event_date - time_30_mins > time_now:
        redis_inst.set('led_colour', 'red')
    else:
        redis_inst.set('led_colour', 'green')

@app.route('/colour')
def get_led_colour():
    return redis_inst.get('led_colour')

if __name__ == "__main__":
    app.run(port=3000, debug=True)
