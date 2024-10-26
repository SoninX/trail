from flask import Flask, request, jsonify, render_template
from transformers import GPT2Tokenizer, GPT2LMHeadModel

# Initialize Flask app
app = Flask(__name__)

# Load the trained model and tokenizer
model = GPT2LMHeadModel.from_pretrained("./trained_model")
tokenizer = GPT2Tokenizer.from_pretrained("./trained_model")

# Route for the main page
@app.route("/")
def home():
    return render_template("index.html")

# Route for handling user input and generating responses
@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.form["user_input"]
    inputs = tokenizer.encode(user_input, return_tensors="pt")
    outputs = model.generate(inputs, max_length=100, num_return_sequences=1)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run(debug=True)
