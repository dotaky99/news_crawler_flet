import threading
import time
import flet
from flet import Page, Text, ElevatedButton, Row

def long_running_task(page: Page, label: Text):
    for i in range(10):
        time.sleep(1)
        page.add(Text(f"Running... {i+1}"))
    label.value = "Task Completed"
    page.update()

def main(page: Page):
    page.title = "Flet with Threading Example"
    
    label = Text(value="Start the long running task by clicking the button below.")
    
    def on_button_click(e):
        page.add(Text("Starting the long running task..."))
        thread = threading.Thread(target=long_running_task, args=(page, label))
        thread.start()
    
    button = ElevatedButton(text="Start Task", on_click=on_button_click)
    
    page.add(
        Row(controls=[label]),
        Row(controls=[button])
    )

if __name__ == "__main__":
    flet.app(target=main)
