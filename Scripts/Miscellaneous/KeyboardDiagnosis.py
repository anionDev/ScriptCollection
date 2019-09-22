import keyboard
import time
def keyhook(event):
    print(str(event.name)+" "+event.event_type)
keyboard.hook(keyhook)
while True:
  time.sleep(10)