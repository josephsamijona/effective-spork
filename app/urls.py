# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', 
         views.PublicQuoteRequestView.as_view(), 
         name='request_quote'),
    path('request-quote/success/', 
         views.QuoteRequestSuccessView.as_view(), 
         name='quote_request_success'),
]