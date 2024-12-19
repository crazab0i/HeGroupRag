#import dependencies
import getpass
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

#set environmental variables: API Keys, routing to LangChain
os.environ["OPENAI_API_KEY"] = ['fill']
os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_ENDPOINT'] = 'https://api.smith.langchain.com'
os.environ['LANGCHAIN_API_KEY'] = ['fill']

# select the model from openai to be used
model = ChatOpenAI(model="gpt-4")

# use str parser
parser = StrOutputParser()

#create template, language requires a matching key in dictionary
system_template = "Translate the following into {language}"

#setting up the prompt template, text requires matching key in dictionary
prompt_template = ChatPromptTemplate.from_messages(
    [("system", system_template), ("user", "{text}")]
)

#create the chain, ties in everything
chain = prompt_template | model | parser

#invoke with the appropriate key, value pairs of language and text
chain.invoke({"language": "italian", "text": "hi"})
