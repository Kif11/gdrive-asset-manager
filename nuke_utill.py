import os
import simplejson

external_paths = []

for node in nuke.allNodes('Read'):
    external_paths.append(node.knob('file').value())

print external_paths

file = os.path.join(nuke.script_directory(), '.dependencies')

with open(file, 'wb') as f:
    simplejson.dump(external_paths, f)

with open(file, 'rb') as f:
    print simplejson.load(f)
