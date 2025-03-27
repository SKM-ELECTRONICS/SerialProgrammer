import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import serial
import time
import subprocess
import os
import serial.tools.list_ports

global eol
eol = b'\n'
# Function to save data to a text file
def save_file(filename, data):
    try:
        with open(filename, 'w') as f:
            for line, delay in data:
                f.write(f"{line},{delay}\n")  # Save each line and its delay
        messagebox.showinfo("Success", f"File saved as {filename}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save file: {e}")


# Function to load data from a text file
def load_file(filename):
    try:
        with open(filename, 'r') as f:
            return [(line.split(',')[0].strip(), int(line.split(',')[1].strip())) for line in f.readlines()]
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load file: {e}")
        return None


# Function to send data over the COM port
def send_file_over_comport(data, comport, baudrate, delay_ms, source_file_name):
    try:
        # Open the COM port with the specified baud rate
        with serial.Serial(comport, baudrate, timeout=1) as ser:
            log_filename = f"logs/{source_file_name}_{time.strftime('%Y%m%d_%H%M%S')}_sent_log.txt"
            with open(log_filename, 'a') as log_file:
                # Send each string with its corresponding delay
                for string, delay in data:
                    byte_data = string.encode('utf-8')  # Convert the string to bytes
                    ser.write(byte_data + eol)  # Send data over COM port

                    # Wait for Arduino response (with 10ms timeout)
                    response = None
                    start_time = time.time()


                    while time.time() - start_time < 4:  # Wait for 100ms
                        if ser.in_waiting > 0:  # Check if there is data to read
                            response = ser.readline().decode('utf-8').strip()  # Read the response from Arduino
                            break  # Stop waiting if response is received

                    current_time = time.time()

                    # Convert to a struct_time (without milliseconds)
                    time_struct = time.localtime(current_time)

                    # Get the seconds and milliseconds separately
                    seconds = time.strftime("%Y-%m-%d %H:%M:%S", time_struct)
                    milliseconds = int((current_time - int(current_time)) * 1000)  # Get the milliseconds part

                    # Combine the timestamp and milliseconds
                    timestamp = f"{seconds}:{milliseconds:03d}"
                    if response:
                        log_file.write(f"{timestamp} - Sent: {string} | Delay: {delay} ms | Arduino Response: {response}\n")
                    else:
                        log_file.write(f"{timestamp} - Sent: {string} | Delay: {delay} ms | No Response\n")

                    # Add delay for the next string
                    time.sleep(delay / 1000)  # Delay between strings in seconds (converted from ms)

            messagebox.showinfo("Success", f"File data sent and logged successfully to {comport}!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send data: {e}")



# Function to test by echoing file content in a command prompt with delay
def test_file_transfer(data):
    try:
        # Create a temporary batch file to echo each string in the file
        temp_batch_file = "temp_echo.bat"
        with open(temp_batch_file, 'w') as f:
            for string, delay in data:
                f.write(f"echo {string}\n")  # Echo the string

                # Set the delay to at least 1 second if it's less than that
                delay_in_seconds = max(delay / 1000.0, 1)  # Ensure the delay is at least 1 second
                f.write(f"timeout /t {int(delay_in_seconds)}\n")  # Add delay (timeout in seconds)


        # Execute the batch file in the command prompt
        subprocess.run([temp_batch_file], shell=True)

        # Log the transfer in a separate file
        log_filename = "test_transfer_log.txt"  # Define the log file name for test
        with open(log_filename, 'a') as log_file:
            for string, delay in data:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                log_file.write(f"{timestamp} - Test Sent: {string} | Delay: {delay} ms\n")

        # Clean up the temporary batch file
        os.remove(temp_batch_file)

    except Exception as e:
        messagebox.showerror("Error", f"Test failed: {e}")



# Function to get the list of available COM ports
def get_available_com_ports():
    com_ports = [port.device for port in serial.tools.list_ports.comports()]
    return com_ports


# GUI application class
class SerialTransferApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SerialProgrammer")
        self.root.geometry("400x500")  # Adjusted window size

        # File data (list of tuples with string and delay)
        self.data = []

        # Labels
        self.file_label = tk.Label(root, text="No file loaded")
        self.file_label.grid(row=0, column=0, columnspan=2, pady=10)

        # COM port dropdown and baud rate
        self.comport_label = tk.Label(root, text="COM Port:")
        self.comport_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.comport_dropdown = ttk.Combobox(root, state="readonly")
        self.comport_dropdown.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        self.populate_com_ports()

        self.baudrate_label = tk.Label(root, text="Baud Rate:")
        self.baudrate_label.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.baudrate_entry = tk.Entry(root)
        self.baudrate_entry.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        # Load and Save file buttons
        self.load_button = tk.Button(root, text="Load File", command=self.load_file)
        self.load_button.grid(row=3, column=0, padx=10, pady=10, sticky="w")

        self.save_button = tk.Button(root, text="Save File", command=self.save_file)
        self.save_button.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        # String input and delay input
        self.string_label = tk.Label(root, text="String to send:")
        self.string_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.string_entry = tk.Entry(root)
        self.string_entry.grid(row=4, column=1, padx=10, pady=5, sticky="w")

        self.delay_label = tk.Label(root, text="Delay (ms):")
        self.delay_label.grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.delay_entry = tk.Entry(root)
        self.delay_entry.grid(row=5, column=1, padx=10, pady=5, sticky="w")

        # Add string button
        self.add_button = tk.Button(root, text="Add String", command=self.add_string)
        self.add_button.grid(row=6, column=0, padx=10, pady=10)

        # Listbox to show added strings
        self.string_listbox = tk.Listbox(root, width=50, height=10)
        self.string_listbox.grid(row=7, column=0, columnspan=2, padx=10, pady=10)

        # Send and Test buttons on the right side
        self.send_button = tk.Button(root, text="Send File", command=self.send_file)
        self.send_button.grid(row=8, column=0, padx=10, pady=10)

        self.test_button = tk.Button(root, text="Test File Transfer", command=self.test_file)
        self.test_button.grid(row=8, column=1, padx=10, pady=10)


    def populate_com_ports(self):
        # Get available COM ports
        com_ports = get_available_com_ports()
        self.comport_dropdown['values'] = com_ports
        if com_ports:
            self.comport_dropdown.current(0)  # Set default to the first available COM port

    def load_file(self):
        filepath = filedialog.askopenfilename(title="Select a File",
                                              filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if filepath:
            self.data = load_file(filepath)
            self.file_label.config(text=f"Loaded: {filepath}")
            self.update_listbox()

    def save_file(self):
        if self.data:
            filename = filedialog.asksaveasfilename(defaultextension=".txt",
                                                    filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
            if filename:
                save_file(filename, self.data)
        else:
            messagebox.showwarning("No data", "Please add data before saving.")

    def send_file(self):
        if not self.data:
            messagebox.showwarning("No data", "Please add strings before sending.")
            return

        # Check if the COM port and baud rate are provided
        comport = self.comport_dropdown.get()
        baudrate = self.baudrate_entry.get()
        delay_ms = self.delay_entry.get()

        if not comport or not baudrate:
            messagebox.showerror("Error", "Please specify a COM port and baud rate.")
            return

        try:
            baudrate = int(baudrate)
            if not delay_ms:  # Check if delay field is empty
                delay_ms = 0  # Default to 0 if no delay is provided
            else:
                delay_ms = int(delay_ms)
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for baud rate and delay.")
            return

        # Get the source file name from the label text (just the file name, not the full path)
        source_file_name = os.path.basename(self.file_label.cget('text').replace("Loaded: ", "")) if hasattr(self,
                                                                                                             'file_label') and self.file_label.cget(
            'text') != "No file loaded" else "unknown_file"

        # Proceed with sending the file if all checks pass
        print(f"Starting to send file: {source_file_name}")  # Debugging line to confirm the button is clicked only once

        send_file_over_comport(self.data, comport, baudrate, delay_ms, source_file_name)  # Only call once

    def add_string(self):
        string = self.string_entry.get()
        delay = self.delay_entry.get()

        if not string or not delay:
            messagebox.showerror("Error", "Please enter both string and delay.")
            return

        try:
            delay = int(delay)
        except ValueError:
            messagebox.showerror("Error", "Delay must be a valid number.")
            return

        self.data.append((string, delay))
        self.update_listbox()
        self.string_entry.delete(0, tk.END)
        self.delay_entry.delete(0, tk.END)

    def update_listbox(self):
        # Clear the listbox and show the data
        self.string_listbox.delete(0, tk.END)
        for string, delay in self.data:
            self.string_listbox.insert(tk.END, f"String: {string} | Delay: {delay} ms")

    def test_file(self):
        if self.data:
            test_file_transfer(self.data)
        else:
            messagebox.showwarning("No data", "Please add strings before testing.")


# Main function to run the GUI
def main():
    root = tk.Tk()
    app = SerialTransferApp(root)
    root.mainloop()


# Run the application
if __name__ == "__main__":
    main()