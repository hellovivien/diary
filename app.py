import streamlit as st
from streamlit.hashing import _CodeHasher
from streamlit.report_thread import get_report_ctx
from streamlit.server.server import Server
import pymongo
# import locale
# locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
from datetime import datetime
from datetime import timedelta  
from datetime import date
from fastapi import FastAPI
import pickle
import requests
import faker
import random
from streamlit_lottie import st_lottie
from bson.objectid import ObjectId
from passlib.hash import bcrypt
from pymongo.message import update
import os
from dotenv import load_dotenv

load_dotenv()
local_api_url = "http://127.0.0.1:8000"
fake = faker.Faker()


def api_url(path):
    return "{}/{}".format(local_api_url, path)

def get_db():
    client = pymongo.MongoClient(st.secrets["mongo_url"])
    return client.diary

db = get_db()


# write html
def html(content, side = False):
    if side:
        st.sidebar.markdown(content, unsafe_allow_html=True)
    else:
        st.markdown(content, unsafe_allow_html=True)


# load css files
def local_css(file_name):
    with open('css/{}'.format(file_name)) as f:
        st.markdown('<style>{}</style>'.format(f.read()), unsafe_allow_html=True)


# fill empty user fields with fake data
def fake_user(user):
    fake_model = {
        'first_name': fake.first_name(),
        'last_name' : fake.last_name(),
        'username' : fake.user_name(),
        'password': 'test',
        'phone_number': fake.phone_number(),
        'email': fake.email(),
        'birthday': fake.date_time_between(start_date='-120y', end_date='-1y')
    }
    for field, value in fake_model.items():
        if field not in user.keys() or not user[field]:
            user[field] = value

# if user has a token he has been logged
def is_logged(state):
    return bool(state.token)

def logout(state):
    state.me = None
    state.token = None
    state.rerun()

# make request to load animation on lottiefiles
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# cool animation
def girl_with_laptop():
    return load_lottieurl("https://assets3.lottiefiles.com/packages/lf20_ul5tg9kq.json")

#authenticate and log in user
def auth(state, user):
    res = requests.post(api_url("token"), data = user).json()
    state.me = db.users.find_one(res['user_id'])
    state.token = res['access_token']    



def main():

    # load css, state and notifications
    local_css('style.css')
    state = _get_state()
    show_notification(state)

    state.auto_login = st.sidebar.checkbox("Auto-login", True)
    html('<hr />', side=True)

    # autologin with random user for dev
    if not is_logged(state) and state.auto_login:
        random_user = db.users.aggregate([ { '$sample': { 'size': 1 } } ]).next()
        random_user['password'] = 'test'
        auth(state, random_user)

    # user is logged so we can load menu
    if is_logged(state):
        _,col1, col2,_ = st.sidebar.beta_columns([1,1,1,1])
        col1.image("avatar.png",width=70)
        col2.markdown("**{}**".format(state.me["first_name"]))
        if col2.button("logout"):
            logout(state)
        pages = {
            "Write": add_post,
            "Read": show_posts,
            "API" : api,
        }

        page = st.sidebar.radio("Menu", tuple(pages.keys()), index=2)

        # clear state if user change page without complete a task
        if page != "Write":
            state.created_post_id = state.something = None

        # Display the selected page with the session state
        pages[page](state)
    
    # user is not logged so he can create an account or sign in
    else:

        # generate coach_name
        if not state.coach_name:
            state.coach_name = fake.first_name_female()

        html('<h1 class="title" >{}<p>My virtual coach</h1>'.format(state.coach_name))
        st_lottie(girl_with_laptop())
        pages = {'create_account':'Create an account', 'sign_in':'Sign in'}
        page = st.sidebar.radio("Welcome", options=list(pages.keys()), format_func=lambda x: pages[x])
        
        if page == "create_account":
            with st.form(key='create_account'):
                st.markdown("**Create an account**")
                user = {}
                user['username'] = st.text_input("username")
                user['password'] = st.text_input("password")
                user['birthday'] = st.date_input("birthday", value=None)
                user['first_name'] = st.text_input("first name")
                user['last_name'] = st.text_input("last name")
                user['phone_number'] = st.text_input("email") 
                user['email'] = st.text_input("phone number")            
                if st.form_submit_button("create"):
                    fake_user(user) # fill empty field with fake data
                    requests.post(api_url("users"), data = user).json()
                    auth(state, user)
        elif page == 'sign_in':
            with st.form(key='signin'):
                st.markdown("**Sign In**")
                user = {}
                user['username'] = st.text_input("username")
                user['password'] = st.text_input("password")          
                if st.form_submit_button("Sign in"):
                    auth(state, user)

    # Mandatory to avoid rollbacks with widgets, must be called at the end of your app
    state.sync()


def add_post(state):
    html('<h1 class="title" >Hello {}<p>How are you feeling today?</p></h1>'.format(state.me['first_name']))
    st_lottie(girl_with_laptop())
    if state.created_post_id:
        show_post(state, db.posts.find_one(state.created_post_id))
    else:
        if st.button("i have no idea"):
            state.something = get_random_text()
        with st.form(key='add_post'):
            text = st.text_area("tell me something", state.something or '')
            if st.form_submit_button("Write"):
                if len(text)>0:
                    post = {}
                    post['user_id'] = state.me['_id']
                    post['text'] = text
                    post['token'] = state.token
                    state.created_post_id = requests.post(api_url("posts"), data = post).json()
                else:
                    st.markdown("Hey i'm just an AI, cant read your mind without any data! 🙊")



def show_posts(state):

    filters = {}
    emotion_labels = ('all', 'fear', 'happy', 'sadness', 'love', 'anger', 'surprise')

    if is_coach():
        users = db.users.find()
        all_users = {'first_name':'All'}
        user_filter = st.sidebar.selectbox(label='Utilisateur', options = [all_users]+[user for user in users],format_func = lambda x: x['first_name'])
    else:
        filters['user_id'] = state.me['_id']


    emotion_filter = st.sidebar.selectbox(label='Emotion', options = emotion_labels, format_func = lambda x: x.capitalize() )
    date_filter = st.sidebar.selectbox("Date filter", ('none', 'calendar', 'slider'), format_func = lambda x: x.capitalize() )
    date_slider = st.sidebar.slider(
        "Calendar date filter",
        value=(datetime(2019, 1, 1), datetime(2022, 1, 1)),
        format="DD/MM/YY")
    calendar = st.sidebar.date_input(
        "Slider date filter")

    if date_filter != 'none':
        if date_filter == 'calendar':
            start_date =  datetime(calendar.year, calendar.month, calendar.day)
            end_date = start_date + timedelta(days=1) 
        elif date_filter == 'slider':
            start_date, end_date = date_slider[0], date_slider[1]
        filters['created_at'] = {'$gt': start_date, '$lt': end_date}

    if emotion_filter != 'all':
        filters['emotion'] = emotion_filter

    posts = list(db.posts.find(filters))      
    posts = sorted(posts, key=lambda k: k['created_at'], reverse=True)
    for post in posts:
        show_post(state, post)


def show_post(state, post):

    author = db.users.find_one({'_id': post['user_id']})
    col1, col2, col3, col4 = st.beta_columns([5,5,1,1])
    if col3.button('edit', key=post['_id']):
        state.post_id = post['_id']
    if col4.button('delete', key=post['_id']):
        requests.delete(api_url("posts/{}".format(post['_id'])), data = {'token': state.token})
        state.created_post_id = None
        state.notif = "Your post has been deleted."
        state.rerun()            
    col1.markdown('**{}** · <small>{}</small>'.format(author['first_name'], post['created_at'].strftime('%A %d/%m/%Y à %H:%M:%S')), unsafe_allow_html=True)
    if state.post_id == post['_id']:
        text = st.text_area("How are you feeling today?", post['text'])
        if st.button('ok', post['_id']):
            requests.put(api_url("posts/{}".format(post['_id'])), data = {'text': text, 'token': state.token})
            state.post_id = None        
    else:
        st.markdown('***<div class="text"><p>{}</p><span class="emotion-label {}-label">{}</span></div>***'.format(post['text'], post['emotion'], post['emotion']),  unsafe_allow_html=True)
    st.write('<hr />',  unsafe_allow_html=True)



def api(state):
    # For security concerns API JWT token should be regenerate for each new connection and you only give private API key to user
    st.markdown("In the wonderful API world you can do many things like **GET**, **POST**, **PUT** and **DELETE**, all you need is a **API key** or **token**")
    st.markdown("Here is your **API token**, keep it secret!")
    html("<p class='text'>{}</p>".format(state.token))
    st.markdown("and here is what you can do with it...")

    st.markdown("**GET** all your posts : return a dict of all your posts")
    url = api_url("posts/token/{your secret token}")
    html('<p class="text">{}</p>'.format(url))
    if st.button("try", key="get_posts"):
        posts = get_your_posts(state)
        html('<p class="text">{}</p>'.format(posts))
        

    st.markdown("**POST** a new post : create a new post and return the ID")
    url = api_url("posts")
    html('<p class="text">{}</p>'.format(url))
    data = {"text":"i tried the API today it was a nightmare", "token":state.token, "user_id":state.me["_id"]}
    form_data_str = st.text_area("form data", data)
    if st.button("try", key="create_post"):
        form_data = eval(form_data_str,{},{})
        new_post = requests.post(api_url("posts"), data = form_data).json()
        html('<p class="text">{}</p>'.format(new_post))

    st.markdown("**GET** last post : return a dict of your last post")
    url = api_url("posts/last/{your secret token}")
    html('<p class="text">{}</p>'.format(url))
    if st.button("try", key="get_last_post"):
        last_post = requests.get(api_url("posts/last/{}".format(state.token))).json()[0]
        html('<p class="text">{}</p>'.format(last_post))        

    st.markdown("**PUT** a post : edit a post")
    last_post = requests.get(api_url("posts/last/{}".format(state.token))).json()[0]
    url = api_url("posts/{post_id}")
    html('<p class="text">{}</p>'.format(url))
    data = {"text":"i tried the API today it was like a dream", "token":state.token}
    form_data_str = st.text_area("form data", data)
    if st.button("try", key="update_post"):
        form_data = eval(form_data_str,{},{})
        updated_post = requests.put(api_url("posts/{}").format(last_post['_id']), data = form_data).json()
        html('<p class="text">{}</p>'.format(updated_post))

    st.markdown("**DELETE** a post : delete a post")
    last_post = requests.get(api_url("posts/last/{}".format(state.token))).json()[0]
    url = api_url("posts/{post_id}")
    html('<p class="text">{}</p>'.format(url))
    data = {'token':state.token}
    form_data_str = st.text_area("form data", data)
    if st.button("try", key="delete_post"):
        form_data = eval(form_data_str,{},{})
        res = requests.delete(api_url("posts/{}".format(last_post['_id'])), data = form_data).json()
        html('<p class="text">{}</p>'.format(res))                  
    

def get_your_posts(state):
    return requests.get(api_url("posts/token/{}".format(state.token))).json()

def get_random_text():
	return list(db.kaggle_data.aggregate([ { '$sample': { 'size': 1 } } ]))[0]['text']


def show_notification(state):
    if state.notif:
        st.write(state.notif)
    state.notif = None


def edit_user(state):
    show_notification(state)
    users = list(db.users.find())
    user_widget = st.empty()
    user = user_widget.selectbox(label='Utilisateur', options = [user for user in users],format_func = lambda x: "{} {} @{}".format(x['last_name'], x['first_name'],x['username']),index=1)
    if st.button("reset fake generator"):
        state.random_int = random.randint(3, 9999999)
    with st.form(key='add_user_form'):
        st.markdown("**Add user**")
        data = {}
        data['username'] = st.text_input("username", user['username'])
        # data['password'] = st.text_input("password", current_user['password'], type="password")
        data['first_name'] = st.text_input("first name", user['first_name'])
        data['last_name'] = st.text_input("last name", user['last_name'])
        data['email'] = st.text_input("email", user['email']) 
        data['phone_number'] = st.text_input("phone number", user['phone_number'])            
        if st.form_submit_button("edit_user"):
            st.write(data)
            res = requests.put("http://127.0.0.1:8000/users/{}".format(user['_id']), data = data)
            st.write(res.json())
            updated_user = db.users.find_one({'_id':user['_id']})
            st.write(updated_user)
            state.notification = "ok c'est modifié"
            state.rerun()

def is_coach():
    return False


class _SessionState:

    def __init__(self, session, hash_funcs):
        """Initialize SessionState instance."""
        self.__dict__["_state"] = {
            "data": {},
            "hash": None,
            "hasher": _CodeHasher(hash_funcs),
            "is_rerun": False,
            "session": session,
        }

    def __call__(self, **kwargs):
        """Initialize state data once."""
        for item, value in kwargs.items():
            if item not in self._state["data"]:
                self._state["data"][item] = value

    def __getitem__(self, item):
        """Return a saved state value, None if item is undefined."""
        return self._state["data"].get(item, None)
        
    def __getattr__(self, item):
        """Return a saved state value, None if item is undefined."""
        return self._state["data"].get(item, None)

    def __setitem__(self, item, value):
        """Set state value."""
        self._state["data"][item] = value

    def __setattr__(self, item, value):
        """Set state value."""
        self._state["data"][item] = value
    
    def clear(self):
        """Clear session state and request a rerun."""
        self._state["data"].clear()
        self.rerun()

    def rerun(self):
        self._state["session"].request_rerun()
    
    def sync(self):
        """Rerun the app with all state values up to date from the beginning to fix rollbacks."""

        # Ensure to rerun only once to avoid infinite loops
        # caused by a constantly changing state value at each run.
        #
        # Example: state.value += 1
        if self._state["is_rerun"]:
            self._state["is_rerun"] = False
        
        elif self._state["hash"] is not None:
            if self._state["hash"] != self._state["hasher"].to_bytes(self._state["data"], None):
                self._state["is_rerun"] = True
                self._state["session"].request_rerun()

        self._state["hash"] = self._state["hasher"].to_bytes(self._state["data"], None)


def _get_session():
    session_id = get_report_ctx().session_id
    session_info = Server.get_current()._get_session_info(session_id)

    if session_info is None:
        raise RuntimeError("Couldn't get your Streamlit Session object.")
    
    return session_info.session


def _get_state(hash_funcs=None):
    session = _get_session()

    if not hasattr(session, "_custom_session_state"):
        session._custom_session_state = _SessionState(session, hash_funcs)

    return session._custom_session_state


if __name__ == "__main__":
    main()