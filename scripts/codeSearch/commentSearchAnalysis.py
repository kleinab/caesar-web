import ast, json
from log.models import Log
from review.models import Comment
from accounts.models import Member
from chunks.models import Chunk, Semester
from django.contrib.auth.models import User
import csv

def formatJson(log):
  logstring = log.log
  if "LOGSTART: " in logstring:
    logstring = logstring.replace("LOGSTART: ", "")
  valid_s = json.dumps(ast.literal_eval(logstring))
  stringJson = json.loads(valid_s)
  rawJson = {}
  for key in stringJson.keys():
    try:
      rawJson[key] = int(stringJson[key])
    except:
      rawJson[key] = stringJson[key]
  return rawJson

def aggregateLogs():
  # id__gt=9499
  logStarts = Log.objects.filter(log__contains='LOGSTART').order_by('timestamp')
  print len(logStarts)
  aggregateLogs = []
  for i in range(len(logStarts)-1):
  # for i in range(10000, len(logStarts)-1):
    print i
    timeStart = logStarts[i].timestamp
    user = logStarts[i].user
    j = i+1
    while logStarts[j].user != user:
      j += 1
      if j == len(logStarts):
        j -= 1
        break
    timeEnd = logStarts[j].timestamp
    logs = Log.objects.filter(user=user, timestamp__gt=timeStart, timestamp__lt=timeEnd)
    if len(logs) > 0:
      logDict = {'user': user.username,
                 'logstart': formatJson(logStarts[i]),
                 'logs': [formatJson(l) for l in logs],
                }
      aggregateLogs.append(logDict)
  timeStart = logStarts[len(logStarts)-1].timestamp
  user = logStarts[len(logStarts)-1].user
  logs = Log.objects.filter(user=user, timestamp__gt=timeStart)
  if len(logs) > 0:
    logDict = {'user': user.username,
               'logstart': formatJson(logStarts[len(logStarts)-1]),
               'logs': [formatJson(l) for l in logs],
              }
    aggregateLogs.append(logDict)
  return aggregateLogs

def buildAggregateLogs():
  data = aggregateLogs()
  with open('scripts/aggregateLogsAll.txt', 'w') as outfile:
    json.dump(data, outfile)

def getReusedComments():
  reused = Comment.objects.filter(similar_comment__isnull=False)
  author_roles = {}
  for comment in reused:
    semester = comment.chunk.file.submission.milestone.assignment.semester
    role = comment.author.membership.filter(semester=semester)[0].role
    author_roles[role] = author_roles.get(role, 0) + 1
  return author_roles

def getEvents(aggregateLogs):
  events = {}
  for entry in aggregateLogs:
    for log in entry["logs"]:
      if "event" in log:
        event = log["event"]
      else:
        event = "select"
      events[event] = events.get(event, 0) + 1
  return events

def getExplorers(aggregateLogs):
  users = {}
  for entry in aggregateLogs:
    user = entry["user"]
    if entry["logstart"]["type"] == "new comment":
      chunk_id = entry["logstart"]["chunk"]
      try:
        semester = Chunk.objects.get(id=chunk_id).file.submission.milestone.assignment.semester
      except:
        print "Failed for chunk", chunk_id
        continue
    elif entry["logstart"]["type"] == "edit comment":
      comment_id = entry["logstart"]["comment_id"]
      try:
        semester = Comment.objects.get(id=comment_id).chunk.file.submission.milestone.assignment.semester
      except:
        print "Failed for comment", comment_id
        continue
    else: # entry["logstart"]["type"] == "new reply"
      parent_id = entry["logstart"]["parent"]
      try:
        semester = Comment.objects.get(id=parent_id).chunk.file.submission.milestone.assignment.semester
      except:
        print "Failed for parent", parent_id
        continue
    role = User.objects.get(username=user).membership.filter(semester=semester)[0].role
    if role not in users:
      users[role] = {}
    users[role][user] = users[role].get(user, 0) + 1
  return users

def getUsers(aggregateLogs):
  users = {}
  for entry in aggregateLogs:
    for log in entry["logs"]:
      if "event" not in log or log["event"] == "return":
        user = entry["user"]
        if entry["logstart"]["type"] == "new comment":
          chunk_id = entry["logstart"]["chunk"]
          try:
            semester = Chunk.objects.get(id=chunk_id).file.submission.milestone.assignment.semester
          except:
            print "Failed for chunk", chunk_id
            continue
        elif entry["logstart"]["type"] == "edit comment":
          comment_id = entry["logstart"]["comment_id"]
          try:
            semester = Comment.objects.get(id=comment_id).chunk.file.submission.milestone.assignment.semester
          except:
            print "Failed for comment", comment_id
            continue
        else: # entry["logstart"]["type"] == "new reply"
          parent_id = entry["logstart"]["parent"]
          try:
            semester = Comment.objects.get(id=parent_id).chunk.file.submission.milestone.assignment.semester
          except:
            print "Failed for parent", parent_id
            continue
        role = User.objects.get(username=user).membership.filter(semester=semester)[0].role
        if role not in users:
          users[role] = {}
        users[role][user] = users[role].get(user, 0) + 1
  return users

def getCommentWriters(aggregateLogs):
  mismatchedUsers = [];
  for entry in aggregateLogs:
    user = entry["user"]
    for log in entry["logs"]:
      try:
        writer = Comment.objects.get(id=log["comment_id"]).author.username
      except:
        continue
      if user != writer:
        mismatchedUsers.append((user, writer))
  return mismatchedUsers

def analyzeAggregateLogs():
  with open("scripts/aggregateLogsAll.txt") as logfile:
    aggregateLogs = json.load(logfile)
  # id__gt=9499
  logStarts = Log.objects.filter(log__contains='LOGSTART').order_by('timestamp')
  # print "Total logStarts:", len(logStarts)
  # print "Uses:", len(aggregateLogs)
  # print "Total Events:", getEvents(aggregateLogs)
  # print "Author roles:", getReusedComments()
  # explorers = getExplorers(aggregateLogs)
  # # print "Users:", users
  # print "Average number of student explorations:", sum(explorers["S"].values())/len(explorers["S"].keys())
  # print "Average number of teacher explorations:", sum(explorers["T"].values())/len(explorers["T"].keys())
  # users = getUsers(aggregateLogs)
  # print "Users:", users
  # print "Average number of student uses:", sum(users["S"].values())/len(users["S"].keys())
  # print "Average number of teacher uses:", sum(users["T"].values())/len(users["T"].keys())
  print "mismatched users: ", getCommentWriters(aggregateLogs)

#buildAggregateLogs()
analyzeAggregateLogs()

def buildDict(comment, commentType, semester):
  d = {}
  d[commentType+'Comment'] = comment.text.encode('ascii',errors='ignore')
  d[commentType+'Comment Author (Role)'] = str(comment.author)+' ('+str(comment.author.membership.get(semester=semester).role)+')'
  d[commentType+'Code Author'] = ', '.join([author.username for author in comment.chunk.file.submission.authors.all()])
  d[commentType+'Chunk Name (Assignment)'] = str(comment.chunk.name)+' ('+str(comment.chunk.file.submission.milestone.assignment.name)+')'
  d[commentType+'Code Link'] = 'https://10.18.6.30/chunks/view/'+str(comment.chunk.id)+'#comment-'+str(comment.id)
  d[commentType+'Date'] = comment.created
  return d

def buildCSV():
  currentSemester = Semester.objects.get(semester='Spring 2015')
  reused = Comment.objects.filter(similar_comment__isnull=False, chunk__file__submission__milestone__assignment__semester=currentSemester)
  parents = [comment.similar_comment for comment in reused]
  semester = reused[1].chunk.file.submission.milestone.assignment.semester

  with open('scripts/commentDataAll.csv', 'wb') as csvfile:
    fieldnames = ['Comment','Comment Author (Role)','Code Author','Chunk Name (Assignment)','Code Link','Date',]
    allfieldnames = ['Reused '+name for name in fieldnames] + ['Parent '+name for name in fieldnames]
    writer = csv.DictWriter(csvfile, fieldnames=allfieldnames)

    writer.writeheader()
    for i in range(1,len(reused)):
      reusedDict = buildDict(reused[i], "Reused ", semester)
      parentDict = buildDict(parents[i], "Parent ", semester)
      rowDict = dict(reusedDict.items() + parentDict.items())
      writer.writerow(rowDict)

# buildCSV()
# with open("scripts/aggregateLogsAll.txt") as logfile:
#   aggregateLogs = json.load(logfile)
#   comments = []
#   for entry in aggregateLogs:
#     for log in entry["logs"]:
#       if "event" not in log or log["event"] == "return":
#         if entry["logstart"]["type"] == "new comment":
#           chunk_id = entry["logstart"]["chunk"]
#           author = User.objects.get(username=entry["user"])
#           comment = Comment.objects.filter(chunk__id=chunk_id, author=author, start=entry["logstart"]["start"], end=entry["logstart"]["end"], parent=None)
#           comments += [c.id for c in comment]
#         elif entry["logstart"]["type"] == "edit comment":
#           comments.append(entry["logstart"]["comment_id"])
#         else: # entry["logstart"]["type"] == "new reply"
#           parent_id = entry["logstart"]["parent"]
#           author = User.objects.get(username=entry["user"])
#           comment = Comment.objects.filter(parent__id=parent_id, author=author)
#           comments += [c.id for c in comment]
#   reused = [comment.id for comment in Comment.objects.filter(similar_comment__isnull=False)]
#   print "Reused comment was created without system."
#   for comment in reused:
#     if comment not in comments:
#       print comment, Comment.objects.get(id=comment).text
#   print "Comment created in system and then deleted"
#   for comment in comments:
#     if comment not in reused:
#       print comment, Comment.objects.get(id=comment).text
