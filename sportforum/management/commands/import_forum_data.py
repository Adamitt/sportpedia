"""
Django management command to import forum data from JSON to database
Usage: python manage.py import_forum_data
"""

from django.core.management.base import BaseCommand
from sportforum.utils import load_forum_data_from_json


class Command(BaseCommand):
    help = 'Import forum posts from forum.json to database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing forum data before importing',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\nStarting forum data import from JSON...\n'))
        
        if options['clear']:
            from sportforum.utils import clear_forum_data
            self.stdout.write(self.style.WARNING('Clearing existing forum data...'))
            result = clear_forum_data()
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Deleted {result['posts_deleted']} posts, "
                    f"{result['replies_deleted']} replies, "
                    f"and {result['tags_deleted']} tags\n"
                )
            )
        
        # Import data
        result = load_forum_data_from_json()
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✓ Successfully imported forum data!\n"
                    f"  Posts created: {result['posts_created']}/{result['total_posts_in_json']}\n"
                    f"  Replies created: {result['replies_created']}\n"
                    f"  Tags created: {result['tags_created']}\n"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"\n✗ Import failed: {result.get('error', 'Unknown error')}\n"
                )
            )
