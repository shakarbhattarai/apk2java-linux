#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#

import sys, os, string
import urllib
import zipfile
from subprocess import call
from optparse import OptionParser

apk_file=''
apk_folder=''
project_name=''
sign_file=''
home=os.path.dirname(os.path.realpath(sys.argv[0]))
tmp='/tmp/apk2java/'
external="https://github.com/TheZ3ro/apk2java-linux/archive/master.zip"

def check_home(path):
  return os.path.isdir(path+"/tool")

def getunzipped(theurl, thedir, report):
  print "Downloading external tool..."
  name = os.path.join(thedir, 'temp.zip')
  try:
    name, hdrs = urllib.urlretrieve(theurl, name, report)
  except IOError, e:
    print "Can't retrieve %r to %r: %s" % (theurl, thedir, e)
    return
  try:
    z = zipfile.ZipFile(name)
  except zipfile.error, e:
    print "Bad zipfile (from %r): %s" % (theurl, e)
    return
  for n in z.namelist():
    (dirname, filename) = os.path.split(n)
    if filename == '':
      # directory
      newdir = thedir + '/' + dirname
      if not os.path.exists(newdir):
          os.mkdir(newdir)
    else:
      # file
      fd = open(thedir+"/"+n, 'w')
      fd.write(z.read(n))
      fd.close()
  z.close()
  os.unlink(name)

def report(blocknr, blocksize, size):
  current = blocknr*blocksize
  sys.stdout.write("\rProgress: {0:.2f}%".format(100.0*current/size))

def apktool(smali):
  print "*********************************************"
  print "**      Extract, fix resource files        **"
  print "*********************************************"
  if apk_file != '':
    if smali == True:
      call(home+'/tool/apktool_200rc3.jar d '+apk_file+' -o '+tmp+project_name+' -f',shell=True)
    else:
      call(home+'/tool/apktool_200rc3.jar d '+apk_file+' -o '+tmp+project_name+' -sf',shell=True)
      os.system('mv %s %s' % (tmp+project_name+'/classes.dex', tmp+project_name+'/original/'))
  print 'Done'

def dex2jar():
  print "*********************************************"
  print "**          Convert 'apk' to 'jar'         **"
  print "*********************************************"
  if apk_file != '':
    call(home+'/tool/dex2jar-0.0.9.15/d2j-dex2jar.sh -f -o '+tmp+project_name+'.jar '+apk_file, shell=True)
    call(home+'/tool/dex2jar-0.0.9.15/d2j-asm-verify.sh '+tmp+project_name+'.jar',shell=True)
    print 'Done'

def procyon():
  print "*********************************************"
  print "**        Decompiling class files          **"
  print "*********************************************"
  if apk_file != '':
    call(home+'/tool/procyon-decompiler-0528.jar -jar '+tmp+project_name+'.jar -o '+tmp+project_name+'/src/',shell=True)
    print 'Done'

def apktool_build():
  print "*********************************************"
  print "**        Building apk from smali          **"
  print "*********************************************"
  if apk_folder != '':
    call(home+'/tool/apktool_200rc3.jar b '+apk_folder+' -o '+tmp+project_name+'-rebuild.apk',shell=True)
    global sign_file 
    sign_file = tmp+project_name+'-rebuild.apk'
    print 'Done'

def jar2jasmin():
  print "*********************************************"
  print "**        Convert 'jar' to 'jasmin'        **"
  print "*********************************************"
  if apk_file != '':
    call(home+'/tool/dex2jar-0.0.9.15/d2j-jar2jasmin.sh -f -o '+tmp+project_name+'/jasmin '+tmp+project_name+'.jar',shell=True)
    print 'Done'

def jasmin_build():
  print "*********************************************"
  print "**          Build apk from jasmin          **"
  print "*********************************************"
  if apk_folder != '':
    call(home+'/tool/dex2jar-0.0.9.15/d2j-jasmin2jar.sh -f -o '+tmp+project_name+'-new.jar '+tmp+project_name+'/jasmin',shell=True)
    call(home+'/tool/dex2jar-0.0.9.15/d2j-asm-verify.sh '+tmp+project_name+'-new.jar',shell=True)
    call(home+'/tool/dex2jar-0.0.9.15/d2j-jar2dex.sh -f -o '+tmp+project_name+'/classes.dex '+tmp+project_name+'-new.jar',shell=True)
    call('zip -r '+tmp+project_name+'-new.apk -j '+tmp+project_name+'/classes.dex',shell=True)
    global sign_file 
    sign_file = tmp+project_name+'-new.apk'
    print 'Done'  

def sign():
  print "*********************************************"
  print "**                Sign apk                 **"
  print "*********************************************"
  call(home+'/tool/dex2jar-0.0.9.15/d2j-apk-sign.sh -f -o '+tmp+project_name+'-signed.apk '+sign_file,shell=True)

def main():
  global apk_folder,apk_file,project_name,home
  usage = "usage: %prog action file [options]"
  parser = OptionParser(usage=usage)
  parser.add_option("--java",action="store_true", dest="java", default=True, help="select java source format [DEFAULT]")
  parser.add_option("--smali",action="store_true", dest="smali", default=False, help="select smali source format")
  parser.add_option("--jasmin",action="store_true", dest="jasmin", default=False, help="select jasmin source format")
  parser.add_option("--no-source",action="store_true", dest="nosc", default=False, help="no source code generation")
  (options, args) = parser.parse_args()

  if home == "/opt/apk2java":
    if check_home(home) == False:
      getunzipped(external, home, report)
  else:
    if check_home(home) == False and check_home("/opt/apk2java") == False:
      getunzipped(external, "/opt/apk2java", report)
      home = "/opt/apk2java"

  exit(0)

  if (options.smali+options.jasmin+options.nosc) > 1:
    print "[ ERROR ] You can only select 1 source format --[smali/jasmin/java/no-source]"
    exit(1)
  if len(args)==2:
    if args[0] == 'd':
      if os.path.isfile(args[1]) and os.path.splitext(args[1])[-1].lower() == '.apk':
        apk_file = args[1]
        project_name = os.path.splitext(os.path.basename(args[1]))[0].lower()
        call("cp "+apk_file+" "+tmp+project_name+"-new.apk",shell=True)
        if options.jasmin == True:
          dex2jar()
          jar2jasmin()
        else:
          apktool(options.smali)
          if options.smali == False and options.nosc == False:
            dex2jar()
            procyon()
      else:
        print "[ ERROR ] You must select a valid APK file!"
        exit(1)
    elif args[0] == 'b':
      if os.path.isdir(args[1]):
        apk_folder = args[1]
        project_name = os.path.basename(os.path.dirname(args[1]).lower())
        print project_name
        if options.jasmin == True:
          jasmin_build()
        elif options.smali == True:
          apktool_build()
        else:
          print "[ ERROR ] Can't build apk with that source format. Only Jasmin or Smali supported"
        sign()
    else:
      parser.error("action can be only 'b' (build) or 'd' (decompile)")
  else:
    parser.print_help()

# Script start Here
if __name__=="__main__":
  main() 
  