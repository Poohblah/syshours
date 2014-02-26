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

######################################
#### FORMATTING FOR E-MAIL OUTPUT ####
######################################

error_message = "Warning: some log entries incomplete; total hours may be inaccurate"

outputstr_template = """
This e-mail has been automagically generated from a log file. If there
are any errors or problems with this output, please feel free to harrass
the sender who forgot to double-check their log file.

date    hours   tasks
----    -----   -----
{block}{total}
"""

blockstr_template = """\
{taskstr}{subtotal}

"""

taskstr_template = "{datestr:<8}{hoursstr:<8}{tasksstr:<8}"

tasksstr_width=55

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
  def __init__(self, entries):
    pass

  def setDates(self, days):
    pass

  def calculateTotalSeconds(self):
    pass

  def printHeader(self):
    pass

  def printFooter(self):
    pass

  def printDayReport(self):
    pass

  def printWeekReport(self):
    pass

  def printReport(self):
    pass

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

#########################################
#### functions for formatting output ####
#########################################

# def getTotalSeconds(arrivestr, leavestr):
#   # sanity checks
#   if not arrivestr or not leavestr:
#     return None
# 
#   # first convert string representations of time to time objects
#   arrivetime, leavetime = str_to_time(arrivestr), str_to_time(leavestr)
# 
#   # get a timedelta object (requires a date object and a time object)
#   today = date.today()
#   td = datetime.combine(today, leavetime) - datetime.combine(today, arrivetime)
# 
#   # return the total seconds  
#   return td.total_seconds()
# 
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
#       for entry in log_list:
#         # don't print the date for subsequent entries in a single day
#         if log_list.index(entry) == 0:
#           printable_datestr = datestr[:5] # (so we don't get the year as well)
#         else:
#           printable_datestr = ''
# 
#         # get the total seconds of the entry
#         secs = getTotalSeconds(entry['arrive'], entry['leave'])
# 
#         # error catching
#         if secs is None:
#           secs = 0
#           error = True
# 
#         subtotal_total_seconds += secs
# 
#         printable_hoursstr = seconds_to_str(secs)
# 
#         # format the "tasks" bit
#         # printable_tasksstr = "\n                ".join(textwrap.wrap(entry['description'], width=55))
#         taskstr_list = textwrap.wrap(entry['description'], width=tasksstr_width)
#         str = "\n".join([taskstr_template.format(datestr=printable_datestr, hoursstr=printable_hoursstr, tasksstr=ts) if taskstr_list.index(ts) == 0 else taskstr_template.format(datestr='', hoursstr='', tasksstr=ts) for ts in taskstr_list]) + "\n\n" # did I just abuse list comprehension? 
# 
#         entrystr += str
# 
#       # ok, now let's get out of that horrendous for loop... two levels left to go
#       blockstr += entrystr
# 
#     # one level left to go
#     total_total_seconds += subtotal_total_seconds
#     subtotal_str = "subtotal: {hrs}".format(hrs=seconds_to_str(subtotal_total_seconds))
#     printable_blockstr = blockstr_template.format(taskstr=blockstr, subtotal=subtotal_str)
#     raw_blocks_str += printable_blockstr
# 
#   # ...and we're out! let's format the final output
#   total_str = "total: {hrs}".format(hrs=seconds_to_str(total_total_seconds))
#   output_str = outputstr_template.format(block=raw_blocks_str, total=total_str)
# 
#   # finally!!
#   print output_str
# 
#   if error:
#     print "{msg}".format(msg=error_message)

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
