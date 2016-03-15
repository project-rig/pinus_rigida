#############################################################
#
# Animate Sudoku spikes output file
# Steve Furber, November 2015
#
#############################################################

import numpy
import pylab
import matplotlib.animation as animation
from   matplotlib.patches import Rectangle

# read in params & spikes file

fp       = open('sudoku_spikes')

params   = numpy.load(fp)
run_time = params[0]                                    # run time in ms
n_cell   = params[1]                                    # number of neurons per cell
n_N      = n_cell/9                                     # number of neurons per value in cell

p_bin    = 200                                          # size of probability bin, ms
n_P      = run_time/p_bin                               # number of probability bins, each 100ms

cumulative = True                                       # accumulate probabilites over entire run
cum_decay  = 0.97                                       # decay rate for old cumulative contributions

init     = numpy.load(fp)                               # initial sudoku state. NB use as init[8-y][x] -> cell[x][y]
corr     = numpy.load(fp)                               # solution.             NB use as corr[8-y][x] -> cell[x][y]

spikes   = [[[] for x in range(9)] for y in range(9)]
for y in range(9):
    for x in range(9):
        spikes[x][y] = numpy.load(fp)                   # spike records

#
# process spikes into p(N) for each N for each cell, for each time bin
#

p = [[[[0.0 for j in range(9)] for i in range(n_P)] for y in range(9)] for x in range(9)]

for x in range(9):
    for y in range(9):
        for i in spikes[x][y]: p[x][y][int(i[1]/p_bin)][int(i[0]/n_N)] += 1.0       # count spikes in each bin

        if cumulative:                                                              # make probabilities cumulative ?
            for j in range(9):
                for i in range(n_P-1): p[x][y][i+1][j] += p[x][y][i][j] * cum_decay

        for i in range(n_P):                                                        # normalise probability bins
            p_tot = sum(p[x][y][i])
            for j in range (9): p[x][y][i][j] = p[x][y][i][j]/p_tot

#
# find most likely digit in each cell at each bin time & compute entropy
#

p_max = [[[[0,0.0] for i in range(n_P)] for y in range(9)] for x in range(9)]

H       = [0.0 for i in range(n_P)]
bits    = 1/numpy.log(2.0)              # for conversion to log2
max_ent = 9*9*numpy.log(9.0)*bits       # maximum possible entropy - all nos equally likely

for i in range(n_P):
    for x in range(9):
        for y in range(9):
            for j in range(9):
                if p[x][y][i][j] > p_max[x][y][i][1]: p_max[x][y][i] = [j+1, p[x][y][i][j]]     # most likely digit
                if p[x][y][i][j] > 0.0: H[i] += -p[x][y][i][j]*numpy.log(p[x][y][i][j])*bits    # entropy

#
# check for consistent solution
#

AllCorr  = [True for i in range(n_P)]
CellCorr = [[[True for i in range(n_P)] for y in range(9)] for x in range(9)]

def checkCell(i, x, y, r, c):
    val = p_max[x][y][i][0]
    if val == p_max[r][c][i][0]:
        AllCorr[i]        = False
        CellCorr[x][y][i] = False
    return

for i in range(n_P):
    for x in range(9):
        for y in range(9):
            for r in range(9):                                      # check row
                if r != x: checkCell(i, x, y, r, y)
            for c in range(9):                                      # check column
                if c != y: checkCell(i, x, y, x, c)
            for r in range(3*(x//3),3*(x//3+1)):
                for c in range(3*(y//3),3*(y//3+1)):                # check square
                    if r != x and c != y: checkCell(i, x, y, r, c)

#
# plot entropy vs time
#

fig1 = pylab.figure()
pylab.xlabel("Time (ms)")               # label plot
pylab.ylabel("Entropy (bits)")
pylab.axis([0, run_time, 0, max_ent])

for i in range(n_P):
    pylab.plot((i+0.5)*p_bin, H[i], "b." if AllCorr[i] else "r.")  # check whether correct solution found

pylab.savefig("Entropy.png")            # save plot

#
# generate the Sudoku movie
#

fig2 = pylab.figure()
pylab.axis([0, 1, 0, 1])
ax   = pylab.gca()
ax.add_patch(Rectangle((0,0), 1, 1, facecolor='white')) # background colour
ax.set_xticklabels([])
ax.set_yticklabels([])

for i in range(10):                                     # draw Sudoku lines
    if i%9==0: lw = 10
    else:      lw = 5 if i%3==0 else 2
    pylab.plot([i/9.0, i/9.0], [0, 1], 'o-', color='k', lw=lw)
    pylab.plot([0, 1], [i/9.0, i/9.0], 'o-', color='k', lw=lw)

cells = [[[] for x in range(9)] for y in range(9)]      # put digit in each cell
for x in range(9):
    for y in range(9):
        cells[x][y] = pylab.text(0.025+x/9.0, 0.035+y/9.0, " "+str(corr[x][y])+" ", color='blue',
                fontsize=20, fontweight='bold', bbox=dict(facecolor='white', edgecolor='white'))

def update(i):                                          # animation process per time step
    for x in range(9):
        for y in range(9):
            num = p_max[x][y][i][0]
            sat = 1-p_max[x][y][i][1]
            cells[x][y].set_text(" "+str(num)+" ")
            if not CellCorr[x][y][i]: cells[x][y].set_color((1,sat,sat))  # incorrect cell - red
            elif init[8-y][x] != 0:   cells[x][y].set_color('grey')       # initialised cell - grey
            else:                     cells[x][y].set_color((sat,1,sat))  # correct cell - green
    return cells

ani = animation.FuncAnimation(fig2, update, numpy.arange(1, n_P), interval=p_bin, blit=False, repeat=False)
#ani.save('sudoku.mp4')
pylab.show()
