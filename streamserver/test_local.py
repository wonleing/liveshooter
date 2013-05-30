#!/usr/bin/python
# -*- coding: utf-8 -*-
import xmlrpclib, os
from ftplib import FTP

IP = "127.0.0.1"
ftp = FTP(IP, "live", "shooter")
uname = "cacino@sina.com"
usns = uname.split('@')[1].split('.')[0]
nickname = "嘚嘚迷糊阁"
icon = "http://tp4.sinaimg.cn/1293220651/180/0"
videotitle = "Feel this moment"
snsid = "3570914724034611"
cateid = 1
vsample = "/home/leon/download/feel_this_moment.mp4"
ftpdir = "/var/ftp/pub/"
s=xmlrpclib.ServerProxy("http://%s:8000" %IP)

userid = s.loginUser(uname, usns, nickname, icon)
print "create user:", userid

videoid = s.genFilename()
print "upload video file name is:", videoid

if s.addTitle(userid, videoid, cateid, videotitle):
    print "add tiltle %s for %s" %(videotitle, videoid)
else:
    print "Error: add video failed"

ftp.storbinary('STOR %s' %videoid, open(vsample, 'rb'))
url = s.finishUpload(videoid)
print "Transcode completed, now you can watch %s" %url

if s.shareVideo(videoid, snsid):
    print "add sns string", snsid, "to video", videoid

if s.likeVideo(1, videoid):
    print "user 1 liked video", videoid

if s.followUser(3, 2):
    print "user 3 followed 2"

ul = s.getFollowing(1)
print "user 1 following these users:", str(ul)

if s.followVideo(1, videoid):
    print "1 followed the owner of %s" %videoid

ul = s.getFollower(1)
print "user 1 is followed by these users:", str(ul)

ru = s.getRecommandUser()
print "recommad user list is", str(ru)

rv = s.getRecommandVideo()
print "recommad video list is", str(rv)

if s.unfollowUser(3, 2):
    print "user 3 unfollowed 2"

if s.unfollowVideo(1, videoid):
    print "1 unfollowed the owner of %s" %videoid

up = s.getUserProfile(userid)
print "retrieved user", userid, "profile", str(up)

vl = s.getUserVideo(userid)
print "user", userid, "has uploaded following video", str(vl)

vl = s.getFeed(userid)
print "user", userid, "feed list is:", str(vl)

if s.unlikeVideo(userid, videoid):
    print "user", userid, "unliked video", videoid

fl = s.getSNSfollowing(1, 'sina')
print "User 1 has these sina friends in our site", fl

ll = s.getLikeVideo(userid)
print "user", userid, "video like list is:", str(ll)

vi = s.getVideoInfo(videoid)
print "video", videoid, "info is:", str(vi)

print "API testing finished!"
