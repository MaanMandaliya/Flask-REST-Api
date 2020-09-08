from flask import Flask, jsonify, request, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, reqparse, Resource, abort
import jwt
import datetime
from functools import wraps

#application create and configuration
app = Flask(__name__)
app.secret_key = 'thisissecretkey'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost:3306/flaskrestapi'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flaskrestapi'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

#database
db = SQLAlchemy(app)

#create rest-api
api = Api(app)

#Model for Video
class VideoModel(db.Model):
    __tablename__ = 'videomaster'
    videoId = db.Column('videoId',db.Integer,primary_key=True,autoincrement=True)
    videoTitle = db.Column('videoTitle',db.String(100),nullable=False)
    videoCreator = db.Column('videoCreator',db.String(50),nullable=False)
    videoLikes = db.Column('videoLikes',db.Integer,nullable=False)
    videoViews = db.Column('videoViews', db.Integer, nullable=False)
    videoPostDate = db.Column('videoPostDate', db.String(20), nullable=False)

    def as_dict(self):
        return {
            'videoId' : self.videoId,
            'videoTitle' : self.videoTitle,
            'videoCreator' : self.videoCreator,
            'videoLikes' : self.videoLikes,
            'videoViews' : self.videoViews,
            'videoPostDate' : self.videoPostDate
        }

    def __repr__(self):
        return f"Video(videoTitle={videoTitle},videoCreator={videoCreator},\
        videoLikes={videoLikes},videoViews={videoViews},videoPostDate={videoPostDate}"

class UserModel(db.Model):
    __tablename__ = 'usermaster'
    userId = db.Column('userId', db.Integer, primary_key=True, autoincrement=True)
    userName = db.Column('userName', db.String(260), nullable=False)
    userPassword = db.Column('userPassword', db.String(50), nullable=False)


    def as_dict(self):
        return {
            'userId': self.userId,
            'userName': self.userName,
            'userPassword': self.userPassword
        }

# To create database and tables
db.create_all()

# to fetch data from HTTP request
#Arguments for post method
video_post_args = reqparse.RequestParser()
video_post_args.add_argument("videoTitle", type=str, help="Title of video", required=True)
video_post_args.add_argument("videoCreator", type=str, help="Creator of video", required=True)
video_post_args.add_argument("videoLikes", type=int, help="Likes on video", required=True)
video_post_args.add_argument("videoViews", type=int, help="Views of video", required=True)
#Arguments for put method
video_put_args = reqparse.RequestParser()
video_put_args.add_argument("videoTitle", type=str, help="Title of video", required=True)
video_put_args.add_argument("videoCreator", type=str, help="Creator of video", required=True)
video_put_args.add_argument("videoLikes", type=int, help="Likes on video", required=True)
video_put_args.add_argument("videoViews", type=int, help="Views of video", required=True)
#Arguments for update/patch method
video_patch_args = reqparse.RequestParser()
video_patch_args.add_argument("videoTitle", type=str, help="Title of video")
video_patch_args.add_argument("videoCreator", type=str, help="Creator of video")
video_patch_args.add_argument("videoLikes", type=int, help="Likes on video")
video_patch_args.add_argument("videoViews", type=int, help="Views of video")

#Video Resource with methods
class Video(Resource):
    def tocken_required(f):
        @wraps(f)
        def decorator(*args,**kwargs):
            token = request.headers['token']
            if not token:
                return jsonify({'message':'token is missing'})
            try:
                data = jwt.decode(token,app.secret_key)
                print("Token data : ",data)
                # current_user = UserModel.query.filter_by(userId=data['userId']).first()
            except:
                return jsonify({'message': 'token is invalid'})
            return f(*args,**kwargs)
        return decorator
    @tocken_required
    def get(self,videoId):
        video = VideoModel.query.filter_by(videoId=videoId).first()
        if not video:
            abort(404, message="video doesn't exist!")
        return video.as_dict(), 200

    @tocken_required
    def post(self,videoId):
        args = video_post_args.parse_args()
        video = VideoModel.query.filter_by(videoId=videoId).first()
        if video:
            abort(409,message="video already exists!")
        video_post = VideoModel(videoId=videoId,videoTitle=args['videoTitle'],videoCreator=args['videoCreator'], \
                           videoLikes=args['videoLikes'],videoViews=args['videoViews'],videoPostDate=datetime.date.today())
        db.session.add(video_post)
        db.session.commit()
        return video_post.as_dict(), 201

    @tocken_required
    def put(self,videoId):
        args = video_put_args.parse_args()
        video = VideoModel.query.get(videoId)
        if not video:
            abort(404, message="video doesn't exist, can't update(put)!")
        for argkey,argvalue in args.items():
            setattr(video, argkey, argvalue)
        setattr(video,"videoPostDate",datetime.date.today())
        db.session.merge(video)
        db.session.commit()
        return video.as_dict(), 202

    @tocken_required
    def patch(self,videoId):
        args = video_patch_args.parse_args()
        video = VideoModel.query.get(videoId)
        if not video:
            abort(404, message="video doesn't exist, can't update(patch)!")
        for argkey,argvalue in args.items():
            if argvalue != None:
                setattr(video, argkey, argvalue)
        setattr(video, "videoPostDate", datetime.date.today())
        db.session.merge(video)
        db.session.commit()
        return video.as_dict(), 202

    @tocken_required
    def delete(self,videoId):
        video = VideoModel.query.get(videoId)
        if not video:
            abort(404, message="video doesn't exist, can't delete!")
        db.session.delete(video)
        db.session.commit()
        return video.as_dict(), 202

#to create databse
# db.drop_all()
# db.create_all()

#API Resource
api.add_resource(Video, "/video/<int:videoId>")

#Application routes
#route to register to use REST-API
@app.route('/register',methods=['GET','POST'])
def register():
    data = request.get_json()
    user = UserModel(userName=data['userName'],userPassword=data['userPassword'])
    db.session.add(user)
    db.session.commit()
    print("user registered successfully!")
    return jsonify({"message":"registered successfully"})

#route for login/authentication to access REST-API
@app.route('/login',methods=["GET","POST"])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        print("auth info missing")
        return make_response('Could not verify',401,{'WWW.Authentication': 'Basic realm: "login required"'})
    user = UserModel.query.filter_by(userName=auth.username).first()
    if user.userPassword == auth.password:
        print("password matched!")
        token = jwt.encode({'userId':user.userId,'exp':datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
        return jsonify({"token":token.decode("UTF-8")})
    print("username or password invalid!",auth.password)
    return make_response('Could not verify',401,{'WWW.Authentication': 'Basic realm: "login required"'})

#to run rest-api
if __name__ == '__main__':
    app.run(debug=True)