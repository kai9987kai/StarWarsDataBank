from tkinter import *
import random
import requests
from tkinter import ttk


random1 = random.randint(1, 88)
main_api = 'https://swapi.co/api/people/' + str(random1) + '/?format=json'
url = main_api
json_data = requests.get(url).json()
window = Tk()
window.attributes("-topmost", True)
window.resizable(False, False)
window.geometry("+500+200")
window.iconbitmap('favicon.ico')
lbl = Label(window, text="Name:")
lbl3 = Label(window, text="Height:")
lbl6 = Label(window, text="Mass:")
lbl7 = Label(window, text="Hair color:")
lbl10 = Label(window, text="Skin color:")
lbl11 = Label(window, text="Eye color:")
lbl14 = Label(window, text="Birth year:")
lbl16 = Label(window, text="Gender:")
lbl2 = Label(window, text=(json_data["name"]))
lbl4 = Label(window, text=(json_data["height"]))
lbl5 = Label(window, text=(json_data["mass"]))
lbl8 = Label(window, text=(json_data["hair_color"]))
lbl9 = Label(window, text=(json_data["skin_color"]))
lbl12 = Label(window, text=(json_data["eye_color"]))
lbl13 = Label(window, text=(json_data["birth_year"]))
lbl15 = Label(window, text=(json_data["gender"]))
lbl.grid(column=1, row=1)
lbl2.grid(column=2, row=1)
lbl3.grid(column=1, row=2)
lbl6.grid(column=1, row=3)
lbl7.grid(column=1, row=4)
lbl4.grid(column=2, row=2)
lbl5.grid(column=2, row=3)
lbl8.grid(column=2, row=4)
lbl9.grid(column=2, row=5)
lbl10.grid(column=1, row=5)
lbl11.grid(column=1, row=6)
lbl12.grid(column=2, row=6)
lbl13.grid(column=2, row=7)
lbl14.grid(column=1, row=7)
lbl15.grid(column=2, row=8)
lbl16.grid(column=1, row=8)
def new12():
    random1 = random.randint(1, 88)
    main_api = 'https://swapi.co/api/people/' + str(random1) + '/?format=json'
    url = main_api
    json_data = requests.get(url).json()
    lbl2.configure(text=json_data["name"])
    lbl4.configure(text=json_data["height"])
    lbl5.configure(text=json_data["mass"])
    lbl8.configure(text=json_data["hair_color"])
    lbl9.configure(text=json_data["skin_color"])
    lbl12.configure(text=json_data["eye_color"])
    lbl13.configure(text=json_data["birth_year"])
    lbl15.configure(text=json_data["gender"])
def exit():
    window.destroy()
ttk.Button(window, text="NEW", command=new12).grid(row=9, column=1)
ttk.Button(window, text="EXIT", command=exit).grid(row=9, column=2)
# create a menu
popup = Menu(window, tearoff=0)
popup.add_command(label="New", command= new12) # , command=next) etc...
popup.add_command(label="Exit", command = exit)


def do_popup(event):
    # display the popup menu
    try:
        popup.tk_popup(event.x_root, event.y_root, 0)
    finally:
        # make sure to release the grab (Tk 8.0a1 only)
        popup.grab_release()

window.bind("<Button-3>", do_popup)
window.mainloop()
