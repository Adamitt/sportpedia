from django import forms
from .models import Gear
from sportlibrary.models import Sport
import json
from pathlib import Path

class GearForm(forms.ModelForm):
    recommended_brands = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Contoh: Yonex, Li-Ning, Victor (pisahkan dengan koma)'}),
        help_text='Masukkan brand yang direkomendasikan, pisahkan dengan koma'
    )
    materials = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Contoh: Carbon Graphite, Steel Shaft (pisahkan dengan koma)'}),
        help_text='Masukkan material/bahan, pisahkan dengan koma'
    )
    care_tips = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tips perawatan gear...'}),
        help_text='Berikan tips perawatan gear'
    )
    ecommerce_link = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'placeholder': 'https://tokopedia.com/...'}),
        help_text='Masukkan link pembelian produk (opsional)'
    )
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Contoh: racket, badminton, gear (pisahkan dengan koma)'}),
        help_text='Masukkan tag/kategori gear'
    )
    image = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'placeholder': 'https://example.com/gambar-produk.jpg'}),
        help_text='Masukkan URL gambar gear'
    )

    class Meta:
        model = Gear
        fields = [
            'sport',
            'name',
            'function',
            'description',
            'level',
            'price_range',
            'recommended_brands',
            'materials',
            'care_tips',
            'ecommerce_link',
            'tags',
            'image',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sport_from_json = False  # flag buat tahu sumbernya dari JSON atau DB

        sports = Sport.objects.all()

        if sports.exists():
            # ✅ kalau ada di DB, pakai queryset ForeignKey biasa
            self.fields['sport'].queryset = sports
            self.fields['sport'].label_from_instance = lambda obj: f"{obj.name} ({obj.category})"
        else:
            # ⚙️ fallback ke JSON
            base_dir = Path(__file__).resolve().parent.parent.parent
            data_path = base_dir / 'database' / 'sports.json'
            try:
                with open(data_path, 'r', encoding='utf-8') as f:
                    sports_json = json.load(f)

                choices = [(str(s['id']), f"{s['name']} ({s.get('category', '-')})") for s in sports_json]
                self.fields['sport'] = forms.ChoiceField(choices=choices, label="Jenis Olahraga")
                self.sport_from_json = True
                self.sports_json_map = {str(s['id']): s['name'] for s in sports_json}
            except Exception as e:
                print(f"⚠️ Gagal memuat sports.json: {e}")
                self.fields['sport'] = forms.ChoiceField(choices=[], label="Jenis Olahraga (tidak tersedia)")

    def clean_recommended_brands(self):
        data = self.cleaned_data.get('recommended_brands', '')
        return [b.strip() for b in data.split(',')] if data else []

    def clean_materials(self):
        data = self.cleaned_data.get('materials', '')
        return [m.strip() for m in data.split(',')] if data else []

    def clean_tags(self):
        data = self.cleaned_data.get('tags', '')
        return [t.strip() for t in data.split(',')] if data else []

    def save(self, commit=True):
        """Override save untuk handle kasus sport dari JSON."""
        instance = super().save(commit=False)

        if self.sport_from_json:
            sport_id = self.cleaned_data['sport']
            try:
                # cari sport dari DB (kalau sempat diimport)
                sport_obj = Sport.objects.filter(pk=sport_id).first()
                if sport_obj:
                    instance.sport = sport_obj
                else:
                    # kalau gak ada di DB, skip tapi log biar tahu
                    print(f"⚠️ Sport ID {sport_id} dari JSON belum ada di DB.")
                    instance.sport = None
            except Exception as e:
                print(f"⚠️ Error mapping sport JSON ke model: {e}")
                instance.sport = None

        if commit:
            instance.save()
        return instance
