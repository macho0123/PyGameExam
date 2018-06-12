import sys, os

import pygame, numpy as np, pyaudio
from pygame.locals import *
import time
import ctypes

print(pygame.version.ver)

start = time.time()
time.clock()   

noteMinUser = 55  # G4
NOTE_MAX = 90  # G7
NOTE_MIN = noteMinUser - 10
FSAMP = 22050       # Sampling frequency in Hz
FRAME_SIZE = 1024   # How many samples per frame?
FRAMES_PER_FFT = 8  # FFT takes average across how many frames?
num_frames = 0

######################################################################
# Derived quantities from constants above. Note that as
# SAMPLES_PER_FFT goes up, the frequency step size decreases (so
# resolution increases); however, it will incur more delay to process
# new sounds.

SAMPLES_PER_FFT = FRAME_SIZE * FRAMES_PER_FFT
FREQ_STEP = float(FSAMP) / SAMPLES_PER_FFT

######################################################################
# For printing out notes

NOTE_NAMES = 'C C# D D# E F F# G G# A A# B'.split()

Gstring = 'G4 G#4 A4 A#4 B4 C4 C#4 D4'.split()
Dstring = 'D4 D#4 E4 F4 F#4 G5 G#5 A5'.split()
Astring = 'A5 A#5 B5 C5 C#5 D5 D#5 E5'.split()
Estring = 'E5 F5 F#6 G6 G#6 A6 A#6 B6'.split()
strings = [Gstring, Dstring, Astring, Estring]

fretPosition = '150,20 160,30'.split()


######################################################################
# These three functions are based upon this very useful webpage:
# https://newt.phys.unsw.edu.au/jw/notes.html

def freq_to_number(f): return 69 + 12*np.log2(f/440.0)
def number_to_freq(n): return 440 * 2.0**((n-69)/12.0)
def note_name(n):      return NOTE_NAMES[n % 12] + str(round(n/12 - 1))

######################################################################
# Ok, ready to go now.

# Get min/max index within FFT of notes we care about.
# See docs for numpy.rfftfreq()
def note_to_fftbin(n):
    return number_to_freq(n) / FREQ_STEP


imin = max(0, int(np.floor(note_to_fftbin(NOTE_MIN - 1))))
imax = min(SAMPLES_PER_FFT, int(np.ceil(note_to_fftbin(NOTE_MAX + 1))))

#allocate space for buffer
buf = np.zeros(SAMPLES_PER_FFT, dtype=np.float32)

# Initialize audio
stream = pyaudio.PyAudio().open(format=pyaudio.paInt16,
                                channels=1,
                                rate=FSAMP,
                                input=True,
                                frames_per_buffer=FRAME_SIZE)

stream.start_stream()


#Hanning window function ( zero-valued outside of some chosen interval.)
#window = 0.5 * (1 - np.cos(np.linspace(0, 2 * np.pi, SAMPLES_PER_FFT, False)))


def getPitchData():

    global num_frames
    # shift the buffer down and new data in
    buf[:-FRAME_SIZE] = buf[FRAME_SIZE:]
    buf[-FRAME_SIZE:] = np.fromstring(stream.read(FRAME_SIZE), np.int16)

    fft = np.fft.rfft(buf)

    # get maximum frequency response in given range
    freq = (np.abs(fft[imin:imax]).argmax() + imin) * FREQ_STEP

    n = freq_to_number(freq)
    n0 = int(round(n))
    nC = round(n - n0, 2)

    num_frames += 1
    if num_frames >= FRAMES_PER_FFT:
      if (n0>noteMinUser):
        return note_name(n0)  # return n-n0 for cents (means accuracy measure) or use nC?

# /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#                                                   PYGAME STARTS HERE
# /////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


display_width = 800
display_height = 600
clock = pygame.time.Clock()

# Color schemes
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 255, 255)
darkBlue = (0, 0, 128)
white = (255, 255, 255)
black = (0, 0, 0)
purple = (42, 44, 206)
pink = (255, 200, 200)

stringToColor = [black, red, blue, white]


# Global variables
playerLocationX = 100
playerLocationY = 200

noteLocationX = 90 # span of one fret, needs to be multiplied by fret number
noteLocationY = 10 
indicatorLocationY = 570

indicatorWidth = 80
indicatorHeight = 21

notesToPlay = []
song = ""
currentNote = -1
BPMfactor = 0.35

class Note:

    def __init__(self, fret, string):

        if (fret!=0):
          self.rect = pygame.rect.Rect((-10 + noteLocationX*fret, noteLocationY, indicatorWidth, indicatorHeight*2))
          self.string = string
        else:
          self.rect = pygame.rect.Rect((50 + noteLocationX*fret, noteLocationY, 10, indicatorHeight*2))
          self.string = string

    def moveUp(self):
        self.rect.move_ip(0, -10)
        pygame.draw.rect(screen, (stringToColor[self.string]), self.rect)

    def moveDown(self):
        self.rect.move_ip(0, 10)
        pygame.draw.rect(screen, (stringToColor[self.string]), self.rect)

    def moveRight(self):
        self.rect.move_ip(10, 0)
        pygame.draw.rect(screen, (stringToColor[self.string]), self.rect)

    def moveLeft(self):
        self.rect.move_ip(-10, 0)
        pygame.draw.rect(screen, (stringToColor[self.string]), self.rect)

    def idle(self):
        pygame.draw.rect(screen, (stringToColor[self.string]), self.rect)


# Class Button
class Button:
    def __init__(self, img_in, x, y, width, height, img_act, x_act, y_act, action=None):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if x + width > mouse[0] > x and y + height > mouse[1] > y:
            screen.blit(img_act, (x_act, y_act))
            if click[0] and action is not None:
                time.sleep(2)
                action()
        else:
            screen.blit(img_in, (x, y))


def indicatePosition(fret, string):

    global indicator

    if (fret > 0):
        indicator = pygame.Surface((indicatorWidth, indicatorHeight), pygame.SRCALPHA)  # per-pixel alpha
        indicatorHitbox = pygame.rect.Rect(-10 + noteLocationX*fret, indicatorLocationY - string*(indicatorHeight + 7 - string/1.5), indicatorWidth, indicatorHeight)
        indicator.fill((255, 255, 255, 128))  # notice the alpha value in the color (use colorkey, should be faster)
        screen.blit(indicator, indicatorHitbox)
        testCollision(indicatorHitbox, string)

    if (fret == 0):
        indicator = pygame.Surface((10, indicatorHeight), pygame.SRCALPHA)  # per-pixel alpha
        indicatorHitbox = pygame.rect.Rect(50 + noteLocationX*fret, indicatorLocationY - string*(indicatorHeight + 7 - string/1.5), 10, indicatorHeight*3) 
        indicator.fill((255, 255, 255, 128))  # notice the alpha value in the color
        screen.blit(indicator, indicatorHitbox)
        testCollision(indicatorHitbox, string)


def text_objects(text, font):
    textSurface = font.render(text, True, white)
    return textSurface, textSurface.get_rect()


def testCollision(indicator, string):
    i = 0
    while i < len(notesToPlay):
      if (notesToPlay[i].string == string):
        if (notesToPlay[i].rect.colliderect(indicator)):
          notesToPlay.pop(i)
      i += 1


def message_display(text):
    x = (display_width / 2)
    y = (display_height / 2)

    largeText = pygame.font.SysFont('Arial', 15, white)
    TextSurf, TextRect = text_objects(text, largeText)
    TextRect.center = (x, y)
    screen.blit(TextSurf, TextRect)

def getNextNote():

  global currentNote

  currentNote += 1
  try:
    return song[currentNote]  #as a string
  except:
    print("Song done")

def update(dt):

    global indicator
    global start
    global BPMfactor

    # Astring = 'A5 A#5 B5 C5 C#5 D5 D#5 E5'.split()

    note = getPitchData()

    for string in strings:
        #stringNum = strings.index(string)
        if (note in string):
            stringNum = strings.index(string)
            fret = string.index(note)
            indicatePosition(fret, stringNum)

    if (time.time() - start > BPMfactor): #calls the function every second (change number to some kind of BPM?)
      start = time.time()
      fileNote = getNextNote()
      for string in strings:
        if (fileNote in string):
          
          stringNum = strings.index(string)
          fret = string.index(fileNote)
          if (fret==7):  #very very dirty way of doing this
              fret=0
              print("I changed fret")
          notesToPlay.append(Note(fret,stringNum))
          print(fileNote)
          print(fret)
          print(stringNum)


    for event in pygame.event.get():

        if event.type == QUIT:
            pygame.quit()
            sys.exit()  

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                songNote = Note(0, 0)
                notesToPlay.append(songNote)
            if event.key == pygame.K_RIGHT:
                songNote = Note(1, 1)
                notesToPlay.append(songNote)
            if event.key == pygame.K_DOWN:
                songNote = Note(2, 2)
                notesToPlay.append(songNote)
            if event.key == pygame.K_UP:
                songNote = Note(3, 3)
                notesToPlay.append(songNote)


def draw(screen):
    """
  Draw things to the window. Called once per frame.
  """
    # Redraw screen here.
    note = getPitchData()
    message_display(note)

    pygame.draw.circle(screen, white, (300,540), 10) # Here <<<
    pygame.draw.circle(screen, white, (480,540), 10) # Here <<<

    i = 0
    while i < len(notesToPlay):
        # print(notesToPlay[i].rect)
        notesToPlay[i].moveDown()
        i = i + 1

    # Flip the display so that the things we drew actually show up.
    pygame.display.flip()


def quitGame():
    pygame.quit()
    quit()


# MainMenu
def mainmenu():
    menu = False

    while menu:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        screen.fill(purple)

        titletext = screen.blit(titleImg, (275, 200))
        startButton = Button(startImg, 280, 260, 60, 20, clickStartImg, 273, 258, runPyGame)
        quitButton = Button(quitImg, 475, 260, 60, 20, clickQuitImg, 470, 258, quitGame)

        pygame.display.update()
        clock.tick(15)


def runPyGame():

    global song

    #init the song (move to menu for multi-song support)
    file = open("JurrasicPark.txt","r")
    for line in file:
      line = line.rstrip('\n')
      song = song + line
    file.close()
    print("Your song is: " + file.name)
    print(song)
    song = song.split(" ")

    # Initialise PyGame.
    pygame.init()

    # init object
    # Note("X1", 4, 4)

    # Set up the clock. This will tick every frame and thus maintain a relatively constant framerate. Hopefully.
    fps = 60.0
    fpsClock = pygame.time.Clock()

    # Set up the window.
    # screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    # screen is the surface representing the window.
    # PyGame surfaces can be thought of as screen sections that you can draw onto.
    # You can also draw surfaces onto other surfaces, rotate surfaces, and transform surfaces.

    # Main game loop.
    dt = 1 / fps  # dt is the time since last frame.
    while True:  # Loop forever!

        # screen.fill((0, 0, 0)) # Fill the screen with black.
        screen.blit(background_image, [0, 0])
        update(dt)  # You can update/draw here, I've just moved the code for neatness.
        draw(screen)
        dt = fpsClock.tick(fps)


screen = pygame.display.set_mode((display_width, display_height))
background_image = pygame.image.load("images/background1.png").convert()
startImg = pygame.image.load("images/starticon.png")
quitImg = pygame.image.load("images/quiticon.png")
titleImg = pygame.image.load("images/titleicon.png")
clickStartImg = pygame.image.load("images/clickedStartIcon.png")
clickQuitImg = pygame.image.load("images/clickedQuitIcon.png")

mainmenu()
runPyGame()
