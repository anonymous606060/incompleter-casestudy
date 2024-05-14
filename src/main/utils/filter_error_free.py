import os, sys
from subprocess import Popen, PIPE

from glob import glob

count = 0
for file in glob('../../../data/lexecutor_fail/*.py.orig'):
    count += 1
    proc = Popen(['python3', file], stdout=PIPE, stderr=PIPE)
    proc.wait()
    out, err = proc.communicate()

    if len(err) == 0:
        proc = Popen(['mv', file.replace('.orig', ''), '../../../data/lexecutor_fail/originally_runs_error_free/'])
        proc.wait()
        proc = Popen(['mv', file, '../../../data/lexecutor_fail/originally_runs_error_free/'])
        proc.wait()

