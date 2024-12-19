from django.shortcuts import render
from django.http import JsonResponse
import os

openai_api_key = os.environ
# Create your views here.
def chatbot(request): 
    if request.method == 'POST':
        message = request.POST.get('message')
        response = 'Hi this is my response'
        return JsonResponse({'message': message, 'response': response})
    return render(request, 'chatbot.html')