from django import template
from django.utils.safestring import mark_safe

from cms.forms import SimpleComment

import datetime
from cms.models import Post, Listing
from comments.models import PigeonComment

from utils.markdownplus import markdownplus as __markdownplus


register = template.Library()

@register.filter
def markdownplus(text):
    return mark_safe(__markdownplus(text))

@register.filter
def twitter_widget(username):
    if username.startswith('@'):
        username = username[1:]
    username = username.strip()
    return u"""<div id="twitter">
    <h4>&nbsp;</h4>
      <script charset="utf-8" src="http://widgets.twimg.com/j/2/widget.js"></script>
      <script>
new TWTR.Widget({
  version: 2,
  type: 'profile',
  rpp: 5,
  interval: 30000,
  width: 'auto',
  height: 300,
  theme: {
    shell: {
      background: '#dddddd',
      color: '#464b61'
    },
    tweets: {
      background: '#ffffff',
      color: '#444444',
      links: '#3b5997'
    }
  },
  features: {
    scrollbar: false,
    loop: false,
    live: false,
    behavior: 'all'
  }
}).render().setUser("%s").start();
</script>
</div>""" % username

@register.inclusion_tag('cms/edit_comment.html')
def edit_comment(comment, user):
    if comment:
        if comment.can_be_edited_by(user):
            initial = { 'comment': comment.comment, 'id': comment.id }
            return {
                    'id': comment.id,
                    'commentform': SimpleComment(prefix='comment', initial=initial)
                   }
        else:
            return {}
    else:
        return { 'id': 'new', 'commentform': SimpleComment(prefix='comment') }

@register.inclusion_tag('cms/activity.html')
def activity_stream(user):
    if not user:
        user = None

    if user and user.is_staff:
        latest_posts = list(Post.objects.all().order_by('-date_published')[:5])
        latest_comments = list(PigeonComment.objects.all().order_by('-submit_date')[:5])
    else:
        listings = Listing.objects.user_readable(user)
        latest_posts = list(Post.objects.filter(listing__in=[l.id for l in listings]).order_by('-date_published')[:5])
        latest_comments_qs = PigeonComment.objects.all().order_by('-submit_date')
        latest_comments = []
        for c in latest_comments_qs:
            if c.can_be_seen_by(user):
                latest_comments.append(c)
            if len(latest_comments) > 5:
                break
    activity = latest_posts + latest_comments
    def sort_activity(a, b):
        def get_time(x):
            if isinstance(x, Post):
                d = x.date_published
                return datetime.datetime(year=d.year, month=d.month, day=d.day)
            else:
                return x.submit_date
        return 1 if get_time(b) > get_time(a) else -1
    activity.sort(cmp=sort_activity)
    results = []
    for a in activity:
        if isinstance(a, Post):
            results.append( ('post', a) )
        else:
            results.append( ('comment', a) )
    return {'activity': results}

@register.filter
def show_user(user):
    if user.first_name:
        return user.first_name + ' ' + user.last_name
    else:
        return user.username

@register.filter
def show_user_short(user):
    if user.first_name:
        return user.first_name
    else:
        return user.username
