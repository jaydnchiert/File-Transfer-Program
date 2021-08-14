import tkinter
import tkinter.filedialog
import tkinter.ttk
import socket
import os
import threading


#Defines socket variables
hostname = socket.gethostname()
IP = socket.gethostbyname(hostname)
PORT = 32561
Headerlength = 10
server = False

#Defines username
username = "" #local username
user = "" #connected person's username

#Setup window
root = tkinter.Tk()
root.title("Blue File - Send files to any computer on the same network.")
root.geometry("600x150")
root.resizable(False, False)


def get_username(number):
	
	global username
	username = username_entry.get()

	if len(username) > Headerlength:
		too_short.pack_forget()
		too_long.pack()
		return False

	if len(username) == 0:
		too_long.pack_forget()
		too_short.pack()
		return False

	switch(number)


def send_username():
	#send username
	client_socket.send(bytes(username, "utf-8"))

	#recieve username
	global user
	user = client_socket.recv(10).decode().strip()


def switch(number):

	#delete everything in the root window
	for frames in root.winfo_children():
		frames.destroy()

	#call page number functions (switch page)
	number()


def close_connection(mode):
	try:
		client_socket.shutdown(socket.SHUT_RDWR)
	except:
		pass
	mode.close()


def cancel(mode):
	close_connection(mode)
	switch(page_1)


def exit(mode):
	close_connection(mode)
	root.destroy()


def remove_messages():
	for messages in bottom_frame.grid_slaves(column = 1, row = 2):
		messages.grid_forget()


def change_recieve():
	global recieve_clicked
	recieve_clicked = True


def finish_recieve():
	global recieving
	recieving = False

	global recieve_clicked
	recieve_clicked = False


def change_port():
	global PORT

	#check if port is an integer
	try:
		PORT = int(advanced_entry.get())

		#check if port is a valid number
		if 1024 <= PORT <= 65535:
			advanced_window.destroy()
		else:
			port_error.grid(column = 0, row = 2, columnspan = 3)
			return False

	#if port is not an integer display error
	except:
		port_error.grid(column = 0, row = 2, columnspan = 3)
		return False


def open_file():

	#open file browser
	file = tkinter.filedialog.askopenfilename(initialdir = "", title = "Select a file")
	#insert file directory into the file entry field
	file_entry.delete(0, 'end')
	file_entry.insert(0, file)


def background_server(server_setup):
	th = threading.Thread(target = server_setup)
	th.start()


def background_recieve(recieve_data):
	th2 = threading.Thread(target = recieve_data)
	th2.start()


def background_send(send_data):
	th3 = threading.Thread(target = send_data)
	th3.start()


def server_setup():

	try:
		#setup server
		global server_socket
		server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #IPV4, TCP
		server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #allows socket to reuse address

		server_socket.bind((IP, PORT)) #binds IP and PORT

		#Establish connection to client
		server_socket.listen() #listens for incoming connections

		global client_socket
		client_socket, client_address = server_socket.accept() #allow for incoming connections

		server = True
	except:
		return False

	send_username()
	switch(page_3)


def client_setup():

	#get IP from enter_ip entry
	IP = enter_ip.get()

	try:
		#setup client
		global client_socket
		client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #setup socket
		client_socket.connect((IP, PORT)) #connect to server
	except:
		connection_error.grid(column = 1, row = 1)
		return False

	send_username()
	switch(page_3)


def recieve_data():

	global recieving
	recieving = False

	global recieve_clicked
	recieve_clicked = False

	file_name = ""
	
	#recieves data in sets of 16bytes until all has been recieved.
	data = bytes()

	Header = client_socket.recv(4096) #recieve header

	recieving = True

	while recieving == True:
		recieve_button.config(state = "normal")

		while recieve_clicked == True:
			recieve_button.config(state = "disabled")

			file_split = str(Header).partition(":") #splits file into 3 sections; name, size, file

			file_name = str(file_split[0]) #gets file name from split

			#convert header to integer by taking the 2nd file split up to the headerlength
			file_size = int(file_split[2][:Headerlength])

			#displays loading bar and sets the size to the file_size-4096
			remove_messages()
			loading_bar.grid(column = 1, row = 2)
			loading_bar["maximum"] = file_size-4096

			#Data = Header - file name - headerlength - 1 (gets rid of b' in file name)
			data = Header[(len(file_name)+Headerlength-1):]

			#removes b' from file name
			file_name = file_name[2:]

			while True:
				if len(data) == file_size: #continue recieving data until the length is the same length as file_size
					finish_recieve()
					break
				
				else:
					new_data = client_socket.recv(4096) #recieve next set of data

					#adds 4096 to the loading bars
					loading_bar["value"] += 4096
					loading_bar.update()

					#add data onto the data variable
					data += new_data

	new_file = open(file_name, "wb") #create a new file with input name

	new_file.write(data) #write to file
	new_file.close() #close file

	#ensure no other feedback messages are showing
	remove_messages()

	#show "file saved"
	saved_file.grid(column = 1, row = 2)


def send_data():

	path = file_entry.get()

	try:
		files = open(path, "rb") #opens the file as read and write

	except FileNotFoundError:
		#ensure no feedback messages show
		for messages in bottom_frame.grid_slaves(column = 1, row = 2):
			messages.grid_forget()

		#show "cannot find file"
		file_error.grid(column = 1, row = 2)
		return False

	file_size = os.path.getsize(path) #obtains file size

	if file_size <= 9999999999:

		#ensures no feedback messages show
		remove_messages()
		#prints "file sending..."
		file_sending.grid(column = 1, row = 2)

		file_name = os.path.basename(path) #gets file name with extension

		data = files.read(file_size) #reads file

		full_send = bytes(f"{file_name}:{file_size:<{Headerlength}}", "utf-8") + data #file size is sent as a string and left aligned as part of the header
		#sends file
		client_socket.send(full_send)

		files.close()

		#ensure there are no feedback messages showing
		remove_messages()
		#show "file sent"
		sent.grid(column = 1, row = 2)

	else:
		#ensure no feedback messages are showing
		remove_messages()
		#show "file too big"
		file_too_big.grid(column = 1, row = 2)
		return False


def page_user():

	#create invisible frames
	top_frame = tkinter.Frame(root)
	top_frame.place(relx = 0, rely = 0, relwidth = 1, relheight = 1)

	bottom_frame = tkinter.Frame(root)
	bottom_frame.place(relx = 0, rely = 0.6, relwidth = 1, relheight = 1)

	#create visible widgets
	username_text = tkinter.Label(top_frame, text = "Enter Username:", font = ("", 12))
	username_text.grid(column = 0, row = 0, padx = 53, pady = 60)

	global username_entry
	username_entry = tkinter.Entry(top_frame, width = 15, font = ("", 12))
	username_entry.grid(column = 1, row = 0)

	confirm_button = tkinter.Button(top_frame, text = "Confirm", font = ("", 12), padx = 15, command = lambda: get_username(page_1))
	confirm_button.grid(column = 2, row = 0, padx = 50)

	#create feedback labels
	global too_long
	too_long = tkinter.Label(bottom_frame, text = "Error: Username is too long.", fg = "red")

	global too_short
	too_short = tkinter.Label(bottom_frame, text = "Error: Username is too short.", fg = "red")

def page_1():

	#create invisible frames
	top_frame = tkinter.Frame(root)
	top_frame.place(relx = 0, rely = 0, relwidth = 1, relheight= 1)

	left_frame = tkinter.Frame(root)
	left_frame.place(relx = 0, rely = 0.3, relwidth = 0.5, relheight = 1)

	right_frame = tkinter.Frame(root)
	right_frame.place(relx = 0.5, rely = 0.3, relwidth = 0.5, relheight = 1)

	#Create visible widgets
	title = tkinter.Label(top_frame, text = "Start Connection", font = ("", 16))
	title.grid(column = 1, row = 0, padx = 115)

	advanced = tkinter.Button(top_frame, text = "Advanced...", font = ("", 8), command = page_changeport)
	advanced.grid(column = 0, row = 0, padx = 20)

	host_button = tkinter.Button(left_frame, text = "Host", font = ("", 12), padx = 40, command = lambda: switch(page_2a))
	host_button.pack()

	host_text = tkinter.Label(left_frame, text = "Allow other's to connect using \nyour IP address.", font = ("", 10))
	host_text.pack(pady = 15)

	join_button = tkinter.Button(right_frame, text = "Join", font = ("", 12), padx = 40, command = lambda: switch(page_2b))
	join_button.pack()

	join_text = tkinter.Label(right_frame, text = "Connect to someone else on your \nnetwork using their IP address.", font = ("", 10))
	join_text.pack(pady = 15)


def page_2a():

	#create invisible frames
	top_frame = tkinter.Frame(root)
	top_frame.place(relx = 0, rely = 0, relwidth = 1, relheight = 1)

	bottom_frame = tkinter.Frame(root)
	bottom_frame.place(relx = 0, rely= 0.3, relwidth = 1, relheight = 1)

	#create visible widgets
	title = tkinter.Label(top_frame, text = "Host Connection", font = ("", 16))
	title.pack()

	waiting = tkinter.Label(bottom_frame, text = "Waiting for incoming connection...", font = ("", 12, "italic"))
	waiting.grid(column = 1, row = 0)

	cancel_button = tkinter.Button(bottom_frame, text = "Cancel", font = ("", 12), padx = 20, command = lambda: cancel(server_socket))
	cancel_button.grid(column = 0, row = 1, padx = 20, pady = 35)

	ip_text = tkinter.Label(bottom_frame, text = f"Your IP address is: {IP}", font = ("", 10))
	ip_text.grid(column = 1, row = 1)

	background_server(server_setup)
	root.protocol("WM_DELETE_WINDOW", lambda: exit(server_socket))


def page_2b():

	#create invisible frames
	top_frame = tkinter.Frame(root)
	top_frame.place(relx = 0, rely = 0, relwidth = 1, relheight = 1)

	middle_frame = tkinter.Frame(root)
	middle_frame.place(relx = 0, rely= 0.3, relwidth = 1, relheight = 1)

	bottom_frame = tkinter.Frame(root)
	bottom_frame.place(relx = 0, rely = 0.7, relwidth = 1, relheight = 1)

	#Create visible widgets
	title = tkinter.Label(top_frame, text = "Join Connection", font = ("", 16))
	title.pack()

	enter_text = tkinter.Label(middle_frame, text = "Enter IP address here:", font = ("", 12))
	enter_text.grid(column = 0, row = 0, padx = 25)

	global enter_ip
	enter_ip = tkinter.Entry(middle_frame, width = 20, font = ("", 12))
	enter_ip.grid(column = 1, row = 0)

	join_button = tkinter.Button(middle_frame, text = "Join", font = ("", 12), padx = 40, command = client_setup)
	join_button.grid(column = 3, row = 0, padx = 25)

	cancel_button = tkinter.Button(bottom_frame, text = "Cancel", font = ("", 12), padx = 20, command = lambda: switch(page_1))
	cancel_button.grid(column = 0, row = 0, padx = 20, sticky = "nw")

	help_text = tkinter.Label(bottom_frame, text = "The host's IP address will be displayed on their screen.")
	help_text.grid(column = 1, row = 0, columnspan = 3, pady = 15)

	#create feedback Labels
	global connection_error
	connection_error = tkinter.Label(middle_frame, text = "Error: Cannot connect to given IP.", fg = "red")

def page_changeport():

	#create window
	global advanced_window
	advanced_window = tkinter.Toplevel(root)
	advanced_window.geometry("260x80")
	advanced_window.resizable(False,False)

	#add visible widgets
	advanced_text = tkinter.Label(advanced_window, text = "Port:")
	advanced_text.grid(column = 0, row = 0, padx = 15, pady = 10)

	global advanced_entry
	advanced_entry = tkinter.Entry(advanced_window, width = 10)
	advanced_entry.grid(column = 1, row = 0)
	advanced_entry.insert(0, PORT)

	advanced_button = tkinter.Button(advanced_window, text = "confirm", padx = 10, command = change_port)
	advanced_button.grid(column = 2, row = 0, padx = 15)

	default_text = tkinter.Label(advanced_window, text = "Default is port is 32561.", fg = "grey")
	default_text.grid(column = 0, row = 1, columnspan = 3)

	#create feedback labels
	global port_error
	port_error = tkinter.Label(advanced_window, text = "Error: Port must be between 1024 - 65535.", fg = "red")


def page_3():

	#create invisible frames
	top_frame = tkinter.Frame(root)
	top_frame.place(relx = 0, rely = 0, relwidth = 1, relheight = 1)

	global bottom_frame
	bottom_frame = tkinter.Frame(root)
	bottom_frame.place(relx = 0, rely= 0.3, relwidth = 1, relheight = 1)

	title = tkinter.Label(top_frame, text = f"Connected to {user}", font = ("", 16))
	title.pack()

	#create visible widgets
	file_text = tkinter.Label(bottom_frame, text = "Choose file:", font = ("", 12))
	file_text.grid(column = 0, row = 0, padx = 25)

	global file_entry
	file_entry = tkinter.Entry(bottom_frame, width = 45, font = ("", 10))
	file_entry.grid(column = 1, row = 0)

	file_browse = tkinter.Button(bottom_frame, text = "Browse...", font = ("", 12), command = open_file)
	file_browse.grid(column = 2, row = 0, padx = 25)

	send_button = tkinter.Button(bottom_frame, text = "Send", font = ("", 12), padx = 20, command = lambda: background_send(send_data))
	send_button.grid(column = 2, row = 3, pady = 6)

	global recieve_button
	recieve_button = tkinter.Button(bottom_frame, text = "Recieve", font = ("", 12), padx = 20, state = "disabled", command = change_recieve)
	recieve_button.grid(column = 1, row = 3)

	cancel_button = tkinter.Button(bottom_frame, text = "Cancel", font = ("", 12), padx = 20)
	cancel_button.grid(column = 0, row = 3, pady = 8)

	#default message
	global send_recieve
	send_recieve = tkinter.Label(bottom_frame, text = "Send or recieve a file.")
	send_recieve.grid(column = 1, row = 2)

	#create feedback messages
	global file_too_big
	file_too_big = tkinter.Label(bottom_frame, text = "Error: File must be under 10gb.", fg = "red")

	global file_error
	file_error = tkinter.Label(bottom_frame, text = "Error: Cannot locate file.", fg = "red")

	global sent
	sent = tkinter.Label(bottom_frame, text = "File sent!", fg = "green")

	global saved_file
	saved_file = tkinter.Label(bottom_frame, text = "File saved!", fg = "green")

	global file_sending
	file_sending = tkinter.Label(bottom_frame, text = "File sending...")

	#create loading bar
	global loading_bar
	loading_bar = tkinter.ttk.Progressbar(bottom_frame, orient = "horizontal", length = 286, mode = "determinate")

	#tests if the server is running in this instance
	if server == True:
		#if server is running, cancel and exit buttons will work in server mode
		root.protocol("WM_DELETE_WINDOW", lambda: exit(server_socket))
		cancel_button.config(command = lambda: cancel(server_socket))

	else:
		#if server is NOT running, cancel and exit buttons will work in client mode
		root.protocol("WM_DELETE_WINDOW", lambda: exit(client_socket))
		cancel_button.config(command = lambda: cancel(client_socket))

	background_recieve(recieve_data)


page_user()
root.mainloop()