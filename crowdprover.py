import cgi
import datetime
import urllib
import webapp2
import codeinfo

from google.appengine.ext import db
from google.appengine.api import users

import jinja2
import os
import sys, os.path

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class Greeting(db.Model):
  """Models an individual Guestbook entry with an author, content, and date."""
  author = db.StringProperty()
  content = db.StringProperty(multiline=True)
  date = db.DateTimeProperty(auto_now_add=True)

class Invariant(db.Model):
  """Models in individual invariant for a piece of code."""
  author = db.StringProperty()
  content = db.StringProperty(multiline=True) #The Invariant is only text for now, but it must be made more structured later
  date = db.DateTimeProperty(auto_now_add=True)
  score = db.IntegerProperty() #After running/checking on the backend, the supplied invariant is to be assigned a score
  codeid = db.StringProperty() #This is the ID of the program for which this is an invariant
  lineno = db.IntegerProperty() #The line number right after which this invariant is expected to hold

def guestbook_key(guestbook_name=None):
  """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
  return db.Key.from_path('Guestbook', guestbook_name or 'default_guestbook')

class MainPage(webapp2.RequestHandler):
    def get(self):
        #guestbook_name=self.request.get('guestbook_name')
        #greetings_query = Greeting.all().ancestor(
            #guestbook_key(guestbook_name)).order('-date')
        #greetings = greetings_query.fetch(10)
        #gkey = guestbook_key(guestbook_name)

        #codeid = "1" #This gets set dynamically later
        f = open('randtext.txt','r') #This depends on codeid

        i = Invariant.all()
        i.filter("codeid =", codeinfo.codeid) #Only display invariants for the current code
        i.order("-score")
        invs = i.run(limit=50) #This gives the top 50 invariants for this program

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'codeid': codeinfo.codeid,
            'url': url,
            'url_linktext': url_linktext,
            'f' : f,
            'invs' : invs,
            #'title' : 'AJAX Add (via GET)' #newajax
        }
        #path = os.path.join(os.path.dirname(__file__),'crowdprover.html') #newajax
        template = jinja_environment.get_template('crowdprover.html')
        #self.response.out.write(template.render(path, template_values)) #newajax
        self.response.out.write(template.render(template_values))

class InvList(webapp2.RequestHandler):
  def post(self):
    # We set the same parent key on the 'Invariant' to ensure each invariant is in
    # the same entity group. Queries across the single entity group will be
    # consistent. However, the write rate to a single entity group should
    # be limited to ~1/second
    invariant = Invariant()

    if users.get_current_user():
      invariant.author = users.get_current_user().nickname()

    invariant.content = self.request.get('content')
    invariant.score = 0
    invariant.codeid = self.request.get('codeid') #codeid must be a hidden field in the form
    invariant.lineno = int(self.request.get('lineno'))

    invariant.put()

    # At this point we must also run the backend and evaluate the validity of the invariant, assign a score etc.

    #self.response.out.write("Well done sirjee")
    self.redirect('/') #redirect back to the main page

#class RPCHandler(webapp.RequestHandler): #newajax
 #   """ Will handle the RPC requests."""
  #  def get(self):
   #     self.error(403) # under construction: access denied



class Guestbook(webapp2.RequestHandler):
  def post(self):
    # We set the same parent key on the 'Greeting' to ensure each greeting is in
    # the same entity group. Queries across the single entity group will be
    # consistent. However, the write rate to a single entity group should
    # be limited to ~1/second.
    guestbook_name = self.request.get('guestbook_name')
    greeting = Greeting(parent=guestbook_key(guestbook_name))

    if users.get_current_user():
      greeting.author = users.get_current_user().nickname()

    greeting.content = self.request.get('content')
    greeting.put()
    self.redirect('/?' + urllib.urlencode({'guestbook_name': guestbook_name}))


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/sign', Guestbook),
                               ('/inv', InvList)],
                               #('/rpc', RPCHandler)], #newajax
                              debug=True)