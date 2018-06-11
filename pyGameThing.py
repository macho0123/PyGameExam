import sys, os
 
import pygame, numpy as np, pyaudio
from pygame.locals import *
import time
import ctypes

print(pygame.version.ver)


noteMinUser = 55   # G4
NOTE_MAX = 90       # G7
NOTE_MIN = noteMinUser - 10
FSAMP = 22050       # Sampling frequency in Hz
FRAME_SIZE = 1024   # How many samples per frame?
FRAMES_PER_FFT = 8 # FFT takes average across how many frames?
num_frames = 0

######################################################################
# Derived quantities from constants above. Note that as
# SAMPLES_PER_FFT goes up, the frequency step size decreases (so
# resolution increases); however, it will incur more delay to process
# new sounds.

SAMPLES_PER_FFT = FRAME_SIZE*FRAMES_PER_FFT
FREQ_STEP = float(FSAMP)/SAMPLES_PER_FFT

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
def note_name(n): 
  return NOTE_NAMES[n % 12] + str(round(n/12 - 1))

######################################################################
# Ok, ready to go now.

# Get min/max index within FFT of notes we care about.
# See docs for numpy.rfftfreq()
def note_to_fftbin(n): 
  return number_to_freq(n)/FREQ_STEP

imin = max(0, int(np.floor(note_to_fftbin(NOTE_MIN-1))))
imax = min(SAMPLES_PER_FFT, int(np.ceil(note_to_fftbin(NOTE_MAX+1))))

# Allocate space to run an FFT. 
buf = np.zeros(SAMPLES_PER_FFT, dtype=np.float32)

# Initialize audio
stream = pyaudio.PyAudio().open(format=pyaudio.paInt16,
                                channels=1,
                                rate=FSAMP,
                                input=True,
                                frames_per_buffer=FRAME_SIZE)

stream.start_stream()

# Create Hanning window function
window = 0.5 * (1 - np.cos(np.linspace(0, 2*np.pi, SAMPLES_PER_FFT, False))) 

def getPitchData():  

  global num_frames
  #while stream.is_active():
  # Shift the buffer down and new data in
  buf[:-FRAME_SIZE] = buf[FRAME_SIZE:]
  buf[-FRAME_SIZE:] = np.fromstring(stream.read(FRAME_SIZE), np.int16)

  # Run the FFT on the windowed buffer
  fft = np.fft.rfft(buf * window)

  # Get frequency of maximum response in range
  freq = (np.abs(fft[imin:imax]).argmax() + imin) * FREQ_STEP

  # Get note number and nearest note
  n = freq_to_number(freq)
  n0 = int(round(n))
  nC = round(n-n0, 2)

  # Console output once we have a full buffer
  num_frames += 1

  if num_frames >= FRAMES_PER_FFT:
    if (n0>noteMinUser):
      return note_name(n0)  # return n-n0 for cents (means accuracy measure)

  #return "a"   #Testing 101

#/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#                                                   PYGAME STARTS HERE
#/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////



display_width = 800
display_height = 600
name = "hello"
clock = pygame.time.Clock()

# Color schemes
red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)
darkBlue = (0,0,128)
white = (255,255,255)
black = (0,0,0)
purple = (42,44,206)
pink = (255,200,200)

# Global variables (pythons grid axis are retarded)
noteLocationX = 100 # span of one fret, needs to be multiplied by fret number
noteLocationY = 300 
indicatorLocationY = 570

indicatorWidth = 80
indicatorHeight = 21

notesToPlay = []


# Note class
class Note:

    def __init__(self ,fret, string):
      if (fret!=0):
        self.rect = pygame.rect.Rect((50 + noteLocationX*fret, noteLocationY, indicatorWidth, indicatorHeight*3))
        self.string = string
      else:
        self.rect = pygame.rect.Rect((50 + noteLocationX*fret, noteLocationY, 10, indicatorHeight*3))
        self.string = string

    def moveUp(self):
        self.rect.move_ip(0, -10)
        pygame.draw.rect(screen, (0, 0, 128), self.rect)

    def moveDown(self):
        self.rect.move_ip(0, 10)
        pygame.draw.rect(screen, (0, 0, 128), self.rect)

    def moveRight(self):
        self.rect.move_ip(10, 0)
        pygame.draw.rect(screen, (0, 0, 128), self.rect)

    def moveLeft(self):
        self.rect.move_ip(-10, 0)
        pygame.draw.rect(screen, (0, 0, 128), self.rect)

    def idle(self):
        pygame.draw.rect(screen, (0, 0, 128), self.rect)

# Class Button
class Button:

    def __init__(self, img_in, x, y, width, height, img_act, x_act, y_act, action = None):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()
        if x + width > mouse[0] > x and y + height > mouse[1] > y:
            screen.blit(img_act,(x_act, y_act))
            if click[0] and action is not None:
                time.sleep(2)
                action()
        else:
            screen.blit(img_in,(x,y))

def indicatePosition(fret, string):

  #hitbox serves as a position for surface too

    if (fret>0):
      indicator = pygame.Surface((indicatorWidth, indicatorHeight), pygame.SRCALPHA)   # per-pixel alpha
      indicatorHitbox = pygame.rect.Rect(50 + noteLocationX*fret, indicatorLocationY - string*(indicatorHeight + 7 - string/1.5), indicatorWidth, indicatorHeight)
      indicator.fill((255,255,255,128))                         # notice the alpha value in the color
      screen.blit(indicator, indicatorHitbox) #takes rectangle as position 2 arguement 
      testCollision(indicatorHitbox)



    if (fret==0):
      indicator = pygame.Surface((10, indicatorHeight), pygame.SRCALPHA)   # per-pixel alpha
      indicatorHitbox = pygame.rect.Rect(50 + noteLocationX*fret, indicatorLocationY - string*(indicatorHeight + 7 - string/1.5), 10, indicatorHeight*3)
      indicator.fill((255,255,255,128))                         # notice the alpha value in the color
      screen.blit(indicator, indicatorHitbox)
      testCollision(indicatorHitbox)



def text_objects(text, font):

    textSurface = font.render(text, True, white)
    return textSurface, textSurface.get_rect()

def testCollision(indicator):
  i = 0
  while i < len(notesToPlay):
    print(notesToPlay[i].rect.y)
    #print(notesToPlay[i].rect)
    if notesToPlay[i].rect.colliderect(indicator):
      print("indicator")
      notesToPlay.pop(i)
    i += 1
        

def message_display(text):

    x = (display_width/2)
    y = (display_height/2)

    largeText = pygame.font.SysFont('Arial',15, white)
    TextSurf, TextRect = text_objects(text, largeText)
    TextRect.center = (x,y)
    screen.blit(TextSurf, TextRect)

def update(dt):

  note = getPitchData()

  for string in strings:
    stringNum = strings.index(string)
    if (note in string):
      fret = string.index(note)
      #print(stringNum, fret)
      indicatePosition(fret, stringNum)
      #testing



      #for rectangle in notesToPlay.items():        print(rectangle)           rectangle.moveDown()
  """
  Update game. Called once per frame.
  dt is the amount of time passed since last frame.
  If you want to have constant apparent movement no matter your framerate,
  what you can do is something like
  
  x += v * dt
  
  and this will scale your velocity based on time. Extend as necessary."""
  # Go through events that are passed to the script by the window.
  for event in pygame.event.get():
    # We need to handle these events. Initially the only one you'll want to care
    # about is the QUIT event, because if you don't handle it, your game will crash
    # whenever someone tries to exit.
    if event.type == QUIT:
      pygame.quit() # Opposite of pygame.init
      sys.exit() # Not including this line crashes the script on Windows. Possibly
      # on other operating systems too, but I don't know for sure.
    # Handle other events as you wish.
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_LEFT:
          songNote = Note(0,0)
          notesToPlay.append(songNote)
        if event.key == pygame.K_RIGHT:
          songNote = Note(1,1)
          notesToPlay.append(songNote)       
        if event.key == pygame.K_DOWN:
          songNote = Note(2,2)
          notesToPlay.append(songNote)
        if event.key == pygame.K_UP:
          songNote = Note(3,3)
          notesToPlay.append(songNote)

          


 
def draw(screen):

  """
  Draw things to the window. Called once per frame.
  """
  # Redraw screen here.
  note = getPitchData()
  message_display(note)

  i = 0
  while i < len(notesToPlay):
    #print(notesToPlay[i].rect)
    notesToPlay[i].moveDown()
    i = i + 1


  # Flip the display so that the things we drew actually show up.
  pygame.display.flip()



def quitGame():
    pygame.quit()
    quit()


#MainMenu
def mainmenu():

    menu = False

    while menu:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        screen.fill(purple)

        titletext = screen.blit(titleImg, (275,200))
        startButton = Button(startImg,280,260,60,20,clickStartImg,273,258,runPyGame)
        quitButton = Button(quitImg,475,260,60,20,clickQuitImg,470,258,quitGame)

        pygame.display.update()
        clock.tick(15)


def runPyGame():
  # Initialise PyGame.
  pygame.init()

  #init object
  #Note("X1", 4, 4)
  
  # Set up the clock. This will tick every frame and thus maintain a relatively constant framerate. Hopefully.
  fps = 60.0
  fpsClock = pygame.time.Clock()
  
  # Set up the window.
  #screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

  
  # screen is the surface representing the window.
  # PyGame surfaces can be thought of as screen sections that you can draw onto.
  # You can also draw surfaces onto other surfaces, rotate surfaces, and transform surfaces.
  
  # Main game loop.
  dt = 1/fps # dt is the time since last frame.
  while True: # Loop forever!

    #screen.fill((0, 0, 0)) # Fill the screen with black.
    screen.blit(background_image, [0, 0])
    update(dt) # You can update/draw here, I've just moved the code for neatness.
    draw(screen)
    dt = fpsClock.tick(fps)



screen = pygame.display.set_mode((display_width, display_height), DOUBLEBUF)
background_image = pygame.image.load("images/background1.png").convert()
startImg = pygame.image.load("images/starticon.png")
quitImg = pygame.image.load("images/quiticon.png")
titleImg = pygame.image.load("images/titleicon.png")
clickStartImg = pygame.image.load("images/clickedStartIcon.png")
clickQuitImg = pygame.image.load("images/clickedQuitIcon.png")
#player = Player()

mainmenu()
runPyGame()
