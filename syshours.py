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

# TODO: implement choosing block support; implement choosing dates support; docstrings; fix odd ordering in output

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

def date_to_str(date):
  return date.strftime("%m/%d/%y")

def get_today_str():
  return date_to_str(get_today())

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
    d = kwargs.get('date')
    if not d: d = get_today_str()

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
      t = kwargs.get('time')
      if not t: t = time_to_str(round_to_15_min(get_now()))
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
    print "subtotal: {hrs}\n\n".format(hrs=seconds_to_str(self.subtotalSeconds))

  def printReport(self):
    self.printHeader()
    for wr in self.report:
      self.printWeekReport(wr)
    self.printFooter()

########################
#### main functions ####
########################

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

def leave(**kwargs):
  write_entry('leave', **kwargs)

def update(**kwargs):
  write_entry('update', **kwargs)

def getDefaultDateList():
  cur_date = get_today()
  return [[date_to_str(cur_date - datetime.timedelta(days=j*7 + i)) for i in range(7)][::-1] for j in range(2)][::-1]

def print_log(**kwargs):
  # get list of dates
  dl = getDefaultDateList()

  # get log
  f = kwargs.get('file')
  if not f: raise SysHoursError('Must supply filename')
  yamler = Yamler(f)
  log = yamler.load()

  # make report for to print
  report = []
  for w in dl:
    r = {}
    for d in w:
      e = log.get(d)
      if e:
        r[d] = e
    if r:
      report.append(r)

  # print it
  p = Printer(report)
  p.printReport()

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
  parser_update = subparsers.add_parser('update')
  parser_print = subparsers.add_parser('print')

  parser_arrive.set_defaults(func=arrive)
  parser_leave.set_defaults(func=leave)
  parser_update.set_defaults(func=update)
  parser_print.set_defaults(func=print_log)

  for p in (parser_arrive, parser_update, parser_leave, parser_print):
    p.add_argument('file', help="autolog.yaml file location. This argument is required.")

  parser_update.add_argument('message', help="message to write to the log. This argument is required.")

  for p in (parser_arrive, parser_leave):
    p.add_argument('-m', '--message', help="message to write to the log.")
    p.add_argument('-t', '--time', help="time in 24-hour HH:MM format. Rounded to the nearest 15 minutes. Defaults to current time.")

  for p in (parser_arrive, parser_update, parser_leave):
    p.add_argument('-d', '--date', help="date in MM/DD/YY format. Defaults to today.")
    p.add_argument('-b', '--block', help="block number in the log. Defaults to latest block.")

  parser_print.add_argument('-d', '--date', help="list of dates in MM/DD/YY format. If not given, defaults to last 14 days. Dates must be separated with a comma. Ranges may be specified with a dash. E.g.: 12/01/90,12/04/90-01/04/91 **NOTE**: this is not yet implemented. Only default dates can be used currently.")

  args = parser.parse_args()
  args.func(**vars(args))

  exit(0)
