class testclass:
    message='hello'
    data={'data1':'DATA ONE'}

    def __init__(self):
        self.r=2

    def say(self,name):
        print('%s, %s' % (name, self.message))
    def __getitem__(self, item):
        return self.data[item]

    @property
    def area(self):
        return self.r * self.r

    @area.setter
    def area(self, value):
        self.r=value

    @area.deleter
    def area(self):
        print("Killed")


t = testclass()
setattr(t, 'data1', 'DATA1 value')
print( t['data1'] )
print(t.data1)
t.data1='abc'
print(t.data1)

print(t.area)
t.area = 3
print(t.area)

del t
