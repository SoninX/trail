import openai
import yfinance as yf
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Set your OpenAI API key
co = cohere.Client(xhJQhunewDW9s173oBXkAQu3q1XUAWNAKK8WjI6n)
# Helper function to get stock symbols based on user input (beginning with the query)
def get_stock_suggestions(query):
    all_stocks = ["AAPL", "AMZN", "TSLA", "GOOGL", "MSFT", "T", "TGT", "TWTR", "TSM", "TXN", "NFLX", "SPY", "BA", "MS"]
    suggestions = [stock for stock in all_stocks if stock.lower().startswith(query.lower())]
    return suggestions

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/suggest-stocks', methods=['GET'])
def suggest_stocks():
    query = request.args.get('query', '')
    suggestions = get_stock_suggestions(query)
    return jsonify({'suggestions': suggestions})

@app.route('/evaluate-stock', methods=['POST'])
def evaluate_stock():
    data = request.get_json()
    stock_name = data.get('stockName')
    evaluation_methods = data.get('evaluationMethods')

    if not is_valid_stock(stock_name):
        return jsonify({'message': 'Invalid stock ticker', 'report': ''})

    # Generate the evaluation results based on the selected methods
    evaluation_results = []
    if 'fundamental' in evaluation_methods:
        evaluation_results.append(f"Performing Fundamental Analysis on {stock_name}")
    if 'technical' in evaluation_methods:
        evaluation_results.append(f"Performing Technical Analysis on {stock_name}")
    if 'ddm' in evaluation_methods:
        evaluation_results.append(f"Applying Dividend Discount Model on {stock_name}")
    if 'valueInvesting' in evaluation_methods:
        evaluation_results.append(f"Applying Value Investing Strategy on {stock_name}")
    if 'growthInvesting' in evaluation_methods:
        evaluation_results.append(f"Performing Growth Investing Analysis on {stock_name}")
    if 'modifiedFlowchart' in evaluation_methods:
        evaluation_results.append(f"Performing Modified Investment Flowchart Analysis on {stock_name}")

    # Combine the evaluation methods into a single string
    detailed_report_input = "\n".join(evaluation_results)

    # Call OpenAI API to generate the detailed report
    ai_report = generate_report_from_ai(detailed_report_input)

    return jsonify({'message': 'Stock evaluation completed!', 'report': ai_report})

@app.route('/send-to-ai', methods=['POST'])
def send_to_ai():
    data = request.get_json()
    stock_name = data.get('stockName')
    evaluation_methods = data.get('evaluationMethods')
    detailed_report = data.get('detailedReport')

    ai_report = generate_report_from_ai(detailed_report)
    return jsonify({'report': ai_report})

def is_valid_stock(stock_name):
    try:
        stock = yf.Ticker(stock_name)
        stock_info = stock.info
        if 'regularMarketPrice' in stock_info:
            return True
        else:
            return False
    except Exception:
        return False

def generate_report_from_ai(detailed_report_input):
    try:
        # Send the evaluation data to OpenAI for generating a detailed report
        response = openai.Completion.create(
            engine="text-davinci-003",  # You can change the model here if needed
            prompt=f"Generate a detailed investment report based on the following evaluation:\n{detailed_report_input}",
            max_tokens=500,  # Adjust based on the length of report needed
            n=1,
            stop=None,
            temperature=0.7,
        )

        # Extract the report from the OpenAI response
        ai_report = response.choices[0].text.strip()
        return ai_report
    except Exception as e:
        return f"Error generating report: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
