import json
__author__ = 'chywoo.park'


f = open("./jsondata.txt", "r")
js = json.loads(f.read())
f.close()

print( js['release'] )
print( js['release']['userid'] )
print( js['release']['repos'] )
