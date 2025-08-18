# Paper_Reference_Check_Helper
This is an effective and light-flash assistant for checking the references and rapidly finding out problems in your papers with just uploading .bib and .tex file of the paper, which can provide great help when you are writing papers agonizingly, especially the literature review. 

# Note when using
You can either pack the program to an .exe file or directly use it by running main_GUI.py in Python. For a flasher use in format of .exe file, remember to use Pyinstaller (my python version is 3.9) to process the main body of the program (not including the .spec file. It is just an instance for my Pyinstaller using record) and then find your .exe in \dist folder after it completes. An example of CLI operation is as follows: "pyinstaller --onefile --windowed --icon="app_icon.ico" --add-data "ref_checker_logic.py;." --add-data "icon.png;." --collect-all "pybtex" main_gui.py".

# Future
This work is supporting just by myself and Gemini (you know). I don't know if I have enough time to improve it. For cooperation, My QQ is 1665395842.
