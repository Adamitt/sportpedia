from django import forms

class ForumPostForm(forms.Form):
    title = forms.CharField(max_length=150)
    content = forms.CharField(widget=forms.Textarea)
    tags = forms.CharField(required=False, help_text="Pisahkan dengan koma, contoh: surf, wave, balance")


class ReplyForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea, label="Balasan Anda")