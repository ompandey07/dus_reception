from django.shortcuts import render , redirect



#############################################
# RENDER INDEX PAGE
#############################################

def index_page(request):
    return render(request, 'Base/index.html')