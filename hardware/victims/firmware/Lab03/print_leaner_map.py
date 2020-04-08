for i in range(16):
    upper = '{:x}'.format((i+3)%16)
    for j in range(16):
        lower = '{:x}'.format((j+5)%16)
        print "0x"+upper+lower+"," ,
    print "\n" ,
