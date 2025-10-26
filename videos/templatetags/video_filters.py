from django import template
import re

register = template.Library()

@register.filter(name='get_youtube_id')
def get_youtube_id(url_string):
    """
    Ekstrak YouTube video ID dari URL.
    Contoh:
    - https://www.youtube.com/watch?v=ktoPXyDI_iY -> ktoPXyDI_iY
    - https://youtu.be/ktoPXyDI_iY -> ktoPXyDI_iY
    """
    if not url_string:
        return None
    
    try:
        # Pola regex untuk ID YouTube
        regex = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
        match = re.search(regex, url_string)
        
        if match:
            return match.group(1) # ID videonya (11 karakter)
            
    except Exception:
        pass
        
    return None # Kembalikan None jika tidak cocok