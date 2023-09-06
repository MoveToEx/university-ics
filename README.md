# DLMU-ics

Generate ics from DLMU system.  

## Installation

```sh
git clone https://github.com/MoveToEx/DLMU-ics
cd DLMU-ics
pip install -r requirements.txt
```

## Usage

~~Before running Python, open your browser and login to [DLMU](http://jw.xpaas.dlmu.edu.cn/eams/homeExt.action).~~  
~~Then run the script in the following format:~~
~~where YYYY/MM/DD specifies the first Monday of the current semester.  ~~

I'm happy to announce that this script is now capable of simulating the login process by sending requests and collect date-related information using responses.  
All you need to do is to start this script and enter your id and password.  

After the script prints `success` on the console, find `output.ics` in the repo directory.  

## Disclaimer


Besides, it's unknown whether we have fully implemented every function of DLMU system, so make sure to check the ics file according to DLMU system.  
We do not take responsibilities for any outcomes of using this program.  
Using this program means that you have understood possible consequences.

## To-Do

- [ ] Full geo location support
- [x] Auto date alignment
