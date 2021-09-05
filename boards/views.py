from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import NewTopicForm,PostForm
from .models import Board, Post, Topic
from django.db.models import Count
from django.views.generic import View
from django.urls import reverse_lazy
from django.views.generic import CreateView,UpdateView,ListView
from django.utils import timezone
from django.utils.decorators import method_decorator


def home(request):
    boards = Board.objects.all()
    return render(request, 'home.html', {'boards': boards})

def board_topics(request, pk):
    board = get_object_or_404(Board, pk=pk)
    topics = board.topics.order_by('-last_updated').annotate(replies=Count('posts') - 1)
    return render(request, 'topics.html', {'board': board,'topics': topics})

@login_required
def new_topic(request, pk):
    board = get_object_or_404(Board, pk=pk)
    if request.method == 'POST':
        form = NewTopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.board = board
            topic.starter = request.user
            topic.save()
            Post.objects.create(
                message=form.cleaned_data.get('message'),
                topic=topic,
                created_by=request.user
            )
            # return redirect('board_topics', pk=board.pk)  # TODO: redirect to the created topic page
            return redirect('topic_posts', pk=pk, topic_pk=topic.pk)  # <- here
    else:
        form = NewTopicForm()
    return render(request, 'new_topic.html', {'board': board, 'form': form})

def topic_posts(request, pk, topic_pk):
    topic = get_object_or_404(Topic, board__pk=pk, pk=topic_pk)
    topic.views += 1
    topic.save()
    return render(request, 'topic_posts.html', {'topic': topic})   

@login_required
def reply_topic(request,pk, topic_pk):
    topic = get_object_or_404(Topic,board_pk=pk,pk=topic_pk)
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.topic=topic
            post.created_by= request.user
            post.save()

            topic.last_updated = timezone.now()  # <- here
            topic.save()                         # <- and here
            return redirect('topic_posts',pk=pk,topic_pk=topic_pk)
    else:
        form = PostForm()
    return render(request,'reply_topic.html',{'topic':topic, 'form':form})

#generic class based view
# from django.views.generic import CreateView

class NewPostView(CreateView):
    model = Post
    form_class = PostForm
    success_url = reverse_lazy('post_list')
    template_name = 'new_post.html'

@method_decorator(login_required,name='dispatch')
class PostUpdateView(UpdateView):
    model = Post
    fields = ('message', )
    template_name = 'edit_post.html'
    pk_url_kwarg = 'post_pk'
    context_object_name = 'post'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(created_by=self.request.user)

    def form_valid(self, form):
        post = form.save(commit=False)
        post.updated_by = self.request.user
        post.updated_at = timezone.now()
        post.save()
        return redirect('topic_posts', pk=post.topic.board.pk, topic_pk=post.topic.pk)

class BoardListView(ListView):
    model = Board
    context_object_name = 'boards'
    template_name = 'home.html'

class PostListView(ListView):
    model = Post
    context_object_name = 'posts'
    template_name = 'topic_posts.html'
    paginate_by = 20

    def get_context_data(self, **kwargs):

        session_key = 'viewed_topic_{}'.format(self.topic.pk)  # <-- here
        if not self.request.session.get(session_key, False):
            self.topic.views += 1
            self.topic.save()
            self.request.session[session_key] = True           # <-- until here

        kwargs['topic'] = self.topic
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        self.topic = get_object_or_404(Topic, board__pk=self.kwargs.get('pk'), pk=self.kwargs.get('topic_pk'))
        queryset = self.topic.posts.order_by('created_at')
        return queryset



#class Based View
# class NewPostView(View):
#     def render(self, request):
#         return render(request, 'new_post.html', {'form': self.form})

#     def post(self, request):
#         self.form = PostForm(request.POST)
#         if self.form.is_valid():
#             self.form.save()
#             return redirect('post_list')
#         return self.render(request)

#     def get(self, request):
#         self.form = PostForm()
#         return self.render(request)





#-----------------------------------------------------------
#new-post --Function Based View
# def new_post(request):
#     if request.method == 'POST':
#         form = PostForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('post_list')
#     else:
#         form = PostForm()
#     return render(request, 'new_post.html', {'form': form})

#Class Based View
# class NewPostView(View):
#     def post(self, request):
#         form = PostForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('post_list')
#         return render(request, 'new_post.html', {'form': form})

#     def get(self, request):
#         form = PostForm()
#         return render(request, 'new_post.html', {'form': form})

#---------------------------------------------------------------------
# from django.contrib.auth.models import User
# Create your views here.
# from django.http import Http404, HttpResponse, response
# from django.shortcuts import get_object_or_404, render,redirect
# import boards
# from boards.models import Board, Post, Topic,User
# from .forms import NewTopicForm

# def home(request):
    # boards = Board.objects.all()
    # boards_names =[]
    # for board in boards:
    #     boards_names.append(board.name)

    # response_html ='<br>'.join(boards_names)
    # print(response_html)
    # return HttpResponse('Hello, World!')
    # return HttpResponse(response_html)
#     return render (request,"home.html",context={"all_boards":Board.objects.all()})

# def board_topics(request,pk):
#     # print('in board topics',pk)
#     # try:
#     #     board_obj = Board.objects.get(pk=pk)
#     # except Board.DoesNotExist:
#     #     raise Http404
#     board_obj = get_object_or_404(Board,pk=pk)
#     return render(request,'topics.html',{'board':board_obj})    

# def new_topic(request,pk):
#     board = get_object_or_404(Board,pk=pk)
#     # print('---------------')
#     if request.method =='POST':
#         subject=request.POST['subject']
#         message=request.POST['message']

#         user = User.objects.first()
#         topic = Topic.objects.create(
#             subject=subject,
#             board=board,
#             starter=user
#             )
#         post=Post.objects.create(
#             message=message,
#             topic=topic,
#             created_by=user,
#         )
#         return redirect('board_topics',pk=board.pk)
#     return render(request,'new_topic.html',{'board':board})
# def new_topic(request,pk):
#     board = get_object_or_404(Board,pk=pk)
#     user=User.objects.first()
#     if request.method == 'POST':
#         form = NewTopicForm(request.POST)
#         if form.is_valid():
#             topic = form.save(commit=False)
#             topic.board=board
#             topic.starter=user
#             topic.save()
#             post=Post.objects.create(
#                 message=form.cleaned_data.get('message'),
#                 topic=topic,
#                 created_by=user
#             )
#             return redirect('board_topics',pk=board.pk)
#         else:
#             form = NewTopicForm()
#         return render(request,'new_topic.html',{'board':board,'form':form})

# def new_topic(request, pk):
#     board = get_object_or_404(Board, pk=pk)
#     user = User.objects.first()  # TODO: get the currently logged in user
#     if request.method == 'POST':
#         form = NewTopicForm(request.POST)
#         if form.is_valid():
#             topic = form.save(commit=False)
#             topic.board = board
#             topic.starter = user
#             topic.save()
#             post = Post.objects.create(
#                 message=form.cleaned_data.get('message'),
#                 topic=topic,
#                 created_by=user
#             )
#             return redirect('board_topics', pk=board.pk)  # TODO: redirect to the created topic page
#     else:
#         form = NewTopicForm()
#     return render(request, 'new_topic.html', {'board': board, 'form': form})
