
Seabirds.net is the website of the World Seabird Union, an umbrella
organisation focused on seabird research. 
They require a website to disseminate information, manage membership,
and to communicate with their members.

# Components

## Static content

Allow for pages with static content (text, images, etc.), arranged in a navigation
hierarchy. Static text will be edited using the markdown syntax. This format is
chosen as it makes it more difficult to produce syntactically incorrect html,
and it discourages the use of complex formatting that will break the
look of the web site. Extensions to the markdown are included, in particular
images and publications may be included in the text using special tags.


## Seabird researchers

The members of the site are primarily seabird researchers (although
other interested and relevant people may apply to join). The site provides the
basic functionality for researchers to register,  login, and change passwords.

Members of the site fall in three categories:
    
* Users (no access to the administration screens, can post, comment, upload photographs,
        and edit their own information)
* Staff (staff can access the administration screens, and edit the static
        content of the site, or alter the layout)
* Superusers (people with a  technical understanding of how the site works,
        with full control)

## Researcher profiles

Seabird researchers have a profile page created for them. The profile page gives
the following information
    
* Personal information (name, email, website, photograph, twitter handle)
* Institutional information (institution, institution website)
* Research interests (a free text section describing their research)
* Seabird interests (selection of seabird families of interest)
* Research field (e.g., ecology, taxonomy, `I am not a researcher')
* Latest posts (title and teaser of most recent posts made to the site)
* Seabird photographs (gallery of seabird photographs uploaded by the user)
* Twitter feed (recent tweets by the user)

The design of the profile page will degrade gracefully, with content only
appearing if it is entered in the profile page. For example, a user that does
not have a twitter account, or that does not want twitter to appear on their page,
will simply not include it in their profile. The display of email addresses is
optional. 

### Opting out

Having created an entry, it is important that users can always
    
* Edit their own information
* Remove themselves from the site

To leave Seabirds.net, users will click through from the profile page to a special
page with a single button and a message such as 'Please remove me from the seabird researchers
database and from Seabirds.net'. If they continue, their profile will be marked as inactive,
they will no longer receive any communication from Seabirds.net, and their profile will not
be displayed.

### Blocking

Staff may also have the occasion to block users. This will be done through the administration
screens of the website. It is expected to only be used if one of the users happens
to become abusive. Blocked users will be unable to post further content, however their profile
will still be visible and will still be editable. To remove their profile from the site, 
make their accounts inactive.

## PETREL database

The PETREL database is a list of the registered users, with the exception that members who
declare they are not seabird researchers will not appear in the database. The database will
have an index page that lists the researchers. It is anticipated that a single long list will
be the simplest in the short term. The list will be able to be filtered by country, by
seabird family, and by research area.

## Posts

The key content of the site are posts. These are content items created by users. Posts contain
a title, a short teaser, a block of text and an optional image. Posts may also be categorised
by seabird family. Posts allow for comments to be made, and when displayed will include
social sharing buttons. At first, comments will only be allowed by logged in users.

Site staff may declare their posts to be WSU news. These are the same as posts, however they
will be displayed on a separate news page. The content of these posts is expected to be 
about organisational business.

## Announcements

Staff will also be able to post announcements. These will be similar to
WSU news posts, but will only consist of a title and a teaser, and will not allow
comments. Announcements will be used for short pieces of information.

## Photographs

Members may upload photographs. In order to make these photographs of wide use, they
will be encouraged to use a creative commons license for the photographs. The form
for uploading photographs will be relatively complex, as it requires the copyright
owner and the source of the photograph to be identified. With this structure, Seabirds.net
will be able to re-use photographs that have been CC licensed from sites such as Flickr.

Photographs will optionally have a caption, allowing for a full description to be provided.

Photographs will be able to be tagged by seabird family. This will allow for a gallery
page displaying seabird photographs, with the option to filter by family. 


## Communication with members

A key role of the website will be to facilitate communication with members. People
are sensitive to getting too many emails, and so this aspect will be handled carefully.
In particular, an option will be provided for people to opt out of all emails
from the website, with the exception of essential communications (such as a reminder that
they haven't updated their profile for the last two years, etc.). There will be three
email lists that may be subscribed too
    
* WSU news and announcements 
* Posts relevant to your seabird families
* All WSU news, and all posts

By default, the first two options will be checked.  The subscriptions will be 
managed by users from the profile page. Emails will be plain text,
with a link back to the post on the site. The footer of each email will
contain instructions on unsubscribing, and on resetting the password.

Each post, news item, or announcement will be sent as a separate message. If the volume becomes
large, a digest feature may be added in the future, but experience shows that people tend not
to read digest emails.

## Publications

The website will allow for members to load references to their seabird related publications. 
Bibliographic references will be entered using the bibtex format. This is one of the formats
that is made available by Google scholar, and citation management software often allows 
for export of references in the bibtex format.

It will also be possible to upload PDFs, providing the user asserts 
that they have the right to do so. This will allow for people to 
share publications, posters, and presentations. A size limit will be placed on 
the uploaded files (say 10 MB).

## Twitter and social sharing

A widget will be placed on the front page that displays all tweets made by @seabirders,
the twitter handle of the WSU. Social sharing buttons will be placed on posts, and
by announcements, allowing them to be tweeted, posted on facebook, emailed, or
posted via googleplus. 

# Administration

The website comes with an administration site that allows for
authorized users administrative control over all the content.


# Hosting and code

The website is written in Django, a python web-framework. No
proprietary code is used, and so there are no 
software licensing costs. All code used for the 
website (with the exception of private information API keys, passwords, etc.,
that must necessarily remain confidential to Seabirds.net)  will be 
released under a license that permits free reuse (specifically,
the permissive MIT/X license), and will be made available through a repository
on Github. Components that are specific to Seabirds.net will be
copyright the WSU. Reflecting prior art, generic components that may
be re-used on other projects will be copyright
of Dragonfly Limited. Because of the permissive license, this will not
restrict the reuse of the code by the WSU or any other party, in any way, 
provided that the original contributions are suitably acknowledged.

The website will be hosted on a third-party server, with WSU staff having 
responsibility for monitoring the website, for paying for the hosting, and
maintaining the registration of the domain name.

# Roadmap

## Stage 1

* Static content
* User profiles
* Petrel database
* Uploading posts, announcements, and images
* Preliminary design

## Stage 2

* Email lists
* Publications
* Image gallery
* Twitter and social sharing
* Minor design changes
* Testing of function across browsers (IE8+, Chrome, Firefox)
* Testing of W3C HTML compliance
    
## The future

* Site wide search
* Internationalization (allowing translation of all content)
* Seabird organisations (page for each organisation)
* Metadata (description of seabird data-sets)
* Species specific information (tagging of content by species, and associated species pages)
* Functionality for conference administration
* Implement OAuth to allow databases to authenticate researchers via Seabirds.net
