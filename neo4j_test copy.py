#created by CHATGPT
import os
from langchain.document_loaders import WebBaseLoader
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from neo4j import GraphDatabase
from langchain.chains import LLMChain
from langchain_core.messages.ai import AIMessage
import json

os.environ["OPENAI_API_KEY"] = "KEY"
os.environ["USER_AGENT"] = "NEO4J Loader"
os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_ENDPOINT'] = 'https://api.smith.langchain.com'
os.environ['LANGCHAIN_API_KEY'] = 'KEY'

# Function to load a document from a URL
def load_document_from_url(url):
    loader = WebBaseLoader([url])
    documents = loader.load()
    return documents

# Set up the OpenAI LLM with ChatOpenAI
llm = ChatOpenAI(model="gpt-3.5-turbo")

# Define the prompt template
prompt_template = """
Given the following text, extract information about vaccine research papers. Return the information in this JSON format:
{{
    "vaccine_papers": [
        {{
            "title": "Title of the paper",
            "vaccine_type": "Type of vaccine (e.g., mRNA, viral vector)",
            "pathogen": "Targeted virus or pathogen (e.g., SARS-CoV-2)",
            "decade": "Decade of development (e.g., 2020s)",
            "relationships": [
                {{"type": "TARGETS", "target": "Pathogen"}},
                {{"type": "DEVELOPED_IN", "target": "Decade"}},
                {{"type": "VACCINE_TYPE", "target": "Vaccine type"}}
            ]
        }}
    ]
}}
Text:
{text}
"""

prompt = PromptTemplate(input_variables=["text"], template=prompt_template)

# Create the LLMChain using the LLM and the prompt
chain = LLMChain(llm=llm, prompt=prompt)

def extract_entities_and_relationships(document):
    result = chain.invoke({"text": document.page_content})
    print("Raw LLM Result:", result)  # Debugging line to see the raw result

    # Check if 'text' key is in the result and parse its content as JSON
    if isinstance(result, dict) and 'text' in result:
        content = result['text']
    elif isinstance(result, AIMessage):
        content = result.content
    else:
        print("Error: Unexpected response format.")
        print("Result format:", type(result))  # Print type of result for better debugging
        return None

    print("Extracted Content:", content)  # Debugging line to see the content

    try:
        # Parse the JSON content within the 'text' field
        parsed_result = json.loads(content)
        print("Parsed Result:", parsed_result)  # Debugging line to verify the parsed result
        return parsed_result
    except json.JSONDecodeError as e:
        print("Error: The content is not valid JSON.")
        print("JSONDecodeError:", e)  # Print JSON parsing error details
        return None


# Neo4j configuration
uri = "PUT A LINK TO DB"
driver = GraphDatabase.driver(uri, auth=("neo4j", "PASSWORD"))

def add_vaccine_paper(tx, title, vaccine_type, pathogen, decade):
    tx.run(
        """
        MERGE (paper:VaccinePaper {title: $title})
        MERGE (type:VaccineType {name: $vaccine_type})
        MERGE (pathogen:Pathogen {name: $pathogen})
        MERGE (decade:Decade {name: $decade})
        MERGE (paper)-[:VACCINE_TYPE]->(type)
        MERGE (paper)-[:TARGETS]->(pathogen)
        MERGE (paper)-[:DEVELOPED_IN]->(decade)
        """,
        title=title, vaccine_type=vaccine_type, pathogen=pathogen, decade=decade
    )

def insert_vaccine_data_into_neo4j(vaccine_data):
    # Check if vaccine_data contains 'vaccine_papers' and it's a list
    if not vaccine_data or 'vaccine_papers' not in vaccine_data or not isinstance(vaccine_data['vaccine_papers'], list):
        print("Error: Invalid structure in extracted data.")
        print("Extracted Data:", vaccine_data)
        return
    
    with driver.session() as session:
        for paper in vaccine_data['vaccine_papers']:
            session.execute_write(
                add_vaccine_paper,
                paper["title"],
                paper["vaccine_type"],
                paper["pathogen"],
                paper["decade"]
            )

def process_vaccine_url_into_neo4j(url):
    documents = load_document_from_url(url)
    for document in documents:
        extracted_data = extract_entities_and_relationships(document)
        print("Extracted Data Before Insertion:", extracted_data)  # Debugging line
        if extracted_data:  # Only try inserting if data is valid
            insert_vaccine_data_into_neo4j(extracted_data)
        else:
            print("Error: No valid extracted data found.")

# Main interaction loop
print('\n\n\nWelcome to NEO4J WebDOC Loader')
while True:
    valid_selection = ['Quit', 'Load', 'quit', 'load']
    choice = input('Select an option: Quit or Load: ')
    if choice not in valid_selection:
        print('Invalid choice, please try again')
        continue

    if choice in ['Quit', 'quit']:
        break
    else:
        print("Let's load a URL!\n")
        url = input("Your URL: ")
        process_vaccine_url_into_neo4j(url)