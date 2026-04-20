from django import forms
from django.forms import ModelForm
from .models import Book, BookReview


class BookForm(ModelForm):
    class Meta:
        model = Book
        fields = [
            'name',
            'web',
            'price',
            'picture',
        ]


class BookReviewForm(forms.ModelForm):
    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={"min": 1, "max": 5}),
    )

    class Meta:
        model = BookReview
        fields = ["rating", "comment"]
