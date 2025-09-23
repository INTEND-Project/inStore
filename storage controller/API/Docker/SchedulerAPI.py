#Version Two
from flask import Flask, jsonify, request
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
import datetime

app = Flask(__name__)

# ScyllaDB setup
#Set-up of database (creates keyspace and table if they don't exist also this is to check if ScyllaDB is online aswell
cluster = Cluster(['scylla-service.scylla.svc.cluster.local'],port=9042)
# Create a session object
session = cluster.connect()

try:
    session = cluster.connect() # Connect to the cluster without a specific keyspace initially to create keyspace and table
    print("--- Setting up database ---")
    keyspace_query = """
        CREATE KEYSPACE IF NOT EXISTS Scheduler
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor' : 1};
    """ 
    session.execute(SimpleStatement(keyspace_query))
    print("Keyspace 'Scheduler' created")

# Create Table
    table_query = """CREATE TABLE IF NOT EXISTS Scheduler.Storage_Controller
    (partition_id TEXT, scheduled timestamp, filename text, source text, action text, destination text,data_id uuid, PRIMARY KEY (partition_id, scheduled, data_id)) WITH CLUSTERING ORDER BY (scheduled ASC);"""

    session.execute(SimpleStatement(table_query))
    print("Table 'Storage_Controller' created in 'Scheduler' keyspace.")
    
except Exception as e:
        print(f"Error : {e}")
        session.shutdown()

@app.route('/LoadData', methods=['POST'])
def LoadDataToQueue():
    try:
        #Take request from API and ensure all parameters are present
        json_data = request.get_json()
        action = json_data['action']
        partition_id = json_data['partition_id']
        filename = json_data['filename']
        source = json_data['source']
        input_time  = json_data['scheduled_time']
        format = "%Y-%m-%d %H:%M:%S.%f%z"
        scheduled_time = datetime.datetime.strptime(input_time, format)
    except KeyError as e:
        #error message
        return jsonify({"error": f"Missing required parameter: {e}"}), 400

    # Check if destination is required
    if action == 'move' or action == 'copy':
        destination = json_data['destination']
                  
    else:
        destination = "none"
    # Send Query into ScyllaDB
    insert_query = session.prepare("""
        INSERT INTO Scheduler.Storage_Controller (partition_id, scheduled, filename, destination, action, source, data_id)
        VALUES (?, ?, ?, ?, ?, ?, now())
    """)
    
    session.execute(insert_query, (
                partition_id,
                scheduled_time,
                filename,
                destination,
                action,
                source
        ))
    return jsonify({"message": f"Action '{action}' for file '{filename}' scheduled at {scheduled_time} in parition {partition_id}"}), 202
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
