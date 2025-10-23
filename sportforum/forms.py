from django import forms
from .models import ForumPost, Reply

class ForumPostForm(forms.ModelForm):
    tags = forms.CharField(
        required=False, 
        help_text="Pisahkan dengan koma, contoh: surf, wave, balance"
    )
    
    class Meta:
        model = ForumPost
        fields = ['sport', 'title', 'content', 'tags']


class ReplyForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea, label="Balasan Anda")