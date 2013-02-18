import datetime

from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Rss201rev2Feed

from cms.models import Post
from cms.templatetags.cms_filters import show_user

from pigeonpost.models import Pigeon

class LatestPostsFeed(Feed):
    title = "Seabirds.net lastest posts"
    link = "/posts/"
    description = "Latests posts on Seabirds.net"
    feed_type = Rss201rev2Feed
    # Last 5 posts
    feed_length = 5

    def items(self):
        items = []
        # filter out staff only posts
        qs = Post.objects.filter(listing__read_permission=None).order_by('-date_published')
        now = datetime.datetime.now()
        for post in qs:
            try:
                # check whether pigeon for post subscribers has been sent
                # if so, we make it available in the feed
                pigeon = post.pigeons.get(render_email_method='email_subscriber')
                if pigeon and pigeon.sent_at and pigeon.sent_at < now:
                    items.append(post)
                    if len(items) > self.feed_length:
                        break
            except Pigeon.DoesNotExist:
                # automatically show any posts that don't have pigeons
                # as we assume these were added outside of the normal
                # publishing process
                items.append(post)
        return items

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.markdown_text

    def item_author_name(self, item):
        return show_user(item.author)

    def item_author_link(self, item):
        return item.author.profile.get().get_absolute_url()




