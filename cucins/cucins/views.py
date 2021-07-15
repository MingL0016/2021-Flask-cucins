# -*- encoding=UTF-8 -*-

from typing import Hashable

from cucins import app, db
from cucins.models import Image, Like, User, Comment
from flask import render_template, redirect, request, jsonify, flash, get_flashed_messages, send_from_directory, url_for
from flask_login import login_required, login_user, logout_user, current_user
import random
import os
import json
import hashlib
import re
import uuid
from flask_login import LoginManager
from cucins.qiniusdk import qiniu_upload_file
from sqlalchemy import and_, or_


@app.route('/')
@app.route('/index')
def index():
    paginate = Image.query.order_by(Image.id.desc()).paginate(
        page=1, per_page=10, error_out=False)
    return render_template('index.html', images=paginate.items, has_next=paginate.has_next)


@app.route('/login/', methods={'post', 'get'})
def login():
    username = request.values.get('username').strip()
    password = request.values.get('password').strip()

    if username == '' or password == '':
        return redirect_with_msg('/reloginpage/', u'用户名或密码不能为空', 'relogin')

    user = User.query.filter_by(username=username).first()

    if user == None:
        return redirect_with_msg('/reloginpage/', u'用户名不存在', 'relogin')

    m = hashlib.md5()
    m.update((password+user.salt).encode('utf-8'))
    if (m.hexdigest() != user.password):
        return redirect_with_msg('/reloginpage/', u'密码错误', 'relogin')

    login_user(user)

    next = request.values.get('next')
    if next != None and next.startswith('/'):
        return redirect(next)

    return redirect('/')


@app.route('/reloginpage/')
def reloginpage():
    msg = ''
    for m in get_flashed_messages(with_categories=False, category_filter=['relogin']):
        msg = msg + m
    return render_template('login.html', msg=msg, next=request.values.get('next'))


def redirect_with_msg(target, msg, category):
    if msg != None:
        flash(msg, category=category)
    return redirect(target)


@app.route('/logout/')
def logout():
    logout_user()
    return redirect('/')


@app.route('/index/<int:page>/<int:per_page>/')
def index_images(page, per_page):
    paginate = Image.query.filter_by().paginate(
        page=page, per_page=per_page, error_out=False)
    map = {'has_next': paginate.has_next}
    images = []
    for image in paginate.items:
        comments = []
        for comment in image.comments:
            comment_item = {'username': comment.user.username,
                            'content': comment.content}
            comments.append(comment_item)
        imgvo = {'id': image.id, 'url': image.url, 'created_date': str(
            image.created_date), 'user.id': image.user.id, 'user.headurl': image.user.head_url, 'user.username': image.user.username, 'comment_count': len(image.comments)}
        imgvo['comments'] = comments
        images.append(imgvo)

    map['images'] = images
    return json.dumps(map)


@app.route('/image/<int:image_id>/')
def image(image_id):
    image = Image.query.get(image_id)
    comments = Comment.query.filter_by(image_id=image_id)
    likes = Like.query.filter_by(image_id=image_id)
    if image == None:
        return redirect('/')
    return render_template('pageDetail.html', image=image, comments=comments, likes=likes)


@app.route('/profile/<int:user_id>/')
@login_required
def profile(user_id):
    user = User.query.get(user_id)
    if user == None:
        return redirect('/')
    paginate = Image.query.order_by(Image.id.desc()).filter_by(
        user_id=user_id).paginate(page=1, per_page=30, error_out=False)
    photo = Image.query.filter_by(user_id=user_id).all()
    return render_template('profile.html', user=user, images=paginate.items, has_next=paginate.has_next, photo=photo)


@app.route('/profile/images/<int:user_id>/<int:page>/<int:per_page>/')
def user_images(user_id, page, per_page):
    paginate = Image.query.filter_by(user_id=user_id).paginate(
        page=page, per_page=per_page, error_out=False)
    map = {'has_next': paginate.has_next}
    images = []
    for image in paginate.items:
        imgvo = {'id': image.id, 'url': image.url,
                 'comment_count': len(image.comments)}
        images.append(imgvo)

    map['images'] = images
    return json.dumps(map)


@app.route('/signup/', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form.get('username')
        usernickname = request.form.get('usernickname')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(username=username).first()
        if user:
            flash('用户已存在', category='error')
        elif username == '' or password1 == '' or password2 == '':
            flash('用户名和密码不能为空', category='error')
        elif len(username) < 5:
            flash('用户名至少5位', category='error')
        elif (is_contains_chinese(username) == True):
            flash('用户名格式不正确(只能英文和数字组合)', category='error')
        elif password1 != password2:
            flash('密码不一致', category='error')
        elif len(password1) < 5:
            flash('密码至少5位', category='error')
        else:
            salt = ''.join(random.sample(
                '0123456789abcdefghigklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', 10))
            m = hashlib.md5()
            m.update((password1 + salt).encode('utf-8'))
            password = m.hexdigest()

            new_user = User(
                username=username, usernickname=usernickname, password=password, salt=salt)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect('/')

    return render_template("signup.html", user=current_user)


@app.route('/image/<image_name>')
def view_image(image_name):
    return send_from_directory(app.config['UPLOAD_DIR'], image_name)


@app.route('/upload/', methods={"post"})
@login_required
def upload():
    file = request.files['file']
    file_ext = ''
    if file.filename.find('.') > 0:
        file_ext = file.filename.rsplit('.')[1].strip().lower()
    if file_ext in app.config['ALLOWED_EXT']:
        file_name = str(uuid.uuid4()).replace('-', '') + '.' + file_ext
        #url = save_to_local(file, file_name)
        url = qiniu_upload_file(file, file_name)
        if url != None:
            db.session.add(Image(url, current_user.id))
            db.session.commit()

    return redirect('/profile/%d' % current_user.id)


@app.route('/changehead/', methods={"post"})
@login_required
def changehead():

    file = request.files['file']
    file_ext = ''
    if file.filename.find('.') > 0:
        file_ext = file.filename.rsplit('.')[1].strip().lower()
    if file_ext in app.config['ALLOWED_EXT']:
        file_name = str(uuid.uuid4()).replace('-', '') + '.' + file_ext
        #url = save_to_local(file, file_name)
        url = qiniu_upload_file(file, file_name)
        if url != None:
            db.session.query(User).filter(
                User.id == current_user.id).update({"head_url": url})
            db.session.commit()

    return redirect('/profile/%d' % current_user.id)


@app.route('/resetnickname/', methods={"post", "get"})
def resetnickname():
    nickname = request.form.get('nickname')
    if request.method != 'POST':
        return render_template('resetnickname.html', user=current_user)
    elif nickname == '':
        flash('昵称不能为空', category='error')
    elif nickname == current_user.usernickname:
        flash('昵称与原昵称一致', category='error')
    else:
        db.session.query(User).filter(User.id == current_user.id).update(
            {"usernickname": nickname})
        db.session.commit()
        return redirect('/')
    return render_template('resetnickname.html', user=current_user)


@app.route('/resetpassword/', methods={"post", "get"})
def changepassword():
    password1 = request.form.get('password1')
    password2 = request.form.get('password2')

    if request.method != 'POST':
        return render_template('resetpassword.html', user=current_user)
    elif password1 == '':
        flash('密码不能为空', category='error')
    elif password1 != password2:
        flash('密码不一致', category='error')
    elif len(password1) < 5:
        flash('密码至少5位', category='error')
    elif hashlib.md5().update((password1+(User.query.filter_by(username=current_user.username).first()).salt).encode('utf-8')) == current_user.password:
        flash('密码与原密码一致', category='error')
    else:
        salt = ''.join(random.sample(
            '0123456789abcdefghigklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', 10))
        m = hashlib.md5()
        m.update((password1 + salt).encode('utf-8'))
        password = m.hexdigest()

        db.session.query(User).filter(User.id == current_user.id).update(
            {"password": password, "salt": salt})
        db.session.commit()
        login_user(current_user, remember=True)
        flash('成功', category='success')
        return redirect('/')
    return render_template('resetpassword.html', user=current_user)


def save_to_local(file, file_name):
    save_dir = app.config['UPLOAD_DIR']
    file.save(os.path.join(save_dir, file_name))
    return 'upload/' + file_name


@app.route('/addcomment/', methods={'post'})
def add_commit():
    image_id = int(request.values['image_id'])
    content = request.values['content']
    comment = Comment(content, image_id, current_user.id)
    db.session.add(comment)
    db.session.commit()

    return json.dumps({"code": 0, "content": content, "id": comment.id, "username": comment.user.usernickname, "user_id": comment.user.id})


@app.route('/addlike/', methods={'post'})
def add_like():
    image_id = int(request.values['image_id'])
    likeid = Like.query.filter_by(image_id=image_id).filter_by(
        user_id=current_user.id).first()
    if likeid != None:
        db.session.delete(likeid)
        db.session.commit()
        return redirect('/'+str(image_id))
    like = Like(image_id, current_user.id)
    db.session.add(like)
    db.session.commit()
    return redirect('/'+str(image_id))


def is_contains_chinese(strs):  # 判断用户名是否含有中文
    for _char in strs:
        if '\u4e00' <= _char <= '\u9fa5':
            return True
    return False
