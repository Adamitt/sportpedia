from django import forms
from .models import Gear
from sportlibrary.models import Sport
import json
from pathlib import Path

class GearForm(forms.ModelForm):
    # ✅ Definisikan sport sebagai CharField (tidak akan di-save otomatis)
    sport = forms.CharField(
        label="Jenis Olahraga",
        widget=forms.Select()
    )
    
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
            # ❌ JANGAN include 'sport' di sini!
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

        # === Ambil sport dari DB ===
        db_sports = [(str(s.id), f"{s.name} ({s.category})") for s in Sport.objects.all()]

        # === Ambil sport dari JSON ===
        base_dir = Path(__file__).resolve().parent.parent.parent
        data_path = base_dir / 'database' / 'sports.json'
        json_sports = []
        if data_path.exists():
            try:
                with open(data_path, 'r', encoding='utf-8') as f:
                    sports_json = json.load(f)
                    json_sports = [
                        (str(s['id']), f"{s['name']} ({s.get('category', '-')})")
                        for s in sports_json
                    ]
            except Exception as e:
                print(f"⚠️ Gagal baca sports.json: {e}")

        # === Gabungkan & hilangkan duplikat ===
        all_sports_dict = {}
        for sport_id, sport_label in (db_sports + json_sports):
            if sport_id not in all_sports_dict:
                all_sports_dict[sport_id] = sport_label
        
        all_sports = list(all_sports_dict.items())
        
        # ✅ Set choices untuk dropdown
        self.fields['sport'].widget.choices = [('', '---------')] + all_sports

    # === Cleaners ===
    def clean_recommended_brands(self):
        data = self.cleaned_data.get('recommended_brands', '')
        return [b.strip() for b in data.split(',')] if data else []

    def clean_materials(self):
        data = self.cleaned_data.get('materials', '')
        return [m.strip() for m in data.split(',')] if data else []

    def clean_tags(self):
        data = self.cleaned_data.get('tags', '')
        return [t.strip() for t in data.split(',')] if data else []