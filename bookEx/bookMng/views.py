from django.shortcuts import render
from .models import Book
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.db.models import Avg
# Create your views here.
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from .models import MainMenu
'''def index(request):
    return HttpResponse("""<h1>This is a test page</h1>""")'''


'''
def index(request):
    return render(request, 'base.html')'''

def index(request):
    return render(request,
                  'bookMng/index.html',
                  {
                      'item_list': MainMenu.objects.all()
                  })

from .forms import BookForm

def postbook(request):
    submitted = False
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            #form.save()
            book = form.save(commit=False)
            try:
                book.username = request.user
            except Exception:
                pass
            book.save()
            return HttpResponseRedirect('/postbook?submitted=True')
    else:
        form = BookForm()
        if 'submitted' in request.GET:
            submitted = True
    return render(request,
                  'bookMng/postbook.html',
                  {
                      'form': form,
                      'item_list': MainMenu.objects.all(),
                      'submitted': submitted
                  })



def displaybooks(request):
    books = Book.objects.annotate(avg_rating=Avg("reviews__rating"))
    for b in books:
        b.pic_path = b.picture.url[14:]
    return render(request,
                  'bookMng/displaybooks.html',
                  {
                      'item_list': MainMenu.objects.all(),
                      'books': books
                  })


class Register(CreateView):
    template_name = 'registration/register.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('register-success')

    def form_valid(self, form):
        form.save()
        return HttpResponseRedirect(self.success_url)

def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    book.pic_path = book.picture.url[14:]

    reviews = BookReview.objects.filter(book=book).order_by("-created_at")

    if request.user.is_authenticated:
        user_review = BookReview.objects.filter(book=book, user=request.user).first()
    else:
        user_review = None

    form = BookReviewForm(instance=user_review)

    return render(request,
                  'bookMng/book_detail.html',
                  {
                      'item_list': MainMenu.objects.all(),
                      'book': book,
                      'reviews': reviews,
                      'user_review': user_review,
                      'form': form,
                  })

def mybooks(request):
    books = Book.objects.filter(username=request.user)
    for b in books:
        b.pic_path = b.picture.url[14:]
    return render(request,
                  'bookMng/mybooks.html',
                  {
                      'item_list': MainMenu.objects.all(),
                      'books': books
                  })

def book_delete(request, book_id):
    book = Book.objects.get(id=book_id)
    book.delete()

    return render(request,
                  'bookMng/book_delete.html',
                  {
                      'item_list': MainMenu.objects.all(),
                  })

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import MessageThread, PrivateMessage, BookReview
from .forms import BookReviewForm

User = get_user_model()


@login_required
@require_GET
def inbox(request: HttpRequest) -> HttpResponse:
    threads = (
        MessageThread.objects
        .filter(Q(user1=request.user) | Q(user2=request.user))
        .prefetch_related("messages", "user1", "user2")
        .order_by("-updated_at")
    )

    thread_data = []
    for thread in threads:
        other_user = thread.other_user(request.user)
        latest_message = thread.latest_message()
        unread_count = thread.unread_count_for(request.user)
        thread_data.append(
            {
                "thread": thread,
                "other_user": other_user,
                "latest_message": latest_message,
                "unread_count": unread_count,
            }
        )

    context = {
        "thread_data": thread_data,
    }
    return render(request, "bookMng/inbox.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def thread_detail(request: HttpRequest, thread_id: int) -> HttpResponse:
    thread = get_object_or_404(
        MessageThread.objects.select_related("user1", "user2"),
        pk=thread_id,
    )

    if not thread.has_participant(request.user):
        raise Http404("Message thread not found.")

    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        if not body:
            messages.error(request, "Message body cannot be empty.")
            return redirect("thread_detail", thread_id=thread.id)

        recipient = thread.other_user(request.user)
        PrivateMessage.objects.create(
            thread=thread,
            sender=request.user,
            recipient=recipient,
            body=body,
        )
        thread.save(update_fields=["updated_at"])
        messages.success(request, "Message sent.")
        return redirect("thread_detail", thread_id=thread.id)

    thread_messages = thread.messages.select_related("sender", "recipient").all()

    unread_messages = thread_messages.filter(recipient=request.user, is_read=False)
    for msg in unread_messages:
        msg.mark_as_read()

    context = {
        "thread": thread,
        "other_user": thread.other_user(request.user),
        "thread_messages": thread_messages,
    }
    return render(request, "bookMng/thread.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def compose_message(request: HttpRequest) -> HttpResponse:
    user_id = request.GET.get("user_id") or request.POST.get("user_id")
    selected_user = None

    if user_id:
        selected_user = get_object_or_404(User, pk=user_id)
        if selected_user == request.user:
            messages.error(request, "You cannot send a message to yourself.")
            return redirect("inbox")

    available_users = User.objects.exclude(pk=request.user.pk).order_by("username")

    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        target_user_id = request.POST.get("user_id")

        if not target_user_id:
            messages.error(request, "Please choose a recipient.")
            return render(
                request,
                "bookMng/compose.html",
                {
                    "available_users": available_users,
                    "selected_user": selected_user,
                },
            )

        recipient = get_object_or_404(User, pk=target_user_id)

        if recipient == request.user:
            messages.error(request, "You cannot send a message to yourself.")
            return redirect("compose_message")

        if not body:
            messages.error(request, "Message body cannot be empty.")
            return render(
                request,
                "bookMng/compose.html",
                {
                    "available_users": available_users,
                    "selected_user": recipient,
                },
            )

        thread = MessageThread.get_or_create_thread(request.user, recipient)
        PrivateMessage.objects.create(
            thread=thread,
            sender=request.user,
            recipient=recipient,
            body=body,
        )
        thread.save(update_fields=["updated_at"])

        messages.success(request, f"Message sent to {recipient.username}.")
        return redirect("thread_detail", thread_id=thread.id)

    context = {
        "available_users": available_users,
        "selected_user": selected_user,
    }
    return render(request, "bookMng/compose.html", context)


@login_required
@require_POST
def mark_thread_read(request: HttpRequest, thread_id: int) -> HttpResponse:
    thread = get_object_or_404(MessageThread, pk=thread_id)

    if not thread.has_participant(request.user):
        raise Http404("Message thread not found.")

    unread_messages = thread.messages.filter(recipient=request.user, is_read=False)
    for msg in unread_messages:
        msg.mark_as_read()

    messages.success(request, "Thread marked as read.")
    return redirect("thread_detail", thread_id=thread.id)


@login_required
@require_POST
def submit_review(request: HttpRequest, book_id: int) -> HttpResponse:
    book = get_object_or_404(Book, pk=book_id)
    form = BookReviewForm(request.POST)

    if not form.is_valid():
        reviews = BookReview.objects.filter(book=book)
        user_review = reviews.filter(user=request.user).first()
        try:
            pic_path = book.picture.url[14:]
        except Exception:
            pic_path = ""
        return render(
            request,
            "bookMng/book_detail.html",
            {
                "item_list": MainMenu.objects.all(),
                "book": book,
                "reviews": reviews,
                "user_review": user_review,
                "form": form,
                "pic_path": pic_path,
            },
        )

    BookReview.objects.update_or_create(
        book=book,
        user=request.user,
        defaults={
            "rating": form.cleaned_data["rating"],
            "comment": form.cleaned_data["comment"],
        },
    )
    return redirect("book_detail", book_id=book.id)


@login_required
@require_POST
def edit_review(request: HttpRequest, book_id: int) -> HttpResponse:
    book = get_object_or_404(Book, pk=book_id)
    review = get_object_or_404(BookReview, book=book, user=request.user)
    form = BookReviewForm(request.POST, instance=review)

    if not form.is_valid():
        reviews = BookReview.objects.filter(book=book)
        try:
            pic_path = book.picture.url[14:]
        except Exception:
            pic_path = ""
        return render(
            request,
            "bookMng/book_detail.html",
            {
                "item_list": MainMenu.objects.all(),
                "book": book,
                "reviews": reviews,
                "user_review": review,
                "form": form,
                "pic_path": pic_path,
            },
        )

    form.save()
    return redirect("book_detail", book_id=book.id)


@login_required
@require_POST
def delete_review(request: HttpRequest, book_id: int) -> HttpResponse:
    book = get_object_or_404(Book, pk=book_id)
    review = get_object_or_404(BookReview, book=book, user=request.user)
    review.delete()
    return redirect("book_detail", book_id=book.id)

def aboutus(request):
    return render(request,
                  'bookMng/aboutus.html',
                  {
                      'item_list': MainMenu.objects.all(),
                  })

def searchbooks(request):
    q = request.GET.get('q', '').strip()
    letter = request.GET.get('letter', '').strip().upper()

    letters = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    books = Book.objects.all().order_by("name")

    if q:
        books = books.filter(name__icontains=q)

    if letter and len(letter) == 1 and letter.isalpha():
        books = books.filter(name__istartswith=letter)
    else:
        letter = ""

    for book in books:
        try:
            book.pic_path = book.picture.url[14:]
        except Exception:
            book.pic_path = ""

    return render(request,
                  'bookMng/searchbooks.html',
                  {
                      'item_list': MainMenu.objects.all(),
                      'books': books,
                      'letters': letters,
                      'selected_letter': letter,
                      'search_query': q,
                  })

def checkout_success(request):
    return render(request,
                  'bookMng/checkout_success.html',
                  {
                      'item_list': MainMenu.objects.all(),
                  })