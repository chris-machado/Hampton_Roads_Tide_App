import boto3, yaml, os, time, tqdm, datetime, pytz
from boto3.dynamodb.conditions import Key, Attr
from threading import Timer
from flask import Flask, request, render_template, session, make_response, jsonify
from flask_cors import CORS, cross_origin

app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


def db_connect():
    config = yaml.safe_load(open('../dynamodb.yaml'))
    dynamo_client = boto3.resource(
            service_name=config['service'],
            region_name=config['region'],
            aws_access_key_id=config['key_id'],
            aws_secret_access_key=config['access_key']
            )
    return dynamo_client.Table('HR_Tide_Data')

def write_database(data):
    table = db_connect()
    with table.batch_writer() as batch:
        counter = 0
        for record in tqdm.tqdm(data):
            batch.put_item(Item = record)
            counter += 1
        print(f'Sucessfully wrote {counter} records.')
        return 'All good'

@app.route("/", methods=["GET"])
def homepage():
    return render_template("index.html")

@app.route("/post", methods=["POST"])
def add_entry():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        data = request.json
        status = write_database(data)
        return render_template("post.html", status=status)  
    else:
        return 'Content-Type not supported!'

@app.route("/get", methods=["GET"])
@cross_origin()
def read_database_by_station():
    args = request.args
    id_num = args.get('station')
    table = db_connect()
    dt = datetime.datetime.now() - datetime.timedelta(days=4)
    dt = dt.strftime('%Y-%m-%d %H:%M')

    lastEvaluatedKey = None
    Table = {}
    while True:
        if lastEvaluatedKey == None:
            response = table.scan(
                FilterExpression=Attr('id').eq(str(id_num)) & Attr('time').gt(dt)
            )
        else:
            response = table.scan(
                ExclusiveStartKey=lastEvaluatedKey, FilterExpression=Attr('id').eq(str(id_num)) & Attr('time').gt(dt)
            )
        for item in response['Items']:
            Table[item['time']] = float(item['water_level'])

        if 'LastEvaluatedKey' in response:
            lastEvaluatedKey = response['LastEvaluatedKey']
        else:
            break  

    data = {}
    for time in Table.keys():
        utc = datetime.datetime.strptime(time, "%Y-%m-%d %H:%M")
        utc = utc.replace(tzinfo=pytz.utc)
        est_edt = utc.astimezone(pytz.timezone('US/Eastern'))
        data[datetime.datetime.strftime(est_edt, '%Y-%m-%d %H:%M')] = Table[time]
    return make_response(jsonify(data))

if __name__ == "__main__":
    app.run(port=8080, debug=True)
