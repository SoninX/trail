import cohere
import finnhub as fin
import pandas as pd
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

client = fin.Client(api_key="d0c4bm1r01qs9fjkgfe0d0c4bm1r01qs9fjkgfeg")
co = cohere.Client("xhJQhunewDW9s173oBXkAQu3q1XUAWNAKK8WjI6n")

cached_symbols_df = None  # Global cache

# Helper function to get stock symbol suggestions (free-tier US stocks only)
def get_stock_suggestions(query):
    all_stocks = [
        {"symbol": "AAPL", "name": "Apple Inc."},
        {"symbol": "AMZN", "name": "Amazon.com Inc."},
        {"symbol": "TSLA", "name": "Tesla Inc."},
        {"symbol": "GOOGL", "name": "Alphabet Inc. (Class A)"},
        {"symbol": "MSFT", "name": "Microsoft Corporation"},
        {"symbol": "T", "name": "AT&T Inc."},
        {"symbol": "TGT", "name": "Target Corporation"},
        {"symbol": "TWTR", "name": "Twitter Inc."},
        {"symbol": "TSM", "name": "Taiwan Semiconductor Manufacturing"},
        {"symbol": "TXN", "name": "Texas Instruments Incorporated"},
        {"symbol": "NFLX", "name": "Netflix Inc."},
        {"symbol": "SPY", "name": "SPDR S&P 500 ETF Trust"},
        {"symbol": "BA", "name": "The Boeing Company"},
        {"symbol": "MS", "name": "Morgan Stanley"},
        {"symbol": "NVDA", "name": "NVIDIA Corporation"},
        {"symbol": "META", "name": "Meta Platforms, Inc."},
        {"symbol": "JPM", "name": "JPMorgan Chase & Co."},
        {"symbol": "WMT", "name": "Walmart Inc."},
        {"symbol": "DIS", "name": "The Walt Disney Company"},
        {"symbol": "INTC", "name": "Intel Corporation"},
        {"symbol": "BRK.B", "name": "Berkshire Hathaway Inc. (Class B)"},
        {"symbol": "KO", "name": "The Coca-Cola Company"},
        {"symbol": "PEP", "name": "PepsiCo, Inc."},
        {"symbol": "PYPL", "name": "PayPal Holdings, Inc."}
    ]

    query = query.lower()
    suggestions = [
        stock for stock in all_stocks
        if query in stock["symbol"].lower() or query in stock["name"].lower()
    ]
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

    evaluation_results = []
    quote = client.quote(stock_name)
    brief_report = f"Evaluation of stock: {stock_name}\n"

    # Fundamental Analysis
    if 'fundamental' in evaluation_methods:
        try:
            metric = client.company_basic_financials(stock_name, 'all')
            summary = metric.get('metric', {})
            eps = summary.get('epsTTM', 'N/A')
            pe_ratio = summary.get('peNormalizedAnnual', 'N/A')
            roe = summary.get('roeAnnual', 'N/A')
            debt_to_equity = summary.get('debtEquityAnnual', 'N/A')

            fundamental_summary = f"""
            - EPS: {eps}
            - P/E Ratio: {pe_ratio}
            - ROE: {roe}
            - Debt-to-Equity Ratio: {debt_to_equity}
            """
            evaluation_results.append(fundamental_summary)
        except:
            evaluation_results.append("Fundamental data not available.")

    # Technical Analysis
    if 'technical' in evaluation_methods:
        try:
            now = pd.Timestamp.now().timestamp()
            past = pd.Timestamp.now() - pd.Timedelta(days=200)
            candles = client.stock_candles(stock_name, 'D', int(past.timestamp()), int(now))

            df = pd.DataFrame(candles)
            if not df.empty and 'c' in df:
                close_prices = pd.Series(df['c'])
                moving_avg_50 = close_prices.rolling(window=50).mean().iloc[-1]
                moving_avg_200 = close_prices.rolling(window=200).mean().iloc[-1] if len(close_prices) >= 200 else 'N/A'
                current_price = close_prices.iloc[-1]

                technical_summary = f"""
                - Current Price: {current_price:.2f}
                - 50-day Moving Average: {moving_avg_50:.2f}
                - 200-day Moving Average: {moving_avg_200}
                """
                evaluation_results.append(technical_summary)
        except:
            evaluation_results.append("Technical data not available.")

    final_verdict = "DON'T BUY"
    if 'BUY' in evaluation_methods:
        final_verdict = "BUY"

    detailed_report_input = "\n".join(evaluation_results)
    ai_report = generate_report_with_cohere(stock_name, brief_report, detailed_report_input, final_verdict)

    return jsonify({'message': 'Stock evaluation completed!', 'report': ai_report})

def is_valid_stock(stock_name):
    global cached_symbols_df
    if cached_symbols_df is None:
        cached_symbols_df = pd.DataFrame(client.stock_symbols('US'))
    return stock_name in cached_symbols_df['symbol'].values

def generate_report_with_cohere(stock_name, brief_report, detailed_report_input, final_verdict):
    try:
        prompt = f"""
        Provide a concise stock evaluation report for {stock_name} with the following sections:

        ## Brief Report:
        {brief_report}

        ## Detailed Parameters Checked:
        {detailed_report_input}

        ## Final Verdict:
        {final_verdict}
        """
        response = co.generate(
            model='command',
            prompt=prompt,
            max_tokens=500,
            temperature=0.7
        )
        return response.generations[0].text.strip()
    except Exception as e:
        return f"Error generating report: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
