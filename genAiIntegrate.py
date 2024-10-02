API_KEY = "AIzaSyCXyzvIur0cpfgsmpKsozT0G7J5ooT8xRc"
from flask import Flask, request, jsonify
import google.generativeai as genai
import pymongo
from datetime import datetime
from pymongo import MongoClient
from flask_cors import CORS
genai.configure(api_key=API_KEY)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, 
     supports_credentials=True, 
     allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Headers"])


model = genai.GenerativeModel("gemini-1.5-pro-latest")
try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["diary_db"]
    collection = db["userData"]
    print("Connected to MongoDB")
except Exception as e:
    print(f"Could not connect to MongoDB: {e}")


def find_emotion(diary_entry):
    prompt = f"""
    You are a chatbot designed to listen to a user's diary entry and identify their emotion. The emotions you can detect are: happy, sad, anxious, and normal.

    Your task is to analyze the diary entry and respond with only the identified emotion as a single word.

    Listen to this user's diary entry: {diary_entry}

    Please determine the user's emotion and provide the response as one of the following words: happy, sad, anxious, or normal.
    """

    
    result = model.generate_content(prompt)
    text_content = result.candidates[0].content.parts[0].text
    text_content_cleaned = text_content.strip()
    return text_content_cleaned
    
   

def find_activity(diary_entry, past_con):
    prompt = f"""
    You are a chatbot that listens to a user's diary entry and suggests an activity to improve their mood. Based on the content of the diary entry and the past activities, provide a specific activity that could help uplift the user's spirits.

    Listen to this user's diary entry: {diary_entry}

    Past conversations: {past_con}

    Before suggesting an activity, offer some kind words and motivation to uplift the user. Then, analyze the diary entry and suggest an appropriate activity to enhance their mood. Output should include the motivational message followed by the suggested activity.
"""


    result = model.generate_content(prompt)
    text_content = result.candidates[0].content.parts[0].text
    text_content_cleaned = text_content.strip()
    return (text_content_cleaned)



print(type(datetime.now().strftime("%Y-%m-%d")))

def store_entry(diary_entry, emotion, activity):
    entry_data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "diary_entry": diary_entry,
        "emotion": emotion,
        "activity": activity
    }
    collection.insert_one(entry_data)
    print("Entry saved to database.")

def retireve_entries():
    entries = collection.find()
    return entries




def check_if_entry_or_date(message):
    prompt = f"""
    You are an assistant that determines whether the provided input is a diary entry or a date.

    If the message is a diary entry, reply with 'Yes'. If it's a date, extract and return the date in the format 'YYYY-MM-DD'. Do not add any additional text in the output.

    Analyze the following message: {message}

    Your response should be either 'Yes' if it's a diary entry, or the extracted date if it is a date.
    """

    result = model.generate_content(prompt)
    text_content = result.candidates[0].content.parts[0].text
    text_content_cleaned = text_content.strip()
    return text_content_cleaned




# while True:
#     prompt = input("Ask me anything: ")
#     if (prompt == "exit"):
#         break
#     past_con = retireve_entries()
#     print(type(check_if_entry_or_date(prompt)))
#     if (check_if_entry_or_date(prompt) == "Yes"):
#         emotion = find_emotion(prompt)
#         activity = find_activity(prompt, past_con)
#         print(f"Emotion: {emotion}")
#         print(f"Activity: {activity}")
#         store_entry(prompt, emotion, activity)
#     else:
#         res = list(collection.find({"date": check_if_entry_or_date(prompt)}))
#         for e in (res):
#             print(e)

@app.route('/chatbot', methods=['POST'])
def chatbot():
    print("came")
    
    user_message = request.json.get('message') 
    print(user_message) # Get the user message from the request body
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    past_con =retireve_entries()
    
    # Check if it's a diary entry or date
    entry_or_date = check_if_entry_or_date(user_message)
    
    if entry_or_date == "Yes":  # It's a diary entry
        emotion = find_emotion(user_message)
        activity = find_activity(user_message, past_con)
        store_entry(user_message, emotion, activity)
        return jsonify({"emotion": emotion, "activity": activity}), 200
    else:  # It's a date
        res = list(collection.find({"date": entry_or_date}))
        message = res[0].get("diary_entry")
        print(message)
        if message:
            return jsonify(message), 200
        else:
            return jsonify({"message": "No entries found for this date"}), 404


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)