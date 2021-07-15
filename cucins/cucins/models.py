# -*- encoding=UTF-8 -*-

from flask.helpers import send_file
from flask_sqlalchemy.model import DefaultMeta
from sqlalchemy.orm import backref
from cucins import app, db, login_manager
from datetime import datetime
import random


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # 0表示点赞 1表示没点赞  没用到 简化了下 在库里的表示点赞 取消点赞删除数据
    likethis = db.Column(db.Integer, default=0)
    created_time = db.Column(db.DateTime)
    user = db.relationship('User')

    def __init__(self, image_id, user_id):  # 初始化
        self.image_id = image_id
        self.user_id = user_id
        self.created_time = datetime.now()

    def __repr__(self):  # 引用
        return '%d' % (self.id)


class Comment(db.Model):  # 评论
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.String(1024))
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_time = db.Column(db.DateTime)
    user = db.relationship('User')

    def __init__(self, content, image_id, user_id):
        self.content = content
        self.image_id = image_id
        self.user_id = user_id
        self.created_time = datetime.now()

    def __repr__(self):
        return '<Comment %d %s>' % (self.id, self.content)


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    url = db.Column(db.String(512))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_date = db.Column(db.DateTime)
    comments = db.relationship('Comment')
    likes = db.relationship('Like')

    def __init__(self, url, user_id):
        self.url = url
        self.user_id = user_id
        self.created_date = datetime.now()

    def __repr__(self):
        return '<Image %d %s>' % (self.id, self.url)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True)
    usernickname = db.Column(db.String(80))
    password = db.Column(db.String(32))
    salt = db.Column(db.String(32))
    head_url = db.Column(db.String(256))
    images = db.relationship('Image', backref='user', lazy='dynamic')
    #likes = db.relationship('Like',backref='user',lazy='dynamic')

    def __init__(self, username, usernickname, password, salt=''):
        self.username = username
        self.usernickname = usernickname
        self.password = password
        self.salt = salt
        # 初始化头像
        self.head_url = '/static/images/(' + \
            str(random.randint(0, 300)) + ').jpg'

    def __repr__(self):
        return '<User %d %s %s >' % (self.id, self.username, self.usernickname)

    # Flask Login接口
    def is_authenticated(self):
        print
        'is_authenticated'
        return True

    def is_active(self):
        print
        'is_active'
        return True

    def is_anonymous(self):
        print
        'is_anonymous'
        return False

    def get_id(self):
        print
        'get_id'
        return self.id


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)
