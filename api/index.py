import firebase_admin
from firebase_admin import firestore
from firebase_admin import credentials
import os

from pythonping import ping

from flask import Flask, request, jsonify

from datetime import datetime

app = Flask(__name__)

json_file_path = os.path.join(os.path.dirname(__file__), 'logbug-c66f4-firebase-adminsdk-k36kb-61ac7dad2c.json')

cred = credentials.Certificate(json_file_path) # firebase credentials

conn = firebase_admin.initialize_app(cred) # firestore app
db = firestore.client() # database connection


@app.route('/') 
def welcome_message():
    return "Welcome to LogBug Mk 1 API!"

@app.route('/getbugs', methods=['GET'])
def get_bugs():
    api_key = request.args.get('api_key')
    
    if not api_key:
        return jsonify({"error": "API key is required"}), 400
    
    # Verify the API key
    orgs = db.collection('orgs').where('api_key', '==', api_key).get()
    if not orgs:
        return jsonify({"error": "Invalid API key"}), 403
    
    org_id = orgs[0].id
    
    # Get bugs for the organization
    bugs = db.collection('bugs').where('orgID', '==', org_id).get()
    # also add the bug id to the response
    bug_list = []
    for bug in bugs:
        bug_data = bug.to_dict()
        bug_data['id'] = bug.id
        bug_list.append(bug_data)
        

    if not bug_list:
        return jsonify({"error": "No bugs found"}), 404
    
    return jsonify(bug_list)

@app.route('/addbug', methods=['POST'])
def add_bug():
    # Ensure the request Content-Type is application/json
    if request.content_type != 'application/json':
        return jsonify({"error": "Content-Type must be application/json"}), 415
    
    # Get the JSON data from the request
    bug_data = request.get_json()

    if not bug_data:
        return jsonify({"error": "No JSON data found"}), 400
    
    api_key = request.args.get('api_key')
    bug_author = ""
    bug_name = bug_data.get('bugName')
    bug_description = bug_data.get('bugDesc')
    priority = bug_data.get('priority')

    isOpen = "true"
    
    if not api_key:
        return jsonify({"error": "API key is required"}), 400
    
    # Verify the API key
    orgs = db.collection('orgs').where('api_key', '==', api_key).get()
    if not orgs:
        return jsonify({"error": "Invalid API key"}), 403
    
    org_id = orgs[0].id

    project = db.collection('projects').where('orgID', '==', org_id).get() 
    project_id = project[0].id

    bug = {
        'bugAuthor': bug_author,
        'bugDesc': bug_description,
        'bugName': bug_name,
        'orgID': org_id,
        'priority': priority,
        'projectID': project_id,
        'isOpen': isOpen,
        'created_at': datetime.utcnow()  # Assuming you want to store the creation time
    }

    db.collection('bugs').add(bug)

    return jsonify({"message": "Bug added successfully"}), 201


@app.route('/updatebug', methods=['PUT'])
def update_bug():
    # Ensure the request Content-Type is application/json
    if request.content_type != 'application/json':
        return jsonify({"error": "Content-Type must be application/json"}), 415
    
    # Get the JSON data from the request
    bug_data = request.get_json()

    if not bug_data:
        return jsonify({"error": "No JSON data found"}), 400
    
    api_key = request.args.get('api_key')
    
    # fields are optional if not provided they will not be updated and will remain the same
    bug_name = bug_data.get('bugName')
    bug_description = bug_data.get('bugDesc')
    priority = bug_data.get('priority')
    isOpen = bug_data.get('isOpen')

    if not api_key:
        return jsonify({"error": "API key is required"}), 400
    
    # Verify the API key
    orgs = db.collection('orgs').where('api_key', '==', api_key).get()
    if not orgs:
        return jsonify({"error": "Invalid API key"}), 403
    
    org_id = orgs[0].id

    # Get the bug ID from the URL
    bug_id = request.args.get('bug_id')
    if not bug_id:
        return jsonify({"error": "Bug ID is required"}), 400
    
    # Get the bug from the database
    bug = db.collection('bugs').document(bug_id).get()
    if not bug.exists:
        return jsonify({"error": "Bug not found"}), 404
    
    # Update the bug
    bug_data = bug.to_dict()
    
    # use swtich case to update the fields
    if bug_name:
        bug_data['bugName'] = bug_name
    if bug_description:
        bug_data['bugDesc'] = bug_description
    if priority:
        bug_data['priority'] = priority
    if isOpen:
        bug_data['isOpen'] = isOpen
    
    db.collection('bugs').document(bug_id).set(bug_data)

    return jsonify({"message": "Bug updated successfully"}), 200


@app.route('/deletebug', methods=['DELETE'])
def delete_bug():
    api_key = request.args.get('api_key')
    
    if not api_key:
        return jsonify({"error": "API key is required"}), 400
    
    # Verify the API key
    orgs = db.collection('orgs').where('api_key', '==', api_key).get()
    if not orgs:
        return jsonify({"error": "Invalid API key"}), 403
    
    org_id = orgs[0].id
    
    # Get the bug ID from the URL
    bug_id = request.args.get('bug_id')
    if not bug_id:
        return jsonify({"error": "Bug ID is required"}), 400
    
    # Get the bug from the database
    bug = db.collection('bugs').document(bug_id).get()
    if not bug.exists:
        return jsonify({"error": "Bug not found"}), 404
    
    # Delete the bug
    db.collection('bugs').document(bug_id).delete()

    return jsonify({"message": "Bug deleted successfully"}), 200


@app.route('/ping', methods=['GET'])
def get_networkping():
    response = ping('thelogbug.com', count=4)

    pingNumber = response.rtt_avg_ms

    stringResponse = "Server Ping: " + str(pingNumber) + "ms"

    return jsonify(stringResponse)
    

if __name__ == '__main__':
    app.run(debug=True, port=5000)
