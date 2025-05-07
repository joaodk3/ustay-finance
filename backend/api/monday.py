import requests
import pandas as pd
from dotenv import load_dotenv
import os

# Load Env variables
load_dotenv()
apiKey = os.getenv('MONDAY_API_KEY')

# API Config
apiUrl = "https://api.monday.com/v2"
headers = {"Authorization": apiKey}

boards = {
    "sales_non_immigrant": 5936289208,
    "non-immigrant": 5944150453,
    "immigrant": 5944150717,
    "educational": 5936306417,
    "sales_immigrant": 8147184384  # Added new board ID
}

# Function to fetch data and create DataFrame with pagination
def fetch_board_data(board_id, max_items=1000):
    all_items = []
    cursor = None
    items_fetched = 0
    while items_fetched < max_items:
        query = f'''
        query GetBoardItems {{
        boards(ids: {board_id}) {{
        items_page(limit: 500{', cursor: "' + cursor + '"' if cursor else ''}) {{
        cursor
        items {{
        id
        name
        column_values {{
        column {{
        title
        }}
        text
        }}
        }}
        }}
        }}
        }}
        '''
        raw_data = {'query': query}
        r = requests.post(url=apiUrl, json=raw_data, headers=headers)
        response = r.json()
        
        # Handle potential errors in API response
        if 'data' not in response or not response['data']['boards']:
            raise ValueError(f"Failed to fetch data from board {board_id}: {response}")
        
        board_data = response['data']['boards'][0]['items_page']
        items = board_data['items']
        cursor = board_data['cursor']
        all_items.extend(items)
        items_fetched += len(items)
        
        # Stop if no more items are returned
        if not cursor or len(items) == 0:
            break
    
    # Process items into a DataFrame
    columns = set()
    data_list = []
    for item in all_items:
        item_data = {'id': item['id'], 'name': item['name']}
        for column_value in item['column_values']:
            column_title = column_value['column']['title']
            columns.add(column_title)
            item_data[column_title] = column_value.get('text', None)
        data_list.append(item_data)
    
    df = pd.DataFrame(data_list, columns=['id', 'name'] + list(columns))
    return df

# Fetch data for sales board and new board
df_sales_1 = fetch_board_data(boards['sales_non_immigrant'])
df_sales_2 = fetch_board_data(boards['sales_immigrant'])

# Combine DataFrames
df_sales = pd.concat([df_sales_1, df_sales_2], ignore_index=True)