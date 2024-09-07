from langchain import OpenAI, Agent
from langchain.tools import requests_tool, browser_tool
import pandas as pd

# Initialize the OpenAI LLM
llm = OpenAI()

# Create an agent with tools for requests and browser interaction
tools = [requests_tool, browser_tool]

agent = Agent(llm=llm, tools=tools)

# Define the task for the agent with specific instructions
task = """
1. Fetch the HTML content from the provided URL.
2. Parse the page to identify the election contests and their respective results.
3. Extract the following columns of information for each contest:
   - Product Name
   - Product Price
    - Product Rating
    - Display Size

5. Format the extracted data into a CSV file with the specified columns.
"""

# URL of the website containing the election results
url = 'https://www.amazon.com/s?k=65+inch+tv&crid=3L2V3JPGP0299&sprefix=%2Caps%2C158&ref=nb_sb_ss_recent_1_0_recent'

# Run the task
response = agent.run(task, inputs={'url': url})

# Assuming the response is a list of dictionaries with the extracted data
data = response  # This is where the extracted data will be stored

# Convert the data into a DataFrame
df = pd.DataFrame(data)

# Save the DataFrame to a CSV file with the specified columns
desired_columns = ['Product Name', 'Product Price', 'Product Rating', 'Display Size']
df.to_csv('amazon_tv_test.csv', columns=desired_columns, index=False)

print("Test results saved to amazon_tv_test.csv")