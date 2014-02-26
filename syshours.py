#!/usr/bin/env python

import os
import copy
import datetime
import textwrap
import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

##########################
#### global variables ####
##########################

prog_description = "Log your hours, you lazy bum."

##########################
#### helper functions ####
##########################

def str_to_time(str):
  return datetime.datetime.strptime(str, '%H:%M').time()

def time_to_str(time):
  return time.strftime('%H:%M')

def round_to_15_min(time):
  time += datetime.timedelta(minutes=7, seconds=30)
  time -= datetime.timedelta(minutes=time.minute%15,
                             seconds=time.second,
                             microseconds=time.microsecond)
  return time

def get_now():
  return datetime.datetime.now()

def get_today():
  return datetime.datetime.today()

def get_today_str():
  return get_today().strftime("%m/%d/%y")

def seconds_to_str(secs):
  hours, minutes = divmod(int(secs) / 60, 60)
  return '{hr}:{min:02}'.format(hr=hours, min=minutes)

def get_total_seconds(arrivestr, leavestr):
  # sanity checks
  if not arrivestr or not leavestr:
    return None

  # first convert string representations of time to time objects
  arrivetime, leavetime = str_to_time(arrivestr), str_to_time(leavestr)

  # get a timedelta object (requires a date object and a time object)
  today = get_today()
  td = datetime.datetime.combine(today, leavetime) - datetime.datetime.combine(today, arrivetime)

  # return the total seconds  
  return td.total_seconds()

###################################
#### class for throwing errors ####
###################################

class SysHoursError(Exception):
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value)

################################################
#### class for writing & reading yaml files ####
################################################

class Yamler:
  def __init__(self, filename):
    self.filename = filename

  def load(self):
    file = open(self.filename)
    data = yaml.load(file, Loader=Loader)
    if not data: data = {}
    file.close()
    return data
  
  def write(self, data):
    file = open(self.filename, 'w')
    output = yaml.dump(data, default_flow_style=False, Dumper=Dumper)
    file.write(output)
    file.close()

######################
#### logger class ####
######################

class Log:
  def __init__(self, log={}):
    self.setLog(log)
    self.blockSkeleton = {
      'arrive'      : '',
      'leave'       : '',
      'description' : ''
      }

  def setLog(self, log):
    self.log = log

  def createBlock(self, dateBlocks, block=None):
    if block is None:
      block = copy.deepcopy(self.blockSkeleton)
    dateBlocks.append(block)

  def getBlocks(self, datestr=get_today_str()):
    result = self.log.get(datestr)
    if not result:
      result = []
      self.createBlock(result)
      self.log[datestr] = result
    return result

  def writeDescription(self, block, desc):
    m = block.get('description')
    if m:
      m += "; "
    else:
      m = ''
    m += desc
    block['description'] = m

  def writeEntry(self, method, **kwargs):

    # throw error if invalid log type
    if not method in ['arrive', 'leave', 'update']:
      raise SysHoursError('invalid log method: %s' % method)

    # set the date to today if not given
    d = kwargs.get('date', get_today_str())

    # create a new block or use the most recent one
    blocks = self.getBlocks()
    e = blocks[-1]

    # set the time if arrive or leave
    if method in ['arrive', 'leave']:

      # create a new block if necessary
      if e[method]:
        self.createBlock(blocks)
        e = blocks[-1]

      # set the time to now if not given
      t = kwargs.get('time', time_to_str(round_to_15_min(get_now())))
      e[method] = t

    # append to the end of the description or create a new one
    m = kwargs.get('message')
    if m:
      self.writeDescription(e, m)

  def arrive(self, **kwargs):
    self.writeEntry('arrive', **kwargs)

  def leave(self, **kwargs):
    self.writeEntry('leave', **kwargs)

  def update(self, message, **kwargs):
    self.writeEntry('update', message=message, **kwargs)

#################################
#### class for printing logs ####
#################################

class Printer:
  '''
  Printer expects a log in the following format:

  [
    {
      'MM/DD/YYYY':
        [
          {
            'arrive': 'HH:MM'
            'description': 'description'
            'leave': 'HH:MM'
          },
          ...
        ],
      ...
    }
    ...
  ]
  '''

  #### FORMATTING FOR PRINTING OUTPUT ####
  
  error_message = "Warning: some log entries incomplete; total hours may be inaccurate"
  
  header_template = """
This e-mail has been automagically generated from a log file. If there
are any errors or problems with this output, please feel free to harrass
the sender who forgot to double-check their log file.

date    hours   tasks
----    -----   -----
"""
  
  blockstr_template = """\
  {taskstr}{subtotal}
  
  """
  
  taskstr_template = "{datestr:<8}{hoursstr:<8}{tasksstr:<8}"
  
  tasksstr_width=55

  #### CLASS METHODS ####

  def __init__(self, report):
    self.totalSeconds = 0
    self.subtotalSeconds = 0
    self.report = report
    self.error = False

  def printHeader(self):
    print Printer.header_template

  def printFooter(self):
    print ''
    print "total: {hrs}".format(hrs=seconds_to_str(self.totalSeconds))
    if self.error:
      print ''
      print Printer.error_message

  def printDayReport(self, datestr, day_report):
    for entry in day_report:

      # get description
      desc = entry.get('description')
      if not desc: desc = 'n/a' # hack to get textwrap to behave

      # get date if necessary
      printable_datestr = ''
      if day_report.index(entry) == 0:
        printable_datestr = datestr[:5] # so we don't get the year as well

      # get the total seconds
      secs = get_total_seconds(entry['arrive'], entry['leave'])
      printable_hoursstr = 'n/a'
      if secs is None:
        self.error = True
      else:
        printable_hoursstr = seconds_to_str(secs)
        self.subtotalSeconds += secs

      # print formatted string
      taskstr_list = textwrap.wrap(desc, width=Printer.tasksstr_width)
      print "\n".join([Printer.taskstr_template.format(datestr=printable_datestr, hoursstr=printable_hoursstr, tasksstr=ts) if taskstr_list.index(ts) == 0 else Printer.taskstr_template.format(datestr='', hoursstr='', tasksstr=ts) for ts in taskstr_list]) + "\n"

  def printWeekReport(self, weekReport):
    self.subtotalSeconds = 0
    for datestr, dayReport in weekReport.iteritems():
      self.printDayReport(datestr, dayReport)
    self.totalSeconds += self.subtotalSeconds
    print "subtotal: {hrs}".format(hrs=seconds_to_str(self.subtotalSeconds))

  def printReport(self):
    self.printHeader()
    for wr in self.report:
      self.printWeekReport(wr)
    self.printFooter()

#########################################
#### functions for formatting output ####
#########################################

# def printLog(file_name):
#   # first thing's first. let's get a list of the blocks of dates we're printing
#   # blocklist = [["11/11/13","11/12/13","11/13/13","11/14/13","11/15/13"],["11/18/13","11/19/13","11/20/13","11/21/13","11/22/13"]]
#   blocklist = [["02/03/14","02/04/14","02/05/14","02/06/14","02/07/14"],["02/10/14","02/11/14","02/12/14","02/13/14","02/14/14"]]
# 
#   # open the log file
#   loadLog(file_name)
# 
#   # before we do anything, write cur_log if there is one still hanging about
#   writeCurLog()
# 
#   # okay, we're ready to start printing the log...
#   error = False
#   total_total_seconds = 0
#   raw_blocks_str = ''
# 
#   for block in blocklist:
#     subtotal_total_seconds = 0
#     blockstr = ''
# 
#     for datestr in block:
#       # sanity check
#       log_list = log['entries'].get(datestr)
#       if not log_list:
#         log_list = []
#       entrystr = ''
#       # log_list = log['entries'][datestr]
# 
# 
#       # ok, now let's get out of that horrendous for loop... two levels left to go
#       blockstr += entrystr
# 
#     # one level left to go
#     total_total_seconds += subtotal_total_seconds
#     printable_blockstr = blockstr_template.format(taskstr=blockstr, subtotal=subtotal_str)
#     raw_blocks_str += printable_blockstr
# 
#   # ...and we're out! let's format the final output
#   output_str = outputstr_template.format(block=raw_blocks_str, total=total_str)
# 
#   # finally!!
#   print output_str
# 
#   if error:
#     print "{msg}".format(msg=error_message)

############################################################
#### functions for creating log entries from user input ####
############################################################

def write_entry(type, **kwargs):
  f = kwargs.get('file')
  if not f: raise SysHoursError('Must supply filename')
  yamler = Yamler(f)
  log = yamler.load()
  sl = Log(log)
  getattr(sl, type)(**kwargs)
  yamler.write(sl.log)

def arrive(**kwargs):
  write_entry('arrive', **kwargs)
  return

def leave(**kwargs):
  write_entry('leave', **kwargs)
  return

def update(**kwargs):
  write_entry('update', **kwargs)
  return

def print_log(args):
  print 'print function'
  return

def view_log(args):
  print 'view function'
  
  # parse dates

  # iterate over dates
  return

def help():
  print 'help function'
  return

##############
#### MAIN ####
##############

if __name__ == "__main__":

  import argparse

  parser = argparse.ArgumentParser(description=prog_description)
  subparsers = parser.add_subparsers(title="commands",
                                     help="COMMAND --help to show help for COMMAND")

  parser_arrive = subparsers.add_parser('arrive')
  parser_leave = subparsers.add_parser('leave')
  parser_print = subparsers.add_parser('print')
  parser_view = subparsers.add_parser('view')

  parser_arrive.set_defaults(func=arrive)
  parser_leave.set_defaults(func=leave)
  parser_print.set_defaults(func=print_log)
  parser_view.set_defaults(func=view_log)

  for p in (parser_arrive, parser_leave, parser_print, parser_view):
    p.add_argument('file', help="autolog.yaml file location. This argument is required.")

  for p in (parser_arrive, parser_leave):
    p.add_argument('-m', '--message', help="message to write to the log. This argument is required.")
    p.add_argument('-t', '--time', help="time in 24-hour HH:MM format. Rounded to the nearest 15 minutes. Defaults to current time.")
    p.add_argument('-d', '--date', help="date in MM/DD/YY format. Defaults to today.")
    p.add_argument('-b', '--block', help="block number in the log. Defaults to latest block.")

  for p in (parser_print, parser_view):
    p.add_argument('-d', '--date', help="list of dates in MM/DD/YY format. If not given, defaults to last 14 days. Dates must be separated with a comma. Ranges may be specified with a dash. E.g.: 12/01/90,12/04/90-01/04/91")

  args = parser.parse_args()
  args.func(vars(args))

  exit(0)
