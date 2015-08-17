from chunks.models import Subject, Semester, Assignment, File
import os.path

subject = Subject.objects.get(name='6.005')
semester = Semester.objects.get(semester='Spring 2015', subject=subject)
assignment = Assignment.objects.get(name='ps0', semester=semester)
files = File.objects.filter(submission__milestone__assignment=assignment)

for f in files:
  newFilename = 'scripts/codeSearch/files/'+"-".join(f.path.split("/"))
  if os.path.isfile(newFilename):
    print f.path
  newFile = open(newFilename, 'w')
  data = f.data.encode('utf-8').strip()
  newFile.write(data)