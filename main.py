import json
import os
from datetime import date,datetime
import itertools
def main():
    print('Welcome to the czy Incremental Learning System!')
    print('Loading default tasklist file...')
    tasklist_filename='tasks.json'
    try:
        with open(tasklist_filename,"r") as taskfile:
            try:
                tasks=json.load(taskfile)
            except ValueError:
                print("Decoding json has failed. Please check "+tasklist_filename+".\nPerhaps you need to fix the format error. If it's empty, delete it and rerun the program.")
                return None
    except IOError:
        print("Tasklist does not exist. Creating one...")
        with open('tasks.json','w+') as taskfile:
            tasks={}
            taskfile.write(json.dumps(tasks))

    today=date.today()
    print('Today is '+str(today)+'. Checking precedent tasks...')
    for k,v in tasks:
        if k < today:
            print('Found precedent task '+v.name+'. Moving it to today...')
            tasks[today]+=tasks.pop(k)

    while True:
        print('T for today\'s tasklist. A to add new task. D \'number\' to do the \'number\'th task.')
        k=input().split()
        if k[0] == 'T' or 't':
            if today not in tasks or tasks[today].len()==0:
                print('It seems that you have nothing to do now. Consider adding new tasks or take a break.')
            else:
                for i in itertools.count(start=0):
                    print('('+str(i)+')  '+tasks[today][i].name)
        if k[0] == 'A' or 'a':
            print('Name?')
            tasks[today].append({'name':input()})
        if k[0] == 'D' or 'd':
            print("Do Stuff!")
            return





    
    

    

            



if __name__ == "__main__":
    main()