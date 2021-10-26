import sys
from commands import commands
from workflow import Workflow

def main(wf):
  query = sys.argv
  requested_command = query[2] + ' ' + query[3]
  commands[requested_command]['handler'](wf, query)

if __name__ == u"__main__":
  wf = Workflow()
  sys.exit(wf.run(main))
