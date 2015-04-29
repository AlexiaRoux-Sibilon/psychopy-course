# -*- coding: utf-8 -*-
"""
This walks you through some common errors which messes timing up.
  1. time visual using win.flip(), not core.wait()
  2. put processing before timing-critical period
  3. put trigger/logging after win.flip() or sound.play()
  4. how to synchronize visual, audio and trigger

Jonas Lindeløv, 2014
"""

# Initiate stimuli etc.
from psychopy import core, visual, parallel, sound
port = parallel.ParallelPort(address=0x0378)
clock = core.Clock()
win = visual.Window(fullscr=True, color='black', allowGUI=False)
soundPyo = sound.SoundPyo('beep2.wav', hamming=False)

import ppc
beep = ppc.Sound('beep2.wav')


"""
Use win.flip() for timing of visual stimuli.
Never use core.wait() for this purpose!
"""
# BAD: using core.wait() to time visual stimuli
stim = visual.TextStim(win, text="Not on time!")
stim.draw()
win.flip()
core.wait(0.05)     # Wait for 50 ms using core.wait()
win.flip()          # Draw blank screen on next flip. This is likely to arrive late, making the stimulus last longer than intended.

# GOOD: using frames
stim = visual.TextStim(win, text="Right on time!")
for frameN in range(3): # Loop for 3 frames
    stim.draw()         # Draw stimulus to buffer on every frame
    win.flip()          # Flip screen on every frame: this is timed to actual update of monitor
win.flip()              # Draw blank screen on next flip.: stimulus stops.


"""
Process heavy stuff in advance.
"""
# BAD: doing process heavy stuff in timing critical periods
for frameN in range(3):
    stim = visual.TextStim(win, text="Not on time!")  # Initialize a whole new stimulus: very heavy on resources and likely to cause a delay.
    stim.setPos((1,2))  # Or: set constant attributes on every loop that really remains constant throughout the trial.
    stim.setColor('green')
    stim.draw()
    win.flip()

# GOOD: do things in advance, outside the loop
stim = visual.TextStim(win, text="Right on time!")
stim.setPos((1,2))
stim.setColor('green')
for frameN in range(3):
    stim.draw()
    win.flip()

"""
Logging of stimuli should be initiated and terminated after win.flip() or sound.play().
"""
# BAD: logging visual events before win.flip(), i.e. out of sync with actual monitor update
clock.reset()
port.setData(255)
for frameN in range(3):
    stim.draw()
    win.flip()              # Note that the first flip might occur many milliseconds after log/trigger
port.setData(0)
duration = clock.getTime()  # Get time since clock.reset(). Note that this is executed while stimulus is still on screen.

# BAD for audio: logging sound before it is initiated.
port.setData(15)
soundPyo.play()  # sound.SoundPyo is better than sound.Sound but still ~80-120 ms delayed with jitter
core.wait(0.1)  # duration of trigger
port.setData(0)


# GOOD: logging just after win.flip()
for frameN in range(3):
    stim.draw()
    win.flip()
    if frameN == 0:             # For first frame, just after stimulus appears on monitor
        clock.reset()           # Set clock time to zero
        port.setData(255)   # Start trigger
win.flip()                      # Show blank screen
duration = clock.getTime()      # Get duration just when blank screen has been presented, i.e. when stimulus ends
port.setData(0)             # Stop trigger

# GOOD for audio:
beep.play()  # using winsound, Windows only! Low latency if soundcard is set up properly
port.setData(15)
core.wait(0.1)  #Duration of trigger
port.setData(0)


"""
Synchronizing visual, audio and trigger.
   * pretty version with not-too-bad synchronization
   * ugly version with pretty exact synchronization
"""

# PRETTY VERSION
# Play sound and show visual and time with trigger.
# See next script if you want them (almost) perfectly synchronized.

for i in range(20):
    for frame in range(3):
        stim.draw()
        win.flip()  # every 16.667 ms
        if frame == 0:
            beep.play()  # play sound! Takes less than 0.1 ms
            port.setData(15)  # takes less than 0.01 ms
            clock.reset()  # takes less than 0.01 ms
    win.flip()
    port.setData(0)  # takes less than 0.01 ms
    duration = clock.getTime()  # takes less than 0.01 ms
    core.wait(0.3)


# UGLY VERSION
# Synchronizing audio and visual to trigger/log.
# This script is so ugly that I wouldn't recommend it. But it is pretty accurate if:
#    * stimuli are delayed relative to trigger
#    * audio delayed relative to visual is in the range of 1 ms to 15.5 ms (on 60Hz monitor)
#    * there's no jitter in audio, visual or trigger onset.
#    * frameInterval is measured precisely for the system

frameInterval = 0.01667  # seconds
visualDelay = 0.005  # seconds relative to trigger
soundDelay = 0.007  # seconds relative to trigger
for i in range(20):
    win.flip()  # to lock clock timing to win.flip before frame 0
    clock.reset()
    for frame in range(3):  # 50 ms on 60 Hz
        stim.draw()

        # sound initiated before flip
        if frame == 0:
            while clock.getTime() < frameInterval + visualDelay - soundDelay: pass  # pause for just the right duration
            beep.play()

        # The flip
        win.flip()

        # trigger initiated after flip
        if frame == 0:
            while clock.getTime() < frameInterval + visualDelay: pass  # let the trigger wait
            port.setData(15)
            clock.reset()

    win.flip()
    port.setData(0)
    while clock.getTime() < frameInterval*3: pass  # let the trigger wait
    duration = clock.getTime()  # this is approximate but usually accurate to below 0.1 ms
    core.wait(0.3)
