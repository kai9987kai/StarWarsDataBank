import urllib3
from tkinter import *
from bs4 import BeautifulSoup
http = urllib3.PoolManager()
urlnum1 = ('https://swapi.co/api/people/1/')
response = http.request('GET', urlnum1)
LukeSkywalker = BeautifulSoup(response.data.decode('utf-8'))
LukeSkywalker1= str(LukeSkywalker)

window = Tk()
window.title("StarWarsAPI")
lbl = Label(window, text=(LukeSkywalker1[9:23]))
lbl4 = Label(window, text="Name:")
lbl5 = Label(window, text="Height:")
lbl6 = Label(window, text="Mass:")
lbl2 = Label(window, text=(LukeSkywalker1[35:38]))
lbl3 = Label(window, text=(LukeSkywalker1[48:50]))
lbl3.grid(column=2, row=4)
lbl2.grid(column=2, row=3)
lbl.grid(column=2, row=2)
lbl4.grid(column=0, row=2)
lbl5.grid(column=0, row=3)
lbl6.grid(column=0, row=4)
window.mainloop()
