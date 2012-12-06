from django import template
from django.utils.safestring import mark_safe

from cms.forms import SimpleComment
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
