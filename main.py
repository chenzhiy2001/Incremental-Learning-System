import os, time, threading, logging, json, itertools
from datetime import date,datetime,timedelta
from tkinter import Tk, Button, Scale, Canvas, Label, StringVar, Entry, \
    Toplevel, messagebox, scrolledtext, END, ttk, Listbox, simpledialog, ANCHOR, \
    Frame
from tkinter.colorchooser import askcolor
from PIL import Image
from interval_algorithm import s1mple

class NanoTask(dict):
    def __init__(self,name,dir='~',repitition_times=0) -> None:
        dict.__init__(self,name=name,dir=dir,repitition_times=repitition_times)

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

class TextHandler(logging.Handler):
    # From: https://stackoverflow.com/a/41959785
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text.configure(state='normal')
            self.text.insert(END, msg + '\n')
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(END)
        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)

def worker():
    # Skeleton worker function, runs in separate thread (see below)   
    while True:
        # Report time / date at 2-second intervals
        time.sleep(300)
        timeStr = time.asctime()
        msg = 'Current time: ' + timeStr
        logging.info(msg) 

class App():
    # Modified from: https://gist.github.com/Kaabasane/a4f1fb10d27611bdd6b4ccf6b9206a9b
    DEFAULT_PEN_SIZE = 5.0
    DEFAULT_COLOR = 'black'

    def __init__(self):
        #super(App, self).__init__()
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

        # self.line_button = Button(self.root, text='Line',
        #                           command=self.use_line)
        # self.line_button.grid(row=1, column=0, sticky="ew")

        # self.poly_button = Button(self.root, text='Polygon',
        #                           command=self.use_poly)
        # self.poly_button.grid(row=1, column=1, sticky="ew")

        # self.black_button = Button(self.root, text='', bg='black',
        #                            activebackground="black",
        #                            command=self.color_default)
        # self.black_button.grid(row=1, column=2, sticky="ew")

        self.clear_button = Button(self.root, text='Clear',
                                   command=lambda: self.c.delete("all"))
        self.clear_button.grid(row=1, column=3, sticky="ew")

        self.save_button = Button(self.root, text="Save",
                                  command=self.save_file)
        self.save_button.grid(row=1, column=4, sticky="ew")

        self.c = Canvas(self.root, bg='white', width=640, height=480)
        self.c.grid(row=2, columnspan=5)

        self.var_status = StringVar(value="Selected: Pen")
        self.lbl_status = Label(self.root, textvariable=self.var_status,anchor="w")
        self.lbl_status.grid(row=3, column=0, columnspan=3,sticky='ew')

        self.setup()

        self.root.title('czy\'s Incremental Learning System')

        
        # Add text widget to display logging info
        st = scrolledtext.ScrolledText(self.root, state='disabled') # type: ignore
        st.configure(font='TkFixedFont')
        st.grid(row=4, column=0, sticky='ew', rowspan=1, columnspan=5)

        # Create textLogger
        text_handler = TextHandler(st)

        # Logging configuration
        logging.basicConfig(filename='test.log',
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s - %(message)s')        

        # Add the handler to logger
        self.logger = logging.getLogger()        
        self.logger.addHandler(text_handler)


        
    
        self.notes_menu_frame = Frame(self.root)
        self.file_nodes = dict()
        self.file_tree = ttk.Treeview(self.notes_menu_frame)
        ysb = ttk.Scrollbar(self.notes_menu_frame, orient='vertical', command=self.file_tree.yview)
        xsb = ttk.Scrollbar(self.notes_menu_frame, orient='horizontal', command=self.file_tree.xview)
        self.file_tree.configure(yscroll=ysb.set, xscroll=xsb.set) # type: ignore
        self.file_tree.heading('#0', text='Your Fucking Notes', anchor='w')

        self.file_tree.grid(row=0, column=0, sticky="en")
        ysb.grid(row=0, column=1, sticky='ns')
        xsb.grid(row=1, column=0, sticky='ew')
        self.notes_menu_frame.grid(row=2,column=5,sticky='nw')

        abspath = os.path.abspath('.')
        self.insert_file_browser_node('', abspath, abspath)
        self.file_tree.bind('<<TreeviewOpen>>', self.open_file_node)

        # load tasklist which generates logs
        self.load_tasklist()

        # start logger
        logger_thread = threading.Thread(target=worker, args=[])
        logger_thread.start()
        
        self.root.mainloop()
        logger_thread.join()
        

        

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

        self.studying=None
    
    def load_tasklist(self):
            # load file
            self.tasklist_filename='tasks.json'
            try:
                with open(self.tasklist_filename,"r",encoding='utf-8') as taskfile:
                    try:
                        self.tasks=json.load(taskfile)
                    except ValueError:
                        self.logger.info("Decoding json has failed. Please check "+self.tasklist_filename+".\nPerhaps you need to fix the format error. If it's empty, delete it and rerun the program.")
                        return None
            except IOError:
                self.logger.info("Tasklist does not exist. Creating one...")
                with open('tasks.json','w+',encoding='utf-8') as taskfile:
                    self.tasks={}
                    json.dump(self.tasks,taskfile, ensure_ascii=False, indent=4)
            self.today=str(date.today())
            self.logger.info('Today is '+self.today+'. Checking precedent tasks...')
            if self.today not in self.tasks:
                self.tasks[self.today]=[]
            print(self.tasks)
            for k in list(self.tasks):
                if datetime.strptime(k, '%Y-%m-%d') < datetime.strptime(self.today, '%Y-%m-%d'):
                    self.logger.info('Found precedent tasks from '+k+'. Moving it to today...')
                    self.tasks[self.today]+=self.tasks.pop(k) #todo: problematic?
            
            # load GUI
            self.tasklist_treeview=ttk.Treeview(self.notes_menu_frame)
            self.tasklist_treeview.heading('#0', text='NanoItems', anchor='w')
            self.tasklist_treeview.grid(row=2, column=0, sticky='nw')

            if self.today not in self.tasks or len(self.tasks[self.today])==0:
                self.tasks[self.today]=[]
                self.logger.info('It seems that you have nothing to do now. Consider adding new tasks or take a break.')
                self.save_tasklist()
            else:
                for todaytask in self.tasks[self.today]:
                    self.tasklist_treeview.insert('',END, text=todaytask['name'])

            self.add_new_task_button=Button(self.notes_menu_frame,text='ADD',command=self.add_new_task)
            self.add_new_task_button.grid(row=3, column=0, sticky='nw')

            self.do_task_button=Button(self.notes_menu_frame,text='DO',command=self.do_task)
            self.do_task_button.grid(row=4, column=0, sticky='nw')

            self.stop_task_button=Button(self.notes_menu_frame,text='STOP',command=self.stop_task)
            self.stop_task_button.grid(row=5, column=0, sticky='nw')

            self.delete_task_button=Button(self.notes_menu_frame,text='DELETE',command=lambda:self.delete_tasklist_item_by_name(self.today,self.tasklist_treeview.item(self.tasklist_treeview.focus())['text']))
            self.delete_task_button.grid(row=6, column=0, sticky='nw')



    def delete_tasklist_item_by_index(self,day,index):
        p=self.tasks[day].pop(index)
        for child in self.tasklist_treeview.get_children():
            if self.tasklist_treeview.item(child)['text']==p['name']:
                self.tasklist_treeview.delete(child)
        self.save_tasklist()
    
    def delete_tasklist_item_by_name(self,day,name):
        for item in self.tasks[day]:
            if item['name']==name: # 重名项怎么办？
                for child in self.tasklist_treeview.get_children():
                    if self.tasklist_treeview.item(child)['text']==name:
                        self.tasklist_treeview.delete(child)
            self.tasks[day].remove(item) # may cause err when remove multiple times
        self.save_tasklist()

    def move_a_tasklist_item_foward(self,offset_day_int,index):
        self.tasks[str(datetime.strptime(self.today, '%Y-%m-%d')+timedelta(days=offset_day_int))].append(self.tasks[self.today].pop(index))
        self.save_tasklist()

    def add_new_task(self):
        name=simpledialog.askstring(title="Task Name?", prompt="We recommend that the task should be a tiny chunk instead of a big project, so that you\'re willing to do them with ease.")
        n=NanoTask(name)
        self.tasks[self.today].append(n)
        print(n)
        self.tasklist_treeview.insert('',END, text=n['name']) # type: ignore
        self.save_tasklist()

    def do_task(self):
        studying_str = self.tasklist_treeview.item(self.tasklist_treeview.focus())['text']
        self.logger.info("Studying: "+studying_str)
        self.studying_str = studying_str
        self.logger.info("Stop studying when you feel it not that fun. Then press STOP.")

    def stop_task(self):
        easiness_str=simpledialog.askinteger('How do you feel?','''
            6 - I finished the task
            5 - EZ, almost done.
            4 - Did a part of them.
            3 - Did something and stuck, frustrated
            2 - Had some ideas but don't know how to do it
            1 - Haven't figured it out
            0 - It's too hard. I'm blackout and didn't do anything.
        ''')
        for index,i in enumerate(self.tasks[self.today]):
            if i['name'] == self.studying_str:
                if int(easiness_str) == 6: # type: ignore
                    self.delete_tasklist_item_by_index(self.today,index)
                else:
                    i['repetition_times']+=1
                    next_study_day=s1mple(i['repetition_times'],int(easiness_str)) # type: ignore
                    self.move_a_tasklist_item_foward(next_study_day,index)

        self.studying_str=None

    def save_tasklist(self):
        with open('tasks.json', 'w', encoding='utf-8') as taskfile:
            json.dump(self.tasks, taskfile, ensure_ascii=False, indent=4)
            self.logger.info('Everything Saved!')




    def use_pen(self):
        self.activate_button(self.pen_button)
        self.size_multiplier = 1

    def use_brush(self):
        self.activate_button(self.brush_button)
        self.size_multiplier = 2.5

    # def use_line(self):
    #     self.activate_button(self.line_button)

    # def use_poly(self):
    #     self.activate_button(self.poly_button)

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
            self.var_status.set(f"Selected: {btn}")
            #self.var_status.set(f"Selected: {btn}\n" +
            #                    ((f"Old (x, y): {oldxy}\n(x, y): ({x}, {y})")
            #                     if x is not None and y is not None else ""))

    def insert_file_browser_node(self, parent, text, abspath):
        node = self.file_tree.insert(parent, 'end', text=text, open=False)
        if os.path.isdir(abspath):
            self.file_nodes[node] = abspath
            self.file_tree.insert(node, 'end')

    def open_file_node(self, event):
        node = self.file_tree.focus()
        abspath = self.file_nodes.pop(node, None)
        if abspath:
            self.file_tree.delete(self.file_tree.get_children(node)) # type: ignore
            for p in os.listdir(abspath):
                self.insert_file_browser_node(node, p, os.path.join(abspath, p))

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




    
if __name__ == '__main__':
    App()
