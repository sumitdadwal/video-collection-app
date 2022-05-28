from django.shortcuts import render, redirect, reverse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Collection, Video
from .forms import VideoForm, SearchForm
from django.forms import formset_factory
from django.http import Http404, JsonResponse
import urllib
import requests
import json
from django.forms.utils import ErrorList
from django.conf import settings




def home(request):
    recent_collections = Collection.objects.all().order_by('-id')[:3]
    popular_collections = [Collection.objects.get(pk=2)]
    return render(request, 'vids/home.html', {'recent_collections':recent_collections, 'popular_collections':popular_collections})
@login_required()
def dashboard(request):
    collections = Collection.objects.filter(user=request.user)
    return render(request, 'vids/dashboard.html', {'collections': collections})
@login_required()
def add_video(request, pk):
    form = VideoForm()
    search_form = SearchForm()
    collection = Collection.objects.get(pk=pk) #verify if the collection belongs to the user
    if collection.user != request.user: #user verfying parameter
        raise Http404
    if request.method == 'POST': #someone has filled out the form
        form = VideoForm(request.POST) 
        if form.is_valid():
            video = Video()
            video.collection = collection #created new collection object
            video.url = form.cleaned_data['url'] 
            parsed_url = urllib.parse.urlparse(video.url) #grab youtube url
            video_id = urllib.parse.parse_qs(parsed_url.query).get('v') #grab video id v=
            if video_id:
                video.youtube_id = video_id[0] #grab 0 from the list
                response = requests.get(f'https://youtube.googleapis.com/youtube/v3/videos?part=snippet&id={video_id[0]}&key={settings.YOUTUBE_API_KEY}')
                json = response.json() # we get response in json
                title = json['items'][0]['snippet']['title'] #API info we want to grab from Youtube API
                video.title = title
                video.save()
                return redirect('detail_collection', pk)
            else:
                errors = form._errors.setdefault('url', ErrorList())
                errors.append('Needs to be a YouTube URL')
    return render(request, 'vids/add_video.html', {'form':form, 'search_form': search_form, 'collection': collection})
@login_required()
def video_search(request):
    search_form = SearchForm(request.GET)
    if search_form.is_valid():
        encoded_search_term = urllib.parse.quote(search_form.cleaned_data['search_term'])
        response = requests.get(f'https://youtube.googleapis.com/youtube/v3/search?part=snippet&maxResults=6&q={encoded_search_term}&key={settings.YOUTUBE_API_KEY}')
        return JsonResponse(response.json())
    return JsonResponse({'error': 'Not able to validate form'})

class SignUp(CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('dashboard')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        view = super(SignUp, self).form_valid(form)
        username, password = form.cleaned_data.get('username'), form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        user = form.save()
        login(self.request, user)
        return view
class CreateCollection(LoginRequiredMixin, CreateView):
    model = Collection
    fields = ['title']
    template_name = 'vids/create_collection.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.user = self.request.user
        super(CreateCollection, self).form_valid(form)
        return redirect('dashboard')

class DetailCollection(DetailView):
    model = Collection
    template_name = 'vids/detail_collection.html'

class UpdateCollection(LoginRequiredMixin, UpdateView):
    model = Collection
    template_name = 'vids/update_collection.html'
    fields = ['title']
    success_url = reverse_lazy('dashboard')

    def get_object(self):
        collection = super(UpdateCollection, self).get_object()
        if not collection.user == self.request.user:
            raise Http404
        return collection

class DeleteCollection(LoginRequiredMixin, DeleteView):
    model = Collection
    template_name = 'vids/delete_collection.html'
    success_url = reverse_lazy('dashboard')

    def get_object(self):
        collection = super(DeleteCollection, self).get_object()
        if not collection.user == self.request.user:
            raise Http404
        return collection

class DeleteVideo(LoginRequiredMixin, DeleteView):
    model = Video
    template_name = 'vids/delete_video.html'
    success_url = reverse_lazy('dashboard')

    def get_object(self):
        video = super(DeleteVideo, self).get_object()
        if not video.collection.user == self.request.user:
            raise Http404
        return video



