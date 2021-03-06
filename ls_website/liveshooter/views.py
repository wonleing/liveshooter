# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import Http404, HttpResponse
from liveshooter.models import Followship, Userlike, User, Uservideo, Video
from ftplib import FTP
import xmlrpclib, os, sina
s=xmlrpclib.ServerProxy("%s:8000" %settings.XMLRPC_URL, encoding='utf-8')
burl = 'http://54.248.182.51/'

def _check_login(request, context):
    if 'login_user' not in request.session:
        request.session['login_user'] = ""
    if 'login_id' not in request.session:
        request.session['login_id'] = ""
    if 'access_token' not in request.session:
        request.session['access_token'] = ""
    if 'expires_in' not in request.session:
        request.session['expires_in'] = 0
    if 'categorys' not in request.session:
        request.session['categorys'] = s.getCategory(True)
    context['login_user'] = request.session['login_user']
    context['login_id'] = str(request.session['login_id'])
    context['categorys'] = request.session['categorys']

def index(request):
    recommand_users = s.getRecommandUser(True)
    recommand_videos = s.getRecommandVideo(True)
    context = {
        'recommand_users': recommand_users,
        'recommand_videos': recommand_videos,
    }
    _check_login(request, context)
    if context['login_id']:
        login_id = int(context['login_id'])
        context['sns_friends'] = s.getSNSfollowing(login_id, True)
        context['follow_users'] = s.getFollowing(login_id, True)
        context['feed_videos'] = s.getFeed(login_id, True)
    return render(request, 'index.html', context)

def user(request, userid):
    try:
        user_profile = s.getUserProfile(int(userid), True)
        user_videos = s.getUserVideo(int(userid), True)
        user_followers = s.getFollower(int(userid), True)
    except:
        raise Http404
    followed = False
    for uf in user_followers:
        if request.session['login_id'] == uf[0]:
            followed = True
    context = {
        'up': user_profile,
        'user_videos': user_videos,
        'followed': followed,
    }
    _check_login(request, context)
    return render(request, 'user.html', context)

def video(request, videoid):
    try:
        video_info = s.getVideoInfo(videoid, True)
    except:
        raise Http404
    comments = None
    for ext in [".mp4", ".flv", ".ogv", ".webm"]:
        if ext in str(os.listdir(settings.MEDIA_ROOT+videoid)):
            break
    user_agent = request.META['HTTP_USER_AGENT'].lower()
    HLS = False
    for a in ['iphone', 'ipad', 'mac os', 'android']:
        if a in user_agent:
            HLS = True
            break
    context = {
        'videoid': videoid,
        'HLS': HLS,
        'ext': ext,
        'vi': video_info,
    }
    _check_login(request, context)
    if video_info[2] and request.session['access_token']:
        wb = sina.Weibo()
        wb.setToken(request.session['access_token'], request.session['expires_in'])
        context['comments'] = wb.getComment(video_info[2])
    context['liked'] = False
    if context['login_id']:
        login_id = int(context['login_id'])
        for v in s.getLikeVideo(login_id, True):
           if videoid == v[0]:
               context['liked'] = True
               break
    return render(request, 'video.html', context)

def follower(request, userid):
    try:
        user_profile = s.getUserProfile(int(userid), True)
        follower_list = s.getFollower(int(userid), True)
    except:
        raise Http404
    context = {
        'up': user_profile,
        'follower_list': follower_list,
    }
    _check_login(request, context)
    return render(request, 'follower.html', context)

def following(request, userid):
    try:
        user_profile = s.getUserProfile(int(userid), True)
        following_list = s.getFollowing(int(userid), True)
    except:
        raise Http404
    context = {
        'up': user_profile,
        'following_list': following_list,
    }
    _check_login(request, context)
    return render(request, 'following.html', context)

def addnew(request, userid):
    context = {
        'uid': str(userid),
    }
    _check_login(request, context)
    return render(request, 'addnew.html', context)

def doadd(request):
    if request.session['access_token'] and request.session['expires_in']:
        userid = int(request.POST.get('userid'))
        videotitle = request.POST.get('videotitle').replace("'", "`").encode('utf-8')
        cateid = int(request.POST.get('category'))
        try:
            videopath = request.FILES['videopath']
        except:
            return HttpResponse('<html><head><META HTTP-EQUIV="refresh" CONTENT="3;URL=user/%s"></head>Please choose a video</html>' %userid)
        videoid = s.genFilename()
        videoname = videoid + "." + videopath._get_name().split(".")[1]
        os.system("mv %s /var/ftp/pub/%s;chmod 644 /var/ftp/pub/%s" %(videopath.temporary_file_path(), videoname, videoname))
        if not s.addTitle(userid, videoid, cateid, videotitle):
             return HttpResponse('<html><head><META HTTP-EQUIV="refresh" CONTENT="3;URL=user/%s"></head>Add video title failed\n%s</html>' \
             %(userid, str(userid)+","+videoid+","+videotitle))
        url = s.finishUpload(videoid)
        msg = videotitle + " " + burl + videoid
        snapshot = burl + videoid + "/" + videoid + ".jpeg"
        wb = sina.Weibo()
        wb.setToken(request.session['access_token'], request.session['expires_in'])
        try:
            ret = wb.post(msg, snapshot)
            s.shareVideo(videoid, ret.mid)
            message = "</br>Posted and link video on your weibo successfully"
        except:
            message = "</br>Failed to post on your weibo because of illegal words or snapshot doesnot exist"
        return HttpResponse('''<html><head><META HTTP-EQUIV="refresh" CONTENT="3;URL=user/%s"></head>
        Your video can be watched here: %s,%s</html>''' %(userid, url, message))
    else:
        return redirect('login')

def login(request):
    context = {}
    _check_login(request, context)
    return render(request, 'login.html', context)

def dologin(request):
    logined = 0
    ac = request.POST.get('account')
    pw = request.POST.get('password')
    site = request.POST.get('site')
    if site == 'sina':
        if '@' not in ac:
            ac += '@sina.com'
        wb = sina.Weibo()
        token = wb.auth(ac, pw)
        if token:
            wb.setToken(token[0], token[1])
            nickname, alink = wb.profile()
            logined = 1
    if logined:
        uid = s.loginUser(ac, site, nickname, alink)
        request.session['login_user'] = nickname
        request.session['login_id'] = uid
        request.session['access_token'] = token[0]
        request.session['expires_in'] = token[1]
        return HttpResponse('''<html><head><META HTTP-EQUIV="refresh" CONTENT="3;URL=user/%s"></head>
        You have logined as %s</html>''' %(request.session['login_id'], request.session['login_user']))
    else:
        return HttpResponse('''<html><head><META HTTP-EQUIV="refresh" CONTENT="3;URL=login"></head>login failed</html>''')

def logout(request):
    request.session['login_user'] = ""
    request.session['login_id'] = ""
    request.session['access_token'] = ""
    request.session['expires_in'] = 0
    return HttpResponse('''<html><head><META HTTP-EQUIV="refresh" CONTENT="3;URL=/"></head>logout successfully!''')

def follow(request):
    uid = int(request.POST['uid'])
    targetid = int(request.POST['targetid'])
    if s.followUser(uid, targetid):
        return HttpResponse()
    else:
        return HttpResponse("fail to follow")

def unfollow(request):
    uid = int(request.POST['uid'])
    targetid = int(request.POST['targetid'])
    if s.unfollowUser(uid, targetid):
        return HttpResponse()
    else:
        return HttpResponse("fail to unfollow")

def likevideo(request):
    uid = int(request.POST['uid'])
    videoid = request.POST['videoid']
    if s.likeVideo(uid, videoid):
        return HttpResponse()
    else:
        return HttpResponse("fail to like video")

def unlikevideo(request):
    uid = int(request.POST['uid'])
    videoid = request.POST['videoid']
    if s.unlikeVideo(uid, videoid):
        return HttpResponse()
    else:
        return HttpResponse("fail to unlike video")

def addcomment(request):
    nc = request.POST['msg'][:140]
    mid = request.POST['mid']
    if request.session['access_token'] and nc and mid:
        wb = sina.Weibo()
        wb.setToken(request.session['access_token'], request.session['expires_in'])
        try:
            wb.addComment(nc, mid)
            return HttpResponse()
        except:
            pass
    return HttpResponse("Fail to add comment. Make sure thread exist and message legal.")

def category(request, cateid):
    cate_name = s.getCateName(int(cateid))
    cate_videos = s.getCateVideos(int(cateid), True)
    context = {
        'cate_name': cate_name,
        'cate_videos': cate_videos,
    }
    _check_login(request, context)
    return render(request, 'category.html', context)

