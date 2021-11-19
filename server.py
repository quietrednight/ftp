import socket
import sys
import time
import os
import struct
import errno
print("\nWelcome to the FTP server.\nTo get started, connect a client.")
filepath = os.getcwd() + r'\files'
#print(filepath)
# Initialise socket stuff
TCP_PORT = 1456 # Just a random choice
BUFFER_SIZE = 1024 # Standard size
s=0
conn=0
addr=0

def initSocket():
    global s,conn,addr
    print('Listening Socket Connection......')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', TCP_PORT))
    s.listen(1)
    #print('Socket Connection request detected!~')
    conn, addr = s.accept()
    print("Connected to by address: {}".format(addr))

def upld():
    # Send message once server is ready to recieve file details
    conn.send(bytes("1",encoding='utf-8'))
    # Recieve file name length, then file name
    file_name_size = struct.unpack("h", conn.recv(2))[0]
    file_name = conn.recv(file_name_size)
    # Send message to let client know server is ready for document content
    conn.send(bytes("1",encoding='utf-8'))
    # Recieve file size
    file_name=filepath+'\\'+file_name.decode(encoding='utf-8')
    file_size = struct.unpack("i", conn.recv(4))[0]
    
    #judge whether file exists
    if(os.path.exists(file_name)):
        if(os.path.getsize(file_name)!=file_size):
            print("This file must be reuploaded\n")
            conn.send(bytes("1",encoding='utf-8'))
            conn.send(struct.pack("i", os.path.getsize(file_name)))
            # Initialise and enter loop to recive file content
            start_time = time.time()
            output_file = open(file_name, "ab")
            bytes_recieved = os.path.getsize(file_name)
            print("\nRecieving...")
            while bytes_recieved < file_size:
                l = conn.recv(BUFFER_SIZE)
                output_file.write(l)
                bytes_recieved += BUFFER_SIZE
                conn.send(bytes('1',encoding="utf-8"))
                conn.recv(BUFFER_SIZE)
            print("\nReuploading complete")
            output_file.close()
            print("\nRecieved file: {}".format(file_name))
            # Send upload performance details
            conn.send(struct.pack("f", time.time() - start_time))
            conn.send(struct.pack("i", file_size))
            #print("\nReuploading complete")
            return
        else: 
            conn.send(bytes("2",encoding='utf-8'))
            print("This file already exists\n")
            return
    else:
        conn.send(bytes("0",encoding='utf-8'))
        # Initialise and enter loop to recive file content
        start_time = time.time()
        output_file = open(file_name, "wb")
        # This keeps track of how many bytes we have recieved, so we know when to stop the loop
        bytes_recieved = 0
        print("\nRecieving...")
        while bytes_recieved < file_size:
            l = conn.recv(BUFFER_SIZE)
            output_file.write(l)
            bytes_recieved += BUFFER_SIZE
            conn.send(bytes('1',encoding="utf-8"))
            conn.recv(BUFFER_SIZE)
        output_file.close()
        print("\nRecieved file: {}".format(file_name))
        # Send upload performance details
        conn.send(struct.pack("f", time.time() - start_time))
        conn.send(struct.pack("i", file_size))
        print("\nReuploading complete")
        return


def list_files():
    print("Listing files...")
    # Get list of files in directory
    listing = os.listdir(filepath)
    # Send over the number of files, so the client knows what to expect (and avoid some errors)
    conn.send(struct.pack("i", len(listing)))
    total_directory_size = 0
    # Send over the file names and sizes whilst totaling the directory size
    for i in listing:
        #print(i)
        # File name size
        conn.send(struct.pack("i", sys.getsizeof(filepath+'\\'+i)))
        # File name
        conn.send(bytes(i,encoding="utf-8"))
        # File content size
        #for syncronising
        conn.recv(BUFFER_SIZE)
        conn.send(struct.pack("i", os.path.getsize(filepath+'\\'+i)))
        total_directory_size += os.path.getsize(filepath+'\\'+i)
        # Make sure that the client and server are syncronised
        conn.recv(BUFFER_SIZE)
    # Sum of file sizes in directory

    conn.send(struct.pack("i", total_directory_size))
    #Final check
    conn.recv(BUFFER_SIZE)

    print("Successfully sent file listing")
    return

def dwld():
    conn.send(bytes("1",encoding="utf-8"))
    file_name_length = struct.unpack("h", conn.recv(2))[0]
    #print (file_name_length)
    file_name = conn.recv(file_name_length)
    print(file_name.decode("utf-8"),'fileSize:=',file_name_length)
    file_name=file_name.decode('utf-8')
    #determine whether this file should be redownload
    if (os.path.exists(filepath+'\\'+file_name)):
        # Then the file exists, and send file size
        conn.send(struct.pack("i", os.path.getsize(filepath+'\\'+file_name)))
    else:
        # Then the file doesn't exist, and send error code
        print("File name not valid")
        conn.send(struct.pack("i", -1))
        return
    mark_file2=conn.recv(BUFFER_SIZE)
    if(mark_file2==b'1'):
        remain_size=struct.unpack("i",conn.recv(4))[0]
        file_name=filepath+'\\'+file_name
        #start_time = time.time()
        print("Resending file...")
        content = open(file_name, "rb")
        l = content.read(remain_size)
        l = content.read(BUFFER_SIZE)
        while l:
            conn.send(l)
            conn.recv(BUFFER_SIZE) #确认包
            l = content.read(BUFFER_SIZE)
        print('File transfer complete！')
        content.close()
        # Get client go-ahead, then send download details
        conn.recv(BUFFER_SIZE)
        #conn.send(struct.pack("f", time.time() - start_time))
        return
    elif(mark_file2==b'2'):
        print("This file has been downloaded.\n")
        return
    else:
        file_name=filepath+'\\'+file_name
        print("sending file...")
        content = open(file_name, "rb")
        l = content.read(BUFFER_SIZE)
        while l:
            conn.send(l)
            l = content.read(BUFFER_SIZE)
        print('File transfer complete！')
        content.close()
        # Get client go-ahead, then send download details
        conn.recv(BUFFER_SIZE)
        #conn.send(struct.pack("f", time.time() - start_time))
        return


def delf():
    # Send go-ahead
    conn.send(bytes("1",encoding='utf-8'))
    # Get file details
    file_name_length = struct.unpack("h", conn.recv(2))[0]
    file_name = conn.recv(file_name_length)
    # Check file exists
    file_name=filepath+'\\'+file_name.decode()
    if os.path.isfile(file_name):
        conn.send(struct.pack("i", 1))
    else:
        # Then the file doesn't exist
        conn.send(struct.pack("i", -1))
        return
    # Wait for deletion conformation
    confirm_delete = conn.recv(BUFFER_SIZE)
    confirm_delete=confirm_delete.decode(encoding='utf-8')
    print(confirm_delete)
    if confirm_delete == "Y":
        try:
            # Delete file
            os.remove(file_name)
            conn.send(struct.pack("i", 1))
        except:
            # Unable to delete file
            print("Failed to delete {}".format(file_name))
            conn.send(struct.pack("i", -1))
    else:
        # User abandoned deletion
        # The server probably recieved "N", but else used as a safety catch-all
        print("Delete abandoned by client!")
        return


def quit():
    # Send quit conformation
    conn.send(bytes("1",encoding="utf-8"))
    # Close and restart the server
    #conn.close()
    s.close()
    #os.execl(sys.executable, sys.executable, *sys.argv)
    return

if __name__ == '__main__':
    initSocket()
    while True:
        # Enter into a while loop to recieve commands from client
        try:
            print("\nWaiting for instruction~",end='\t')
            data = conn.recv(BUFFER_SIZE)
            print("Recieved instruction: {}".format(data))
            if data.decode("GBK") == '':
                print('Last Socket is corrupted!~')
                quit()
                initSocket()
            # Check the command and respond correctly
            if data == bytes("UPLD", encoding="utf-8"):
                print('Upload Files Request Committed~!')
                upld()
            elif data == bytes("LIST", encoding="utf-8"):
                list_files()
            elif data == bytes("DWLD",encoding="utf-8"):
                print("download file detected~")
                dwld()
            elif data == bytes("DELF",encoding="utf-8"):
                delf()
            elif data == bytes("QUIT",encoding="utf-8"):
                quit()
            # Reset the data to loop
            data = None
        except socket.error as e:
            if e.errno == errno.WSAECONNRESET:
                #quit()
                print(e)
                print('Socket Reset!~')
                initSocket()
            else:
                print(e)
                initSocket()

