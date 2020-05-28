import keyboard
import time

def keyhook(event):
    print(str(event.name)+" "+event.event_type)

def SCKeyboardDiagnosis_cli():
    keyboard.hook(keyhook)
    while True:
      time.sleep(10)

if __name__ == '__main__':
    SCKeyboardDiagnosis_cli()
