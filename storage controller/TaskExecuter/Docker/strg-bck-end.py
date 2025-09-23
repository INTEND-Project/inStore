#The Phantom Menace
from time import sleep
import boto3
import logging
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from datetime import datetime, timezone, timedelta

#scyllaDB address
cluster = Cluster(['scylla-service.scylla.svc.cluster.local'], port=9042)
loop = True

while(loop):
    try:
        #connect to Scylla
        session = cluster.connect()
        print("--- Connecting --")

        #Query to get the newest command SCyllaDB orders the data by date so each time it should be the newest
        #need to add waiting till the time
        query = """SELECT * FROM Scheduler.Storage_controller LIMIT 1"""

        # retrieve parameters needed with data inside them 
        prepared_query = session.prepare(query)
        results = session.execute(prepared_query)
        if not results.one() is None:
            uuid = results.one().data_id
            time = results.one().scheduled
            partition = results.one().partition_id
            action = results.one().action
            destination = results.one().destination
            source = results.one().source
            filename = results.one().filename
            print("query retrieval complete")
            current_time = datetime.now()
            # Format the current time
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S.%f%z")
            scheduled_time  = time.strftime("%Y-%m-%d %H:%M:%S.%f%z")
            #If nothing is queued in the database wait 30s and check again
            print("checking")
            if scheduled_time < formatted_time:

                #Remove query from queue so that if multiple agent versions of this are present avoid conflict
                query = "DELETE FROM Scheduler.Storage_controller WHERE partition_id = ? AND scheduled = ? AND data_id = ? ;"
                prepared_query = session.prepare(query)
                results2 = session.execute(prepared_query,(partition,time, uuid))
                print("Query consumed")
            
            # This section will change based on the storage system connected to the Task Executer
            # Hence why this part is created on if systems 
            #connect to S3 there is another call to connect in the purge section command
                s3 = boto3.client('s3',
                    aws_access_key_id='minioadmin',
                    aws_secret_access_key='minioadmin',
                                  endpoint_url="minio-internal.minio-dev.svc.cluster.local:9000")

                if action == "move":
                    print("move")
                    try:
                        # Move the file
                        response = s3.copy_object(
                                Bucket=destination,
                                CopySource="/" + source + "/" + filename,
                                Key=filename)

                        print("File moved successfully")

                    # Delete the file
                        s3.delete_object(
                            Bucket=source,
                            Key=filename)

                    except Exception as e:
                        logging.error(f"Error moving file: {e}")

                if action == "delete":
                    print("delete")
                        # Delete the file
                    try:
                        s3.delete_object(
                            Bucket=source,
                            Key=filename
                            )
                        print("File deleted sucessfully")

                    except Exception as e:
                        logging.error(f"Error moving file: {e}")

                if action == "copy":
                    print("copy")
                    try:
                        response = s3.copy_object(
                                    Bucket=destination,
                                    CopySource="/" + source + "/" + filename,
                                    Key=filename)

                        print("File copied successfully")
                    
                    except Exception as e:
                        logging.error(f"Error moving file: {e}")

                if action == "purge cache":
                    print("purge")
                    
                    try:
                        s3 = boto3.resource(
                                    's3',
                                    aws_access_key_id='minioadmin',
                                    aws_secret_access_key='minioadmin',
                                    endpoint_url="minio-internal.minio-dev.svc.cluster.local:9000"
                                    )

                        bucket = s3.Bucket(str(destination))
                        #Delete all objects in the bucket                
                        bucket.objects.all().delete()
                        # Delete the bucket itself
                        bucket.delete()
                        print("cache cleared")

                    except Exception as e:
                        logging.error(f"Error moving file: {e}")

            else:
                print("waiting")
                sleep(10)
        else:
            print("waiting")
            sleep(10)

    except Exception as e:
        print(f"Error: {e}")
        sleep(30)
        session.shutdown()
