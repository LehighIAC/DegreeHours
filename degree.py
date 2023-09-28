"""
GUI of degree days/hours calculator
Requires Internet connection
Weather data source: meteostat.net
Copyright 2023 Lehigh University Industrial Assessment Center
"""

import tkinter as tk
import tkintermapview
import sys, platform, webbrowser
from datetime import datetime
from meteostat import Point, Hourly, Daily, units

def popup():
    """
    Show a pop-up window if there is an exception
    """
    popup = tk.Tk()
    # center the pop-up window
    popup.eval('tk::PlaceWindow . center')
    popup.wm_title("Error")
    # The error message is the exception message
    label = tk.Label(popup, text=sys.exc_info()[1], padx=pad, pady=pad)
    label.pack()
    # close the pop-up window
    button = tk.Button(popup, text="OK", command = popup.destroy)
    button.pack(padx=pad, pady=pad)
    popup.mainloop()

def calculate():
    """
    Calculate degree days/hours
    """
    try:
        # Get values from GUI
        mode = radio_mode.get()
        unit = radio_unit.get()
        type = radio_type.get().split()[1]
        basetemp = spin_basetemp.get()
        setback = spin_setback.get()
        history = int(menu_selected.get().split()[0])
        
        # Select mode
        sign = 1 if mode == "Cooling" else -1
        
        # Assemble schedule tuple
        schedule = []
        for i in range(7):
            if allday_list[i].get() == 1:
                start = 0
                end = 24
            elif holiday_list[i].get() == 1:
                start = 0
                end = 0
            else:
                start = int(start_list[i].get())
                end = int(end_list[i].get())
                #if start > end:
                #    raise Exception("Opening hours must be earlier than closing hours.")
            schedule.append((start, end))
        schedule = tuple(schedule)

        # Set time range
        starttime = datetime(2023 - history, 1, 1)
        endtime = datetime(2022, 12, 31, 23, 59)

        # Fetch data
        Point.method = 'nearest'
        # If you see "None of ['station', 'time'] are in the columns" error, try to increase the radius
        Point.radius = 50000
        # To-do: use open-elevation to get altitude information.
        plant = Point(latitude, longitude)
        if type == "Hours":
            data = Hourly(plant, starttime, endtime)
            if unit == "Fahrenheit":
                data.convert(units.imperial)
            data.normalize()
            data = data.interpolate()
            data = data.fetch()

            # Calculate degree hours
            data['basetemp'] = basetemp
            data['day'] = data.index.dayofweek
            data['hour'] = data.index.hour
            for day in range(7):
                data.loc[(data['day'] == day) & (data['hour'] < schedule[day][0]), 'basetemp'] = setback
                data.loc[(data['day'] == day) & (data['hour'] >= schedule[day][1]), 'basetemp'] = setback
            data['degreehour'] = data.apply(lambda x: max((x['temp'] - x['basetemp'])*sign, 0), axis=1)
            result = data.degreehour.sum() / history
        else:
            # Fetch data
            data = Daily(plant, starttime, endtime)
            if unit == "Fahrenheit":
                data.convert(units.imperial)
            data.normalize()
            data = data.interpolate()
            data = data.fetch()

            # Calculate degree days
            data['degreeday'] = data.apply(lambda x: max((x['tavg'] - basetemp) * sign, 0), axis=1)
            result = data.degreeday.sum() / history

        resultdegree.set("{:,}".format(int(result)))
    except:
        popup()

def unit_conversion():
    """
    Unit Conversion between Celsius and Fahrenheit
    """
    # If clicking the button again
    unit = radio_unit.get()
    if unit_backup.get() == unit:
        return
    try:
        basetemp = spin_basetemp.get()
        setback = spin_setback.get()
        if unit == "Fahrenheit":
            # Validate tempreature range
            if basetemp < 0 or basetemp > 100:
                raise Exception("Base temperature must be between 0 and 100 Celsius.")
            if setback < 0 or setback > 100:
                raise Exception("Setback temperature must be between 0 and 100 Celsius.")
            spinbasetemp.config(from_=32, to=212)
            spin_basetemp.set(round(basetemp*9/5+32))
            spinsetback.config(from_=32, to=212)
            spin_setback.set(round(setback*9/5+32))
        else:
            # Validate tempreature range
            if basetemp < 32 or basetemp > 212:
                raise Exception("Base temperature must be between 32 and 212 Fahrenheit.")
            if setback < 32 or setback > 212:
                raise Exception("Setback temperature must be between 32 and 212 Fahrenheit.")
            spinbasetemp.config(from_=0, to=100)
            spin_basetemp.set(round((basetemp-32)*5/9))
            spinsetback.config(from_=0, to=100)
            spin_setback.set(round((setback-32)*5/9))
        unit_backup.set(unit)
    except:
        if unit == "Fahrenheit":
            radio_unit.set("Celsius")
        else:
            radio_unit.set("Fahrenheit")
        popup()

def update_widget():
    """
    Update widgets when switching degree days/hours
    """
    resultlabel.set("      "+radio_mode.get()+ " " + radio_type.get() + ":")
    if radio_type.get() == "Degree Days":
        # disable setback temp
        spinsetback.config(state='disabled')
        # disable all schedule grid widgets
        for i in range(7):
            for j in range(4):
                frame_right.grid_slaves(row=j+2,column=i+1)[0].config(state='disabled')
    else:
        # enable setback temp
        spinsetback.config(state='normal')
        # restore schedule grid widgets
        check_hours()

def opening_hours(event):
    """
    Check opening hours
    """
    try:
        for i in range(7):
            start = start_list[i].get()
            if int(start) > int(end_list[i].get()):
                raise Exception("Opening hour must be earlier than closing hour.")
            else:
                start_backup[i].set(start)
    except:
        start_list[i].set(start_backup[i].get())
        popup()
            
def closing_hours(event):
    """
    Check closing hours
    """
    try:
        for i in range(7):
            end = end_list[i].get()
            if int(end) < int(start_list[i].get()):
                raise Exception("Closing hour must be later than opening hour.")
            else:
                end_backup[i].set(end)
    except:
        end_list[i].set(end_backup[i].get())
        popup()

def check_hours():
    """
    Update widgets when checking allday or holiday
    """
    for i in range(7):
        dropdown_start = frame_right.grid_slaves(row=2,column=i+1)[0]
        dropdown_end = frame_right.grid_slaves(row=3,column=i+1)[0]
        check_allday = frame_right.grid_slaves(row=4,column=i+1)[0]
        check_holiday = frame_right.grid_slaves(row=5,column=i+1)[0]
        # if the check_allday box is checked
        if allday_list[i].get() == 1:
            # disable other dropdowns
            dropdown_start.config(state='disabled')
            dropdown_end.config(state='disabled')
            check_allday.config(state='normal')
            check_holiday.config(state='disabled')
        # if the check_holiday box is checked
        elif holiday_list[i].get() == 1:
            # disable other dropdowns
            dropdown_start.config(state='disabled')
            dropdown_end.config(state='disabled')
            check_allday.config(state='disabled')
            check_holiday.config(state='normal')
        else:
            # enable everything
            dropdown_start.config(state='normal')
            dropdown_end.config(state='normal')
            check_allday.config(state='normal')
            check_holiday.config(state='normal')

def update_marker(coordinates):
    """
    Update marker position and text when clicking on the map
    """
    global latitude, longitude
    latitude = coordinates[0]
    longitude = coordinates[1]
    # update marker position
    marker.set_position(latitude, longitude)
    # update marker text
    marker.set_text("{:.4f}, {:.4f}".format(latitude, longitude))

def search_address():
    """
    Search the address and update the map
    """
    # convert address to coordinates
    global latitude, longitude
    location = tkintermapview.convert_address_to_coordinates(Address.get())
    if location == None:
        try:
            raise Exception("Address not found.")
        except:
            popup()
            return
    latitude = location[0]
    longitude = location[1]
    # update map view
    map_widget.set_position(latitude,longitude)
    map_widget.set_zoom(14)
    # update marker
    location = (latitude, longitude)
    update_marker(location)

def config():
    # GUI config for Windows and macOS
    if platform.system() == 'Darwin':
        MacConfig = dict()
        MacConfig['addrentry'] = 38
        MacConfig['gobutton'] = 2
        MacConfig['mapwidth'] = 400
        MacConfig['mapheight'] = 300
        MacConfig['middlelabel'] = 11
        MacConfig['middleradio'] = 10
        MacConfig['middlespin'] = 8
        MacConfig['middledrop'] = 6
        MacConfig['rightlabel'] = 5
        MacConfig['rightdrop'] = 2
        MacConfig['rightresult'] = 8
        return MacConfig
    else:
        WinConfig = dict()
        WinConfig['addrentry'] = 60
        WinConfig['gobutton'] = 4
        WinConfig['mapwidth'] = 400
        WinConfig['mapheight'] = 300
        WinConfig['middlelabel'] = 13
        WinConfig['middleradio'] = 9
        WinConfig['middlespin'] = 12
        WinConfig['middledrop'] = 7
        WinConfig['rightlabel'] = 6
        WinConfig['rightdrop'] = 2
        WinConfig['rightresult'] = 10
        return WinConfig
    
# initialize GUI
root = tk.Tk()
# bind enter key to search address
root.bind('<Return>', lambda event=None: button_search.invoke())
# not resizable
root.resizable(False, False)
# GUI title
root.title("IAC Degree Days/Hours Calculator")
# default padding
pad = 5
# load config for operating system
Config = config()

# left frame
frame_left = tk.Frame(root)

# search frame
frame_search = tk.Frame(frame_left)
# initialize address
Address = tk.StringVar()
Address.set("Packard Laboratory, Bethlehem, PA")
# address entry
entry_addr = tk.Entry(frame_search, textvariable=Address, width=Config['addrentry'])
entry_addr.pack(side='left')
# search button
button_search = tk.Button(frame_search, text ="Go", width=Config['gobutton'], command = search_address)
button_search.pack(side='right')
frame_search.pack(side='top')

# initialize map view
location = tkintermapview.convert_address_to_coordinates(Address.get())
global latitude, longitude
latitude = location[0]
longitude = location[1]
map_widget = tkintermapview.TkinterMapView(frame_left, width=Config['mapwidth'], height=Config['mapheight'], corner_radius=0)
map_widget.set_position(latitude , longitude)
map_widget.set_zoom(14)
# initialize marker
marker = map_widget.set_marker(latitude, longitude)
marker.set_text("{:.4f}, {:.4f}".format(latitude , longitude))
# add left click command
map_widget.add_left_click_map_command(update_marker)
map_widget.pack(side='bottom')

frame_left.pack(side='left')

# middle frame
frame_middle = tk.Frame(root)

# label column
tk.Label(frame_middle, text="Mode", width=Config['middlelabel'], anchor='w').grid(row=0, rowspan=2, column=0)
tk.Label(frame_middle, text="Method", width=Config['middlelabel'], anchor='w').grid(row=2, rowspan=2, column=0)
tk.Label(frame_middle, text="Temp. Unit", width=Config['middlelabel'], anchor='w').grid(row=4, rowspan=2, column=0)
tk.Label(frame_middle, text="Base Temp.", width=Config['middlelabel'], anchor='w').grid(row=6, column=0, pady=pad)
tk.Label(frame_middle, text="Setback Temp.", width=Config['middlelabel'], anchor='w').grid(row=7, column=0, pady=pad)
tk.Label(frame_middle, text="History", width=Config['middlelabel'], anchor='w').grid(row=8, column=0, pady=pad)

# mode radio button
radio_mode = tk.StringVar()
radio_mode.set("Cooling")
radiocool = tk.Radiobutton(frame_middle, text="Cooling", variable=radio_mode, value="Cooling", command=update_widget, width=Config['middleradio'], anchor='w')
radiocool.grid(row=0, column=1, pady=pad, sticky='w')
radioheat = tk.Radiobutton(frame_middle, text="Heating", variable=radio_mode, value="Heating", command=update_widget, width=Config['middleradio'], anchor='w')
radioheat.grid(row=1, column=1, pady=pad, sticky='w')

# type radio button
radio_type = tk.StringVar()
radio_type.set("Degree Hours")
radioday = tk.Radiobutton(frame_middle, text="Deg. Days", variable=radio_type, value="Degree Days", command=update_widget, width=Config['middleradio'], anchor='w')
radioday.grid(row=2, column=1, pady=pad, sticky='w')
radiohour = tk.Radiobutton(frame_middle, text="Deg. Hours", variable=radio_type, value="Degree Hours", command=update_widget, width=Config['middleradio'], anchor='w')
radiohour.grid(row=3, column=1, pady=pad, sticky='w')

# unit radio button
radio_unit = tk.StringVar()
radio_unit.set("Fahrenheit")
unit_backup = tk.StringVar()
unit_backup.set("Fahrenheit")
radiocool = tk.Radiobutton(frame_middle, text="Celsius", variable=radio_unit, value="Celsius", command=unit_conversion, width=Config['middleradio'], anchor='w')
radiocool.grid(row=4, column=1, pady=pad, sticky='w')
radioheat = tk.Radiobutton(frame_middle, text="Fahrenheit", variable=radio_unit, value="Fahrenheit", command=unit_conversion, width=Config['middleradio'], anchor='w')
radioheat.grid(row=5, column=1, pady=pad, sticky='w')

# temperature spinbox
spin_basetemp = tk.IntVar()
spin_basetemp.set(65)
spinbasetemp = tk.Spinbox(frame_middle, textvariable=spin_basetemp, width=Config['middlespin'])
spinbasetemp.config(from_=32, to=212)
spinbasetemp.grid(row=6, column=1, pady=pad, sticky='w')
spin_setback = tk.IntVar()
spin_setback.set(65)
spinsetback = tk.Spinbox(frame_middle, textvariable=spin_setback, width=Config['middlespin'])
spinsetback.config(from_=32, to=212)
spinsetback.grid(row=7, column=1, pady=pad, sticky='w')

# history optionmenu
manu_options = ["1 year","2 years","3 years","4 years","5 years"]
menu_selected = tk.StringVar()
menu_selected.set("4 years")
menu_history = tk.OptionMenu(frame_middle, menu_selected, *manu_options)
menu_history.config(width=Config['middledrop'], anchor='w') 
menu_history.grid(row=8, column=1, pady=pad, sticky='w')

frame_middle.pack(side='left', padx=pad, pady=pad)

# right frame
frame_right = tk.Frame(root)

# label column
tk.Label(frame_right, text="Thermostat Programming Schedule").grid(row=0, column=0, columnspan=8, pady=pad)
tk.Label(frame_right, text="Start", width=Config['rightlabel'], anchor='w').grid(row=2, column=0, pady=2*pad)
tk.Label(frame_right, text="End", width=Config['rightlabel'], anchor='w').grid(row=3, column=0, pady=2*pad)
tk.Label(frame_right, text="All-day", width=Config['rightlabel'], anchor='w').grid(row=4, column=0, pady=pad)
tk.Label(frame_right, text="Holiday", width=Config['rightlabel'], anchor='w').grid(row=5, column=0, pady=pad)

days=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
hours=list(range(0,25))
start_list = []
end_list = []
start_backup = []
end_backup = []
allday_list = []
holiday_list = []
for i in range(7):
    # Day label
    tk.Label(frame_right, text=days[i]).grid(row=1, column=i+1)

    # Start time entry
    start_var = tk.StringVar()
    start_var.set("9")
    start_list.append(start_var)
    start_backup_var = tk.StringVar()
    start_backup_var.set("9")
    start_backup.append(start_backup_var)
    dropdown_start = tk.OptionMenu(frame_right, start_var, *hours, command=opening_hours)
    dropdown_start.config(width=Config['rightdrop'])
    dropdown_start.grid(row=2, column=i+1)

    # End time entry
    end_var = tk.StringVar()
    end_var.set("17")
    end_list.append(end_var)
    end_backup_var = tk.StringVar()
    end_backup_var.set("17")
    end_backup.append(end_backup_var)
    dropdown_end = tk.OptionMenu(frame_right, end_var, *hours, command=closing_hours)
    dropdown_end.config(width=Config['rightdrop'])
    dropdown_end.grid(row=3, column=i+1)

    # all day check box
    allday_var = tk.IntVar()
    allday_list.append(allday_var)
    checkbox_allday = tk.Checkbutton(frame_right, variable=allday_var, command=check_hours)
    checkbox_allday.grid(row=4, column=i+1)

    # holiday check box
    holiday_var = tk.IntVar()
    holiday_list.append(holiday_var)
    checkbox_holiday = tk.Checkbutton(frame_right, variable=holiday_var, command=check_hours)
    checkbox_holiday.grid(row=5, column=i+1)

# calculate botton
button_calc = tk.Button(frame_right, text ="Calculate", width=Config['rightresult'], command = calculate)
button_calc.grid(row=6, column=1, columnspan=2, pady=3*pad)

# result label
resultlabel = tk.StringVar()
resultlabel.set("      Cooling Degree Hours:")
label_result = tk.Label(frame_right, textvariable = resultlabel)
label_result.grid(row=6, column=3, columnspan=3, pady=3*pad, sticky='w')

# result entry
resultdegree = tk.StringVar()
resultdegree.set(0)
entry_result = tk.Entry(frame_right, textvariable=resultdegree, width=Config['rightresult'], justify='right')
entry_result.config(fg="red", state='readonly', readonlybackground="white")
entry_result.grid(row=6, column=6, columnspan=2, pady=3*pad)

# map label
label_datasource = tk.Label(frame_right, text="Map Data: OpenStreetMap")
label_datasource.config(fg="blue", cursor="hand2")
# hyperlink to meteostat.net/en
label_datasource.bind("<Button-1>", lambda e: webbrowser.open_new_tab("https://www.openstreetmap.org"))
label_datasource.grid(row=7, column=1, columnspan=3)

# weather label
label_datasource = tk.Label(frame_right, text="Weather Data: Meteostat")
label_datasource.config(fg="blue", cursor="hand2")
# hyperlink to meteostat.net/en
label_datasource.bind("<Button-1>", lambda e: webbrowser.open_new_tab("https://meteostat.net/en"))
label_datasource.grid(row=7, column=4, columnspan=3)

# copyright label
label_copyright = tk.Label(frame_right, text="© 2023 Lehigh University Industrial Assessment Center")
label_copyright.config(fg="blue", cursor="hand2")
# hyperlink to iac.lehigh.edu
label_copyright.bind("<Button-1>", lambda e: webbrowser.open_new_tab("https://luiac.cc.lehigh.edu"))
label_copyright.grid(row=8, column=1, columnspan=6)

frame_right.pack(side='right', padx=pad, pady=pad)

# center the window
root.eval('tk::PlaceWindow . center')
root.mainloop()