from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import os
import hashlib
from pytz import timezone
from datetime import datetime

korea_timezone = timezone('Asia/Seoul')

app = Flask(__name__)
app.secret_key = os.urandom(24)

# DB 기본코드
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'database.db')

db = SQLAlchemy(app)


# Member 테이블 생성
class Member(db.Model):
    # member_id
    member_id = db.Column(db.Integer, primary_key=True)
    # 로그인 ID
    member_login_id = db.Column(db.String(), nullable=False, unique=True)
    # 비밀번호
    password = db.Column(db.String(), nullable=False)
    # 이름
    member_name = db.Column(db.String(), nullable=False)
    # 별명
    member_nickname = db.Column(db.String(), nullable=False)
    # 프로필 사진
    member_profile = db.Column(db.String(), nullable=True)
    # 권한
    member_role = db.Column(db.String(), nullable=False, default='member')

    def __repr__(self):
            return (f'{self.member_id} | {self.member_login_id} | {self.password} | {self.member_name} '
                    f'| {self.member_nickname} | {self.member_role}')


# 게시글 테이블 생성
class Post(db.Model):
    # 게시글 ID
    post_id = db.Column(db.Integer, primary_key=True)
    # member_id
    member_id = db.Column(db.Integer, db.ForeignKey(
        'member.member_id'), nullable=False)
    # 글 제목
    post_title = db.Column(db.String(), nullable=False)
    # 글 내용
    post_content = db.Column(db.Text, nullable=False)
    # 조회수
    post_views = db.Column(db.Integer, nullable=False, default=0)
    # 좋아요 수
    post_likes = db.Column(db.Integer, nullable=False, default=0)
    # 비밀글 여부
    post_is_private = db.Column(db.Boolean, default=False)
    # 등록일
    post_registration_date = db.Column(
        db.DateTime, default=datetime.now(korea_timezone))

    def __repr__(self):
        return (f'{self.post_id} | {self.member_id} | {self.post_title} | {self.post_content} '
                f'| {self.post_views} | {self.post_likes} | {self.post_is_private} | {self.post_registration_date}')


# Comment 테이블 생성
class Comment(db.Model):
    # comment_id
    comment_id = db.Column(db.Integer, primary_key=True)
    # post_id
    # ForeignKey 테스트하느라 default값 넣어둠. 삭제해야됨
    post_id = db.Column(db.Integer, db.ForeignKey(
        'post.post_id'), nullable=False, default=1)
    # member_id
    member_id = db.Column(db.Integer, db.ForeignKey(
        'member.member_id'), nullable=False, default=1)
    # 댓글 내용
    comment_body = db.Column(db.String(), nullable=False)
    # 비밀 여부
    is_secret = db.Column(db.String())
    # 등록일
    comment_date = db.Column(db.DateTime, default=datetime.now(korea_timezone))

    def __repr__(self):
        return (f'{self.comment_id} | {self.post_id} | {self.member_id} | {self.comment_body} '
                f'| {self.is_secret} | {self.comment_date}')


with app.app_context():
    db.create_all()

UPLOAD_FOLDER = os.getcwd() + '/static/upload'  # 절대 파일 경로
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # 확장자 검증


# 메인 페이지
@app.route('/')
def home():
    return render_template("index.html", member=session.get("member"))


# 회원가입
@app.route('/member_add', methods=['POST'])
def member_add():
    member_login_id = request.form['member_login_id']
    password = request.form['password']
    member_name = request.form['member_name']
    member_nickname = request.form['member_nickname']
    file = request.files['member_profile']
    file_name = ""
    # 파일 있는지 확인
    if file:
        # 확장자 체크
        if file.filename.split('.')[-1] in ALLOWED_EXTENSIONS:
            # os.makedirs(UPLOAD_FOLDER)
            # 파일명은 중복되면 에러가 나기때문에 앞에 member_id 추가
            file_name = member_login_id+"_"+file.filename
            # 파일 저장
            file.save(os.path.join(UPLOAD_FOLDER, file_name))
        else:
            return render_template("message.html", message="이미지 파일만 가능합니다!", return_url="/")

    member = Member(member_login_id=member_login_id, password=hashlib.sha256(password.encode("UTF-8")).hexdigest()
                    , member_name=member_name, member_nickname=member_nickname, member_profile=file_name)
    db.session.add(member)
    db.session.commit()

    return render_template("message.html", message="정상적으로 등록되었습니다.", return_url="/")


# 아이디 중복 체크
@app.route('/member_id_check', methods=['POST'])
def member_id_check():
    member_login_id = request.form['member_login_id']
    if Member.query.filter_by(member_login_id=member_login_id).count():
        return jsonify(True)
    else:
        return jsonify(False)


# 로그인
@app.route('/member_login', methods=['POST'])
def member_login():
    member_login_id = request.form['member_login_id']
    password = request.form['password']
    member = Member.query.filter_by(member_login_id=member_login_id,
                                    password=hashlib.sha256(password.encode("UTF-8")).hexdigest())
    prev_url = request.form.get('prev_url','/')
    if member.count():
        session["member"] = {
            "member_login_id": member.first().member_login_id,
            "member_name": member.first().member_name,
            "member_nickname": member.first().member_nickname,
            "member_profile": member.first().member_profile
        }
        return render_template("message.html", message=f"{member.first().member_name}님으로 로그인 했습니다.", return_url=prev_url)
    else:
        return render_template("message.html", message="회원정보를 찾을 수 없습니다.", return_url=prev_url)


# 로그아웃
@app.route('/member_logout', methods=['GET'])
def member_logout():
    del session["member"]
    return render_template("message.html", message="로그아웃 완료했습니다.", return_url="/")


# 게시글 목록 페이지
@app.route("/post_list")
def post_list():
    print(session.get("member"))
    post = Post.query.order_by(Post.post_registration_date.desc()).all()
    # print(post)
    return render_template("post_list.html", member=session.get("member"), post_list=post)


# 게시글 페이지
@app.route("/post_instance")
def post_instance():
    print(session.get("member"))
    return render_template("post_instance.html", member=session.get("member"))


# 게시글 등록 // 관리자 접근권한은 나중에..?
@app.route("/post_add", methods=['POST'])
def post_add():
    member_id = request.form['member_login_id']
    post_title = request.form['post_title']
    post_content = request.form['post_content']

    post = Post(member_id=member_id, post_title=post_title,
                post_content=post_content)
    print(post)
    db.session.add(post)
    db.session.commit()
    # redirect(url_for("post_list"))
    # return render_template("post_list.html")
    return redirect(url_for("post_list"))


# 게시글 내용 페이지(작성한 게시글이 보이고, 댓글을 달 수 있음.)
@app.route('/post_content', methods=['GET', 'POST'])
def post_content():
    # 댓글 데이터 전송
    if request.method == 'POST':
        print('ABCD')
        post_id = request.form['post_id']
        comment_body_receive = request.form["comment_body"]
        is_secret_receive = request.form.get("is_secret", "No")
        comment = Comment(comment_body=comment_body_receive,
                          is_secret=is_secret_receive)
        db.session.add(comment)
        db.session.commit()
        comment_list = Comment.query.all()
        return render_template("message.html", message="댓글이 작성되었습니다.", return_url=f"/post_content?post_id={post_id}")
    # 댓글 데이터 요청
    elif request.method == 'GET':
        post_id = request.args.get('post_id')
        post = Post.query.filter_by(post_id=post_id).first()
        comment_list = Comment.query.all()
        print('ㄱㄴㄷㄹ',comment_list)
        return render_template("post_content.html", member=session.get("member"), post=post, comment_list=comment_list)


# # 댓글 테스트 페이지
# @app.route('/comment', methods=['GET', 'POST'])
# def comment():
#     # 댓글 데이터 전송
#     if request.method == 'POST':
#         comment_body_receive = request.form["comment_body"]
#         is_secret_receive = request.form.get("is_secret", "No")
#         comment = Comment(comment_body=comment_body_receive,
#                           is_secret=is_secret_receive)
#         db.session.add(comment)
#         db.session.commit()
#         comment_list = Comment.query.all()
#     # 댓글 데이터 요청
#     elif request.method == 'GET':
#         comment_list = Comment.query.all()
#     return render_template("comment.html", data=comment_list, return_url="/comment")

# ================수정 전====================================
# 게시글 내용 페이지
# @app.route('/post_content', methods=['GET'])
# def post_content():
#     print(session.get("member"))
#     post_id = request.args.get('post_id')
#     # print(123123, post_id)
#     post = Post.query.filter_by(post_id=post_id).first()
#     # print(123123, post)
#     return render_template("post_content.html", member=session.get("member"), post=post)


# # 댓글 테스트 페이지
# @app.route('/comment', methods=['GET', 'POST'])
# def comment():
#     # 댓글 데이터 전송
#     if request.method == 'POST':
#         comment_body_receive = request.form["comment_body"]
#         is_secret_receive = request.form.get("is_secret", "No")
#         comment = Comment(comment_body=comment_body_receive,
#                           is_secret=is_secret_receive)
#         db.session.add(comment)
#         db.session.commit()
#         comment_list = Comment.query.all()
#     # 댓글 데이터 요청
#     elif request.method == 'GET':
#         comment_list = Comment.query.all()
#     return render_template("comment.html", data=comment_list, return_url="/comment")
# ==============================================================

# 게시글 수정 페이지
@app.route('/post_update', methods=['GET', 'POST'])
def post_update():
    if request.method == "POST":
        post_id = request.form['post_id']
        post_title = request.form['post_title']
        post_content = request.form['post_content']
        post_is_private = request.form.get('post_is_private', False)
        post = Post.query.filter_by(post_id=post_id).first()
        post.post_title = post_title
        post.post_content = post_content
        post.post_is_private = post_is_private
        db.session.commit()
        return render_template("message.html", message="게시글을 수정하였습니다."
                               , return_url="/post_content?post_id="+post_id)
    elif request.method == 'GET':
        post_id = request.args.get('post_id')
        post = Post.query.filter_by(post_id=post_id).first()
        return render_template("post_update.html", member=session.get("member"), post=post)


# 게시글 목록의 시간 형식 정하기
@app.template_filter('strftime')
def _jinja2_filter_datetime(date):
    native = date.replace(tzinfo=None)
    format= '%Y-%m-%d %I:%M:%S %p'
    return native.strftime(format)


if __name__ == '__main__':  
    app.run(host='0.0.0.0', port=5005, debug=True)
    
    