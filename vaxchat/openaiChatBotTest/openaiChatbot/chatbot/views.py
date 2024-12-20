from django.shortcuts import render
from django.http import JsonResponse
import os
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv("openai.env")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_KEY")
def ask_openai(message):
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY")
    ) 
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": message,
            }
        ],
        model = 'gpt-3.5-turbo',
        temperature=0.7,
        max_tokens=150,
        n=1,
    )
    return response.choices[0].message.content

# Create your views here.
def chatbot(request): 
    if request.method == 'POST':
        message = request.POST.get('message')
        response = ask_openai(message)
        return JsonResponse({'message': message, 'response': response})
    return render(request, 'chatbot.html')