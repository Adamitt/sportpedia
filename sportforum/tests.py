from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from sportforum.models import ForumPost, Reply, Tag
import json
from datetime import datetime


class ForumPostModelTest(TestCase):
    """Test ForumPost model"""
    
    def setUp(self):
        """Setup test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.post = ForumPost.objects.create(
            sport='basket',
            title='Test Post',
            author=self.user,
            content='This is a test post content'
        )
    
    def test_forum_post_creation(self):
        """Test creating a forum post"""
        self.assertEqual(self.post.title, 'Test Post')
        self.assertEqual(self.post.sport, 'basket')
        self.assertEqual(self.post.author, self.user)
        self.assertEqual(self.post.views, 0)
        self.assertIsNotNone(self.post.id)
    
    def test_forum_post_str(self):
        """Test __str__ method"""
        expected = f"Test Post (Basket)"
        self.assertEqual(str(self.post), expected)
    
    def test_total_likes_property(self):
        """Test total_likes property"""
        self.assertEqual(self.post.total_likes, 0)
        
        # Add likes
        user2 = User.objects.create_user(username='user2', password='pass')
        self.post.likes.add(user2)
        self.assertEqual(self.post.total_likes, 1)
        
        self.post.likes.add(self.user)
        self.assertEqual(self.post.total_likes, 2)
    
    def test_post_ordering(self):
        """Test posts are ordered by date_posted descending"""
        from django.utils import timezone
        import time
        
        # Ensure time difference between posts
        time.sleep(0.01)
        
        post2 = ForumPost.objects.create(
            sport='futsal',
            title='Newer Post',
            author=self.user,
            content='Newer content'
        )
        
        posts = list(ForumPost.objects.all())
        # Newer post should come first
        self.assertEqual(posts[0].title, 'Newer Post')
        self.assertEqual(posts[1].title, 'Test Post')


class ReplyModelTest(TestCase):
    """Test Reply model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.post = ForumPost.objects.create(
            sport='basket',
            title='Test Post',
            author=self.user,
            content='Test content'
        )
    
    def test_reply_creation(self):
        """Test creating a reply"""
        reply = Reply.objects.create(
            post=self.post,
            user=self.user,
            comment='Test reply comment'
        )
        
        self.assertEqual(reply.post, self.post)
        self.assertEqual(reply.user, self.user)
        self.assertEqual(reply.comment, 'Test reply comment')
        self.assertIsNotNone(reply.date)
    
    def test_reply_str(self):
        """Test __str__ method"""
        reply = Reply.objects.create(
            post=self.post,
            user=self.user,
            comment='Test comment'
        )
        expected = f"Reply by {self.user} on {self.post}"
        self.assertEqual(str(reply), expected)
    
    def test_reply_related_name(self):
        """Test replies can be accessed from post"""
        reply1 = Reply.objects.create(
            post=self.post,
            user=self.user,
            comment='Reply 1'
        )
        reply2 = Reply.objects.create(
            post=self.post,
            user=self.user,
            comment='Reply 2'
        )
        
        self.assertEqual(self.post.replies.count(), 2)
        self.assertIn(reply1, self.post.replies.all())
        self.assertIn(reply2, self.post.replies.all())


class TagModelTest(TestCase):
    """Test Tag model"""
    
    def test_tag_creation(self):
        """Test creating a tag"""
        tag = Tag.objects.create(name='Beginner')
        
        self.assertEqual(tag.name, 'Beginner')
        self.assertEqual(tag.slug, 'beginner')
    
    def test_tag_slug_auto_generation(self):
        """Test slug is auto-generated from name"""
        tag = Tag.objects.create(name='Advanced Tips')
        self.assertEqual(tag.slug, 'advanced-tips')
    
    def test_tag_str(self):
        """Test __str__ method"""
        tag = Tag.objects.create(name='Tutorial')
        self.assertEqual(str(tag), 'Tutorial')
    
    def test_tag_unique_name(self):
        """Test tag name must be unique"""
        Tag.objects.create(name='Unique')
        
        from django.db.utils import IntegrityError
        with self.assertRaises(IntegrityError):
            Tag.objects.create(name='Unique')


class ForumViewsTest(TestCase):
    """Test forum views"""
    
    def setUp(self):
        """Setup test client and user"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.post = ForumPost.objects.create(
            sport='basket',
            title='Test Post',
            author=self.user,
            content='Test content'
        )
    
    def test_show_forum_view(self):
        """Test forum list page"""
        response = self.client.get(reverse('sportforum:show_forum'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sportforum/forum_post.html')
        self.assertIn('categories', response.context)
    
    def test_post_detail_view_get(self):
        """Test post detail page GET request"""
        response = self.client.get(
            reverse('sportforum:post_detail', args=[self.post.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sportforum/post_detail.html')
        # Context contains string representation of UUID
        self.assertEqual(str(response.context['id']), str(self.post.id))
    
    def test_post_detail_not_found(self):
        """Test post detail with invalid ID redirects"""
        import uuid
        fake_id = uuid.uuid4()
        response = self.client.get(
            reverse('sportforum:post_detail', args=[fake_id])
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_add_post_ajax_unauthenticated(self):
        """Test AJAX post creation requires login"""
        response = self.client.post(
            reverse('sportforum:add_post_ajax'),
            {
                'sport': 'basket',
                'title': 'New Post',
                'content': 'New content'
            }
        )
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_add_post_ajax_success(self):
        """Test successful AJAX post creation"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('sportforum:add_post_ajax'),
            {
                'sport': 'futsal',
                'title': 'AJAX Post',
                'content': 'AJAX content',
                'tags': 'beginner, tutorial'
            }
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('post_id', data)
        
        # Verify post was created
        new_post = ForumPost.objects.get(title='AJAX Post')
        self.assertEqual(new_post.sport, 'futsal')
        self.assertEqual(new_post.author, self.user)
        self.assertEqual(new_post.tags.count(), 2)
    
    def test_add_post_ajax_missing_fields(self):
        """Test AJAX post creation with missing fields"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('sportforum:add_post_ajax'),
            {
                'sport': 'basket',
                'title': 'Incomplete'
                # Missing content
            }
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_toggle_like_authenticated(self):
        """Test toggling like when authenticated"""
        self.client.login(username='testuser', password='testpass123')
        
        # Like the post
        response = self.client.post(
            reverse('sportforum:toggle_like', args=[self.post.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['liked'])
        self.assertEqual(data['total_likes'], 1)
        
        # Unlike the post
        response = self.client.post(
            reverse('sportforum:toggle_like', args=[self.post.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        data = json.loads(response.content)
        self.assertFalse(data['liked'])
        self.assertEqual(data['total_likes'], 0)
    
    def test_toggle_like_unauthenticated(self):
        """Test toggling like when not authenticated"""
        response = self.client.post(
            reverse('sportforum:toggle_like', args=[self.post.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertFalse(data['authenticated'])
    
    def test_edit_post_by_author(self):
        """Test editing post by author"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('sportforum:edit_post', args=[self.post.id])
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sportforum/edit_post.html')
        
        # Test POST - without tags to avoid ManyToMany conflict
        response = self.client.post(
            reverse('sportforum:edit_post', args=[self.post.id]),
            {
                'sport': 'futsal',
                'title': 'Updated Title',
                'content': 'Updated content',
            }
        )
        
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Updated Title')
        self.assertEqual(self.post.sport, 'futsal')
        self.assertEqual(self.post.content, 'Updated content')
    
    def test_edit_post_with_tags(self):
        """Test editing post with tags"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test POST with tags
        response = self.client.post(
            reverse('sportforum:edit_post', args=[self.post.id]),
            {
                'sport': 'basket',
                'title': 'Post with Tags',
                'content': 'Content with tags',
                'tags': 'beginner, tutorial'
            }
        )
        
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, 'Post with Tags')
        self.assertEqual(self.post.tags.count(), 2)
        tag_names = [tag.name for tag in self.post.tags.all()]
        self.assertIn('beginner', tag_names)
        self.assertIn('tutorial', tag_names)
    
    def test_edit_post_by_non_author(self):
        """Test editing post by non-author is forbidden"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='pass123'
        )
        self.client.login(username='otheruser', password='pass123')
        
        response = self.client.get(
            reverse('sportforum:edit_post', args=[self.post.id])
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_delete_post_by_author(self):
        """Test deleting post by author"""
        self.client.login(username='testuser', password='testpass123')
        
        post_id = self.post.id
        response = self.client.post(
            reverse('sportforum:delete_post', args=[post_id])
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ForumPost.objects.filter(id=post_id).exists())
    
    def test_delete_post_by_non_author(self):
        """Test deleting post by non-author is forbidden"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='pass123'
        )
        self.client.login(username='otheruser', password='pass123')
        
        response = self.client.post(
            reverse('sportforum:delete_post', args=[self.post.id])
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ForumPost.objects.filter(id=self.post.id).exists())
    
    def test_show_json_view(self):
        """Test JSON endpoint returns posts"""
        response = self.client.get(reverse('sportforum:show_json'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        
        # Check first post has expected fields
        post_data = data[0]
        self.assertIn('id', post_data)
        self.assertIn('title', post_data)
        self.assertIn('author', post_data)
        self.assertIn('content', post_data)
    
    def test_show_json_with_sport_filter(self):
        """Test JSON endpoint with sport filter"""
        # Create another post with different sport
        ForumPost.objects.create(
            sport='futsal',
            title='Futsal Post',
            author=self.user,
            content='Futsal content'
        )
        
        response = self.client.get(
            reverse('sportforum:show_json') + '?sport=basket'
        )
        
        data = json.loads(response.content)
        # All returned posts should be basket (filter JSON posts by slug)
        db_posts = [p for p in data if p.get('source') == 'database']
        for post in db_posts:
            self.assertEqual(post['sport_slug'], 'basket')


class ReplyViewTest(TestCase):
    """Test reply functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.post = ForumPost.objects.create(
            sport='basket',
            title='Test Post',
            author=self.user,
            content='Test content'
        )
    
    def test_add_reply_authenticated(self):
        """Test adding reply when authenticated"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(
            reverse('sportforum:post_detail', args=[self.post.id]),
            {'comment': 'Test reply'}
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect back
        self.assertEqual(self.post.replies.count(), 1)
        
        reply = self.post.replies.first()
        self.assertEqual(reply.comment, 'Test reply')
        self.assertEqual(reply.user, self.user)
    
    def test_add_reply_unauthenticated(self):
        """Test adding reply when not authenticated redirects to login"""
        response = self.client.post(
            reverse('sportforum:post_detail', args=[self.post.id]),
            {'comment': 'Test reply'}
        )
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.post.replies.count(), 0)
