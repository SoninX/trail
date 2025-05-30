import cohere
import yfinance as yf
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

co = cohere.Client("xhJQhunewDW9s173oBXkAQu3q1XUAWNAKK8WjI6n")
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

    evaluation_results = []
    stock = yf.Ticker(stock_name)
    info = stock.info
    history = stock.history(period="6mo")

    # Brief Report
    brief_report = f"Evaluation of stock: {stock_name}\n"

    # Fundamental Analysis
    if 'fundamental' in evaluation_methods:
        eps = info.get('trailingEps', 'N/A')
        pe_ratio = info.get('trailingPE', 'N/A')
        roe = info.get('returnOnEquity', 'N/A')
        debt_to_equity = info.get('debtToEquity', 'N/A')

        fundamental_summary = f"""
        - EPS: {eps}
        - P/E Ratio: {pe_ratio}
        - ROE: {roe}
        - Debt-to-Equity Ratio: {debt_to_equity}
        """
        evaluation_results.append(fundamental_summary)

    # Technical Analysis
    if 'technical' in evaluation_methods:
        moving_avg_50 = history['Close'].rolling(window=50).mean().iloc[-1]
        moving_avg_200 = history['Close'].rolling(window=200).mean().iloc[-1] if len(history) >= 200 else 'N/A'
        current_price = history['Close'].iloc[-1]

        technical_summary = f"""
        - Current Price: {current_price:.2f}
        - 50-day Moving Average: {moving_avg_50:.2f}
        - 200-day Moving Average: {moving_avg_200}
        """
        evaluation_results.append(technical_summary)

    # Dividend Discount Model (DDM)
    if 'ddm' in evaluation_methods:
        dividend_yield = info.get('dividendYield')
        dividend = info.get('dividendRate')
        required_return = 0.08  # assumed
        if dividend and required_return and required_return != dividend_yield:
            ddm_value = dividend / required_return
        else:
            ddm_value = 'N/A'

        ddm_summary = f"""
        - Dividend: {dividend}
        - Assumed Required Return: {required_return}
        - Estimated Value (DDM): {ddm_value}
        """
        evaluation_results.append(ddm_summary)

    # Value Investing
    if 'valueInvesting' in evaluation_methods:
        intrinsic_value = info.get('bookValue', 'N/A')
        current_price = info.get('currentPrice', 'N/A')
        margin_of_safety = 'N/A'
        if isinstance(intrinsic_value, (int, float)) and isinstance(current_price, (int, float)):
            margin_of_safety = ((intrinsic_value - current_price) / current_price) * 100

        value_summary = f"""
        - Book Value per Share: {intrinsic_value}
        - Current Price: {current_price}
        - Margin of Safety: {margin_of_safety}%
        """
        evaluation_results.append(value_summary)

    # Growth Investing
    if 'growthInvesting' in evaluation_methods:
        revenue_growth = info.get('revenueGrowth', 'N/A')
        profit_margins = info.get('profitMargins', 'N/A')
        growth_summary = f"""
        - Revenue Growth: {revenue_growth}
        - Profit Margins: {profit_margins}
        """
        evaluation_results.append(growth_summary)

    # Modified Investment Flowchart
    if 'modifiedFlowchart' in evaluation_methods:
        payout_ratio = info.get('payoutRatio', 'N/A')
        beta = info.get('beta', 'N/A')
        flowchart_summary = f"""
        - Payout Ratio: {payout_ratio}
        - Beta: {beta}
        """
        evaluation_results.append(flowchart_summary)

    # Final Verdict
    final_verdict = "DON'T BUY"
    if 'BUY' in evaluation_methods:  # Assuming a condition for Buy. You can adjust this logic as per your evaluation
        final_verdict = "BUY"

    # AI Report Generation with Cohere
    detailed_report_input = "\n".join(evaluation_results)
    ai_report = generate_report_with_cohere(stock_name, brief_report, detailed_report_input, final_verdict)

    return jsonify({'message': 'Stock evaluation completed!', 'report': ai_report})


@app.route('/send-to-ai', methods=['POST'])
def send_to_ai():
    data = request.get_json()
    stock_name = data.get('stockName')
    evaluation_methods = data.get('evaluationMethods')
    detailed_report = data.get('detailedReport')

    # Assuming you have the necessary variables like brief_report, final_verdict, etc.
    brief_report = "Microsoft Corporation (MS) stock should not be purchased at this time."  # Example brief report
    final_verdict = "DON'T BUY"  # Example final verdict

    # Generate the detailed report input based on the evaluation results (like your fundamental, technical, etc. metrics)
    detailed_report_input = "\n".join(detailed_report)  # Assuming 'detailedReport' is a list or string

    ai_report = generate_report_with_cohere(stock_name, brief_report, detailed_report_input, final_verdict)
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

def generate_report_with_cohere(stock_name, brief_report, detailed_report_input, final_verdict):
    try:
        prompt = f"""
        Provide a concise stock evaluation report for {stock_name} with the following sections:

        1. **Brief Report**: Summarize the stock evaluation with a focus on key highlights and a recommendation based on the data.
        2. **Detailed Parameters Checked**: List all parameters checked with their values (if available) in a simple format.
        3. **Final Verdict**: Provide a clear "BUY" or "DON'T BUY" recommendation based on the analysis.

        Don't include any additional commentary, explanations, or extra details beyond what's asked.
        
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
            max_tokens=500,  # Limit the response size to avoid exceeding the token limit
            temperature=0.7
        )

        # Extract the report from the Cohere response
        ai_report = response.generations[0].text.strip()

        return ai_report
    except Exception as e:
        return f"Error generating report: {str(e)}"


if __name__ == '__main__':
    app.run(debug=True)
