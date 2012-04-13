from django import template

register = template.Library()

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
      links: '#464b61'
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
