from flask import Flask, render_template, request, jsonify
import pandas as pd
from flask import request

app = Flask(__name__, static_url_path='/static')

# Read the combined_df DataFrame from the CSV file
combined_df = pd.read_csv("Scraped-data.csv")

# Store chat history
chat_history = []
combined_df['processed_price'] = combined_df['price'].replace('[^\\d,]', '', regex=True).str.replace(',', '').astype(float)

# Dashboard data
dashboard_data = {
    'total_listings': len(combined_df),
    'average_price': combined_df['processed_price'].mean(),
    'average_rating': combined_df['Reviews'].mean(),
    'average_review_count': combined_df['Review Count'].mean(),
    'total_questions': combined_df['Questions Answered'].sum(),
    'top_products': combined_df.nlargest(5, 'Reviews')[['name', 'Reviews', 'product_id']]
}

def handle_dashboard_query():
    return {
        'total_listings': len(combined_df),
        'average_price': combined_df['processed_price'].mean(),
        'average_rating': combined_df['Reviews'].mean(),
        'average_review_count': combined_df['Review Count'].mean(),
        'total_questions': combined_df['Questions Answered'].sum(),
        'top_products': combined_df.nlargest(5, 'Reviews')[['name', 'Reviews', 'product_id']]
    }

def handle_greeting():
    return "Chatbot: Hello! How can I assist you today?"

def handle_goodbye():
    return "Chatbot: Goodbye! Have a great day!"

def handle_mobile_queries(query):
    if not query.strip():
        return "Chatbot: Please enter a valid query."
    
    # Check if the query contains 'top' or 'best' along with a mobile name
    if any(keyword in query.lower() for keyword in ['top', 'best']):
        mobile_name = extract_mobile_name(query)
        if mobile_name:
            # Search for the mobile name in the data
            matching_products = combined_df[combined_df['name'].str.lower().str.contains(mobile_name, case=False, na=False)]
            
            if not matching_products.empty:
                # Retrieve and format the top 5 products based on ratings
                top_products = matching_products.nlargest(5, 'Reviews')[['name', 'Reviews', 'price']]
                return format_output(top_products)
            else:
                return "Chatbot: No matching products found for the specified mobile name."
        else:
            # If mobile name is not provided, print the top 5 products from all data
            top_products_all = combined_df.nlargest(5, 'Reviews')[['name', 'Reviews', 'price']]
            return format_output(top_products_all)

    prices = [word.replace("Rs.", "").replace(",", "").strip() for word in query.split() if word.replace("Rs.", "").replace(",", "").strip().isdigit()]
    # Handle queries related to mobile products
    if 'between' in query.lower():
        result = combined_df[(combined_df["price"].apply(lambda x: float(x.replace("Rs.", "").replace(",", "").strip())) >= float(prices[0])) & (combined_df["price"].apply(lambda x: float(x.replace("Rs.", "").replace(",", "").strip())) <= float(prices[1]))]
        if any(keyword in query.lower() for keyword in ['top', 'best']):
            top_products = result.nlargest(5, 'Reviews')[['name', 'Reviews', 'processed_price']]
            return format_output( top_products)
        else:
            return format_output(result)
    elif any(keyword in query.lower() for keyword in ['under', 'over', 'above', 'below']):
        # Handle price queries (e.g., under 30k, over 45k, under 50000)
        price_condition = extract_price_condition(query)
        prices = [word.replace("Rs.", "").replace(",", "").strip() for word in query.split() if word.replace("Rs.", "").replace(",", "").strip().isdigit()]
        if price_condition:
            if 'under' or 'less than' in query.lower():
                result = combined_df[combined_df["price"].apply(lambda x: float(x.replace("Rs.", "").replace(",", "").strip())) < float(prices[0])]
                if any(keyword in query.lower() for keyword in ['top', 'best']):
                    top_products = result.nlargest(5, 'Reviews')[['name', 'Reviews', 'processed_price']]
                    return format_output( top_products)
                else:
                     return format_output(result)
            elif 'over' or 'more than' in query.lower():
                result = combined_df[combined_df["price"].apply(lambda x: float(x.replace("Rs.", "").replace(",", "").strip())) > float(prices[0])]
                if any(keyword in query.lower() for keyword in ['top', 'best']):
                    top_products = result.nlargest(5, 'Reviews')[['name', 'Reviews', 'processed_price']]
                    return format_output( top_products)
                else:
                    return format_output(result)
            elif 'above' in query.lower():
                result = combined_df[combined_df["price"].apply(lambda x: float(x.replace("Rs.", "").replace(",", "").strip())) > float(prices[0])]
                if any(keyword in query.lower() for keyword in ['top', 'best']):
                    top_products = result.nlargest(5, 'Reviews')[['name', 'Reviews', 'processed_price']]
                    return format_output( top_products)
                else:
                    return format_output(result)
            elif 'below' in query.lower():
                result = combined_df[combined_df["price"].apply(lambda x: float(x.replace("Rs.", "").replace(",", "").strip())) < float(prices[0])]
                if any(keyword in query.lower() for keyword in ['top', 'best']):
                    top_products = result.nlargest(5, 'Reviews')[['name', 'Reviews', 'processed_price']]
                    return format_output( top_products)
                else:
                    return format_output(result)
        else:
            return "Chatbot: Invalid price query format. Please use 'under', 'over', 'above', or 'below' followed by a numeric value."
    elif 'best' in query.lower():
        # Handle best phones based on specifications query
        best_phones = find_best_phones_by_specifications(query)
        return format_output(best_phones)
    elif 'top' in query.lower():
        # Handle best phones based on specifications query
        best_phones = find_best_phones_by_specifications(query)
        return format_output(best_phones)
    elif 'search' or 'give' in query.lower():
        # Handle specific phone search query
        searched_phone = search_specific_phone(query)
        return format_output(searched_phone)
    elif 'show' in query.lower():
        # Handle specific phone search query
        searched_phone = search_specific_phone(query)
        return format_output(searched_phone)
    else:
        return "Chatbot: Sorry, I couldn't understand the query."

# Modify the price condition extraction function to handle 'under' condition
def extract_price_condition(query):
    # Extract numerical values from the query for price condition
    prices = [word.replace("k", "000").replace("Rs.", "").replace(",", "").strip() for word in query.split() if word.replace("k", "000").replace("Rs.", "").replace(",", "").strip().isdigit()]

    if len(prices) == 1:
        condition = query.lower()
        return condition, float(prices[0])
    else:
        return None

def extract_mobile_name(query):
    # Extract the mobile name from the query
    words = query.split()
    index_of_top_best = next((i for i, word in enumerate(words) if word.lower() in ['top', 'best']), None)
    
    if index_of_top_best is not None and index_of_top_best + 1 < len(words):
        # Combine words from the position after 'top' or 'best' until the end
        mobile_name = ' '.join(words[index_of_top_best + 1:])
        return mobile_name.strip()
    else:
        return None

def extract_price_range(query):
    # Extract numerical values from the query for price range
    prices = [word.replace("k", "000").replace("Rs.", "").replace(",", "").strip() for word in query.split() if word.replace("k", "000").replace("Rs.", "").replace(",", "").strip().isdigit()]

    if len(prices) == 2:
        return float(prices[0]), float(prices[1])
    else:
        return None

def filter_by_price_range(data, price_range):
    min_price, max_price = price_range
    return data[(data['price'] >= min_price) & (data['price'] <= max_price)]

def extract_price_condition(query):
    # Extract numerical values from the query for price condition
    prices = [word.replace("k", "000").replace("Rs.", "").replace(",", "").strip() for word in query.split() if word.replace("k", "000").replace("Rs.", "").replace(",", "").strip().isdigit()]

    if len(prices) == 1:
        return query.lower(), float(prices[0])
    else:
        return None

def filter_by_price_condition(data, price_condition):
    condition, price = price_condition
    if 'under' in condition:
        return data[data['price'] < price]
    elif 'over' in condition or 'above' in condition:
        return data[data['price'] > price]
    elif 'below' in condition:
        return data[data['price'] <= price]
    else:
        return None

def find_best_phones_by_specifications(query):
    # Extract specifications from the query
    specifications = extract_specifications(query)

    # Filter data based on specifications
    filtered_df = filter_by_specifications(combined_df, specifications)

    # Return the top 5 phones based on ratings
    return filtered_df.sort_values(by='Reviews', ascending=False).head(5)

def extract_specifications(query):
    # Extract specifications from the query (e.g., 64 GB RAM, 48 MP camera)
    specifications = {}
    if 'ram' in query.lower():
        specifications['Memory'] = extract_numeric_value_specifications(query)
    if 'camera' in query.lower():
        specifications['Camera'] = extract_numeric_value_specifications(query)

    return specifications

def extract_numeric_value_specifications(query):
    # Extract numeric values from the query
    return [word.strip() for word in query.split() if word.strip().isdigit()]

def filter_by_specifications(data, specifications):
    # Filter data based on specifications
    for column, value in specifications.items():
        if column in data.columns:
            data = data[data[column].astype(str) == value]

    return data

def search_specific_phone(query):
    # Extract the phone name from the query
    phone_name = query.lower().replace('search', '').replace('find', '').replace('give', '').replace('show', '').strip()

    # Search for the phone in the data
    return combined_df[combined_df['name'].str.lower().str.contains(phone_name, case=False, na=False)]

def format_output(result):
    if not result.empty:
        response = "<table border='1'><tr>"
        for column in result.columns:
            response += f"<th>{column}</th>"
        response += "</tr>"
        for _, row in result.iterrows():
            response += "<tr>"
            for value in row:
                response += f"<td>{value}</td>"
            response += "</tr>"
        response += "</table>"
    else:
        response = "Chatbot: No matching results found."

    return response

@app.route('/')
def index():
    return render_template('dashboard.html', chat_history=chat_history, dashboard_data=dashboard_data)

@app.route('/chatbot', methods=['POST'])
def chatbot():
    if 'user_input' in request.form:
        user_input = request.form['user_input']
        # Process text input

    elif 'audio_file' in request.files:
        audio_file = request.files['audio_file']

    user_input = request.form['user_input']

    if user_input.lower() in ['bye', 'goodbye', 'ok, take care', 'ok, bye', 'exit']:
        response = "Chatbot: Goodbye! Have a great day!"
    elif any(greet in user_input.lower() for greet in ['hey', 'hello', 'hi']):
        response = handle_greeting()
    elif 'dashboard' in user_input.lower():
        dashboard_response = handle_dashboard_query()
        response = f"Chatbot: Dashboard data - {dashboard_response}"
    else:
        response = handle_mobile_queries(user_input)

    # Add user and chatbot messages to chat history
    chat_history.append("User: " + user_input)
    chat_history.append(response)

    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(debug=True)


    