import json
import os
from datetime import date,datetime,timedelta
import itertools
import interval_algorithm
from tkinter import Tk, Button, Scale, Canvas, Label, StringVar, Entry, \
    Toplevel, messagebox
from tkinter.colorchooser import askcolor
from PIL import Image

class FilenamePopup:
    def __init__(self, master):
        top = self.top = Toplevel(master)
        self.lbl = Label(top, text="Choose a file name:")
        self.lbl.pack()
        self.ent_filename = Entry(top)
        self.ent_filename.pack()
        self.btn_ok = Button(top, text='Ok', command=self.cleanup)
        self.btn_ok.pack()

    def cleanup(self):
        self.filename = self.ent_filename.get()
        self.top.destroy()


class App(object):

    DEFAULT_PEN_SIZE = 5.0
    DEFAULT_COLOR = 'black'

    def __init__(self):
        self.root = Tk()

        self.pen_button = Button(self.root, text='Pen', 
                                 command=self.use_pen)
        self.pen_button.grid(row=0, column=0, sticky="ew")

        self.brush_button = Button(self.root, text='Brush',
                                   command=self.use_brush)
        self.brush_button.grid(row=0, column=1, sticky="ew")
        
        self.color_button = Button(self.root, text='Color',
                                   command=self.choose_color)
        self.color_button.grid(row=0, column=2, sticky="ew")

        self.eraser_button = Button(self.root, text='Eraser',
                                    command=self.use_eraser)
        self.eraser_button.grid(row=0, column=3, sticky="ew")

        self.size_scale = Scale(self.root, from_=1, to=10,
                                orient='horizontal')
        self.size_scale.grid(row=0, column=4, sticky="ew")

        self.line_button = Button(self.root, text='Line',
                                  command=self.use_line)
        self.line_button.grid(row=1, column=0, sticky="ew")

        self.poly_button = Button(self.root, text='Polygon',
                                  command=self.use_poly)
        self.poly_button.grid(row=1, column=1, sticky="ew")

        self.black_button = Button(self.root, text='', bg='black',
                                   activebackground="black",
                                   command=self.color_default)
        self.black_button.grid(row=1, column=2, sticky="ew")

        self.clear_button = Button(self.root, text='Clear',
                                   command=lambda: self.c.delete("all"))
        self.clear_button.grid(row=1, column=3, sticky="ew")

        self.save_button = Button(self.root, text="Save",
                                  command=self.save_file)
        self.save_button.grid(row=1, column=4, sticky="ew")

        self.c = Canvas(self.root, bg='white', width=600, height=600)
        self.c.grid(row=2, columnspan=5)

        self.var_status = StringVar(value="Selected: Pen")
        self.lbl_status = Label(self.root, textvariable=self.var_status)
        self.lbl_status.grid(row=3, column=4, rowspan=3)

        self.root.title('czy\'s Incremental Learning System')


        self.setup()
        self.root.mainloop()

    def setup(self):
        self.old_x, self.old_y = None, None
        self.color = self.DEFAULT_COLOR
        self.eraser_on = False
        self.active_button = None
        self.size_multiplier = 1

        self.activate_button(self.pen_button)
        self.c.bind('<B1-Motion>', self.paint)
        self.c.bind('<ButtonRelease-1>', self.reset)

        self.c.bind('<Button-1>', self.point)
        self.root.bind('<Escape>', self.line_reset)
        self.line_start = (None, None)

    def use_pen(self):
        self.activate_button(self.pen_button)
        self.size_multiplier = 1

    def use_brush(self):
        self.activate_button(self.brush_button)
        self.size_multiplier = 2.5

    def use_line(self):
        self.activate_button(self.line_button)

    def use_poly(self):
        self.activate_button(self.poly_button)

    def choose_color(self):
        self.eraser_on = False
        color = askcolor(color=self.color)[1]
        if color is not None:
            self.color = color

    def use_eraser(self):
        self.activate_button(self.eraser_button, eraser_mode=True)

    def activate_button(self, some_button, eraser_mode=False):
        self.set_status()
        if self.active_button:
            self.active_button.config(relief='raised')
        some_button.config(relief='sunken')
        self.active_button = some_button
        self.eraser_on = eraser_mode

    def paint(self, event):
        self.set_status(event.x, event.y)
        line_width = self.size_scale.get() * self.size_multiplier
        paint_color = 'white' if self.eraser_on else self.color
        if self.old_x and self.old_y:
            self.c.create_line(self.old_x, self.old_y, event.x, event.y,
                               width=line_width, fill=paint_color,
                               capstyle='round', smooth=True, splinesteps=36)
        self.old_x = event.x
        self.old_y = event.y

    def line(self, x, y):
        line_width = self.size_scale.get() * self.size_multiplier
        paint_color = 'white' if self.eraser_on else self.color
        self.c.create_line(self.line_start[0], self.line_start[1], x, y, # type: ignore
                           width=line_width, fill=paint_color,
                           capstyle='round', smooth=True, splinesteps=36)

    def point(self, event):
        self.set_status(event.x, event.y)
        btn = self.active_button["text"] # type: ignore
        if btn in ("Line", "Polygon"):
            self.size_multiplier = 1
            if any(self.line_start):
                self.line(event.x, event.y)
                self.line_start = ((None, None) if btn == 'Line'
                                   else (event.x, event.y))
            else:
                self.line_start = (event.x, event.y)

    def reset(self, event):
        self.old_x, self.old_y = None, None

    def line_reset(self, event):
        self.line_start = (None, None)

    def color_default(self):
        self.color = self.DEFAULT_COLOR

    def set_status(self, x=None, y=None):
        if self.active_button:
            btn = self.active_button["text"]
            oldxy = (self.line_start if btn in ("Line", "Polygon")
                     else (self.old_x, self.old_y))

            self.var_status.set(f"Selected: {btn}\n" +
                                ((f"Old (x, y): {oldxy}\n(x, y): ({x}, {y})")
                                 if x is not None and y is not None else ""))

    def save_file(self):
        self.popup = FilenamePopup(self.root)
        self.save_button["state"] = "disabled"
        self.root.wait_window(self.popup.top)

        filepng = self.popup.filename + '.png'

        if not os.path.exists(filepng) or \
                messagebox.askyesno("File already exists", "Overwrite?"):
            fileps = self.popup.filename + '.eps'

            self.c.postscript(file=fileps)
            img = Image.open(fileps)
            img.save(filepng, 'png')
            os.remove(fileps)

            self.save_button["state"] = "normal"

            messagebox.showinfo("File Save", "File saved!")
        else:
            messagebox.showwarning("File Save", "File not saved!")

        self.save_button["state"] = "normal"




def main():
    print('Welcome to the czy Incremental Learning System!')
    print('Loading default tasklist file...')
    tasklist_filename='tasks.json'
    try:
        with open(tasklist_filename,"r",encoding='utf-8') as taskfile:
            try:
                tasks=json.load(taskfile)
            except ValueError:
                print("Decoding json has failed. Please check "+tasklist_filename+".\nPerhaps you need to fix the format error. If it's empty, delete it and rerun the program.")
                return None
    except IOError:
        print("Tasklist does not exist. Creating one...")
        with open('tasks.json','w+',encoding='utf-8') as taskfile:
            tasks={}
            json.dump(tasks,taskfile, ensure_ascii=False, indent=4)

    today=str(date.today())
    print('Today is '+today+'. Checking precedent tasks...')
    for k,v in tasks:
        if datetime.strptime(k, '%Y-%m-%d') < datetime.strptime(today, '%Y-%m-%d'):
            print('Found precedent task '+v.name+'. Moving it to today...')
            tasks[today]+=tasks.pop(k)
    
    if today not in tasks:
        tasks[today]=[]

    while True:
        print('`t` for today\'s tasklist. `a` to add new task. `d` \'number\' to do the \'number\'th task. q to save and quit.')
        k=input().split()
        if k[0] == 't':
            if today not in tasks or len(tasks[today])==0:
                print('It seems that you have nothing to do now. Consider adding new tasks or take a break.')
            else:
                for i in itertools.count(start=0):
                    print('('+str(i)+')  '+tasks[today][i].name)
        if k[0] == 'a':
            print('Name? We recommend that the task should be a tiny chunk instead of a big project, so that you\'re willing to do them with ease.')
            tasks[today].append({'name':input()})
        if k[0] == 'd':
            print("Studying: "+tasks[today][int(k[1])])
            print("When you feel tired, stop studying and press Enter.")
            input()
            print("How do you feel?")
            print('''
            6 - I finished the task
            5 - EZ
            4 - Did a part of them.
            3 - correct response recalled with serious difficulty
            2 - Had some ideas but don't know how to do it
            1 - Haven't figured it out
            0 - It's too hard. I'm blackout and didn't do anything.
            ''')
            input()#todo: advices based on algorithm.json
            print("When to study this next time?")# todo: this task is finished
            tasks[str(datetime.strptime(today, '%Y-%m-%d')+timedelta(days=int(input())))].append(tasks[today].pop(int(k[1])))

        
        if k[0] == 'q':
            with open('tasks.json', 'w', encoding='utf-8') as taskfile:
                json.dump(tasks, taskfile, ensure_ascii=False, indent=4)
            print('Everything Saved. Bye!')
            return

    
if __name__ == '__main__':
    App()