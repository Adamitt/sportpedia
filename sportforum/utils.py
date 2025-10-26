"""
Utility functions for SportForum app
Includes data import from JSON to database
"""

import json
from pathlib import Path
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime
from sportforum.models import ForumPost, Reply, Tag


def load_forum_data_from_json():
    """
    Import forum posts from forum.json to database
    This will create posts, replies, and tags in the database
    """
    base_dir = Path(__file__).resolve().parent.parent
    json_path = base_dir / 'database' / 'forum.json'
    
    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            forum_data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading forum.json: {e}")
        return {
            'success': False,
            'error': str(e),
            'posts_created': 0,
            'replies_created': 0,
            'tags_created': 0
        }
    
    posts_created = 0
    replies_created = 0
    tags_created = 0
    
    # Get or create a default user for JSON posts
    default_user, _ = User.objects.get_or_create(
        username='json_importer',
        defaults={
            'email': 'json@sportpedia.com',
            'first_name': 'JSON',
            'last_name': 'Importer'
        }
    )
    
    # Map of sport names to sport choices
    sport_mapping = {
        'Bulu Tangkis': 'bulu-tangkis',
        'Yoga': 'yoga',
        'Tenis': 'tenis',
        'Renang': 'renang',
        'Panahan': 'panahan',
        'Lari': 'lari',
        'Basket': 'basket',
        'Futsal': 'futsal',
        'Bersepeda': 'bersepeda',
        'Tenis Meja': 'tenis-meja',
        'Voli': 'voli',
        'Panjat Tebing': 'panjat-tebing',
        'Muay Thai': 'muay-thai',
        'Golf': 'golf',
        'Selancar': 'selancar',
        'Pencak Silat': 'pencak-silat',
        'Baseball': 'baseball',
        'Skateboard': 'skateboard',
        'Calisthenics': 'calisthenics',
        'Wall Climbing': 'wall-climbing',
    }
    
    for post_data in forum_data:
        try:
            # Get sport slug
            sport_name = post_data.get('sport', '')
            sport_slug = sport_mapping.get(sport_name, sport_name.lower().replace(' ', '-'))
            
            # Skip if sport not in choices
            valid_sports = [choice[0] for choice in ForumPost.SPORT_CHOICES]
            if sport_slug not in valid_sports:
                print(f"Skipping post '{post_data.get('title')}' - invalid sport: {sport_name}")
                continue
            
            # Get or create author
            author_username = post_data.get('author', 'anonymous')
            author, _ = User.objects.get_or_create(
                username=author_username,
                defaults={
                    'email': f'{author_username}@sportpedia.com',
                    'first_name': author_username.capitalize()
                }
            )
            
            # Parse date
            date_str = post_data.get('date_posted', '')
            try:
                post_date = datetime.strptime(date_str, '%Y-%m-%d')
                post_date = timezone.make_aware(post_date)
            except (ValueError, TypeError):
                post_date = timezone.now()
            
            # Check if post already exists (by title and author)
            existing_post = ForumPost.objects.filter(
                title=post_data.get('title'),
                author=author
            ).first()
            
            if existing_post:
                print(f"Post '{post_data.get('title')}' by {author_username} already exists, skipping...")
                continue
            
            # Create post
            post = ForumPost.objects.create(
                sport=sport_slug,
                title=post_data.get('title', 'Untitled'),
                author=author,
                content=post_data.get('content', ''),
                views=post_data.get('views', 0),
                date_posted=post_date
            )
            posts_created += 1
            
            # Add likes (create dummy users for each like)
            likes_count = post_data.get('likes', 0)
            if likes_count > 0:
                # Create unique users for each like to make it more realistic
                import random
                for i in range(likes_count):
                    # Generate unique username with random suffix
                    like_user, _ = User.objects.get_or_create(
                        username=f'user_{random.randint(1000, 9999)}_{i}',
                        defaults={
                            'email': f'user{i}@sportpedia.com',
                            'first_name': f'User{i}'
                        }
                    )
                    post.likes.add(like_user)
            
            # Add tags
            tags_list = post_data.get('tags', [])
            for tag_name in tags_list:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                if created:
                    tags_created += 1
                post.tags.add(tag)
            
            # Add replies
            replies_list = post_data.get('replies', [])
            for reply_data in replies_list:
                reply_username = reply_data.get('user', 'anonymous')
                reply_user, _ = User.objects.get_or_create(
                    username=reply_username,
                    defaults={
                        'email': f'{reply_username}@sportpedia.com',
                        'first_name': reply_username.capitalize()
                    }
                )
                
                # Parse reply date
                reply_date_str = reply_data.get('date', '')
                try:
                    reply_date = datetime.strptime(reply_date_str, '%Y-%m-%d')
                    reply_date = timezone.make_aware(reply_date)
                except (ValueError, TypeError):
                    reply_date = timezone.now()
                
                reply = Reply.objects.create(
                    post=post,
                    user=reply_user,
                    comment=reply_data.get('comment', '')
                )
                # Update reply date manually
                Reply.objects.filter(pk=reply.pk).update(date=reply_date)
                replies_created += 1
            
            print(f"✓ Created post: {post.title} ({posts_created})")
            
        except Exception as e:
            print(f"✗ Error creating post '{post_data.get('title', 'Unknown')}': {e}")
            continue
    
    result = {
        'success': True,
        'posts_created': posts_created,
        'replies_created': replies_created,
        'tags_created': tags_created,
        'total_posts_in_json': len(forum_data)
    }
    
    print(f"\n{'='*50}")
    print(f"Import Summary:")
    print(f"  Posts created: {posts_created}/{len(forum_data)}")
    print(f"  Replies created: {replies_created}")
    print(f"  Tags created: {tags_created}")
    print(f"{'='*50}\n")
    
    return result


def clear_forum_data():
    """
    Clear all forum posts, replies, and tags from database
    WARNING: This will delete all forum data!
    """
    reply_count = Reply.objects.count()
    post_count = ForumPost.objects.count()
    tag_count = Tag.objects.count()
    
    Reply.objects.all().delete()
    ForumPost.objects.all().delete()
    Tag.objects.all().delete()
    
    print(f"Deleted {post_count} posts, {reply_count} replies, and {tag_count} tags")
    
    return {
        'posts_deleted': post_count,
        'replies_deleted': reply_count,
        'tags_deleted': tag_count
    }
