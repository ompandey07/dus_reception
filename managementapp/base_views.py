from django.shortcuts import render , redirect



#############################################
# RENDER INDEX PAGE
#############################################

def index_page(request):
    return render(request, 'Base/index.html')



def unauthorized_page(request):
    return render(request, 'Errors/401.html')