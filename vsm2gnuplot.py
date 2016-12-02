import sys
import fileinput

def main():
    data = []
    for line in fileinput.input(): # read from stdin or file
        data.append(line)
    for datum in data[1:]:
        # extract name, ms, hc, hk
        dspl = datum.split('|')
        name = dspl[0].strip()
        ms = float(dspl[1].strip())
        hc = float(dspl[2].strip())
        hk = float(dspl[3].strip())
        print(writegplot(name, ms, hc, hk))
        # write gnuplot file using those
        return None

def writegplot(fname, ms, hc, hk):
    r = 'set term x11 \n'
    drawline = 'set arrow from {:f}, {:f} to {:f}, {:f} nohead'
    r += drawline.format(-hk, -ms, hk, ms) + '\n'
    r += drawline.format(-hc, -ms, -hc, ms) + '\n'
    r += drawline.format(hc, -ms, hc, ms) + '\n'
    r += 'plot "{:s}" with linespoints'.format(fname) + '\n'
    r += 'replot' + '\n'
    return r
    

if __name__ == '__main__':
    main()

