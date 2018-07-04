
def rangefloat(start, end, num=50, forever=False):
    num = int(num)
    step = (end - start)/num
    for i in (start+step*i for i in range(num)):
        yield i
    while forever is True:
        yield end