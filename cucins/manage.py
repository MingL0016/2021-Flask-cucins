# -*- encoding=UTF-8 -*-

from cucins import app, db
from flask_script import Manager
from cucins.models import Like, User, Image, Comment
import random

manager = Manager(app)


def get_image_url():
    return '/static/images/(' + str(random.randint(0, 300)) + ').jpg'

# 初始化数据库 使用命令行


@manager.command
def init():
    db.drop_all()
    db.create_all()
    for i in range(0, 10):
        db.session.add(User('Tsetuser' + str(i+1),
                       'Testnickname' + str(i+1), 'a' + str(i+1)))
        for j in range(0, 100):
            db.session.add(Image(get_image_url(), i+1))
    db.session.commit()


if __name__ == '__main__':
    manager.run()
